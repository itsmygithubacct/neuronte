/* Writes what libneuronte-media decodes as raw frames on standard output,
 * the bytes `ffmpeg ... -f rawvideo -pix_fmt FORMAT -` writes, so tests can
 * compare the two directly.
 *
 *   neuronte-media-decode URL START FILTERS FORMAT DECODER_THREADS FILTER_THREADS [FRAMES]
 *
 * FORMAT is rgb24 or gbrp. Exit status: 0 done, 1 decoding failed,
 * 2 usage, 3 the input is declined and needs the ffmpeg command. */
#include "neuronte_media.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    if (argc < 7 || argc > 8 || (strcmp(argv[4], "rgb24") && strcmp(argv[4], "gbrp"))) {
        fprintf(stderr, "usage: %s URL START FILTERS rgb24|gbrp DECODER_THREADS FILTER_THREADS [FRAMES]\n", argv[0]);
        return 2;
    }
    int planar = !strcmp(argv[4], "gbrp");
    long long limit = argc == 8 ? atoll(argv[7]) : -1;
    char message[1024];
    neuronte_media *media;
    int status = neuronte_media_open(&media, argv[1], argv[2], argv[3], argv[4],
                                     atoi(argv[5]), atoi(argv[6]), message, sizeof message);
    if (status == NEURONTE_MEDIA_UNSUPPORTED)
        return 3;
    if (status != NEURONTE_MEDIA_OK) {
        fprintf(stderr, "%s\n", *message ? message : "cannot open the input");
        return status == NEURONTE_MEDIA_ARG ? 2 : 1;
    }
    struct neuronte_media_frame frame;
    long long count = 0;
    while ((limit < 0 || count < limit) && (status = neuronte_media_next(media, &frame, -1)) == NEURONTE_MEDIA_OK) {
        int planes = planar ? 3 : 1;
        size_t row = (size_t)frame.width * (planar ? 1 : 3);
        if (frame.planes < planes) {
            fprintf(stderr, "a frame has %d planes\n", frame.planes);
            status = NEURONTE_MEDIA_ERROR;
            break;
        }
        for (int p = 0; p < planes; ++p)
            for (int y = 0; y < frame.height; ++y)
                if (fwrite(frame.data[p] + (size_t)y * frame.linesize[p], 1, row, stdout) != row) {
                    neuronte_media_close(media);
                    return 1;
                }
        count++;
    }
    if (status == NEURONTE_MEDIA_ERROR)
        fprintf(stderr, "%s\n", neuronte_media_message(media));
    neuronte_media_close(media);
    return fflush(stdout) || status == NEURONTE_MEDIA_ERROR;
}
