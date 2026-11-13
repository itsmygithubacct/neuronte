/* The libneuronte-media API around the frames: arguments, inputs it cannot
 * open or declines, timeouts, the end, closing while the decoder thread is
 * busy or waiting, and two decoders at once. tests/check_media.py builds the
 * inputs and runs this under AddressSanitizer and UBSan:
 *
 *   test_media VIDEO DECLINED
 *
 * VIDEO is a short file the library accepts, DECLINED one it declines. */
#include "neuronte_media.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FILTERS "fps=25,scale=48:32:flags=area"
#define FRAME (48 * 32)

static int failures;
static int auto_threads;                /* 0, or TEST_MEDIA_THREADS */

static void check(int ok, const char *what)
{
    if (!ok) {
        fprintf(stderr, "test_media: %s\n", what);
        failures++;
    }
}

static neuronte_media *open_video(const char *url, const char *start, int threads)
{
    neuronte_media *media = (neuronte_media *)1;
    char message[256];
    if (auto_threads)
        threads = auto_threads;
    int status = neuronte_media_open(&media, url, start, FILTERS, "gbrp", threads, 1, message, sizeof message);
    check(status == NEURONTE_MEDIA_OK && media, "a supported video opens");
    if (status != NEURONTE_MEDIA_OK)
        fprintf(stderr, "  %d %s\n", status, message);
    return status == NEURONTE_MEDIA_OK ? media : NULL;
}

/* Reads every frame, folding the samples into a checksum. */
static long read_all(neuronte_media *media, unsigned long long *sum)
{
    struct neuronte_media_frame frame;
    long count = 0;
    int status;
    *sum = 1469598103934665603ULL;
    while ((status = neuronte_media_next(media, &frame, -1)) == NEURONTE_MEDIA_OK) {
        check(frame.number == count, "frames are numbered from 0");
        check(frame.width == 48 && frame.height == 32 && frame.planes == 3, "frames have the filtered size and planes");
        for (int p = 0; p < 3; ++p)
            for (int y = 0; y < frame.height; ++y)
                for (int x = 0; x < frame.width; ++x)
                    *sum = (*sum ^ frame.data[p][y * frame.linesize[p] + x]) * 1099511628211ULL;
        count++;
    }
    check(status == NEURONTE_MEDIA_END, "the frames end without an error");
    check(neuronte_media_next(media, &frame, -1) == NEURONTE_MEDIA_END, "the end is repeated");
    check(neuronte_media_next(media, &frame, 0) == NEURONTE_MEDIA_END, "the end is repeated without waiting");
    check(!*neuronte_media_message(media), "no message after a clean end");
    return count;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s VIDEO DECLINED\n", argv[0]);
        return 2;
    }
    const char *video = argv[1], *declined = argv[2];
    /* TEST_MEDIA_THREADS=1 keeps FFmpeg's own threads out of a
     * ThreadSanitizer run, which cannot see their synchronization. */
    if (getenv("TEST_MEDIA_THREADS"))
        auto_threads = atoi(getenv("TEST_MEDIA_THREADS"));
    neuronte_media *media;
    char message[256];
    struct neuronte_media_frame frame;

    /* Arguments */
    check(neuronte_media_open(NULL, video, "0", FILTERS, "gbrp", auto_threads, 1, NULL, 0) == NEURONTE_MEDIA_ARG, "no handle");
    media = (neuronte_media *)1;
    check(neuronte_media_open(&media, video, "soon", FILTERS, "gbrp", auto_threads, 1, NULL, 0) == NEURONTE_MEDIA_ARG && !media,
          "an unreadable start");
    check(neuronte_media_open(&media, video, "0", FILTERS, "nonsense", 0, 1, NULL, 0) == NEURONTE_MEDIA_ARG,
          "an unknown format");
    check(neuronte_media_open(&media, video, "0", FILTERS, "gbrp", -1, 1, NULL, 0) == NEURONTE_MEDIA_ARG,
          "negative threads");
    check(neuronte_media_open(&media, NULL, "0", FILTERS, "gbrp", auto_threads, 1, NULL, 0) == NEURONTE_MEDIA_ARG, "no input");
    check(neuronte_media_next(NULL, &frame, 0) == NEURONTE_MEDIA_ARG, "next without a decoder");
    check(!*neuronte_media_message(NULL), "no message without a decoder");
    neuronte_media_close(NULL);

    /* Inputs that cannot be opened, and inputs left to the command */
    message[0] = 'x';
    check(neuronte_media_open(&media, "/nonexistent/video.mp4", "0", FILTERS, "gbrp", auto_threads, 1, message, sizeof message) ==
          NEURONTE_MEDIA_ERROR && !media && strstr(message, "No such file"), "a missing file names the error");
    memset(message, 'x', sizeof message);
    check(neuronte_media_open(&media, "/nonexistent/video.mp4", "0", FILTERS, "gbrp", auto_threads, 1, message, 4) ==
          NEURONTE_MEDIA_ERROR && strlen(message) == 3 && message[4] == 'x', "a message fits a short buffer");
    check(neuronte_media_open(&media, declined, "0", FILTERS, "gbrp", auto_threads, 1, message, sizeof message) ==
          NEURONTE_MEDIA_UNSUPPORTED && !media, "a declined input");
    check(neuronte_media_open(&media, video, "0", "nosuchfilter", "gbrp", auto_threads, 1, message, sizeof message) == NEURONTE_MEDIA_OK,
          "filters are built with the first frame");
    if (media) {
        check(neuronte_media_next(media, &frame, -1) == NEURONTE_MEDIA_ERROR, "unknown filters fail");
        check(strlen(neuronte_media_message(media)) > 0, "and say why");
        neuronte_media_close(media);
    }

    /* Every frame, twice: a new decoder repeats the same frames */
    unsigned long long first, second;
    long count = 0;
    if ((media = open_video(video, "0.5", 0))) {
        count = read_all(media, &first);
        neuronte_media_close(media);
    }
    if ((media = open_video(video, "0.5", 1))) {
        check(read_all(media, &second) == count && second == first, "one decoder thread gives the same frames");
        neuronte_media_close(media);
    }
    check(count > 10, "the video has frames");

    /* Two at once are independent */
    neuronte_media *a = open_video(video, "0.5", 0), *b = open_video(video, "0.5", 0);
    if (a && b) {
        struct neuronte_media_frame fa, fb;
        long same = 0;
        while (neuronte_media_next(a, &fa, -1) == NEURONTE_MEDIA_OK &&
               neuronte_media_next(b, &fb, -1) == NEURONTE_MEDIA_OK) {
            int equal = fa.number == fb.number;
            for (int p = 0; p < 3 && equal; ++p)
                for (int y = 0; y < 32 && equal; ++y)
                    equal = !memcmp(fa.data[p] + y * fa.linesize[p], fb.data[p] + y * fb.linesize[p], 48);
            same += equal;
        }
        check(same == count, "concurrent decoders give the same frames");
    }
    neuronte_media_close(a);
    neuronte_media_close(b);

    /* Closing while the thread decodes, waits on a full queue, or has
     * just started; and a timeout that expires */
    for (int i = 0; i < 30; ++i) {
        if (!(media = open_video(video, i % 3 ? "0" : "1.2", i % 2)))
            break;
        int status = neuronte_media_next(media, &frame, i % 5 ? -1 : 0);
        check(status == NEURONTE_MEDIA_OK || (status == NEURONTE_MEDIA_AGAIN && i % 5 == 0), "a frame or a timeout");
        if (i % 4 == 1)
            neuronte_media_next(media, &frame, 1);
        neuronte_media_close(media);
    }
    if ((media = open_video(video, "0", 0))) {
        neuronte_media_close(media);
    }

    /* Past the end: no frames, cleanly */
    if ((media = open_video(video, "100", 0))) {
        check(neuronte_media_next(media, &frame, -1) == NEURONTE_MEDIA_END, "a start past the end has no frames");
        neuronte_media_close(media);
    }

    if (failures)
        return 1;
    printf("media decoder: arguments, declined inputs, end, timeouts, closing and concurrency passed\n");
    return 0;
}
