/* In-process video decoding for the Neuronte player.
 *
 * neuronte_media_open repeats, inside the calling process, what the command
 *
 *   ffmpeg -v error -nostdin -filter_threads F -threads:v D -ss START -i URL
 *          -an -sn -vf FILTERS -f rawvideo -pix_fmt FORMAT -
 *
 * does with FFmpeg 7.1's libraries: the same open and probe, seek, stream
 * choice, decoder, filter graph and constant-rate output, so the frames are
 * the same bytes the command writes. Playback then needs no process start,
 * no second probe and no pipe for each seek. Inputs whose handling this
 * library does not reproduce are declined with NEURONTE_MEDIA_UNSUPPORTED,
 * and the caller runs the command instead. This library depends on
 * libavformat, libavcodec, libavfilter and libavutil; libneuronte does not.
 *
 * The first open installs an av_log callback for the whole process. It
 * keeps FFmpeg's error lines, as -v error would print them, for
 * neuronte_media_message instead of writing them to standard error.
 */
#ifndef NEURONTE_MEDIA_H
#define NEURONTE_MEDIA_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    NEURONTE_MEDIA_OK = 0,
    NEURONTE_MEDIA_END = 1,             /* neuronte_media_next: no more frames */
    NEURONTE_MEDIA_AGAIN = 2,           /* neuronte_media_next: none within the timeout */
    NEURONTE_MEDIA_ERROR = -1,          /* see neuronte_media_message */
    NEURONTE_MEDIA_UNSUPPORTED = -2,    /* run the ffmpeg command instead */
    NEURONTE_MEDIA_ARG = -3
};

typedef struct neuronte_media neuronte_media;

/* One decoded picture. data and linesize follow FFmpeg's plane order for
 * the format (gbrp: G, B, R). The memory is owned by the decoder and stays
 * valid until the next neuronte_media_next or neuronte_media_close. */
struct neuronte_media_frame {
    const uint8_t *data[4];
    int linesize[4];
    int width, height;
    int planes;
    int64_t number;     /* 0 for the first frame written */
};

/* start is the -ss argument as text, so it is parsed the same way.
 * filters is the -vf argument, format an FFmpeg pixel format name.
 * On NEURONTE_MEDIA_OK *out is a decoder that is already reading ahead
 * on its own thread; otherwise *out is NULL. A NEURONTE_MEDIA_ERROR
 * message, if any, is copied into message (which may be NULL). */
int neuronte_media_open(neuronte_media **out, const char *url, const char *start,
                        const char *filters, const char *format,
                        int decoder_threads, int filter_threads,
                        char *message, int message_size);

/* Waits up to timeout_ms (forever if negative) for the next frame, and
 * releases the previous one. Returns NEURONTE_MEDIA_OK, NEURONTE_MEDIA_AGAIN
 * when none was ready in time, NEURONTE_MEDIA_END, or NEURONTE_MEDIA_ERROR
 * when decoding failed where the command would have failed. */
int neuronte_media_next(neuronte_media *media, struct neuronte_media_frame *frame, int timeout_ms);

/* Why decoding failed, or "" when it did not. */
const char *neuronte_media_message(const neuronte_media *media);

/* Stops the decoder thread and frees everything; NULL is ignored. */
void neuronte_media_close(neuronte_media *media);

#ifdef __cplusplus
}
#endif

#endif
