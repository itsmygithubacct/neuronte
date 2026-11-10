/* neuronte-bench WEIGHTS
 *
 * Times neuronte_coverage() with no cache, over the 95 printable ASCII
 * characters, at several cell sizes. One thread. MIT licence. */
#define _POSIX_C_SOURCE 199309L
#include "neuronte.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

int main(int argc, char **argv)
{
    static const int sizes[][2] = {{8, 0}, {8, 1}, {12, 0}, {16, 0}, {16, 1}, {24, 0}, {32, 0}, {48, 0}};
    neuronte *n;
    float *cov;
    size_t k;
    int rc;

    if (argc != 2) {
        fprintf(stderr, "usage: %s WEIGHTS\n", argv[0]);
        return 2;
    }
    rc = neuronte_open_file(argv[1], &n);
    if (rc != NEURONTE_OK) {
        fprintf(stderr, "%s: cannot load weights (%d)\n", argv[1], rc);
        return 1;
    }
    cov = malloc(48 * 96 * sizeof *cov);
    if (!cov)
        return 1;
    printf("%-10s %-8s %12s %14s %16s\n", "cell", "samples", "ms per cell", "us per sample", "95 cells, ms");
    for (k = 0; k < sizeof sizes / sizeof sizes[0]; k++) {
        int w = sizes[k][0], h = 2 * w, ss = sizes[k][1] ? sizes[k][1] : (w < 24 ? 2 : 1);
        double t0, t;
        uint32_t c;
        char cell[16];
        t0 = now();
        for (c = 32; c < 127; c++)
            if (neuronte_coverage(n, c, w, h, ss, cov) != NEURONTE_OK)
                return 1;
        t = now() - t0;
        snprintf(cell, sizeof cell, "%dx%d", w, h);
        printf("%-10s %dx%-6d %12.3f %14.3f %16.1f\n", cell, ss, ss, t * 1e3 / 95,
               t * 1e6 / (95.0 * w * h * ss * ss), t * 1e3);
    }
    free(cov);
    neuronte_close(n);
    return 0;
}
