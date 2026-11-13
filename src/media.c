/* SPDX-License-Identifier: LGPL-2.1-or-later
 *
 * Adapted from FFmpeg 7.1's fftools. See THIRD_PARTY_NOTICES.md and
 * LICENSES/FFmpeg-LGPL-2.1-or-later.txt for the upstream notice and licence.
 * Modified for Neuronte: one video stream, a reusable decoding API and a
 * bounded frame queue; unsupported command behaviours are declined.
 *
 * In-process video decoding with the frames of the FFmpeg 7.1 command line.
 *
 * Each step below names the fftools function it reproduces (ffmpeg_demux.c,
 * ffmpeg_dec.c, ffmpeg_filter.c, ffmpeg_mux_init.c of FFmpeg 7.1) for the
 * command in neuronte_media.h. The libraries do the decoding, filtering and
 * scaling; this file repeats the command's own decisions around them: the
 * seek point and timestamp offset, packet and frame timestamps, the filter
 * graph it builds and rebuilds, and the constant frame rate of rawvideo
 * output. A new decoder opens and probes the input again, as a new process
 * would, so its frames never depend on what an earlier one read.
 */
#define _POSIX_C_SOURCE 200809L
#include "neuronte_media.h"

#include <libavcodec/avcodec.h>
#include <libavfilter/avfilter.h>
#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>
#include <libavformat/avformat.h>
#include <libavutil/avstring.h>
#include <libavutil/bprint.h>
#include <libavutil/display.h>
#include <libavutil/intreadwrite.h>
#include <libavutil/mathematics.h>
#include <libavutil/opt.h>
#include <libavutil/parseutils.h>
#include <libavutil/pixdesc.h>
#include <libavutil/time.h>

#include <math.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* The command's behaviour reproduced here is FFmpeg 7.1's; other library
 * versions are declined at run time so the command is used instead. */
#if LIBAVFORMAT_VERSION_MAJOR != 61 || LIBAVFORMAT_VERSION_MINOR < 7 || \
    LIBAVCODEC_VERSION_MAJOR != 61 || LIBAVCODEC_VERSION_MINOR < 19 || \
    LIBAVFILTER_VERSION_MAJOR != 10 || LIBAVFILTER_VERSION_MINOR < 4 || \
    LIBAVUTIL_VERSION_MAJOR != 59 || LIBAVUTIL_VERSION_MINOR < 39
#error "src/media.c reproduces FFmpeg 7.1 and needs its headers"
#endif

#define QUEUE 3                         /* decoded frames ahead of the reader */

/* ffmpeg_opt.c defaults */
static const float dts_error_threshold = 3600 * 30;

struct neuronte_media {
    /* Input (ffmpeg_demux.c) */
    AVFormatContext *ic;
    AVStream *st;
    int64_t ts_offset;                  /* AV_TIME_BASE units */
    int wrap_correction_done, saw_first_ts;
    int64_t first_dts, dts, next_dts;   /* AV_TIME_BASE units */
    const AVCodecDescriptor *codec_desc;
    int vscfr;                          /* VSYNC_VSCFR rather than VSYNC_CFR */

    /* Decoder (ffmpeg_dec.c) */
    AVCodecContext *dec;
    int apply_cropping;
    AVRational sar_override, framerate_in;
    int64_t last_frame_pts, last_frame_duration_est;
    AVRational last_frame_tb;
    uint64_t frames_decoded, decode_errors;
    int preroll;                       /* discard non-reference pictures only before a seek */

    /* Filter graph (ffmpeg_filter.c) */
    char *filters;
    char threads[16];
    enum AVPixelFormat format;
    AVFilterGraph *graph;
    AVFilterContext *source, *sink;
    int in_format, in_width, in_height;
    enum AVColorSpace in_space;
    enum AVColorRange in_range;
    AVRational in_tb, in_sar, guessed_rate;
    int32_t matrix[9];
    int matrix_present;
    unsigned crop_top, crop_bottom, crop_left, crop_right;
    int crop;
    int configured;                     /* the first graph fixed the output */
    int out_width, out_height;
    enum AVColorSpace out_space;
    enum AVColorRange out_range;

    /* Constant-rate output (video_sync_process, fg_output_frame) */
    AVRational tb_out, framerate;
    int tb_out_locked;
    int64_t next_pts, frame_number, frames_prev_hist[3];
    AVFrame *last_frame, *filtered;
    int last_dropped, got_frame, eof_out;

    /* The decoding thread and the frames it has ready */
    pthread_t thread;
    int thread_started;
    pthread_mutex_t lock;
    pthread_cond_t changed;
    AVFrame *queue[QUEUE];
    int head, count;
    atomic_int stop;
    int finished, failed;
    AVFrame *current;
    int64_t delivered;
    char message[1024];
};

/* -v error: the command prints error lines and nothing else. They are kept
 * here instead, for the caller to report as it would report the command's. */
static pthread_mutex_t log_lock = PTHREAD_MUTEX_INITIALIZER;
static char log_text[1024];

static void log_callback(void *avcl, int level, const char *fmt, va_list vl)
{
    char line[512];
    int prefix = 1;
    if (level > AV_LOG_ERROR)
        return;
    av_log_format_line2(avcl, level, fmt, vl, line, sizeof line, &prefix);
    pthread_mutex_lock(&log_lock);
    size_t have = strlen(log_text), add = strlen(line);
    if (add >= sizeof log_text)
        have = 0, add = sizeof log_text - 1;
    if (have + add >= sizeof log_text) {
        size_t drop = have + add - (sizeof log_text - 1);
        memmove(log_text, log_text + drop, have - drop + 1);
        have -= drop;
    }
    memcpy(log_text + have, line + strlen(line) - add, add + 1);
    pthread_mutex_unlock(&log_lock);
}

static pthread_once_t log_once = PTHREAD_ONCE_INIT;
static void log_install(void) { av_log_set_callback(log_callback); }

static void set_message(neuronte_media *m, const char *what, int err)
{
    char reason[AV_ERROR_MAX_STRING_SIZE] = "";
    if (err)
        av_strerror(err, reason, sizeof reason);
    pthread_mutex_lock(&log_lock);
    av_strlcpy(m->message, log_text, sizeof m->message);
    pthread_mutex_unlock(&log_lock);
    if (what) {
        av_strlcat(m->message, what, sizeof m->message);
        if (err) {
            av_strlcat(m->message, ": ", sizeof m->message);
            av_strlcat(m->message, reason, sizeof m->message);
        }
    }
    size_t n = strlen(m->message);
    while (n && (m->message[n - 1] == '\n' || m->message[n - 1] == ' '))
        m->message[--n] = 0;
}

static int stopped(neuronte_media *m) { return atomic_load(&m->stop); }
static int interrupted(void *opaque) { return stopped(opaque); }

/* get_format: the first software format. */
static enum AVPixelFormat get_format(AVCodecContext *s, const enum AVPixelFormat *formats)
{
    const enum AVPixelFormat *p;
    (void)s;
    for (p = formats; *p != AV_PIX_FMT_NONE; p++)
        if (!(av_pix_fmt_desc_get(*p)->flags & AV_PIX_FMT_FLAG_HWACCEL))
            break;
    return *p;
}

/* mid_pred from libavutil/mathops.h */
static int64_t mid_pred(int64_t a, int64_t b, int64_t c)
{
    if (a > b) {
        if (c > b) b = c > a ? a : c;
    } else if (b > c) {
        b = c > a ? c : a;
    }
    return b;
}

/* cmdutils.c get_rotation, including its NaN for an all-zero matrix */
static double get_rotation(const int32_t *matrix)
{
    double theta = -round(av_display_rotation_get(matrix));
    theta -= 360 * floor(theta / 360 + 0.9 / 360);
    return theta;
}

/* ffmpeg_demux.c ts_fixup, ts_discontinuity_detect (formats without
 * AVFMT_TS_DISCONT) and ist_dts_update, for the one decoded stream. The
 * wrap correction starts from the input's start time, which is what
 * ffmpeg_opt.c correct_input_start_times leaves for these formats. */
static void ts_fixup(neuronte_media *m, AVPacket *pkt)
{
    AVStream *st = m->st;
    const AVCodecParameters *par = st->codecpar;
    const int64_t start_time = m->ic->start_time;
    pkt->time_base = st->time_base;

    if (!m->wrap_correction_done && start_time != AV_NOPTS_VALUE && st->pts_wrap_bits < 64) {
        int64_t stime = av_rescale_q(start_time, AV_TIME_BASE_Q, pkt->time_base);
        int64_t stime2 = stime + (1ULL << st->pts_wrap_bits);
        m->wrap_correction_done = 1;
        if (stime2 > stime && pkt->dts != AV_NOPTS_VALUE &&
            pkt->dts > stime + (1LL << (st->pts_wrap_bits - 1))) {
            pkt->dts -= 1ULL << st->pts_wrap_bits;
            m->wrap_correction_done = 0;
        }
        if (stime2 > stime && pkt->pts != AV_NOPTS_VALUE &&
            pkt->pts > stime + (1LL << (st->pts_wrap_bits - 1))) {
            pkt->pts -= 1ULL << st->pts_wrap_bits;
            m->wrap_correction_done = 0;
        }
    }
    if (pkt->dts != AV_NOPTS_VALUE)
        pkt->dts += av_rescale_q(m->ts_offset, AV_TIME_BASE_Q, pkt->time_base);
    if (pkt->pts != AV_NOPTS_VALUE)
        pkt->pts += av_rescale_q(m->ts_offset, AV_TIME_BASE_Q, pkt->time_base);
    /* ts_scale 1.0: the command multiplies through a double */
    if (pkt->pts != AV_NOPTS_VALUE)
        pkt->pts = (int64_t)(pkt->pts * 1.0);
    if (pkt->dts != AV_NOPTS_VALUE)
        pkt->dts = (int64_t)(pkt->dts * 1.0);

    if (pkt->dts != AV_NOPTS_VALUE && m->next_dts != AV_NOPTS_VALUE) {
        int64_t pkt_dts = av_rescale_q_rnd(pkt->dts, pkt->time_base, AV_TIME_BASE_Q,
                                           AV_ROUND_NEAR_INF | AV_ROUND_PASS_MINMAX);
        int64_t delta = pkt_dts - m->next_dts;
        if (llabs(delta) > 1LL * dts_error_threshold * AV_TIME_BASE)
            pkt->dts = AV_NOPTS_VALUE;
        if (pkt->pts != AV_NOPTS_VALUE) {
            int64_t pkt_pts = av_rescale_q(pkt->pts, pkt->time_base, AV_TIME_BASE_Q);
            delta = pkt_pts - m->next_dts;
            if (llabs(delta) > 1LL * dts_error_threshold * AV_TIME_BASE)
                pkt->pts = AV_NOPTS_VALUE;
        }
    }

    if (!m->saw_first_ts) {
        m->first_dts = m->dts = st->avg_frame_rate.num ?
            -par->video_delay * AV_TIME_BASE / av_q2d(st->avg_frame_rate) : 0;
        if (pkt->pts != AV_NOPTS_VALUE) {
            m->first_dts = m->dts += av_rescale_q(pkt->pts, pkt->time_base, AV_TIME_BASE_Q);
        }
        m->saw_first_ts = 1;
    }
    if (m->next_dts == AV_NOPTS_VALUE)
        m->next_dts = m->dts;
    if (pkt->dts != AV_NOPTS_VALUE)
        m->next_dts = m->dts = av_rescale_q(pkt->dts, pkt->time_base, AV_TIME_BASE_Q);
    m->dts = m->next_dts;
    if (pkt->duration) {
        m->next_dts += av_rescale_q(pkt->duration, pkt->time_base, AV_TIME_BASE_Q);
    } else if (par->framerate.num != 0) {
        AVRational field_rate = av_mul_q(par->framerate, (AVRational){ 2, 1 });
        int fields = 2;
        AVCodecParserContext *parser = av_stream_get_parser(st);
        if (m->codec_desc && (m->codec_desc->props & AV_CODEC_PROP_FIELDS) && parser)
            fields = 1 + parser->repeat_pict;
        m->next_dts += av_rescale_q(fields, av_inv_q(field_rate), AV_TIME_BASE_Q);
    }
}

/* ffmpeg_dec.c video_duration_estimate, with reliable timestamps and no
 * forced input rate. */
static int64_t duration_estimate(const neuronte_media *m, const AVFrame *frame)
{
    int64_t codec_duration = 0;
    const int64_t ts_diff = frame->pts != AV_NOPTS_VALUE && m->last_frame_pts != AV_NOPTS_VALUE ?
                            frame->pts - m->last_frame_pts : -1;
    const int duration_unreliable = frame->duration == 1 && ts_diff > 2 * frame->duration;
    if (frame->duration > 0 && !duration_unreliable)
        return frame->duration;
    if (m->dec->framerate.den && m->dec->framerate.num) {
        int fields = frame->repeat_pict + 2;
        AVRational field_rate = av_mul_q(m->dec->framerate, (AVRational){ 2, 1 });
        codec_duration = av_rescale_q(fields, av_inv_q(field_rate), frame->time_base);
    }
    if (ts_diff > 0)
        return ts_diff;
    if (frame->duration > 0)
        return frame->duration;
    if (codec_duration > 0)
        return codec_duration;
    if (m->framerate_in.num && m->framerate_in.den) {
        int64_t d = av_rescale_q(1, av_inv_q(m->framerate_in), frame->time_base);
        if (d > 0)
            return d;
    }
    return FFMAX(m->last_frame_duration_est, 1);
}

/* Hands one output frame to the reader, waiting while the queue is full. */
static int deliver(neuronte_media *m, const AVFrame *frame, int64_t pts)
{
    AVFrame *ref = av_frame_clone(frame);
    if (!ref)
        return AVERROR(ENOMEM);
    ref->pts = pts;
    pthread_mutex_lock(&m->lock);
    while (m->count == QUEUE && !stopped(m))
        pthread_cond_wait(&m->changed, &m->lock);
    if (stopped(m)) {
        pthread_mutex_unlock(&m->lock);
        av_frame_free(&ref);
        return AVERROR_EXIT;
    }
    m->queue[(m->head + m->count) % QUEUE] = ref;
    m->count++;
    pthread_cond_broadcast(&m->changed);
    pthread_mutex_unlock(&m->lock);
    return 0;
}

/* ffmpeg_filter.c adjust_frame_pts_to_encoder_tb, output start time 0 */
static double adjust_pts(AVFrame *frame, AVRational tb_dst)
{
    double float_pts = AV_NOPTS_VALUE;
    AVRational tb = tb_dst, filter_tb = frame->time_base;
    const int extra_bits = av_clip(29 - av_log2(tb.den), 0, 16);
    if (frame->pts == AV_NOPTS_VALUE)
        return float_pts;
    tb.den <<= extra_bits;
    float_pts = av_rescale_q(frame->pts, filter_tb, tb);
    float_pts /= 1 << extra_bits;
    if (float_pts != llrint(float_pts))
        float_pts += FFSIGN(float_pts) * 1.0 / (1 << 17);
    frame->pts = av_rescale_q(frame->pts, filter_tb, tb_dst);
    frame->time_base = tb_dst;
    return float_pts;
}

/* ffmpeg_filter.c video_sync_process for VSYNC_CFR and VSYNC_VSCFR */
static void video_sync(neuronte_media *m, AVFrame *frame, int64_t *nb_frames, int64_t *nb_frames_prev)
{
    double delta0, delta, sync_ipts, duration;
    if (!frame) {
        *nb_frames_prev = *nb_frames = mid_pred(m->frames_prev_hist[0], m->frames_prev_hist[1],
                                                m->frames_prev_hist[2]);
        if (!*nb_frames && m->last_dropped)
            m->last_dropped++;
        goto finish;
    }
    duration = frame->duration * av_q2d(frame->time_base) / av_q2d(m->tb_out);
    sync_ipts = adjust_pts(frame, m->tb_out);
    delta0 = sync_ipts - m->next_pts;
    delta = delta0 + duration;
    *nb_frames_prev = 0;
    *nb_frames = 1;
    if (delta0 < 0 && delta > 0) {
        sync_ipts = m->next_pts;
        duration += delta0;
        delta0 = 0;
    }
    if (m->vscfr && m->frame_number == 0 && delta0 >= 0.5) {
        delta = duration;
        delta0 = 0;
        m->next_pts = llrint(sync_ipts);
    }
    if (delta < -1.1)
        *nb_frames = 0;
    else if (delta > 1.1) {
        *nb_frames = llrintf(delta);
        if (delta0 > 1.1)
            *nb_frames_prev = llrintf(delta0 - 0.6);
    }
    frame->duration = 1;
finish:
    memmove(m->frames_prev_hist + 1, m->frames_prev_hist, sizeof m->frames_prev_hist[0] * 2);
    m->frames_prev_hist[0] = *nb_frames_prev;
    if (*nb_frames > (*nb_frames_prev && m->last_dropped) + (*nb_frames > *nb_frames_prev) &&
        *nb_frames > dts_error_threshold * 30) {
        av_log(NULL, AV_LOG_ERROR, "%"PRId64" frame duplication too large, skipping\n", *nb_frames - 1);
        *nb_frames = 0;
        return;
    }
    m->last_dropped = *nb_frames == *nb_frames_prev && frame;
}

/* ffmpeg_filter.c fg_output_frame for video; frame NULL at the end */
static int output_frame(neuronte_media *m, AVFrame *frame)
{
    AVFrame *prev = m->last_frame;
    int64_t nb_frames = !!frame, nb_frames_prev = 0;
    if (frame || m->got_frame)
        video_sync(m, frame, &nb_frames, &nb_frames_prev);
    for (int64_t i = 0; i < nb_frames; i++) {
        AVFrame *in = i < nb_frames_prev && prev->buf[0] ? prev : frame;
        if (!in)
            break;
        int ret = deliver(m, in, m->next_pts);
        if (ret < 0)
            return ret;
        m->frame_number++;
        m->next_pts++;
        m->got_frame = 1;
    }
    if (frame) {
        av_frame_unref(prev);
        av_frame_move_ref(prev, frame);
    } else {
        m->eof_out = 1;
    }
    return 0;
}

/* ffmpeg_filter.c choose_out_timebase: rawvideo, no -r or -enc_time_base */
static void choose_out_timebase(neuronte_media *m, const AVFrame *frame)
{
    AVRational tb = { 0, 0 }, fr = m->framerate;
    if (!fr.num) {
        AVRational sink = av_buffersink_get_frame_rate(m->sink);
        if (sink.num > 0 && sink.den > 0)
            fr = sink;
    }
    if (!fr.num)
        fr = (AVRational){ 25, 1 };
    if (!(tb.num > 0 && tb.den > 0))
        tb = av_inv_q(fr);
    if (!(tb.num > 0 && tb.den > 0))
        tb = frame->time_base;
    m->framerate = fr;
    m->tb_out = tb;
    m->tb_out_locked = 1;
}

/* ffmpeg_filter.c fg_output_step: 0 after a frame, 1 when none is ready */
static int output_step(neuronte_media *m)
{
    AVFrame *frame = m->filtered;
    int ret = av_buffersink_get_frame_flags(m->sink, frame, AV_BUFFERSINK_FLAG_NO_REQUEST);
    if (ret == AVERROR_EOF && !m->eof_out) {
        ret = output_frame(m, NULL);
        return ret < 0 ? ret : 1;
    } else if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
        return 1;
    } else if (ret < 0) {
        return ret;
    }
    if (m->eof_out) {
        av_frame_unref(frame);
        return 0;
    }
    frame->time_base = av_buffersink_get_time_base(m->sink);
    if (!m->tb_out_locked)
        choose_out_timebase(m, frame);
    if (!frame->duration) {
        AVRational fr = av_buffersink_get_frame_rate(m->sink);
        if (fr.num > 0 && fr.den > 0)
            frame->duration = av_rescale_q(1, av_inv_q(fr), frame->time_base);
    }
    ret = output_frame(m, frame);
    av_frame_unref(frame);
    return ret < 0 ? ret : 0;
}

/* ffmpeg_filter.c read_frames: everything the graph has ready */
static int read_frames(neuronte_media *m)
{
    if (!m->graph)
        return 0;
    for (;;) {
        int ret = avfilter_graph_request_oldest(m->graph);
        if (ret == AVERROR(EAGAIN))
            return 0;
        if (ret < 0)
            return ret;
        while (!(ret = output_step(m)))
            ;
        if (ret < 0)
            return ret;
    }
}

static int insert_filter(AVFilterContext **last, const char *name, const char *args)
{
    AVFilterContext *ctx;
    const AVFilter *filter = avfilter_get_by_name(name);
    if (!filter)
        return AVERROR_BUG;
    int ret = avfilter_graph_create_filter(&ctx, filter, name, args, NULL, (*last)->graph);
    if (ret < 0)
        return ret;
    if ((ret = avfilter_link(*last, 0, ctx, 0)) < 0)
        return ret;
    *last = ctx;
    return 0;
}

/* ffmpeg_filter.c configure_filtergraph with configure_input_video_filter
 * and configure_output_video_filter, for one simple video graph. */
static int configure_graph(neuronte_media *m)
{
    AVFilterGraphSegment *seg = NULL;
    AVFilterInOut *inputs = NULL, *outputs = NULL;
    AVFilterContext *last;
    AVBPrint args;
    char text[256];
    int ret;

    avfilter_graph_free(&m->graph);
    m->source = m->sink = NULL;
    if (!(m->graph = avfilter_graph_alloc()))
        return AVERROR(ENOMEM);
    if ((ret = av_opt_set(m->graph, "threads", m->threads, 0)) < 0)
        return ret;

    /* graph_parse and graph_opts_apply */
    if ((ret = avfilter_graph_segment_parse(m->graph, m->filters, 0, &seg)) < 0)
        return ret;
    if ((ret = avfilter_graph_segment_create_filters(seg, 0)) < 0)
        goto done;
    for (size_t i = 0; i < seg->nb_chains; i++) {
        for (size_t j = 0; j < seg->chains[i]->nb_filters; j++) {
            AVFilterParams *p = seg->chains[i]->filters[j];
            const AVDictionaryEntry *e = NULL;
            while ((e = av_dict_iterate(p->opts, e)))
                if ((ret = av_opt_set(p->filter, e->key, e->value, AV_OPT_SEARCH_CHILDREN)) < 0)
                    goto done;
            av_dict_free(&p->opts);
        }
    }
    if ((ret = avfilter_graph_segment_apply(seg, 0, &inputs, &outputs)) < 0)
        goto done;
    if (!inputs || inputs->next || !outputs || outputs->next ||
        avfilter_pad_get_type(inputs->filter_ctx->input_pads, inputs->pad_idx) != AVMEDIA_TYPE_VIDEO) {
        ret = AVERROR(EINVAL);
        goto done;
    }

    /* The input: buffer source, container crop, rotation and the -ss trim */
    AVRational sar = m->in_sar;
    if (!sar.den)
        sar = (AVRational){ 0, 1 };
    av_bprint_init(&args, 0, AV_BPRINT_SIZE_AUTOMATIC);
    av_bprintf(&args, "video_size=%dx%d:pix_fmt=%d:time_base=%d/%d:pixel_aspect=%d/%d:colorspace=%d:range=%d",
               m->in_width, m->in_height, m->in_format, m->in_tb.num, m->in_tb.den,
               sar.num, sar.den, m->in_space, m->in_range);
    if (m->guessed_rate.num && m->guessed_rate.den)
        av_bprintf(&args, ":frame_rate=%d/%d", m->guessed_rate.num, m->guessed_rate.den);
    ret = avfilter_graph_create_filter(&m->source, avfilter_get_by_name("buffer"), "graph 0 input",
                                       args.str, NULL, m->graph);
    av_bprint_finalize(&args, NULL);
    if (ret < 0)
        goto done;
    last = m->source;
    if (m->crop) {
        snprintf(text, sizeof text, "w=iw-%u-%u:h=ih-%u-%u:x=%u:y=%u", m->crop_left, m->crop_right,
                 m->crop_top, m->crop_bottom, m->crop_left, m->crop_top);
        if ((ret = insert_filter(&last, "crop", text)) < 0)
            goto done;
    }
    {
        double theta = get_rotation(m->matrix);
        if (fabs(theta - 90) < 1.0)
            ret = insert_filter(&last, "transpose", m->matrix[3] > 0 ? "cclock_flip" : "clock");
        else if (fabs(theta - 180) < 1.0) {
            if (m->matrix[0] < 0 && (ret = insert_filter(&last, "hflip", NULL)) < 0)
                goto done;
            if (m->matrix[4] < 0)
                ret = insert_filter(&last, "vflip", NULL);
        } else if (fabs(theta - 270) < 1.0)
            ret = insert_filter(&last, "transpose", m->matrix[3] < 0 ? "clock_flip" : "cclock");
        else if (fabs(theta) > 1.0) {
            snprintf(text, sizeof text, "%f*PI/180", theta);
            ret = insert_filter(&last, "rotate", text);
        } else if (fabs(theta) < 1.0) {
            if (m->matrix[4] < 0)
                ret = insert_filter(&last, "vflip", NULL);
        }
        if (ret < 0)
            goto done;
    }
    {
        AVFilterContext *trim = avfilter_graph_alloc_filter(m->graph, avfilter_get_by_name("trim"), "trim_in");
        if (!trim) {
            ret = AVERROR(ENOMEM);
            goto done;
        }
        if ((ret = av_opt_set_int(trim, "starti", 0, AV_OPT_SEARCH_CHILDREN)) < 0 ||
            (ret = avfilter_init_str(trim, NULL)) < 0 || (ret = avfilter_link(last, 0, trim, 0)) < 0)
            goto done;
        last = trim;
    }
    if ((ret = avfilter_link(last, 0, inputs->filter_ctx, inputs->pad_idx)) < 0)
        goto done;

    /* The output: the size and colours fixed by the first graph, the
     * pixel format, and the sink */
    if ((ret = avfilter_graph_create_filter(&m->sink, avfilter_get_by_name("buffersink"), "out",
                                            NULL, NULL, m->graph)) < 0)
        goto done;
    last = outputs->filter_ctx;
    int pad = outputs->pad_idx;
    if (m->configured && (m->out_width || m->out_height)) {
        AVFilterContext *scale;
        snprintf(text, sizeof text, "%d:%d", m->out_width, m->out_height);
        if ((ret = avfilter_graph_create_filter(&scale, avfilter_get_by_name("scale"), "scaler_out",
                                                text, NULL, m->graph)) < 0 ||
            (ret = avfilter_link(last, pad, scale, 0)) < 0)
            goto done;
        last = scale;
        pad = 0;
    }
    av_bprint_init(&args, 0, AV_BPRINT_SIZE_AUTOMATIC);
    av_bprintf(&args, "pix_fmts=%s:", av_get_pix_fmt_name(m->format));
    if (m->configured && m->out_space != AVCOL_SPC_UNSPECIFIED)
        av_bprintf(&args, "color_spaces=%s:", av_color_space_name(m->out_space));
    if (m->configured && m->out_range != AVCOL_RANGE_UNSPECIFIED)
        av_bprintf(&args, "color_ranges=%s:", av_color_range_name(m->out_range));
    {
        AVFilterContext *format;
        ret = avfilter_graph_create_filter(&format, avfilter_get_by_name("format"), "format",
                                           args.str, NULL, m->graph);
        av_bprint_finalize(&args, NULL);
        if (ret < 0 || (ret = avfilter_link(last, pad, format, 0)) < 0)
            goto done;
        last = format;
    }
    if ((ret = avfilter_link(last, 0, m->sink, 0)) < 0)
        goto done;
    if ((ret = avfilter_graph_config(m->graph, NULL)) < 0)
        goto done;

    m->format = av_buffersink_get_format(m->sink);
    m->out_width = av_buffersink_get_w(m->sink);
    m->out_height = av_buffersink_get_h(m->sink);
    m->out_space = av_buffersink_get_colorspace(m->sink);
    m->out_range = av_buffersink_get_color_range(m->sink);
    m->configured = 1;
    if (!m->tb_out_locked) {
        AVRational fr = av_buffersink_get_frame_rate(m->sink);
        if (m->framerate.num <= 0 && m->framerate.den <= 0 && fr.num > 0 && fr.den > 0)
            m->framerate = fr;
        m->tb_out = av_buffersink_get_time_base(m->sink);
    }
done:
    avfilter_graph_segment_free(&seg);
    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);
    if (ret < 0) {
        avfilter_graph_free(&m->graph);
        m->source = m->sink = NULL;
    }
    return ret;
}

/* ffmpeg_filter.c send_frame, then read_frames as the filter thread does */
static int send_frame(neuronte_media *m, AVFrame *frame)
{
    int reinit = m->in_format != frame->format || m->in_width != frame->width ||
                 m->in_height != frame->height || m->in_space != frame->colorspace ||
                 m->in_range != frame->color_range;
    AVFrameSideData *sd = av_frame_get_side_data(frame, AV_FRAME_DATA_DISPLAYMATRIX);
    if (sd) {
        if (!m->matrix_present || memcmp(sd->data, m->matrix, sizeof m->matrix))
            reinit = 1;
    } else if (m->matrix_present) {
        reinit = 1;
    }
    if (reinit) {
        m->in_tb = frame->time_base;
        m->in_format = frame->format;
        m->in_width = frame->width;
        m->in_height = frame->height;
        m->in_sar = frame->sample_aspect_ratio;
        m->in_space = frame->colorspace;
        m->in_range = frame->color_range;
        if (sd)
            memcpy(m->matrix, sd->data, sizeof m->matrix);
        m->matrix_present = !!sd;
    }
    int ret;
    if (reinit || !m->graph) {
        if (m->graph && (ret = read_frames(m)) < 0)
            return ret;
        if ((ret = configure_graph(m)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Error reinitializing filters!\n");
            return ret;
        }
    }
    frame->pts = av_rescale_q(frame->pts, frame->time_base, m->in_tb);
    frame->duration = av_rescale_q(frame->duration, frame->time_base, m->in_tb);
    frame->time_base = m->in_tb;
    av_frame_remove_side_data(frame, AV_FRAME_DATA_DISPLAYMATRIX);
    if ((ret = av_buffersrc_add_frame_flags(m->source, frame, AV_BUFFERSRC_FLAG_PUSH)) < 0) {
        av_frame_unref(frame);
        return ret;
    }
    return read_frames(m);
}

/* ffmpeg_dec.c video_frame_process */
static int frame_process(neuronte_media *m, AVFrame *frame)
{
    frame->pts = frame->best_effort_timestamp;
    if (frame->pts == AV_NOPTS_VALUE)
        frame->pts = m->last_frame_pts == AV_NOPTS_VALUE ? 0 :
                     m->last_frame_pts + m->last_frame_duration_est;
    m->last_frame_duration_est = duration_estimate(m, frame);
    m->last_frame_pts = frame->pts;
    m->last_frame_tb = frame->time_base;
    if (m->sar_override.num)
        frame->sample_aspect_ratio = m->sar_override;
    if (m->apply_cropping && av_frame_apply_cropping(frame, AV_FRAME_CROP_UNALIGNED) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Error applying decoder cropping\n");
        return AVERROR(EINVAL);
    }
    return 0;
}

/* ffmpeg_dec.c packet_decode; pkt NULL drains the decoder */
static int decode(neuronte_media *m, AVPacket *pkt, AVFrame *frame)
{
    if (pkt && pkt->size == 0)
        return 0;
    /* A seek still decodes every reference picture. Non-reference H.264
     * pictures well before the trim point cannot contribute output pixels.
     * Keep the final second of preroll, including its timing history. */
    if (m->preroll && (!pkt || pkt->pts == AV_NOPTS_VALUE ||
                      av_compare_ts(pkt->pts, pkt->time_base, -1, (AVRational){1, 1}) >= 0))
        m->preroll = 0;
    m->dec->skip_frame = m->preroll ? AVDISCARD_NONREF : AVDISCARD_DEFAULT;
    int ret = avcodec_send_packet(m->dec, pkt);
    if (ret < 0 && !(ret == AVERROR_EOF && !pkt)) {
        if (ret == AVERROR(EAGAIN))
            return AVERROR_BUG;
        av_log(NULL, AV_LOG_ERROR, "Error submitting %s to decoder: %s\n", pkt ? "packet" : "EOF",
               av_err2str(ret));
        if (ret != AVERROR_EOF) {
            m->decode_errors++;
            return 0;
        }
        return ret;
    }
    for (;;) {
        av_frame_unref(frame);
        ret = avcodec_receive_frame(m->dec, frame);
        if (ret == AVERROR(EAGAIN))
            return 0;
        if (ret == AVERROR_EOF)
            return ret;
        if (ret < 0) {
            av_log(NULL, AV_LOG_ERROR, "Decoding error: %s\n", av_err2str(ret));
            m->decode_errors++;
            continue;
        }
        m->frames_decoded++;
        frame->time_base = m->dec->pkt_timebase;
        if ((ret = frame_process(m, frame)) < 0)
            return ret;
        if ((ret = send_frame(m, frame)) < 0)
            return ret;
    }
}

/* ffmpeg_filter.c send_eof with the decoder's end timestamp, then what the
 * filter thread does until its output closes. */
static int finish(neuronte_media *m)
{
    int ret = 0;
    if (!m->graph)
        return 0;                       /* nothing was decoded: no frames */
    int64_t pts = m->last_frame_pts == AV_NOPTS_VALUE ? AV_NOPTS_VALUE :
                  m->last_frame_pts + m->last_frame_duration_est;
    pts = av_rescale_q_rnd(pts, m->last_frame_tb, m->in_tb, AV_ROUND_NEAR_INF | AV_ROUND_PASS_MINMAX);
    if ((ret = av_buffersrc_close(m->source, pts, AV_BUFFERSRC_FLAG_PUSH)) < 0)
        return ret;
    ret = read_frames(m);
    if (ret < 0 && ret != AVERROR_EOF)
        return ret;
    return m->eof_out ? 0 : output_frame(m, NULL);
}

static void *worker(void *opaque)
{
    neuronte_media *m = opaque;
    AVPacket *pkt = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();
    int ret = pkt && frame ? 0 : AVERROR(ENOMEM), decoder_ended = 0;

    while (ret >= 0 && !stopped(m)) {
        ret = av_read_frame(m->ic, pkt);
        if (ret == AVERROR(EAGAIN)) {
            av_usleep(10000);
            ret = 0;
            continue;
        }
        if (ret < 0) {
            if (ret != AVERROR_EOF && !stopped(m))
                av_log(NULL, AV_LOG_ERROR, "Error during demuxing: %s\n", av_err2str(ret));
            ret = 0;                    /* the command ends its input either way */
            break;
        }
        if (pkt->stream_index != m->st->index) {
            av_packet_unref(pkt);
            continue;
        }
        ts_fixup(m, pkt);
        ret = decode(m, pkt, frame);
        av_packet_unref(pkt);
        if (ret == AVERROR_EOF) {
            decoder_ended = 1;
            ret = 0;
            break;
        }
    }
    if (ret >= 0 && !stopped(m) && !decoder_ended) {
        ret = decode(m, NULL, frame);
        if (ret == AVERROR_EOF)
            ret = 0;
    }
    if (ret >= 0 && !stopped(m))
        ret = finish(m);
    if (ret >= 0 && !stopped(m)) {
        /* decoder_thread divides the uint64_t counts as integers, so the
         * rate is 1 only when errors decoded no frame at all, else 0. */
        const float max_error_rate = 2.0 / 3;
        uint64_t frames = m->frames_decoded, errors = m->decode_errors;
        float rate = frames || errors ? errors / (frames + errors) : 0.f;
        if (rate > max_error_rate) {
            av_log(NULL, AV_LOG_FATAL, "Decode error rate %g exceeds maximum %g\n", rate, max_error_rate);
            ret = AVERROR(EINVAL);
        }
    }
    av_packet_free(&pkt);
    av_frame_free(&frame);

    pthread_mutex_lock(&m->lock);
    if (ret < 0 && ret != AVERROR_EXIT && !stopped(m)) {
        m->failed = 1;
        set_message(m, "decoding failed", ret);
    }
    m->finished = 1;
    pthread_cond_broadcast(&m->changed);
    pthread_mutex_unlock(&m->lock);
    return NULL;
}

/* The libraries this was built against, as FFmpeg 7.1's command line ships
 * with them; a different minor version may come with a different command. */
static int same_libraries(void)
{
    return avformat_version() >> 8 == LIBAVFORMAT_VERSION_INT >> 8 &&
           avcodec_version() >> 8 == LIBAVCODEC_VERSION_INT >> 8 &&
           avfilter_version() >> 8 == LIBAVFILTER_VERSION_INT >> 8 &&
           avutil_version() >> 8 == LIBAVUTIL_VERSION_INT >> 8;
}

static void release(neuronte_media *m)
{
    for (int i = 0; i < m->count; ++i)
        av_frame_free(&m->queue[(m->head + i) % QUEUE]);
    av_frame_free(&m->current);
    av_frame_free(&m->last_frame);
    av_frame_free(&m->filtered);
    avfilter_graph_free(&m->graph);
    avcodec_free_context(&m->dec);
    avformat_close_input(&m->ic);
    av_freep(&m->filters);
    pthread_cond_destroy(&m->changed);
    pthread_mutex_destroy(&m->lock);
    av_free(m);
}

int neuronte_media_open(neuronte_media **out, const char *url, const char *start,
                        const char *filters, const char *format,
                        int decoder_threads, int filter_threads,
                        char *message, int message_size)
{
    int64_t start_us;
    enum AVPixelFormat pix_fmt;
    if (message && message_size > 0)
        message[0] = 0;
    if (!out)
        return NEURONTE_MEDIA_ARG;
    *out = NULL;
    if (!url || !start || !filters || !format || decoder_threads < 0 || filter_threads < 0 ||
        av_parse_time(&start_us, start, 1) < 0 || (pix_fmt = av_get_pix_fmt(format)) == AV_PIX_FMT_NONE)
        return NEURONTE_MEDIA_ARG;
    if (!same_libraries())
        return NEURONTE_MEDIA_UNSUPPORTED;
    pthread_once(&log_once, log_install);
    pthread_mutex_lock(&log_lock);
    log_text[0] = 0;
    pthread_mutex_unlock(&log_lock);

    neuronte_media *m = av_mallocz(sizeof *m);
    if (!m)
        return NEURONTE_MEDIA_ERROR;
    pthread_condattr_t monotonic;
    pthread_mutex_init(&m->lock, NULL);
    pthread_condattr_init(&monotonic);
    pthread_condattr_setclock(&monotonic, CLOCK_MONOTONIC);
    pthread_cond_init(&m->changed, &monotonic);
    pthread_condattr_destroy(&monotonic);
    atomic_init(&m->stop, 0);
    m->first_dts = m->next_dts = AV_NOPTS_VALUE;
    m->last_frame_pts = AV_NOPTS_VALUE;
    m->in_format = -1;
    m->format = pix_fmt;
    snprintf(m->threads, sizeof m->threads, "%d", filter_threads);
    int status = NEURONTE_MEDIA_ERROR, ret;
    AVDictionary *options = NULL;
    AVCodecParameters *par = NULL;

    if (!(m->filters = av_strdup(filters)) || !(m->last_frame = av_frame_alloc()) ||
        !(m->filtered = av_frame_alloc()) || !(m->ic = avformat_alloc_context()))
        goto fail;
    m->ic->flags |= AVFMT_FLAG_NONBLOCK;
    m->ic->interrupt_callback = (AVIOInterruptCB){ interrupted, m };

    /* ifile_open */
    av_dict_set(&options, "scan_all_pmts", "1", AV_DICT_DONT_OVERWRITE);
    ret = avformat_open_input(&m->ic, url, NULL, &options);
    av_dict_free(&options);
    if (ret < 0) {
        set_message(m, url, ret);
        goto fail;
    }
    if (m->ic->iformat->flags & (AVFMT_TS_DISCONT | AVFMT_NOTIMESTAMPS)) {
        status = NEURONTE_MEDIA_UNSUPPORTED;
        goto fail;
    }
    if (avformat_find_stream_info(m->ic, NULL) < 0 && !m->ic->nb_streams) {
        set_message(m, "could not find codec parameters", 0);
        goto fail;
    }
    int64_t timestamp = start_us;
    if (m->ic->start_time != AV_NOPTS_VALUE)
        timestamp += m->ic->start_time;
    {
        int64_t seek_timestamp = timestamp;
        if (!(m->ic->iformat->flags & AVFMT_SEEK_TO_PTS)) {
            for (unsigned i = 0; i < m->ic->nb_streams; i++)
                if (m->ic->streams[i]->codecpar->video_delay) {
                    seek_timestamp -= 3 * AV_TIME_BASE / 23;
                    break;
                }
        }
        avformat_seek_file(m->ic, -1, INT64_MIN, seek_timestamp, seek_timestamp, 0);
    }
    m->ts_offset = -timestamp;

    /* ist_add marks every stream unused; map_auto_video picks the video */
    int64_t best = 0;
    for (unsigned i = 0; i < m->ic->nb_streams; i++) {
        AVStream *st = m->ic->streams[i];
        st->discard = AVDISCARD_ALL;
        if (st->codecpar->codec_type != AVMEDIA_TYPE_VIDEO)
            continue;
        int64_t score = st->codecpar->width * (int64_t)st->codecpar->height +
                        100000000 * !!(st->event_flags & AVSTREAM_EVENT_FLAG_NEW_PACKETS) +
                        5000000 * !!(st->disposition & AV_DISPOSITION_DEFAULT);
        if (st->disposition & AV_DISPOSITION_ATTACHED_PIC)
            score = 1;
        if (score > best) {
            best = score;
            m->st = st;
        }
    }
    if (m->st)
        best -= 5000000 * !!(m->st->disposition & AV_DISPOSITION_DEFAULT) *
                !(m->st->disposition & AV_DISPOSITION_ATTACHED_PIC);
    if (!m->st || best <= 0 || (m->st->disposition & AV_DISPOSITION_ATTACHED_PIC)) {
        status = NEURONTE_MEDIA_UNSUPPORTED;
        goto fail;
    }
    m->st->discard = AVDISCARD_NONE;
    m->vscfr = m->ic->nb_streams == 1;
    m->codec_desc = avcodec_descriptor_get(m->st->codecpar->codec_id);

    /* ist_add, ist_filter_add and dec_open */
    const AVCodec *codec = avcodec_find_decoder(m->st->codecpar->codec_id);
    if (!codec) {
        status = NEURONTE_MEDIA_UNSUPPORTED;
        goto fail;
    }
    if (!(par = avcodec_parameters_alloc()) || avcodec_parameters_copy(par, m->st->codecpar) < 0)
        goto fail;
    if (m->st->sample_aspect_ratio.num)
        par->sample_aspect_ratio = m->st->sample_aspect_ratio;
    m->sar_override = par->sample_aspect_ratio;
    m->framerate_in = m->st->avg_frame_rate;
    m->guessed_rate = av_guess_frame_rate(m->ic, m->st, NULL);
    {
        const AVPacketSideData *sd = av_packet_side_data_get(par->coded_side_data, par->nb_coded_side_data,
                                                             AV_PKT_DATA_FRAME_CROPPING);
        if (sd && sd->size >= sizeof(uint32_t) * 4) {
            m->crop_top = AV_RL32(sd->data + 0);
            m->crop_bottom = AV_RL32(sd->data + 4);
            m->crop_left = AV_RL32(sd->data + 8);
            m->crop_right = AV_RL32(sd->data + 12);
            m->crop = !!(m->crop_top | m->crop_bottom | m->crop_left | m->crop_right);
        }
    }
    if (!(m->dec = avcodec_alloc_context3(codec)) || avcodec_parameters_to_context(m->dec, par) < 0)
        goto fail;
    m->dec->get_format = get_format;
    m->dec->pkt_timebase = m->st->time_base;
    {
        char threads[16];
        snprintf(threads, sizeof threads, "%d", decoder_threads);
        av_dict_set(&options, "threads", threads, 0);
        ret = av_opt_set_dict2(m->dec, &options, AV_OPT_SEARCH_CHILDREN);
        av_dict_free(&options);
        if (ret < 0)
            goto fail;
    }
    m->dec->flags |= AV_CODEC_FLAG_COPY_OPAQUE;
    m->preroll = start_us > 0 && m->dec->codec_id == AV_CODEC_ID_H264;
    m->apply_cropping = m->dec->apply_cropping;
    m->dec->apply_cropping = 0;
    if ((ret = avcodec_open2(m->dec, codec, NULL)) < 0) {
        set_message(m, "Error while opening decoder", ret);
        goto fail;
    }
    avcodec_parameters_free(&par);

    if (pthread_create(&m->thread, NULL, worker, m))
        goto fail;
    m->thread_started = 1;
    *out = m;
    return NEURONTE_MEDIA_OK;

fail:
    if (message && message_size > 0)
        snprintf(message, message_size, "%s", m->message);
    avcodec_parameters_free(&par);
    release(m);
    return status;
}

int neuronte_media_next(neuronte_media *m, struct neuronte_media_frame *frame, int timeout_ms)
{
    struct timespec until;
    if (!m || !frame)
        return NEURONTE_MEDIA_ARG;
    memset(frame, 0, sizeof *frame);
    if (timeout_ms >= 0) {
        clock_gettime(CLOCK_MONOTONIC, &until);
        until.tv_sec += timeout_ms / 1000;
        until.tv_nsec += (long)(timeout_ms % 1000) * 1000000L;
        if (until.tv_nsec >= 1000000000L) {
            until.tv_sec++;
            until.tv_nsec -= 1000000000L;
        }
    }
    pthread_mutex_lock(&m->lock);
    av_frame_free(&m->current);
    while (!m->count && !m->finished) {
        if (timeout_ms < 0) {
            pthread_cond_wait(&m->changed, &m->lock);
        } else if (pthread_cond_timedwait(&m->changed, &m->lock, &until)) {
            pthread_mutex_unlock(&m->lock);
            return NEURONTE_MEDIA_AGAIN;
        }
    }
    int status;
    if (m->count) {
        m->current = m->queue[m->head];
        m->queue[m->head] = NULL;
        m->head = (m->head + 1) % QUEUE;
        m->count--;
        pthread_cond_broadcast(&m->changed);
        status = NEURONTE_MEDIA_OK;
    } else {
        status = m->failed ? NEURONTE_MEDIA_ERROR : NEURONTE_MEDIA_END;
    }
    pthread_mutex_unlock(&m->lock);
    if (status == NEURONTE_MEDIA_OK) {
        const AVFrame *f = m->current;
        for (int i = 0; i < 4 && f->data[i]; ++i) {
            frame->data[i] = f->data[i];
            frame->linesize[i] = f->linesize[i];
            frame->planes = i + 1;
        }
        frame->width = f->width;
        frame->height = f->height;
        frame->number = m->delivered++;
    }
    return status;
}

const char *neuronte_media_message(const neuronte_media *m)
{
    return m ? m->message : "";
}

void neuronte_media_close(neuronte_media *m)
{
    if (!m)
        return;
    if (m->thread_started) {
        pthread_mutex_lock(&m->lock);
        atomic_store(&m->stop, 1);
        pthread_cond_broadcast(&m->changed);
        pthread_mutex_unlock(&m->lock);
        pthread_join(m->thread, NULL);
    }
    release(m);
}
