/* Loader refusals, drawing, clipping, blending and bundles. MIT licence.
 * usage: test_api WEIGHTS.nrt [--full] [--accent] [--pixel]
 * --full adds checks of box drawing, blocks and Braille, --accent of
 * accented letters, and --pixel of the sextants and octants, for weights
 * trained on them. Given a one-net file, it also checks the loader's
 * refusals by damaging that file, and builds bundles from it to check the
 * router. Given a bundle, it checks the drawing only. */
#define _POSIX_C_SOURCE 200809L
#include "neuronte.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

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

static float sum_of(const float *c, int n)
{
    float s = 0;
    int i;
    for (i = 0; i < n; i++)
        s += c[i];
    return s;
}

/* The most ink in column x (or row y, if x < 0) of a cw x ch cell. */
static float most_in(const float *c, int cw, int ch, int x, int y)
{
    float m = 0;
    int i;
    for (i = 0; i < (x >= 0 ? ch : cw); i++) {
        float v = x >= 0 ? c[i * cw + x] : c[y * cw + i];
        m = v > m ? v : m;
    }
    return m;
}

/* A net of hidden width 8 with every weight 0: f is 0, coverage 0.5. */
static unsigned char *zero_net(const unsigned char *like, size_t *len)
{
    size_t params = 8 * 90 + 8 + 2 * (8 * 8 + 8) + 8 + 1;
    unsigned char *p = calloc(1, 204 + 4 * params);
    if (p) {
        memcpy(p, like, 204);
        put32(p + 20, 8);
    }
    *len = 204 + 4 * params;
    return p;
}

/* A bundle of nets a and b, with the ranges given as (first, last, net)
 * triples, a fallback net and, when g > 0, a gate of hidden width g whose
 * parameters are gate (g x 64 l1 weight, g bias, 2 x g out weight, 2 bias). */
static unsigned char *bundle(const unsigned char *a, size_t alen, const unsigned char *b, size_t blen,
                             const uint32_t *ranges, uint32_t nranges, uint32_t fallback, uint32_t g,
                             const float *gate, const unsigned char *masks_from, size_t *len)
{
    size_t gp = g ? 43 + (size_t)g * 64 + g + 2 * g + 2 : 0, off = 28, i;
    unsigned char *p;
    *len = 28 + 8 + 12 * (size_t)nranges + 4 * gp + alen + blen;
    p = malloc(*len);
    if (!p)
        return NULL;
    memcpy(p, "NEURONTE", 8);
    put32(p + 8, 2);
    put32(p + 12, 2);
    put32(p + 16, nranges);
    put32(p + 20, fallback);
    put32(p + 24, g);
    put32(p + off, (uint32_t)alen);
    put32(p + off + 4, (uint32_t)blen);
    off += 8;
    for (i = 0; i < 3 * (size_t)nranges; i++, off += 4)
        put32(p + off, ranges[i]);
    if (g) {
        memcpy(p + off, masks_from + 32, 43 * 4);
        off += 43 * 4;
        for (i = 0; i < gp - 43; i++, off += 4) {
            uint32_t u;
            memcpy(&u, &gate[i], 4);
            put32(p + off, u);
        }
    }
    memcpy(p + off, a, alen);
    memcpy(p + off + alen, b, blen);
    return p;
}

static void bundle_checks(const unsigned char *data, size_t len)
{
    enum { W = 16, H = 32, G = 8 };
    static const uint32_t az[] = {0x41, 0x5A, 1};
    float c[W * H], d[W * H], gate[G * 64 + G + 2 * G + 2];
    size_t zlen, blen, i;
    unsigned char *z = zero_net(data, &zlen), *b;
    neuronte *n, *one;

    if (!z || neuronte_open(data, len, &one) != NEURONTE_OK) {
        FAIL("bundle checks: cannot open the net");
        free(z);
        return;
    }

    /* Net 1, all zeros, draws A..Z; the real net draws the rest. */
    b = bundle(data, len, z, zlen, az, 1, 0, 0, NULL, data, &blen);
    if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK) {
        FAIL("a bundle of two nets refused");
    } else {
        if (neuronte_nets(n) != 2 || neuronte_nets(one) != 1)
            FAIL("nets: %d in the bundle, %d in the one-net file", neuronte_nets(n), neuronte_nets(one));
        if (neuronte_route(n, 'A') != 1 || neuronte_route(n, 'Z') != 1 || neuronte_route(n, '@') != 0 ||
            neuronte_route(n, '[') != 0 || neuronte_route(n, 0x4E2D) != 0 || neuronte_route(one, 'A') != 0)
            FAIL("table routes wrong");
        if (neuronte_parameters(n) != neuronte_parameters(one) + 881)
            FAIL("bundle has %zu parameters", neuronte_parameters(n));
        neuronte_coverage(n, 'A', W, H, 0, c);
        for (i = 0; i < W * H; i++)
            if (c[i] != 0.5f) {
                FAIL("A in the bundle is not drawn by the zero net");
                break;
            }
        neuronte_coverage(n, 'g', W, H, 0, c);
        neuronte_coverage(one, 'g', W, H, 0, d);
        if (memcmp(c, d, sizeof c) != 0)
            FAIL("g in the bundle differs from the net alone");
        {
            uint32_t px[W * H], q[W * H];
            for (i = 0; i < W * H; i++)
                px[i] = q[i] = 0xFF000000u;
            neuronte_draw_scalar(n, px, W, W, H, 0, 0, W, H, 'g', 0xFFFFFFFFu);
            neuronte_draw_scalar(one, q, W, W, H, 0, 0, W, H, 'g', 0xFFFFFFFFu);
            if (memcmp(px, q, sizeof px) != 0)
                FAIL("draw g in the bundle differs from the net alone");
        }
        /* The same bytes from a file. */
        {
            char path[] = "/tmp/neuronte-test-XXXXXX";
            int fd = mkstemp(path);
            neuronte *f;
            if (fd < 0 || write(fd, b, blen) != (ssize_t)blen) {
                FAIL("cannot write a bundle file");
            } else {
                if (neuronte_open_file(path, &f) != NEURONTE_OK) {
                    FAIL("open_file refused a bundle");
                } else {
                    neuronte_coverage(f, 'g', W, H, 0, c);
                    if (memcmp(c, d, sizeof c) != 0 || neuronte_route(f, 'Q') != 1)
                        FAIL("bundle from a file differs");
                    neuronte_close(f);
                }
                if (write(fd, "", 1) != 1 || neuronte_open_file(path, &f) != NEURONTE_ERR_FORMAT)
                    FAIL("a bundle file one byte long accepted");
                if (ftruncate(fd, (off_t)blen - 1) != 0 || neuronte_open_file(path, &f) != NEURONTE_ERR_FORMAT)
                    FAIL("a bundle file one byte short accepted");
                if (ftruncate(fd, 30) != 0 || neuronte_open_file(path, &f) != NEURONTE_ERR_FORMAT)
                    FAIL("a bundle file cut in its header accepted");
            }
            if (fd >= 0) {
                close(fd);
                unlink(path);
            }
        }
        neuronte_close(n);
    }
    free(b);

    b = bundle(data, len, z, zlen, az, 1, 1, 0, NULL, data, &blen);
    if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK) {
        FAIL("a bundle with fallback 1 refused");
    } else {
        if (neuronte_route(n, 'a') != 1 || neuronte_route(n, 'A') != 1)
            FAIL("fallback 1 not taken");
        neuronte_close(n);
    }
    free(b);

    /* A gate whose hidden unit 3 is code bit 5 of the scalar (+1 or -1):
     * net 1 when bit 5 is set, net 0 when clear. */
    memset(gate, 0, sizeof gate);
    gate[3 * 64 + 5] = 1.0f;          /* l1 row 3, column 5 */
    gate[G * 64 + G + 1 * G + 3] = 2.0f; /* out row 1, column 3 */
    gate[G * 64 + G + 2 * G] = 1.0f;     /* out bias of net 0 */
    b = bundle(data, len, z, zlen, az, 1, 0, G, gate, data, &blen);
    if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK) {
        FAIL("a bundle with a gate refused");
    } else {
        /* 0x40 and 0x80 have bit 5 clear, 0x60 and 0x7E set; A..Z by table. */
        if (neuronte_route(n, 0x40) != 0 || neuronte_route(n, 0x80) != 0 || neuronte_route(n, 0x60) != 1 ||
            neuronte_route(n, 0x7E) != 1 || neuronte_route(n, 'A') != 1 || neuronte_route(n, 'Z') != 1)
            FAIL("gate routes wrong");
        if (neuronte_parameters(n) != neuronte_parameters(one) + 881 + G * 64 + G + 2 * G + 2)
            FAIL("bundle with a gate has %zu parameters", neuronte_parameters(n));
        neuronte_close(n);
    }
    free(b);

    /* Refusals. */
    {
        static const uint32_t overlap[] = {0x41, 0x5A, 1, 0x50, 0x60, 0};
        static const uint32_t unsorted[] = {0x61, 0x7A, 1, 0x41, 0x5A, 0};
        static const uint32_t bad_net[] = {0x41, 0x5A, 2};
        static const uint32_t past[] = {0x41, 0x110000, 1};
        static const uint32_t reversed[] = {0x5A, 0x41, 1};
        struct { const char *name; const uint32_t *r; uint32_t nr, fb, g; } cases[] = {
            {"overlapping ranges", overlap, 2, 0, 0},  {"unsorted ranges", unsorted, 2, 0, 0},
            {"a range to net 2 of 2", bad_net, 1, 0, 0}, {"a range past U+10FFFF", past, 1, 0, 0},
            {"a range ending before it starts", reversed, 1, 0, 0}, {"fallback 2 of 2", az, 1, 2, 0},
            {"gate width 257", az, 1, 0, 257},
        };
        unsigned char *gb;
        size_t gl;
        for (i = 0; i < sizeof cases / sizeof cases[0]; i++) {
            float *big = calloc(257 * 64 + 257 + 2 * 257 + 2, sizeof *big);
            b = bundle(data, len, z, zlen, cases[i].r, cases[i].nr, cases[i].fb, cases[i].g, big, data, &blen);
            if (b)
                expect_open(cases[i].name, b, blen, NEURONTE_ERR_FORMAT);
            free(b);
            free(big);
        }
        b = bundle(data, len, z, zlen, az, 1, 0, 0, NULL, data, &blen);
        expect_open("bundle one byte short", b, blen - 1, NEURONTE_ERR_FORMAT);
        put32(b + 12, 0);
        expect_open("bundle of 0 nets", b, blen, NEURONTE_ERR_FORMAT);
        put32(b + 12, 17);
        expect_open("bundle of 17 nets", b, blen, NEURONTE_ERR_FORMAT);
        put32(b + 12, 2);
        /* The two lengths moved by 4 each way: the total is right, the
         * nets are not. */
        put32(b + 28, (uint32_t)len - 4);
        put32(b + 32, (uint32_t)zlen + 4);
        expect_open("net lengths shifted", b, blen, NEURONTE_ERR_FORMAT);
        put32(b + 28, (uint32_t)len);
        put32(b + 32, (uint32_t)zlen);
        expect_open("bundle restored", b, blen, NEURONTE_OK);
        put32(b + 28 + 8 + 12 + len + 20, 100); /* net 1 hidden width */
        expect_open("a net of width 100 in a bundle", b, blen, NEURONTE_ERR_SHAPE);
        free(b);

        gb = bundle(data, len, z, zlen, az, 1, 0, G, gate, data, &gl);
        put32(gb + 28 + 8 + 12, 0);
        expect_open("gate with a zero mask", gb, gl, NEURONTE_ERR_FORMAT);
        free(gb);
        gb = bundle(data, len, z, zlen, az, 1, 0, G, gate, data, &gl);
        put32(gb + 28 + 8 + 12 + 43 * 4 + 4 * 7, 0x7FC00000u);
        expect_open("gate with a NaN", gb, gl, NEURONTE_ERR_FORMAT);
        free(gb);
    }
    {
        unsigned char *v1 = malloc(len);
        memcpy(v1, data, len);
        put32(v1 + 8, 2);
        expect_open("a one-net file marked version 2", v1, len, NEURONTE_ERR_FORMAT);
        free(v1);
    }
    neuronte_close(one);
    free(z);
}

static void full_checks(neuronte *n)
{
    enum { W = 16, H = 32 };
    float c[W * H], d[W * H];
    int i;

    /* Box lines reach the cell edges, so neighbouring cells join. */
    neuronte_coverage(n, 0x2500, W, H, 0, c);
    if (most_in(c, W, H, 0, 0) < 0.9f || most_in(c, W, H, W - 1, 0) < 0.9f)
        FAIL("U+2500 does not reach both sides");
    if (most_in(c, W, H, -1, 0) > 0.1f || most_in(c, W, H, -1, H - 1) > 0.1f)
        FAIL("U+2500 has ink at the top or bottom");
    neuronte_coverage(n, 0x2502, W, H, 0, c);
    if (most_in(c, W, H, -1, 0) < 0.9f || most_in(c, W, H, -1, H - 1) < 0.9f)
        FAIL("U+2502 does not reach the top and bottom");
    neuronte_coverage(n, 0x253C, W, H, 0, c);
    if (most_in(c, W, H, 0, 0) < 0.9f || most_in(c, W, H, W - 1, 0) < 0.9f ||
        most_in(c, W, H, -1, 0) < 0.9f || most_in(c, W, H, -1, H - 1) < 0.9f)
        FAIL("U+253C does not reach all four sides");

    /* Blocks. */
    neuronte_coverage(n, 0x2588, W, H, 0, c);
    for (i = 0; i < W * H; i++)
        if (c[i] < 0.97f) {
            FAIL("U+2588 has a gap of %g at %d", c[i], i);
            break;
        }
    neuronte_coverage(n, 0x2580, W, H, 0, c);
    if (sum_of(c, W * H / 2) < 0.95f * W * H / 2 || sum_of(c + W * H / 2, W * H / 2) > 0.05f * W * H / 2)
        FAIL("U+2580 is not the upper half");

    /* Blank characters. */
    neuronte_coverage(n, 0x2800, W, H, 0, c);
    neuronte_coverage(n, 0x00A0, W, H, 0, d);
    for (i = 0; i < W * H; i++)
        if (c[i] > 0.05f || d[i] > 0.05f) {
            FAIL("U+2800 or U+00A0 has ink at %d", i);
            break;
        }

    /* Eight Braille dots carry about eight times the ink of one. */
    neuronte_coverage(n, 0x28FF, W, H, 0, c);
    neuronte_coverage(n, 0x2801, W, H, 0, d);
    if (!(sum_of(c, W * H) > 6.5f * sum_of(d, W * H) && sum_of(c, W * H) < 9.5f * sum_of(d, W * H)))
        FAIL("U+28FF has %g ink against %g for U+2801", sum_of(c, W * H), sum_of(d, W * H));
}

/* The share of the inked pixels of two cells, over rows r0..r1, that
 * both ink: 1 when they agree there. */
static float agree(const float *a, const float *b, int w, int r0, int r1)
{
    int i, both = 0, either = 0;
    for (i = r0 * w; i <= r1 * w + w - 1; i++) {
        int x = a[i] > 0.5f, y = b[i] > 0.5f;
        both += x && y;
        either += x || y;
    }
    return either ? (float)both / (float)either : 1.0f;
}

static void accent_checks(neuronte *n)
{
    enum { W = 16, H = 32 };
    /* Lowercase letters with a mark above, and the letter without it. In
     * a 16 x 32 cell the x-height is row 12.8 and the baseline row 24. */
    static const uint32_t above[][2] = {{0xE9, 'e'}, {0xE4, 'a'}, {0xF4, 'o'}, {0xF1, 'n'},
                                        {0xFC, 'u'}, {0x161, 's'}, {0x17E, 'z'}, {0x107, 'c'}};
    float a[W * H], b[W * H];
    size_t k;
    int i;

    for (k = 0; k < sizeof above / sizeof above[0]; k++) {
        float ink = 0, base_ink = 0;
        neuronte_coverage(n, above[k][0], W, H, 0, a);
        neuronte_coverage(n, above[k][1], W, H, 0, b);
        if (agree(a, b, W, 14, 31) < 0.85f)
            FAIL("U+%04X is not its letter below the x-height (%.2f)", (unsigned)above[k][0],
                 agree(a, b, W, 14, 31));
        for (i = 0; i < W * 11; i++) {
            ink += a[i];
            base_ink += b[i];
        }
        if (ink < 4.0f || base_ink > 1.0f)
            FAIL("U+%04X has %.1f ink above its letter, which has %.1f", (unsigned)above[k][0], ink, base_ink);
    }
    /* A mark below: c with cedilla is c down to the baseline. */
    neuronte_coverage(n, 0xE7, W, H, 0, a);
    neuronte_coverage(n, 'c', W, H, 0, b);
    {
        float ink = 0, base_ink = 0;
        for (i = W * 26; i < W * H; i++) {
            ink += a[i];
            base_ink += b[i];
        }
        if (agree(a, b, W, 12, 23) < 0.85f || ink < 4.0f || base_ink > 1.0f)
            FAIL("U+00E7 is not c with a mark below (%.2f, %.1f, %.1f)", agree(a, b, W, 12, 23), ink, base_ink);
    }
}

/* The 26 octant patterns Unicode encodes outside U+1CD00..U+1CDE5, and
 * their characters: space, 17 block elements and 8 substitutes. Bit n - 1
 * is cell n of the lattice 1 2 / 3 4 / 5 6 / 7 8. */
static const uint32_t elsewhere[26][2] = {
    {0, 0x20},      {255, 0x2588},   {15, 0x2580},    {240, 0x2584},   {85, 0x258C},
    {170, 0x2590},  {192, 0x2582},   {252, 0x2586},   {80, 0x2596},    {160, 0x2597},
    {5, 0x2598},    {245, 0x2599},   {165, 0x259A},   {95, 0x259B},    {175, 0x259C},
    {10, 0x259D},   {90, 0x259E},    {250, 0x259F},   {3, 0x1FB82},    {63, 0x1FB85},
    {20, 0x1FBE6},  {40, 0x1FBE7},   {128, 0x1CEA0},  {64, 0x1CEA3},   {1, 0x1CEA8},
    {2, 0x1CEAB}};

/* The character for an octant pattern. An octant's code point is its
 * pattern's rank among the 230 patterns not encoded elsewhere;
 * train/mosaics.py checks that against Unicode's data. */
static uint32_t octant_char(int bits)
{
    int i, b, rank = 0;
    for (i = 0; i < 26; i++)
        if ((int)elsewhere[i][0] == bits)
            return elsewhere[i][1];
    for (b = 0; b < bits; b++) {
        int other = 0;
        for (i = 0; i < 26; i++)
            other |= (int)elsewhere[i][0] == b;
        rank += !other;
    }
    return 0x1CD00 + (uint32_t)rank;
}

/* Each sub-cell of a 2-column lattice of `rows` rows, at 16 x 32 with
 * 2 x 2 samples, is inked (mean above 0.9) when its bit is set and clear
 * (below 0.1) when not, leaving out the pixels within one pixel of an inner
 * boundary. A full column also inks the cell's top and bottom rows, so
 * cells stacked in a column show no gap. */
static void lattice_check(neuronte *n, uint32_t s, int bits, int rows)
{
    enum { W = 16, H = 32 };
    float c[W * H];
    int r, k, x, y;

    neuronte_coverage(n, s, W, H, 2, c);
    for (r = 0; r < rows; r++)
        for (k = 0; k < 2; k++) {
            float top = (float)H * r / rows, bot = (float)H * (r + 1) / rows, sum = 0, mean;
            int count = 0, set = bits >> (2 * r + k) & 1;
            for (y = 0; y < H; y++) {
                float cy = y + 0.5f;
                if (cy < top || cy >= bot || (r > 0 && cy - top < 1.0f) || (r < rows - 1 && bot - cy < 1.0f))
                    continue;
                for (x = k * W / 2; x < (k + 1) * W / 2; x++)
                    if (fabsf(x + 0.5f - W / 2.0f) >= 1.0f) {
                        sum += c[y * W + x];
                        count++;
                    }
            }
            mean = sum / (float)count;
            if (set ? mean < 0.9f : mean > 0.1f)
                FAIL("U+%04X sub-cell %d has mean coverage %.3f", (unsigned)s, 2 * r + k + 1, mean);
        }
    for (k = 0; k < 2; k++) {
        int full = 1;
        for (r = 0; r < rows; r++)
            full &= bits >> (2 * r + k) & 1;
        if (full)
            for (x = k * W / 2; x < (k + 1) * W / 2; x++)
                if (fabsf(x + 0.5f - W / 2.0f) >= 1.0f && (c[x] < 0.9f || c[(H - 1) * W + x] < 0.9f)) {
                    FAIL("U+%04X column %d does not reach the top and bottom", (unsigned)s, k + 1);
                    break;
                }
    }
}

static void pixel_checks(neuronte *n)
{
    float c[8], worst = 0;
    int k, bits, i, wrong = 0;

    /* Sextants: U+1FB00 + k is pattern k + 1, skipping 21 and 42, the
     * left and right half blocks. */
    for (k = 0; k < 60; k++) {
        int p = k + 1;
        p += p >= 21;
        p += p >= 42;
        lattice_check(n, 0x1FB00 + (uint32_t)k, p, 3);
    }
    /* Every octant pattern, the block elements and substitutes among them. */
    for (bits = 1; bits < 256; bits++)
        lattice_check(n, octant_char(bits), bits, 4);

    /* At a 2 x 4 cell each sub-cell is one pixel. Video at that size shows
     * a frame exactly only if every pixel is on the right side of 0.5. */
    for (bits = 1; bits < 256; bits++) {
        neuronte_coverage(n, octant_char(bits), 2, 4, 0, c);
        for (i = 0; i < 8; i++) {
            float want = (float)(bits >> i & 1), d = fabsf(c[i] - want);
            wrong += d >= 0.5f;
            worst = d > worst ? d : worst;
        }
    }
    if (wrong || worst > 0.25f)
        FAIL("at 2 x 4, %d of 2040 octant pixels are wrong; the largest distance from 0 or 1 is %.3f",
             wrong, worst);
}

int main(int argc, char **argv)
{
    unsigned char *data, *copy;
    size_t len;
    neuronte *n;
    enum { CW = 16, CH = 32, BW = 64, BH = 48 };
    float cov[CW * CH], cov2[CW * CH];
    uint32_t buf[BW * BH], ref[BW * BH];
    int i, rc, bundled, full = 0, accent = 0, pixel = 0;

    for (i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--full") == 0)
            full = 1;
        else if (strcmp(argv[i], "--accent") == 0)
            accent = 1;
        else if (strcmp(argv[i], "--pixel") == 0)
            pixel = 1;
        else
            argc = 0;
    }
    if (argc < 2) {
        fprintf(stderr, "usage: %s WEIGHTS.nrt [--full] [--accent] [--pixel]\n", argv[0]);
        return 2;
    }
    data = slurp(argv[1], &len);
    if (!data) {
        perror(argv[1]);
        return 2;
    }
    copy = malloc(len + 1);
    bundled = len >= 12 && data[8] == 2;
    if (bundled)
        goto drawing;

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
    put32(copy + 8, 3);
    expect_open("version 3", copy, len, NEURONTE_ERR_FORMAT);
    memcpy(copy, data, len);
    put32(copy + 20, 64);
    expect_open("hidden width 64 in a file of another width", copy, len, NEURONTE_ERR_FORMAT);
    put32(copy + 20, 100);
    expect_open("hidden width 100", copy, len, NEURONTE_ERR_SHAPE);
    put32(copy + 20, 0);
    expect_open("hidden width 0", copy, len, NEURONTE_ERR_SHAPE);
    put32(copy + 20, 2048);
    expect_open("hidden width 2048", copy, len, NEURONTE_ERR_SHAPE);
    {
        size_t zlen;
        unsigned char *z = zero_net(data, &zlen);
        if (!z || neuronte_open(z, zlen, &n) != NEURONTE_OK) {
            FAIL("width 8 net refused");
        } else {
            if (neuronte_parameters(n) != 881)
                FAIL("width 8 net has %zu parameters, want 881", neuronte_parameters(n));
            neuronte_coverage(n, 'A', CW, CH, 0, cov);
            for (i = 0; i < CW * CH; i++)
                if (cov[i] != 0.5f) {
                    FAIL("zero net gives coverage %g", cov[i]);
                    break;
                }
            neuronte_close(n);
        }
        free(z);
    }
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

drawing:
    rc = neuronte_open(data, len, &n);
    if (rc != NEURONTE_OK) {
        printf("cannot open weights (%d)\n", rc);
        return 1;
    }
    if (!bundled && neuronte_parameters(n) != (len - 204) / 4)
        FAIL("parameters %zu for a file of %zu bytes", neuronte_parameters(n), len);
    if (bundled && (neuronte_nets(n) < 2 || neuronte_parameters(n) == 0 ||
                    4 * neuronte_parameters(n) >= len))
        FAIL("bundle of %d nets, %zu parameters, %zu bytes", neuronte_nets(n), neuronte_parameters(n), len);
    {
        neuronte *f;
        if (neuronte_open_file(argv[1], &f) != NEURONTE_OK) {
            FAIL("open_file refused the file open took");
        } else {
            neuronte_coverage(n, 'g', CW, CH, 0, cov);
            neuronte_coverage(f, 'g', CW, CH, 0, cov2);
            if (memcmp(cov, cov2, sizeof cov) != 0)
                FAIL("open_file and open draw g differently");
            neuronte_close(f);
        }
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

    /* The cache: a cell drawn after 1,100 others, which push it out, is
     * drawn again the same. */
    {
        enum { SW = 4, SH = 8 };
        uint32_t a[SW * SH], b[SW * SH], junk[SW * SH];
        uint32_t k;
        for (i = 0; i < SW * SH; i++)
            a[i] = b[i] = 0xFF000000u;
        neuronte_draw_scalar(n, a, SW, SW, SH, 0, 0, SW, SH, '&', 0xFFFFFFFFu);
        for (k = 0x100; k < 0x100 + 1100; k++)
            neuronte_draw_scalar(n, junk, SW, SW, SH, 0, 0, SW, SH, k, 0xFFFFFFFFu);
        neuronte_draw_scalar(n, b, SW, SW, SH, 0, 0, SW, SH, '&', 0xFFFFFFFFu);
        if (memcmp(a, b, sizeof a) != 0)
            FAIL("a cell drawn after the cache turned over differs");
    }

    if (neuronte_set_samples(n, 9) != NEURONTE_ERR_ARG || neuronte_set_samples(n, 1) != NEURONTE_OK)
        FAIL("set_samples bounds");

    if (full)
        full_checks(n);
    if (accent)
        accent_checks(n);
    if (pixel)
        pixel_checks(n);
    if (!bundled)
        bundle_checks(data, len);

    neuronte_close(n);
    free(copy);
    free(data);
    puts(failed ? "test_api: FAILED" : "test_api: passed");
    return failed;
}
