/* neuronte-bench WEIGHTS
 * neuronte-bench FULL BUNDLE
 *
 * With one file, times neuronte_coverage() with no cache over the 95
 * printable ASCII characters at several cell sizes.
 *
 * With two, compares a net trained on everything with a bundle that
 * routes each character to a smaller net: for each class of characters
 * (ASCII, drawing, symbols, accented letters, pixel mosaics), the time
 * per cell from each file, where the
 * bundle's time includes its router, and then the router's own time per
 * call. One thread. MIT licence. */
#define _POSIX_C_SOURCE 199309L
#include "neuronte.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec * 1e-9;
}

static int open_or_say(const char *path, neuronte **n)
{
    int rc = neuronte_open_file(path, n);
    if (rc != NEURONTE_OK)
        fprintf(stderr, "%s: cannot load weights (%d)\n", path, rc);
    return rc;
}

static int one(const char *path)
{
    static const int sizes[][2] = {{8, 0}, {8, 1}, {12, 0}, {16, 0}, {16, 1}, {24, 0}, {32, 0}, {48, 0}};
    neuronte *n;
    float *cov;
    size_t k;

    if (open_or_say(path, &n) != NEURONTE_OK)
        return 1;
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

/* The classes, as the training sets define them. */
#define MAX_CLASS 640
struct cls {
    const char *name;
    uint32_t s[MAX_CLASS];
    int count;
};

static void add_range(struct cls *c, uint32_t lo, uint32_t hi, uint32_t step)
{
    for (; lo <= hi && c->count < MAX_CLASS; lo += step)
        c->s[c->count++] = lo;
}

static void add_utf8(struct cls *c, const char *t)
{
    size_t off = 0, len = strlen(t);
    while (off < len && c->count < MAX_CLASS)
        off += neuronte_utf8_decode(t + off, len - off, &c->s[c->count++]);
}

/* Seconds per cell for the first cells of the class, the best of passes. */
static double per_cell(neuronte *n, const struct cls *c, int w, int ss, int cells, int passes, float *cov)
{
    double best = 1e30;
    int p, i;
    if (cells > c->count)
        cells = c->count;
    for (p = 0; p < passes; p++) {
        double t0 = now(), t;
        for (i = 0; i < cells; i++)
            neuronte_coverage(n, c->s[i * c->count / cells], w, 2 * w, ss, cov);
        t = (now() - t0) / cells;
        best = t < best ? t : best;
    }
    return best;
}

/* Nanoseconds per neuronte_route() call over the scalars. */
static double route_ns(neuronte *n, const uint32_t *s, int count)
{
    const long calls = 2000000;
    volatile int sink = 0;
    double t0 = now();
    long i;
    for (i = 0; i < calls; i++)
        sink += neuronte_route(n, s[i % count]);
    (void)sink;
    return (now() - t0) * 1e9 / (double)calls;
}

static int compare(const char *full_path, const char *bundle_path)
{
    static const int sizes[][3] = {{8, 2, 3}, {16, 2, 2}, {48, 1, 1}}; /* width, samples, passes */
    static struct cls classes[5];
    uint32_t outside[256];
    neuronte *full, *b;
    float *cov;
    int k, z, i;

    if (open_or_say(full_path, &full) != NEURONTE_OK)
        return 1;
    if (open_or_say(bundle_path, &b) != NEURONTE_OK)
        return 1;
    cov = malloc(48 * 96 * sizeof *cov);
    if (!cov)
        return 1;
    classes[0].name = "ascii";
    add_range(&classes[0], 0x20, 0x7E, 1);
    classes[1].name = "draw";
    add_range(&classes[1], 0x2500, 0x257F, 1);
    add_range(&classes[1], 0x2591, 0x2593, 1);
    classes[2].name = "symbol";
    add_utf8(&classes[2], "\xc2\xa0©°·½×–—‘’“”•…›※⁙←↑→↓↗⇣≈≡⋅⎿⏵▲▸▼▾◆◈◉●◐◑◯☐☒✔✢✳✶✻✽❯⸬");
    classes[3].name = "accent";
    add_range(&classes[3], 0xC0, 0xD6, 1);
    add_range(&classes[3], 0xD8, 0x17F, 1);
    /* Blocks without the shades, Braille, sextants, octants and the octant
     * substitutes. A net trained on everything before the mosaics draws
     * them wrongly, but takes the same time. */
    classes[4].name = "pixel";
    add_range(&classes[4], 0x2580, 0x2590, 1);
    add_range(&classes[4], 0x2594, 0x259F, 1);
    add_range(&classes[4], 0x2800, 0x28FF, 1);
    add_range(&classes[4], 0x1FB00, 0x1FB3B, 1);
    add_range(&classes[4], 0x1CD00, 0x1CDE5, 1);
    add_range(&classes[4], 0x1CEA0, 0x1CEA0, 1);
    add_range(&classes[4], 0x1CEA3, 0x1CEA3, 1);
    add_range(&classes[4], 0x1CEA8, 0x1CEA8, 1);
    add_range(&classes[4], 0x1CEAB, 0x1CEAB, 1);
    add_range(&classes[4], 0x1FB82, 0x1FB82, 1);
    add_range(&classes[4], 0x1FB85, 0x1FB85, 1);
    add_range(&classes[4], 0x1FBE6, 0x1FBE7, 1);

    printf("full:   %s, %zu parameters, nets %d\n", full_path, neuronte_parameters(full), neuronte_nets(full));
    printf("bundle: %s, %zu parameters, nets %d\n\n", bundle_path, neuronte_parameters(b), neuronte_nets(b));
    printf("%-7s %5s %4s  %-10s %13s %15s %8s\n", "class", "cells", "net", "cell", "full ms/cell",
           "bundle ms/cell", "speedup");
    for (k = 0; k < 5; k++) {
        const struct cls *c = &classes[k];
        int net = neuronte_route(b, c->s[0]);
        char netname[8];
        for (i = 1; i < c->count; i++)
            if (neuronte_route(b, c->s[i]) != net)
                net = -1;
        snprintf(netname, sizeof netname, net < 0 ? "mixed" : "%d", net);
        for (z = 0; z < 3; z++) {
            int w = sizes[z][0], ss = sizes[z][1], cells = w >= 48 ? 24 : 96;
            double tf = per_cell(full, c, w, ss, cells, sizes[z][2], cov);
            double tb = per_cell(b, c, w, ss, cells, sizes[z][2], cov);
            char cell[24], count[12];
            snprintf(cell, sizeof cell, "%dx%d %dx%d", w, 2 * w, ss, ss);
            snprintf(count, sizeof count, "%d", c->count);
            printf("%-7s %5s %4s  %-10s %13.2f %15.2f %7.2fx\n", z == 0 ? c->name : "", z == 0 ? count : "",
                   z == 0 ? netname : "", cell, tf * 1e3, tb * 1e3, tf / tb);
        }
    }

    /* Scalars no net was trained on: past the table, to the gate or the
     * fallback net. */
    for (i = 0; i < 256; i++)
        outside[i] = 0x4E00 + 97u * (uint32_t)i;
    printf("\nrouter, ns per call:");
    for (k = 0; k < 5; k++)
        printf("  %s %.1f", classes[k].name, route_ns(b, classes[k].s, classes[k].count));
    printf("  outside the table %.1f\n", route_ns(b, outside, 256));
    free(cov);
    neuronte_close(full);
    neuronte_close(b);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc == 2)
        return one(argv[1]);
    if (argc == 3)
        return compare(argv[1], argv[2]);
    fprintf(stderr, "usage: %s WEIGHTS\n       %s FULL BUNDLE\n", argv[0], argv[0]);
    return 2;
}
