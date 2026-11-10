/* Loader refusals, drawing, clipping and blending. MIT licence.
 * usage: test_api WEIGHTS.nrt */
#include "neuronte.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failed;
#define FAIL(...) (printf("FAIL " __VA_ARGS__), putchar('\n'), failed = 1)

static unsigned char *slurp(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    unsigned char *buf;
    long n;
    if (!f)
        return NULL;
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    buf = malloc((size_t)n);
    if (buf && fread(buf, 1, (size_t)n, f) != (size_t)n) {
        free(buf);
        buf = NULL;
    }
    fclose(f);
    *len = (size_t)n;
    return buf;
}

static void expect_open(const char *name, const unsigned char *data, size_t len, int want)
{
    neuronte *n = (neuronte *)1;
    int rc = neuronte_open(data, len, &n);
    if (rc != want)
        FAIL("%s: open returned %d, want %d", name, rc, want);
    if (rc != NEURONTE_OK && n != NULL)
        FAIL("%s: handle not cleared on failure", name);
    neuronte_close(rc == NEURONTE_OK ? n : NULL);
}

static void put32(unsigned char *p, uint32_t v)
{
    p[0] = v & 0xFF;
    p[1] = v >> 8 & 0xFF;
    p[2] = v >> 16 & 0xFF;
    p[3] = v >> 24;
}

int main(int argc, char **argv)
{
    unsigned char *data, *copy;
    size_t len;
    neuronte *n;
    enum { CW = 16, CH = 32, BW = 64, BH = 48 };
    float cov[CW * CH], cov2[CW * CH];
    uint32_t buf[BW * BH], ref[BW * BH];
    int i, rc;

    if (argc != 2) {
        fprintf(stderr, "usage: %s WEIGHTS.nrt\n", argv[0]);
        return 2;
    }
    data = slurp(argv[1], &len);
    if (!data) {
        perror(argv[1]);
        return 2;
    }
    copy = malloc(len + 1);

    /* Refusals. */
    expect_open("good file", data, len, NEURONTE_OK);
    expect_open("one byte short", data, len - 1, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    copy[len] = 0;
    expect_open("one byte long", copy, len + 1, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    copy[0] = 'X';
    expect_open("bad magic", copy, len, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    put32(copy + 8, 2);
    expect_open("version 2", copy, len, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    put32(copy + 20, 64);
    expect_open("hidden width 64", copy, len, NEURONTE_ERR_SHAPE);
    memcpy(copy, data, len);
    put32(copy + 12, 4);
    expect_open("4 octaves", copy, len, NEURONTE_ERR_SHAPE);
    memcpy(copy, data, len);
    put32(copy + 204 + 4 * 1000, 0x7FC00000u); /* a NaN in l1 */
    expect_open("NaN weight", copy, len, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    put32(copy + 32, 0);
    expect_open("zero mask", copy, len, NEURONTE_ERR_FORMAT);
    if (neuronte_open(NULL, len, &n) != NEURONTE_ERR_ARG)
        FAIL("null data accepted");
    if (neuronte_open_file("/nonexistent/neuronte.nrt", &n) != NEURONTE_ERR_IO)
        FAIL("missing file not reported as IO");

    rc = neuronte_open(data, len, &n);
    if (rc != NEURONTE_OK) {
        printf("cannot open weights (%d)\n", rc);
        return 1;
    }

    /* The same character twice gives the same cell, bit for bit. */
    neuronte_coverage(n, 'A', CW, CH, 0, cov);
    neuronte_coverage(n, 'A', CW, CH, 0, cov2);
    if (memcmp(cov, cov2, sizeof cov) != 0)
        FAIL("A drawn twice differs");
    {
        float mx = 0, sum = 0;
        for (i = 0; i < CW * CH; i++) {
            if (cov[i] < 0 || cov[i] > 1 || isnan(cov[i]))
                FAIL("coverage %g out of range", cov[i]);
            mx = cov[i] > mx ? cov[i] : mx;
            sum += cov[i];
        }
        if (mx < 0.9f || sum < 20)
            FAIL("A has too little ink (max %g, sum %g)", mx, sum);
    }
    neuronte_coverage(n, ' ', CW, CH, 0, cov);
    for (i = 0; i < CW * CH; i++)
        if (cov[i] > 0.05f) {
            FAIL("space has ink %g at %d", cov[i], i);
            break;
        }
    /* A surrogate and a value past U+10FFFF are drawn as U+FFFD. */
    neuronte_coverage(n, 0xFFFD, CW, CH, 0, cov);
    neuronte_coverage(n, 0xD800, CW, CH, 0, cov2);
    if (memcmp(cov, cov2, sizeof cov) != 0)
        FAIL("surrogate not drawn as U+FFFD");
    neuronte_coverage(n, 0x110000, CW, CH, 0, cov2);
    if (memcmp(cov, cov2, sizeof cov) != 0)
        FAIL("U+110000 not drawn as U+FFFD");
    /* A character never trained still gets ink. */
    neuronte_coverage(n, 0x4E2D, CW, CH, 0, cov);
    {
        float sum = 0;
        for (i = 0; i < CW * CH; i++)
            sum += cov[i];
        if (sum < 0.01f * CW * CH)
            FAIL("U+4E2D is blank");
    }
    if (neuronte_coverage(n, 'A', 0, CH, 0, cov) != NEURONTE_ERR_ARG ||
        neuronte_coverage(n, 'A', CW, CH, 9, cov) != NEURONTE_ERR_ARG)
        FAIL("bad sizes accepted");

    /* ASCII and UTF-8 text give the same pixels as the scalar call. */
    for (i = 0; i < BW * BH; i++)
        buf[i] = ref[i] = 0xFF000000u;
    if (neuronte_draw_utf8(n, buf, BW, BW, BH, 3, 2, CW, CH, "A", 1, 0xFFFFFFFFu) != 1)
        FAIL("draw_utf8 A did not draw one cell");
    neuronte_draw_scalar(n, ref, BW, BW, BH, 3, 2, CW, CH, 0x41, 0xFFFFFFFFu);
    if (memcmp(buf, ref, sizeof buf) != 0)
        FAIL("ASCII A and scalar U+0041 differ");
    for (i = 0; i < BW * BH; i++)
        buf[i] = ref[i] = 0xFF000000u;
    if (neuronte_draw_utf8(n, buf, BW, BW, BH, 0, 0, CW, CH, "\xc3\xa9", 2, 0xFFFFFFFFu) != 1)
        FAIL("two-byte UTF-8 is not one cell");
    neuronte_draw_scalar(n, ref, BW, BW, BH, 0, 0, CW, CH, 0xE9, 0xFFFFFFFFu);
    if (memcmp(buf, ref, sizeof buf) != 0)
        FAIL("UTF-8 e-acute and scalar U+00E9 differ");
    for (i = 0; i < BW * BH; i++)
        buf[i] = ref[i] = 0xFF000000u;
    neuronte_draw_utf8(n, buf, BW, BW, BH, 0, 0, CW, CH, "\xff", 1, 0xFFFFFFFFu);
    neuronte_draw_scalar(n, ref, BW, BW, BH, 0, 0, CW, CH, 0xFFFD, 0xFFFFFFFFu);
    if (memcmp(buf, ref, sizeof buf) != 0)
        FAIL("a bad byte is not drawn as U+FFFD");

    /* Clipping: a cell hanging off every edge writes only inside the
     * buffer, and the guard columns of a narrower width stay untouched. */
    for (i = 0; i < BW * BH; i++)
        buf[i] = 0xFF000000u;
    neuronte_draw_scalar(n, buf, BW, BW - 8, BH, -5, -7, CW, CH, '#', 0xFFFFFFFFu);
    neuronte_draw_scalar(n, buf, BW, BW - 8, BH, BW - 8 - 6, BH - 10, CW, CH, '#', 0xFFFFFFFFu);
    for (i = 0; i < BH; i++) {
        int c;
        for (c = BW - 8; c < BW; c++)
            if (buf[i * BW + c] != 0xFF000000u) {
                FAIL("wrote past width at row %d col %d", i, c);
                i = BH;
                break;
            }
    }
    {
        int inked = 0;
        for (i = 0; i < BW * BH; i++)
            inked += buf[i] != 0xFF000000u;
        if (inked == 0)
            FAIL("clipped cells drew nothing");
    }

    /* Blending: a transparent colour changes nothing; full ink gives the
     * colour; the alpha of an opaque destination stays opaque. */
    for (i = 0; i < BW * BH; i++)
        buf[i] = ref[i] = 0xFF336699u;
    neuronte_draw_scalar(n, buf, BW, BW, BH, 0, 0, CW, CH, 'W', 0x00FFFFFFu);
    if (memcmp(buf, ref, sizeof buf) != 0)
        FAIL("transparent colour changed the buffer");
    neuronte_draw_scalar(n, buf, BW, BW, BH, 0, 0, CW, CH, 'W', 0xFFFF0000u);
    neuronte_coverage(n, 'W', CW, CH, 0, cov);
    for (i = 0; i < CW * CH; i++) {
        uint32_t d = buf[(i / CW) * BW + i % CW];
        if (d >> 24 != 0xFF)
            FAIL("opaque destination lost alpha");
        if (cov[i] >= 0.999f && d != 0xFFFF0000u)
            FAIL("full ink pixel is %08X", (unsigned)d);
        if (cov[i] == 0.0f && d != 0xFF336699u)
            FAIL("empty pixel changed to %08X", (unsigned)d);
        if (failed)
            break;
    }

    if (neuronte_set_samples(n, 9) != NEURONTE_ERR_ARG || neuronte_set_samples(n, 1) != NEURONTE_OK)
        FAIL("set_samples bounds");

    neuronte_close(n);
    free(copy);
    free(data);
    puts(failed ? "test_api: FAILED" : "test_api: passed");
    return failed;
}
