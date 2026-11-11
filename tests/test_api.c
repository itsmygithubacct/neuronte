/* Loader refusals, drawing, clipping, blending and bundles. MIT licence.
 * usage: test_api WEIGHTS.nrt [--full] [--accent] [--pixel] [--colour [--trained]]
 * --full adds checks of box drawing, blocks and Braille, --accent of
 * accented letters, and --pixel of the sextants and octants, for weights
 * trained on them. Given a one-net file, it also checks the loader's
 * refusals by damaging that file, and builds bundles from it to check the
 * router. Given a bundle, it checks the drawing only. --colour checks a
 * version 3 file: the palette, the head, the edge table and the composite.
 * With --trained the file is a trained icon net, not the test fixture: K
 * may be more than 3, and a scalar outside the labelled set may return any
 * entry, since only the fixture's head is built to return 0 for it.
 * Either way it checks the advance table and the drawing file on images
 * it builds. */
#define _POSIX_C_SOURCE 200809L
#include "neuronte.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int failed;
static int trained_net; /* --trained: a trained colour net, not the fixture */
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

static uint32_t get32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint32_t get16(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8;
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
        static const uint32_t past[] = {0x41, 0x200000, 1};
        static const uint32_t reversed[] = {0x5A, 0x41, 1};
        struct { const char *name; const uint32_t *r; uint32_t nr, fb, g; } cases[] = {
            {"overlapping ranges", overlap, 2, 0, 0},  {"unsorted ranges", unsorted, 2, 0, 0},
            {"a range to net 2 of 2", bad_net, 1, 0, 0}, {"a range past the 21-bit code limit", past, 1, 0, 0},
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

    /* A distance net has no edge record, so asking for snapping leaves the
     * line where it was, and the horizontal stroke still meets the vertical. */
    {
        float hline[W * H], vline[W * H];
        int row = 0, col = 0, x, y;
        float best;
        if (neuronte_set_snap(n, -1) != NEURONTE_OK)
            FAIL("set_snap(-1) on a distance net");
        neuronte_coverage(n, 0x2500, W, H, 0, hline);
        if (neuronte_set_snap(n, 64) != NEURONTE_OK)
            FAIL("set_snap(64)");
        neuronte_coverage(n, 0x2500, W, H, 0, c);
        if (memcmp(hline, c, sizeof hline) != 0)
            FAIL("U+2500 changed when snapping was asked for");
        neuronte_set_snap(n, 0);
        neuronte_coverage(n, 0x2500, W, H, 0, c);
        if (memcmp(hline, c, sizeof hline) != 0)
            FAIL("U+2500 changed with snapping off");
        neuronte_set_snap(n, 64);
        neuronte_coverage(n, 0x2502, W, H, 0, vline);
        neuronte_set_snap(n, 0);
        neuronte_coverage(n, 0x2502, W, H, 0, c);
        if (memcmp(vline, c, sizeof vline) != 0)
            FAIL("U+2502 changed with snapping off");
        neuronte_set_snap(n, -1);
        best = -1.0f;
        for (y = 0; y < H; y++) {
            float s = 0;
            for (x = 0; x < W; x++)
                s += hline[y * W + x];
            if (s > best) {
                best = s;
                row = y;
            }
        }
        best = -1.0f;
        for (x = 0; x < W; x++) {
            float s = 0;
            for (y = 0; y < H; y++)
                s += vline[y * W + x];
            if (s > best) {
                best = s;
                col = x;
            }
        }
        if (hline[row * W] < 0.9f || hline[row * W + (W - 1)] < 0.9f)
            FAIL("U+2500's inked row does not reach both sides");
        if (vline[col] < 0.9f || vline[(H - 1) * W + col] < 0.9f)
            FAIL("U+2502's inked column does not reach both ends");
        if (hline[row * W + col] < 0.9f || vline[row * W + col] < 0.9f)
            FAIL("U+2500 and U+2502 do not meet");
    }

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

/* A bundle of n whole weight files, no gate, with the given ranges. */
static unsigned char *bundle_n(const unsigned char **parts, const size_t *lens, int n,
                               const uint32_t *ranges, uint32_t nranges, uint32_t fallback, size_t *len)
{
    size_t off, i;
    unsigned char *p;
    *len = 28 + 4 * (size_t)n + 12 * (size_t)nranges;
    for (i = 0; i < (size_t)n; i++)
        *len += lens[i];
    p = malloc(*len);
    if (!p)
        return NULL;
    memcpy(p, "NEURONTE", 8);
    put32(p + 8, 2);
    put32(p + 12, (uint32_t)n);
    put32(p + 16, nranges);
    put32(p + 20, fallback);
    put32(p + 24, 0);
    off = 28;
    for (i = 0; i < (size_t)n; i++, off += 4)
        put32(p + off, (uint32_t)lens[i]);
    for (i = 0; i < nranges; i++, off += 12) {
        put32(p + off, ranges[3 * i]);
        put32(p + off + 4, ranges[3 * i + 1]);
        put32(p + off + 8, ranges[3 * i + 2]);
    }
    for (i = 0; i < (size_t)n; i++) {
        memcpy(p + off, parts[i], lens[i]);
        off += lens[i];
    }
    return p;
}

/* A distance net of hidden width 8 and zero weights, with the colour file's
 * tau and parity masks. Coverage of it is 0.5. */
static unsigned char *mono8(const unsigned char *colour, size_t *len)
{
    size_t params = 8 * 90 + 8 + 2 * (8 * 8 + 8) + 8 + 1;
    unsigned char *p = calloc(1, 204 + 4 * params);
    if (!p)
        return NULL;
    memcpy(p, colour, 32);
    put32(p + 8, 1);
    put32(p + 20, 8);
    memcpy(p + 32, colour + 56, 43 * 4);
    *len = 204 + 4 * params;
    return p;
}

/* The synthetic version 3 file. The four labelled glyphs and the entries
 * their drawings name, padded out to K with entry 0. */
static void colour_checks(const unsigned char *data, size_t len, const char *path)
{
    static const uint32_t labelled[] = {0xE654, 0xF04C, 0xF007A, 0xF036D};
    static const uint8_t want[4][3] = {{2, 1, 0}, {0, 0, 0}, {2, 0, 0}, {0, 1, 2}};
    enum { W = 16, H = 32 };
    neuronte *n = NULL, *f = NULL;
    uint32_t Hden, K, R, E, snap;
    size_t trunk, headn, off, i;
    int one_edge = 0, g, layer, px;
    uint8_t pal[96], ent[16];
    float *masks = NULL, *masks2 = NULL;
    float cov[W * H], cov2[W * H];

    if (len < 420 || get32(data + 8) != 3) {
        FAIL("colour checks need a version 3 file");
        return;
    }
    Hden = get32(data + 20);
    K = get32(data + 32);
    R = get32(data + 44);
    E = get32(data + 48);
    snap = get32(data + 52);
    if (K < 1 || K > 16 || R < 8 || R % 8 != 0 || snap != 14 || E < 1) {
        FAIL("colour header K %u R %u snap %u records %u", K, R, snap, E);
        return;
    }
    trunk = 2 * (size_t)Hden * Hden + (93 + (size_t)K) * Hden + K;
    headn = (size_t)R * (65 + 5 * (size_t)K) + 5 * (size_t)K;
    expect_open("colour file", data, len, NEURONTE_OK);
    expect_open("colour one byte short", data, len - 1, NEURONTE_ERR_FORMAT);
    {
        unsigned char *copy = malloc(len + 1);
        if (!copy) {
            FAIL("out of memory");
            return;
        }
        memcpy(copy, data, len);
        copy[len] = 0;
        expect_open("colour one byte long", copy, len + 1, NEURONTE_ERR_FORMAT);
        copy[0] = 'X';
        expect_open("colour bad magic", copy, len, NEURONTE_ERR_FORMAT);
        free(copy);
    }
    if (neuronte_open(data, len, &n) != NEURONTE_OK) {
        FAIL("colour file did not open");
        return;
    }
    if (neuronte_layers(n) != (int)K)
        FAIL("layers %d, file says %u", neuronte_layers(n), K);
    if (neuronte_parameters(n) != trunk + headn)
        FAIL("parameters %zu, trunk %zu head %zu", neuronte_parameters(n), trunk, headn);
    if (neuronte_palette(n, 0, pal) != NEURONTE_OK || memcmp(pal, data + 228, 96) != 0)
        FAIL("dark palette differs from the file");
    if (neuronte_palette(n, 1, pal) != NEURONTE_OK || memcmp(pal, data + 324, 96) != 0)
        FAIL("light palette differs from the file");
    if (neuronte_set_theme(n, 2) != NEURONTE_ERR_ARG || neuronte_set_snap(n, -2) != NEURONTE_ERR_ARG)
        FAIL("theme and snap bounds");
    if (neuronte_open_file(path, &f) != NEURONTE_OK) {
        FAIL("open_file refused the colour file");
    } else {
        neuronte_coverage(n, 0xF04C, W, H, 0, cov);
        neuronte_coverage(f, 0xF04C, W, H, 0, cov2);
        if (memcmp(cov, cov2, sizeof cov) != 0)
            FAIL("open_file and open disagree on U+F04C");
        neuronte_close(f);
    }
    {
        char tmp[] = "/tmp/neuronte-colour-XXXXXX";
        int fd = mkstemp(tmp);
        if (fd < 0 || write(fd, data, len) != (ssize_t)len) {
            FAIL("cannot write the colour file");
        } else {
            if (write(fd, "", 1) != 1 || neuronte_open_file(tmp, &f) != NEURONTE_ERR_FORMAT)
                FAIL("a colour file one byte long was accepted");
            if (ftruncate(fd, (off_t)len - 1) != 0 || neuronte_open_file(tmp, &f) != NEURONTE_ERR_FORMAT)
                FAIL("a colour file one byte short was accepted");
            if (ftruncate(fd, 100) != 0 || neuronte_open_file(tmp, &f) != NEURONTE_ERR_FORMAT)
                FAIL("a colour file cut in its header was accepted");
        }
        if (fd >= 0) {
            close(fd);
            unlink(tmp);
        }
    }

    off = 420 + 4 * (trunk + headn);
    for (i = 0; i < E; i++) {
        uint32_t layer_i, t;
        if (off + 4 > len)
            break;
        off += 4;
        for (layer_i = 0; layer_i < K; layer_i++) {
            uint32_t nx, ny;
            if (off + 4 > len)
                goto edges_done;
            nx = get16(data + off);
            ny = get16(data + off + 2);
            off += 4;
            if (off + (size_t)(nx + ny) * 8 > len)
                goto edges_done;
            for (t = 0; t < nx + ny; t++, off += 8) {
                uint32_t bits = get32(data + off), side = get32(data + off + 4);
                float pos;
                memcpy(&pos, &bits, sizeof pos);
                if (side > 1 || pos != pos)
                    FAIL("edge %u of record %zu is damaged", t, i);
                else
                    one_edge = 1;
            }
        }
    }
edges_done:
    if (off != len || !one_edge)
        FAIL("edge table did not round-trip (%zu bytes left, edge %d)", len - (off < len ? off : len), one_edge);

    masks = malloc((size_t)K * W * H * sizeof *masks);
    masks2 = malloc((size_t)K * W * H * sizeof *masks2);
    if (!masks || !masks2) {
        FAIL("out of memory");
        goto bundles;
    }
    if (trained_net ? K < 3 : K != 3) {
        FAIL("the labelled-entry check wants K = 3%s, the file says %u", trained_net ? " or more" : "", K);
        goto bundles;
    }
    for (g = 0; g < 4; g++) {
        if (neuronte_coverage_layers(n, labelled[g], W, H, 0, masks, ent) != NEURONTE_OK)
            FAIL("coverage_layers U+%X", labelled[g]);
        for (layer = 0; layer < (int)K; layer++) {
            unsigned w = layer < 3 ? want[g][layer] : 0;
            if (ent[layer] != w)
                FAIL("U+%X layer %d entry %u, drawings say %u", labelled[g], layer, ent[layer], w);
        }
    }
    if (neuronte_coverage_layers(n, 0x41, W, H, 0, masks, ent) != NEURONTE_OK)
        FAIL("coverage_layers of an unlabelled scalar");
    for (layer = 0; layer < (int)K && !trained_net; layer++)
        if (ent[layer] != 0)
            FAIL("U+0041 layer %d entry %u", layer, ent[layer]);
    neuronte_coverage(n, 0xF036D, W, H, 0, cov);
    if (neuronte_coverage_layers(n, 0xF036D, W, H, 0, masks, ent) != NEURONTE_OK)
        FAIL("coverage_layers U+F036D");
    for (px = 0; px < W * H; px++) {
        float a = 0;
        for (layer = 0; layer < (int)K; layer++) {
            float c = masks[(size_t)layer * W * H + px];
            if (ent[layer] == 1)
                a *= 1.0f - c;
            else
                a = c + a * (1.0f - c);
        }
        if (cov[px] != a) {
            FAIL("coverage and the composited layers differ at %d", px);
            break;
        }
    }

    /* 16 px is not under the file's threshold of 14. Forcing the threshold
     * above 16 snaps, and this icon's edges already sit on pixels. The
     * comparison is the masks: the composited alpha of this glyph is full. */
    if (neuronte_set_snap(n, 0) != NEURONTE_OK)
        FAIL("set_snap(0)");
    if (neuronte_coverage_layers(n, 0xF04C, W, H, 0, masks, ent) != NEURONTE_OK)
        FAIL("U+F04C masks at 16 px");
    if (neuronte_set_snap(n, 17) != NEURONTE_OK)
        FAIL("set_snap(17)");
    if (neuronte_coverage_layers(n, 0xF04C, W, H, 0, masks2, ent) != NEURONTE_OK)
        FAIL("U+F04C masks with snapping forced on");
    if (memcmp(masks, masks2, (size_t)K * W * H * sizeof *masks) != 0)
        FAIL("a grid-aligned icon changed at 16 px with snapping on");
    {
        size_t bytes = (size_t)K * 12 * 24 * sizeof *masks;
        float *saved = malloc(bytes);
        if (!saved) {
            FAIL("out of memory");
        } else {
            if (neuronte_set_snap(n, -1) != NEURONTE_OK)
                FAIL("set_snap(-1)");
            if (neuronte_coverage_layers(n, 0xF04C, 12, 24, 0, masks, ent) != NEURONTE_OK)
                FAIL("U+F04C masks at 12 px");
            memcpy(saved, masks, bytes);
            neuronte_set_snap(n, 0);
            if (neuronte_coverage_layers(n, 0xF04C, 12, 24, 0, masks2, ent) != NEURONTE_OK)
                FAIL("U+F04C masks with snapping off");
            if (memcmp(saved, masks2, bytes) == 0)
                FAIL("snapping at 12 px left U+F04C unchanged");
            neuronte_set_snap(n, -1);
            if (neuronte_coverage_layers(n, 0xF04C, 12, 24, 0, masks2, ent) != NEURONTE_OK)
                FAIL("U+F04C masks with the file threshold restored");
            if (memcmp(saved, masks2, bytes) != 0)
                FAIL("set_snap(-1) did not restore the file threshold");
            free(saved);
        }
    }

    neuronte_set_theme(n, 0);
    if (neuronte_coverage_layers(n, 0xF036D, W, H, 0, masks, ent) != NEURONTE_OK)
        FAIL("masks before the theme change");
    neuronte_set_theme(n, 1);
    if (neuronte_coverage_layers(n, 0xF036D, W, H, 0, masks2, ent) != NEURONTE_OK)
        FAIL("masks after the theme change");
    if (memcmp(masks, masks2, (size_t)K * W * H * sizeof *masks) != 0)
        FAIL("the theme changed the masks");
    {
        uint32_t dark[W * H], light[W * H], again[W * H], fg[W * H];
        for (px = 0; px < W * H; px++)
            dark[px] = light[px] = again[px] = fg[px] = 0xFF000000u;
        neuronte_set_theme(n, 0);
        neuronte_set_snap(n, -1);
        neuronte_draw_scalar(n, dark, W, W, H, 0, 0, W, H, 0xF036D, 0xFFFFFFFFu);
        neuronte_draw_scalar(n, fg, W, W, H, 0, 0, W, H, 0xF04C, 0xFFFFFFFFu);
        neuronte_set_theme(n, 1);
        neuronte_draw_scalar(n, light, W, W, H, 0, 0, W, H, 0xF036D, 0xFFFFFFFFu);
        neuronte_draw_scalar(n, again, W, W, H, 0, 0, W, H, 0xF04C, 0xFFFFFFFFu);
        if (memcmp(dark, light, sizeof dark) == 0)
            FAIL("dark and light drew U+F036D the same");
        if (memcmp(fg, again, sizeof fg) != 0)
            FAIL("the theme changed an icon painted in the caller's colour");
        for (px = 0; px < W * H; px++)
            again[px] = 0xFF000000u;
        neuronte_set_theme(n, 0);
        neuronte_draw_scalar(n, again, W, W, H, 0, 0, W, H, 0xF036D, 0xFFFFFFFFu);
        if (memcmp(dark, again, sizeof dark) != 0)
            FAIL("returning to the dark theme did not restore the pixels");
    }

bundles:
    free(masks);
    free(masks2);
    neuronte_close(n);
    n = NULL;
    {
        const unsigned char *one[1];
        size_t one_len[1];
        unsigned char *b;
        size_t blen;
        one[0] = data;
        one_len[0] = len;
        b = bundle_n(one, one_len, 1, NULL, 0, 0, &blen);
        if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK)
            FAIL("a bundle of one colour net refused");
        else if (neuronte_layers(n) != (int)K || neuronte_parameters(n) != trunk + headn)
            FAIL("one-net colour bundle has %d layers and %zu parameters", neuronte_layers(n),
                 neuronte_parameters(n));
        neuronte_close(n);
        n = NULL;
        free(b);
    }
    {
        const unsigned char *two[2];
        size_t two_len[2];
        unsigned char *b, *alt;
        size_t blen;
        two[0] = two[1] = data;
        two_len[0] = two_len[1] = len;
        b = bundle_n(two, two_len, 2, NULL, 0, 0, &blen);
        if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK)
            FAIL("a bundle of two colour nets with one palette refused");
        else if (neuronte_parameters(n) != 2 * (trunk + headn))
            FAIL("two colour nets have %zu parameters", neuronte_parameters(n));
        neuronte_close(n);
        n = NULL;
        free(b);
        alt = malloc(len);
        if (!alt) {
            FAIL("out of memory");
            return;
        }
        memcpy(alt, data, len);
        alt[228 + 6] ^= 1;
        two[1] = alt;
        b = bundle_n(two, two_len, 2, NULL, 0, 0, &blen);
        expect_open("colour bundle with two palettes", b, blen, NEURONTE_ERR_FORMAT);
        free(b);
        memcpy(alt, data, len);
        put32(alt + 52, 15);
        b = bundle_n(two, two_len, 2, NULL, 0, 0, &blen);
        expect_open("colour bundle with two snap thresholds", b, blen, NEURONTE_ERR_FORMAT);
        free(b);
        free(alt);
    }
    {
        unsigned char *z;
        size_t zlen, blen;
        const unsigned char *parts[2];
        size_t lens[2];
        uint32_t range[3] = {0xE654, 0xF036D, 1};
        unsigned char *b;
        float *plane;
        z = mono8(data, &zlen);
        parts[0] = z;
        parts[1] = data;
        lens[0] = zlen;
        lens[1] = len;
        b = z ? bundle_n(parts, lens, 2, range, 1, 0, &blen) : NULL;
        if (!b || neuronte_open(b, blen, &n) != NEURONTE_OK) {
            FAIL("a bundle of a distance net and a colour net refused");
        } else {
            if (neuronte_route(n, 'A') != 0 || neuronte_route(n, 0xF04C) != 1 || neuronte_layers(n) != (int)K)
                FAIL("mixed bundle routes A to %d and U+F04C to %d, layers %d", neuronte_route(n, 'A'),
                     neuronte_route(n, 0xF04C), neuronte_layers(n));
            neuronte_coverage(n, 'A', W, H, 0, cov);
            for (px = 0; px < W * H; px++)
                if (cov[px] != 0.5f) {
                    FAIL("A in the mixed bundle is not the zero net");
                    break;
                }
            neuronte_set_snap(n, 64);
            neuronte_coverage(n, 'A', W, H, 0, cov2);
            if (memcmp(cov, cov2, sizeof cov) != 0)
                FAIL("snapping changed the distance net in the bundle");
            plane = calloc((size_t)K * W * H, sizeof *plane);
            if (!plane || neuronte_coverage_layers(n, 'A', W, H, 0, plane, ent) != NEURONTE_OK)
                FAIL("coverage_layers of A in the mixed bundle");
            else {
                for (px = 0; px < W * H; px++)
                    if (plane[px] != 0.5f) {
                        FAIL("mixed bundle mask 0 is %g", plane[px]);
                        break;
                    }
                for (layer = 1; layer < (int)K; layer++)
                    for (px = 0; px < W * H; px++)
                        if (plane[(size_t)layer * W * H + px] != 0.0f) {
                            FAIL("mixed bundle mask %d is not empty", layer);
                            layer = (int)K;
                            break;
                        }
                for (layer = 0; layer < (int)K; layer++)
                    if (ent[layer] != 0)
                        FAIL("mixed bundle entry %d is %u", layer, ent[layer]);
            }
            free(plane);
            if (neuronte_palette(n, 0, pal) != NEURONTE_OK || memcmp(pal, data + 228, 96) != 0)
                FAIL("mixed bundle palette");
            neuronte_close(n);
            n = NULL;
        }
        free(b);
        free(z);
    }
}

/* An advance table of count records, each scalar, regular, bold. */
static unsigned char *adv_table(uint32_t (*rec)[3], uint32_t count, uint32_t fallback, size_t *len)
{
    unsigned char *t = malloc(32 + 8 * (size_t)count);
    uint32_t i;
    memcpy(t, "NEURONTE", 8);
    put32(t + 8, 4);
    put32(t + 12, 10);
    put32(t + 16, 10);
    put32(t + 20, 2);
    put32(t + 24, count);
    put32(t + 28, fallback);
    for (i = 0; i < count; i++) {
        put32(t + 32 + 8 * i, rec[i][0]);
        put32(t + 36 + 8 * i, rec[i][1] | rec[i][2] << 16);
    }
    *len = 32 + 8 * (size_t)count;
    return t;
}

/* A drawing file of the members given, in order. */
static unsigned char *drawing(const unsigned char *const *member, const size_t *mlen, uint32_t count, size_t *len)
{
    size_t off = 16 + 8 * (size_t)count, total = off;
    unsigned char *d;
    uint32_t i;
    for (i = 0; i < count; i++)
        total += mlen[i];
    d = malloc(total + 1);
    memcpy(d, "NEURONTE", 8);
    put32(d + 8, 5);
    put32(d + 12, count);
    for (i = 0; i < count; i++) {
        put32(d + 16 + 8 * i, (uint32_t)off);
        put32(d + 20 + 8 * i, (uint32_t)mlen[i]);
        memcpy(d + off, member[i], mlen[i]);
        off += mlen[i];
    }
    d[total] = 0;
    *len = total;
    return d;
}

static void expect_file(const char *name, const unsigned char *data, size_t len, int want)
{
    char path[] = "/tmp/neuronte-test-XXXXXX";
    int fd = mkstemp(path), rc;
    neuronte *n = NULL;
    FILE *f = fd < 0 ? NULL : fdopen(fd, "wb");
    if (!f || fwrite(data, 1, len, f) != len) {
        FAIL("%s: cannot write a temporary file", name);
    } else {
        fclose(f);
        f = NULL;
        rc = neuronte_open_file(path, &n);
        if (rc != want)
            FAIL("%s: open_file returned %d, want %d", name, rc, want);
        neuronte_close(n);
    }
    if (f)
        fclose(f);
    if (fd >= 0)
        unlink(path);
}

/* neuronte_draw_text on a handle with a net and the advances of
 * advance_checks: space 10 and 30 steps, A 45 and 50, B 55 and 64,
 * ? 100 and 150, ~ 200 and 200. */
static void draw_text_checks(neuronte *n)
{
    enum { W = 96, H = 30, EM = 11 };
    static const char text[] = "AB?~ \xc3\xa9" "A"; /* e with acute has no advance: drawn as ? */
    static const uint32_t drawn[] = {'A', 'B', '?', '~', ' ', '?', 'A'};
    uint32_t got[W * H], want[W * H], color = 0xC0FF8040u;
    int bold, x0 = 3, y0 = 2, rc;
    size_t i;

    for (bold = 0; bold < 2; bold++) {
        int pen = x0, px, py;
        for (i = 0; i < W * H; i++)
            got[i] = want[i] = 0xFF102030u;
        for (i = 0; i < sizeof drawn / sizeof *drawn; i++)
            pen += neuronte_advance(n, i == 5 ? 0xE9 : drawn[i], bold, EM);
        rc = neuronte_draw_text(n, got, W, W, H, x0, y0, EM, bold, text, sizeof text - 1, color);
        if (rc != neuronte_text_width(n, text, sizeof text - 1, bold, EM) || rc != pen - x0)
            FAIL("draw_text weight %d returned %d, want %d", bold, rc, pen - x0);
        /* Regular is exactly the one-cell call at each pen position. */
        if (!bold) {
            pen = x0;
            for (i = 0; i < sizeof drawn / sizeof *drawn; i++) {
                neuronte_draw_scalar(n, want, W, W, H, pen, y0, EM, 2 * EM, drawn[i], color);
                pen += neuronte_advance(n, drawn[i], 0, EM);
            }
            if (memcmp(got, want, sizeof got) != 0)
                FAIL("draw_text: regular text is not its cells drawn at the pen positions");
        } else {
            /* Bold: every pixel regular inks is inked, so is the pixel to
             * its right, and nothing left of the first pen is touched. */
            uint32_t reg[W * H];
            int bad = 0;
            for (i = 0; i < W * H; i++)
                reg[i] = 0xFF102030u;
            pen = x0;
            for (i = 0; i < sizeof drawn / sizeof *drawn; i++) {
                neuronte_draw_scalar(n, reg, W, W, H, pen, y0, EM, 2 * EM, drawn[i], color);
                pen += neuronte_advance(n, i == 5 ? 0xE9 : drawn[i], 1, EM);
            }
            for (py = 0; py < H; py++)
                for (px = 0; px < W - 1; px++)
                    if (reg[py * W + px] != 0xFF102030u &&
                        (got[py * W + px] == 0xFF102030u || got[py * W + px + 1] == 0xFF102030u))
                        bad++;
            for (py = 0; py < H; py++)
                for (px = 0; px < x0; px++)
                    if (got[py * W + px] != 0xFF102030u)
                        bad++;
            if (bad)
                FAIL("draw_text: bold is not the letter struck twice (%d pixels)", bad);
        }
    }
    /* Clipped on every side, the part inside is the same pixels. */
    {
        uint32_t whole[W * H], part[W * H];
        int px, py, bad = 0;
        for (i = 0; i < W * H; i++)
            whole[i] = part[i] = 0;
        neuronte_draw_text(n, whole, W, W, H, 3, 2, EM, 1, "AB?", 3, 0xFFFFFFFFu);
        rc = neuronte_draw_text(n, part + 5 * W + 8, W, 12, 9, 3 - 8, 2 - 5, EM, 1, "AB?", 3, 0xFFFFFFFFu);
        for (py = 0; py < H; py++)
            for (px = 0; px < W; px++) {
                int in = px >= 8 && px < 20 && py >= 5 && py < 14;
                if (part[py * W + px] != (in ? whole[py * W + px] : 0))
                    bad++;
            }
        if (bad || rc != neuronte_text_width(n, "AB?", 3, 1, EM))
            FAIL("draw_text: clipping changed %d pixels, or the width", bad);
    }
    /* Binary: a pixel is the colour where coverage is more than half, and
     * untouched elsewhere; bold is the two strikes' pixels together. */
    {
        uint32_t one[W * H], two[W * H], bg = 0xFF102030u, fg = 0xFFE0D0C0u;
        float cov[EM * 2 * EM];
        int px, py, bad = 0, on = 0;
        for (i = 0; i < W * H; i++)
            one[i] = two[i] = got[i] = bg;
        if (neuronte_set_binary(n, 2) != NEURONTE_ERR_ARG || neuronte_set_binary(n, -1) != NEURONTE_ERR_ARG ||
            neuronte_set_binary(NULL, 1) != NEURONTE_ERR_ARG || neuronte_set_binary(n, 1) != NEURONTE_OK)
            FAIL("set_binary argument checks");
        neuronte_coverage(n, 'B', EM, 2 * EM, 0, cov);
        neuronte_draw_scalar(n, one, W, W, H, 4, 3, EM, 2 * EM, 'B', fg);
        neuronte_draw_text(n, two, W, W, H, 4, 3, EM, 0, "B", 1, fg);
        neuronte_draw_text(n, got, W, W, H, 4, 3, EM, 1, "B", 1, fg);
        for (py = 0; py < H; py++)
            for (px = 0; px < W; px++) {
                int cx = px - 4, cy = py - 3, in = cx >= 0 && cx < EM && cy >= 0 && cy < 2 * EM;
                int ink = in && cov[cy * EM + cx] > 0.5f;
                int left = cx >= 1 && cx <= EM && cy >= 0 && cy < 2 * EM && cov[cy * EM + cx - 1] > 0.5f;
                on += ink;
                if (one[py * W + px] != (ink ? fg : bg) || two[py * W + px] != one[py * W + px] ||
                    got[py * W + px] != (ink || left ? fg : bg))
                    bad++;
            }
        if (bad || on == 0)
            FAIL("binary drawing: %d pixels are not the coverage cut at one half (%d inked)", bad, on);
        /* A half-clear colour is blended once, at full coverage or not at all. */
        for (i = 0; i < W * H; i++)
            one[i] = bg;
        neuronte_draw_scalar(n, one, W, W, H, 4, 3, EM, 2 * EM, 'B', 0x80FFFFFFu);
        bad = 0;
        {
            uint32_t seen = 0;
            for (i = 0; i < W * H; i++)
                if (one[i] != bg) {
                    if (!seen)
                        seen = one[i];
                    if (one[i] != seen)
                        bad++;
                }
            if (bad || !seen)
                FAIL("binary drawing with a half-clear colour is not one blended colour");
        }
        if (neuronte_set_binary(n, 0) != NEURONTE_OK)
            FAIL("set_binary off");
        for (i = 0; i < W * H; i++)
            one[i] = bg;
        neuronte_draw_scalar(n, one, W, W, H, 4, 3, EM, 2 * EM, 'B', fg);
        for (i = 0, on = 0; i < W * H; i++)
            on += one[i] != bg && one[i] != fg;
        if (on == 0)
            FAIL("with binary off, no edge pixel is blended");
    }
    if (neuronte_draw_text(n, got, W, W, H, 0, 0, EM, 2, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, got, W, W, H, 0, 0, 0, 0, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, got, W, W, H, 0, 0, NEURONTE_MAX_CELL / 2 + 1, 0, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, NULL, W, W, H, 0, 0, EM, 0, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, got, W - 1, W, H, 0, 0, EM, 0, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, got, W, W, H, 0, 0, EM, 0, NULL, 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(NULL, got, W, W, H, 0, 0, EM, 0, "A", 1, color) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, got, W, W, H, 0, 0, EM, 0, "", 0, color) != 0 ||
        neuronte_draw_text(n, got, W, W, H, 0, 0, EM, 0, "AB", 2, 0x00FFFFFFu) != neuronte_text_width(n, "AB", 2, 0, EM))
        FAIL("draw_text argument checks");
}

/* Fully clipped text keeps its cell count or its measured width. An em
 * that does not fit in a cell, including one whose doubled height does not
 * fit in int, is an argument error. The pen may sit on INT_MAX. */
static void text_edge_checks(neuronte *n)
{
    uint32_t pix[2] = {0x11111111u, 0x22222222u};
    int width = neuronte_text_width(n, "A", 1, 0, 10);
    int both = neuronte_text_width(n, "AB", 2, 0, 10);
    int bold = neuronte_text_width(n, "A", 1, 1, 10);

    if (width < 0 || both < 0 || bold < 0)
        FAIL("text edges: width");
    if (neuronte_draw_utf8(n, pix, 1, 1, 2, INT_MAX, 0, 1, 2, "A", 1, 0xFFFFFFFFu) != 1 ||
        neuronte_draw_utf8(n, pix, 1, 1, 2, INT_MAX, 0, 1, 2, "AB", 2, 0xFFFFFFFFu) != 2 ||
        neuronte_draw_utf8(n, pix, 1, 1, 2, 0, INT_MAX, 1, 2, "A", 1, 0xFFFFFFFFu) != 1 ||
        neuronte_draw_text(n, pix, 1, 1, 2, INT_MAX, 0, 10, 0, "A", 1, 0xFFFFFFFFu) != width ||
        neuronte_draw_text(n, pix, 1, 1, 2, INT_MAX - 3, 0, 10, 0, "A", 1, 0xFFFFFFFFu) != width ||
        neuronte_draw_text(n, pix, 1, 1, 2, INT_MAX, 0, 10, 0, "AB", 2, 0xFFFFFFFFu) != both ||
        neuronte_draw_text(n, pix, 1, 1, 2, INT_MAX, 0, 10, 1, "A", 1, 0xFFFFFFFFu) != bold ||
        neuronte_draw_text(n, pix, 1, 1, 2, 0, INT_MAX, 10, 0, "A", 1, 0xFFFFFFFFu) != width ||
        pix[0] != 0x11111111u || pix[1] != 0x22222222u)
        FAIL("fully clipped text at the edge of int");
    if (neuronte_draw_text(n, pix, 1, 1, 2, 0, 0, INT_MAX, 0, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, pix, 1, 1, 2, 0, 0, INT_MIN, 0, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, pix, 1, 1, 2, INT_MAX, 0, INT_MAX, 0, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG ||
        pix[0] != 0x11111111u || pix[1] != 0x22222222u)
        FAIL("draw_text em out of range");
}

/* The advance table, version 4, and the drawing file, version 5. net is a
 * version 1 image, or NULL when the weights under test are a bundle. */
static void advance_checks(const unsigned char *net, size_t netlen)
{
    /* The example in the format note, byte for byte. */
    static const unsigned char example[56] = {
        0x4e, 0x45, 0x55, 0x52, 0x4f, 0x4e, 0x54, 0x45, 0x04, 0, 0, 0, 0x0a, 0, 0, 0,
        0x0a, 0, 0, 0, 0x02, 0, 0, 0, 0x03, 0, 0, 0, 0x3f, 0, 0, 0,
        0x20, 0, 0, 0, 0x1e, 0, 0x1e, 0, 0x3f, 0, 0, 0, 0x37, 0, 0x3e, 0,
        0x26, 0x20, 0, 0, 0x5a, 0, 0x60, 0};
    /* Steps, and the pixels they are at an em of 10 and of 11. */
    static const int px[][3] = {{10, 1, 1},   {30, 3, 3},   {45, 5, 5},    {50, 5, 6},  {55, 6, 6},
                                {64, 6, 7},   {100, 10, 11}, {150, 15, 17}, {200, 20, 22}};
    static const uint32_t rows[6][3] = {{0x20, 10, 30},  {0x41, 45, 50},  {0x42, 55, 64}, {0x3f, 100, 150},
                                       {0x7e, 200, 200}, {0x2026, 90, 96}};
    uint32_t sorted[6][3];
    unsigned char *t, *d, bad[57];
    const unsigned char *member[3];
    size_t tlen, dlen, mlen[3], i;
    neuronte *n = NULL;
    float one[2];
    uint32_t pix[2] = {0, 0};
    uint8_t ent[1] = {0};

    if (neuronte_open(example, sizeof example, &n) != NEURONTE_OK) {
        FAIL("the note's example table does not open");
        return;
    }
    if (neuronte_advances(n) != 3 || neuronte_nets(n) != 0 || neuronte_parameters(n) != 0)
        FAIL("example table: %d records, %d nets", neuronte_advances(n), neuronte_nets(n));
    if (neuronte_advance_steps(n, 0x20, 0) != 30 || neuronte_advance_steps(n, 0x20, 1) != 30 ||
        neuronte_advance_steps(n, 0x3f, 0) != 55 || neuronte_advance_steps(n, 0x3f, 1) != 62 ||
        neuronte_advance_steps(n, 0x2026, 0) != 90 || neuronte_advance_steps(n, 0x2026, 1) != 96)
        FAIL("example table: steps read wrong");
    /* A missing character is the fallback, measured and named. */
    if (neuronte_advance_steps(n, 'A', 0) != 55 || neuronte_advance_steps(n, 0x07, 1) != 62 ||
        neuronte_advance_steps(n, 0x10FFFF, 0) != 55 || neuronte_advance_steps(n, 0xFFFFFFFFu, 0) != 55)
        FAIL("a missing character is not measured as the fallback");
    if (neuronte_advance_scalar(n, 'A') != 0x3f || neuronte_advance_scalar(n, 0x2026) != 0x2026 ||
        neuronte_advance_scalar(n, 0x20) != 0x20 || neuronte_advance_scalar(NULL, 'A') != NEURONTE_REPLACEMENT)
        FAIL("advance_scalar");
    if (neuronte_advance(n, 0x3f, 0, 10) != 6 || neuronte_advance(n, 0x3f, 0, 11) != 6 ||
        neuronte_advance(n, 0x3f, 1, 10) != 6 || neuronte_advance(n, 0x3f, 1, 11) != 7)
        FAIL("example table: pixels of ?");
    /* " ?" and an ellipsis, then a letter and a bad byte, both missing. */
    if (neuronte_text_width(n, " ?\xe2\x80\xa6", 5, 0, 10) != 3 + 6 + 9 ||
        neuronte_text_width(n, " ?\xe2\x80\xa6", 5, 1, 11) != 3 + 7 + 11 ||
        neuronte_text_width(n, "A\xff", 2, 0, 10) != 12 || neuronte_text_width(n, "", 0, 0, 10) != 0 ||
        neuronte_text_width(n, NULL, 0, 0, 11) != 0)
        FAIL("text_width");
    if (neuronte_advance_steps(n, 'A', 2) != NEURONTE_ERR_ARG || neuronte_advance_steps(n, 'A', -1) != NEURONTE_ERR_ARG ||
        neuronte_advance(n, 'A', 0, 0) != NEURONTE_ERR_ARG ||
        neuronte_advance(n, 'A', 0, NEURONTE_MAX_CELL + 1) != NEURONTE_ERR_ARG ||
        neuronte_advance(n, 'A', 0, NEURONTE_MAX_CELL) != (55 * NEURONTE_MAX_CELL + 50) / 100 ||
        neuronte_text_width(n, "a", 1, 2, 10) != NEURONTE_ERR_ARG ||
        neuronte_text_width(n, "a", 1, 0, 0) != NEURONTE_ERR_ARG ||
        neuronte_text_width(n, NULL, 1, 0, 10) != NEURONTE_ERR_ARG ||
        neuronte_advance_steps(NULL, 'A', 0) != NEURONTE_ERR_ARG || neuronte_advances(NULL) != 0)
        FAIL("advance argument checks");
    /* A table by itself measures and cannot draw. */
    if (neuronte_route(n, 'A') != NEURONTE_ERR_ARG || neuronte_coverage(n, 'A', 1, 2, 1, one) != NEURONTE_ERR_ARG ||
        neuronte_coverage_layers(n, 'A', 1, 2, 1, one, ent) != NEURONTE_ERR_ARG ||
        neuronte_draw_scalar(n, pix, 1, 1, 2, 0, 0, 1, 2, 'A', 0xFFFFFFFFu) != NEURONTE_ERR_ARG ||
        neuronte_draw_utf8(n, pix, 1, 1, 2, 0, 0, 1, 2, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG ||
        neuronte_draw_text(n, pix, 1, 1, 2, 0, 0, 1, 0, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG || pix[0] || pix[1])
        FAIL("a table with no net let a draw call through");
    neuronte_close(n);
    expect_file("example table from a file", example, sizeof example, NEURONTE_OK);

    /* The rounding table, through a table that holds those steps. */
    for (i = 0; i < sizeof px / sizeof *px; i++) {
        uint32_t r[1][3] = {{0x3f, (uint32_t)px[i][0], (uint32_t)px[i][0]}};
        t = adv_table(r, 1, 0x3f, &tlen);
        if (neuronte_open(t, tlen, &n) != NEURONTE_OK)
            FAIL("table of one record, %d steps", px[i][0]);
        else if (neuronte_advance(n, 0x3f, 0, 10) != px[i][1] || neuronte_advance(n, 0x3f, 1, 11) != px[i][2])
            FAIL("%d steps are %d and %d pixels, want %d and %d", px[i][0], neuronte_advance(n, 0x3f, 0, 10),
                 neuronte_advance(n, 0x3f, 1, 11), px[i][1], px[i][2]);
        neuronte_close(n);
        n = NULL;
        free(t);
    }

    /* Refusals. Nothing is repaired. */
    memcpy(bad, example, sizeof example);
    bad[56] = 0;
    expect_open("table one byte short", bad, 55, NEURONTE_ERR_FORMAT);
    expect_open("table one byte long", bad, 57, NEURONTE_ERR_FORMAT);
    expect_file("table one byte short, from a file", bad, 55, NEURONTE_ERR_FORMAT);
    expect_file("table one byte long, from a file", bad, 57, NEURONTE_ERR_FORMAT);
    expect_open("table header only", bad, 32, NEURONTE_ERR_FORMAT);
#define BAD(name, at, value, width) \
    (memcpy(bad, example, sizeof example), width == 4 ? put32(bad + (at), (value)) : \
     (void)(bad[at] = (value) & 0xFF, bad[(at) + 1] = (value) >> 8), \
     expect_open(name, bad, sizeof example, NEURONTE_ERR_FORMAT))
    BAD("table with 12 units per em", 12, 12, 4);
    BAD("table with 16 steps per unit", 16, 16, 4);
    BAD("table with one weight", 20, 1, 4);
    BAD("table with three weights", 20, 3, 4);
    BAD("table with no records", 24, 0, 4);
    BAD("table with 4097 records", 24, 4097, 4);
    BAD("table with a record count that is not its length", 24, 2, 4);
    BAD("table whose fallback has no record", 28, 0x41, 4);
    BAD("table with a repeated scalar", 40, 0x20, 4);
    BAD("table out of order", 40, 0x2027, 4);
    BAD("table with a surrogate", 48, 0xD800, 4);
    BAD("table with a scalar above U+10FFFF", 48, 0x110000, 4);
    BAD("regular advance of 9 steps", 36, 9, 2);
    BAD("bold advance of 201 steps", 38, 201, 2);
    BAD("bold advance of 0 steps", 54, 0, 2);
#undef BAD

    /* 4096 records open; lookups at both ends and between. */
    {
        static uint32_t big[4096][3];
        for (i = 0; i < 4096; i++) {
            big[i][0] = 0x100 + 2 * (uint32_t)i;
            big[i][1] = 10 + (uint32_t)i % 191;
            big[i][2] = 200 - (uint32_t)i % 191;
        }
        t = adv_table(big, 4096, 0x100, &tlen);
        if (neuronte_open(t, tlen, &n) != NEURONTE_OK) {
            FAIL("table of 4096 records");
        } else {
            for (i = 0; i < 4096; i++)
                if (neuronte_advance_steps(n, big[i][0], 0) != (int)big[i][1] ||
                    neuronte_advance_steps(n, big[i][0], 1) != (int)big[i][2] ||
                    neuronte_advance_scalar(n, big[i][0] + 1) != 0x100) {
                    FAIL("table of 4096 records: record %d", (int)i);
                    break;
                }
            if (neuronte_advance_scalar(n, 0xFF) != 0x100 || neuronte_advance_scalar(n, 0) != 0x100)
                FAIL("table of 4096 records: below the first record");
        }
        neuronte_close(n);
        n = NULL;
        expect_file("table of 4096 records from a file", t, tlen, NEURONTE_OK);
        free(t);
    }

    /* The records may be given in any order here; sort them for the file. */
    memcpy(sorted, rows, sizeof sorted);
    for (i = 0; i < 6; i++) {
        size_t j;
        for (j = i + 1; j < 6; j++)
            if (sorted[j][0] < sorted[i][0]) {
                uint32_t swap[3];
                memcpy(swap, sorted[i], sizeof swap);
                memcpy(sorted[i], sorted[j], sizeof swap);
                memcpy(sorted[j], swap, sizeof swap);
            }
    }
    t = adv_table(sorted, 6, 0x3f, &tlen);

    /* A drawing file of the table alone. */
    member[0] = t;
    mlen[0] = tlen;
    d = drawing(member, mlen, 1, &dlen);
    if (neuronte_open(d, dlen, &n) != NEURONTE_OK) {
        FAIL("drawing file of one table");
    } else if (neuronte_advances(n) != 6 || neuronte_nets(n) != 0 || neuronte_advance(n, 'B', 1, 11) != 7 ||
               neuronte_text_width(n, "AB~", 3, 0, 10) != 5 + 6 + 20) {
        FAIL("drawing file of one table: measures wrong");
    } else if (neuronte_coverage_layers(n, 'A', 1, 2, 1, one, ent) != NEURONTE_ERR_ARG) {
        FAIL("drawing file of one table: coverage_layers");
    }
    neuronte_close(n);
    n = NULL;
    expect_file("drawing file of one table, from a file", d, dlen, NEURONTE_OK);
    expect_file("drawing file one byte long, from a file", d, dlen + 1, NEURONTE_ERR_FORMAT);
    expect_open("drawing file one byte short", d, dlen - 1, NEURONTE_ERR_FORMAT);
    expect_open("drawing file one byte long", d, dlen + 1, NEURONTE_ERR_FORMAT);
    put32(d + 12, 0);
    expect_open("drawing file with no members", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 12, 17);
    expect_open("drawing file with 17 members", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 12, 1);
    put32(d + 16, 25);
    expect_open("member that does not start after the directory", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 16, 24);
    put32(d + 20, 11);
    expect_open("member of 11 bytes", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 20, (uint32_t)tlen);
    d[24] = 'X';
    expect_open("member with a bad magic", d, dlen, NEURONTE_ERR_FORMAT);
    d[24] = 'N';
    put32(d + 24 + 8, 2);
    expect_open("bundle inside a drawing file", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 24 + 8, 5);
    expect_open("drawing file inside a drawing file", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 24 + 8, 6);
    expect_open("member of a later version", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 24 + 8, 4);
    put32(d + 24 + 36, 9);
    expect_open("drawing file whose table has a bad advance", d, dlen, NEURONTE_ERR_FORMAT);
    free(d);

    /* Two tables are one too many. A version word of 3 that is not a colour
     * net is refused, rather than skipped. */
    member[1] = t;
    mlen[1] = tlen;
    d = drawing(member, mlen, 2, &dlen);
    expect_open("drawing file of two tables", d, dlen, NEURONTE_ERR_FORMAT);
    put32(d + 32 + 8, 3);
    expect_open("drawing file whose colour member is not a colour net", d, dlen, NEURONTE_ERR_FORMAT);
    free(d);

    /* A net and the table: draws as the net does, and measures. */
    if (net) {
        neuronte *lone = NULL;
        float a[8 * 16], b[8 * 16];
        member[0] = net;
        mlen[0] = netlen;
        member[1] = t;
        mlen[1] = tlen;
        member[2] = net;
        mlen[2] = netlen;
        d = drawing(member, mlen, 3, &dlen);
        if (neuronte_open(d, dlen, &n) != NEURONTE_OK || neuronte_open(net, netlen, &lone) != NEURONTE_OK) {
            FAIL("drawing file of a net, a table and a net");
        } else {
            if (neuronte_nets(n) != 2 || neuronte_advances(n) != 6 || neuronte_route(n, 'A') != 0 ||
                neuronte_parameters(n) != 2 * neuronte_parameters(lone))
                FAIL("drawing file: %d nets, %d records", neuronte_nets(n), neuronte_advances(n));
            if (neuronte_coverage(n, 'A', 8, 16, 0, a) != NEURONTE_OK ||
                neuronte_coverage(lone, 'A', 8, 16, 0, b) != NEURONTE_OK || memcmp(a, b, sizeof a) != 0)
                FAIL("drawing file: A is not what its net draws");
            if (neuronte_advance(n, 'A', 0, 10) != 5 || neuronte_advance(n, 'A', 1, 11) != 6)
                FAIL("drawing file: advance of A");
            draw_text_checks(n);
            text_edge_checks(n);
        }
        neuronte_close(n);
        neuronte_close(lone);
        n = NULL;
        expect_file("drawing file of a net, a table and a net, from a file", d, dlen, NEURONTE_OK);
        expect_file("that file one byte long", d, dlen + 1, NEURONTE_ERR_FORMAT);
        expect_file("that file one byte short", d, dlen - 1, NEURONTE_ERR_FORMAT);
        d[16 + 8 * 3 + 20] ^= 0xFF; /* the first net's hidden width */
        expect_open("drawing file whose net is damaged", d, dlen, NEURONTE_ERR_SHAPE);
        free(d);
        /* A net with no table still has no advances. */
        d = drawing(member, mlen, 1, &dlen);
        if (neuronte_open(d, dlen, &n) != NEURONTE_OK || neuronte_advances(n) != 0 ||
            neuronte_advance(n, 'A', 0, 10) != NEURONTE_ERR_ARG ||
            neuronte_text_width(n, "A", 1, 0, 10) != NEURONTE_ERR_ARG ||
            neuronte_draw_text(n, pix, 1, 1, 2, 0, 0, 1, 0, "A", 1, 0xFFFFFFFFu) != NEURONTE_ERR_ARG)
            FAIL("drawing file of one net: has advances");
        neuronte_close(n);
        free(d);
    }
    free(t);
}

int main(int argc, char **argv)
{
    unsigned char *data, *copy;
    size_t len;
    neuronte *n;
    enum { CW = 16, CH = 32, BW = 64, BH = 48 };
    float cov[CW * CH], cov2[CW * CH];
    uint32_t buf[BW * BH], ref[BW * BH];
    int i, rc, bundled, full = 0, accent = 0, pixel = 0, colour = 0;

    for (i = 2; i < argc; i++) {
        if (strcmp(argv[i], "--full") == 0)
            full = 1;
        else if (strcmp(argv[i], "--accent") == 0)
            accent = 1;
        else if (strcmp(argv[i], "--pixel") == 0)
            pixel = 1;
        else if (strcmp(argv[i], "--colour") == 0)
            colour = 1;
        else if (strcmp(argv[i], "--trained") == 0)
            trained_net = 1;
        else
            argc = 0;
    }
    if (argc < 2 || (trained_net && !colour)) {
        fprintf(stderr, "usage: %s WEIGHTS.nrt [--full] [--accent] [--pixel] [--colour [--trained]]\n", argv[0]);
        return 2;
    }
    data = slurp(argv[1], &len);
    if (!data) {
        perror(argv[1]);
        return 2;
    }
    copy = malloc(len + 1);
    if (colour) {
        colour_checks(data, len, argv[1]);
        free(copy);
        free(data);
        puts(failed ? "test_api: FAILED" : "test_api: passed");
        return failed;
    }
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
    if (!bundled && data[8] != 3 && neuronte_parameters(n) != (len - 204) / 4)
        FAIL("parameters %zu for a file of %zu bytes", neuronte_parameters(n), len);
    if (neuronte_layers(n) != 1)
        FAIL("a distance file reports %d layers", neuronte_layers(n));
    {
        uint8_t pal[96], ent = 7;
        float plane[CW * CH];
        if (neuronte_palette(n, 0, pal) != NEURONTE_OK)
            FAIL("palette on a distance file");
        for (i = 0; i < 96; i++)
            if (pal[i]) {
                FAIL("a distance file palette is not zero");
                break;
            }
        if (neuronte_set_theme(n, 2) != NEURONTE_ERR_ARG || neuronte_set_snap(n, -2) != NEURONTE_ERR_ARG)
            FAIL("theme and snap bounds on a distance file");
        if (neuronte_coverage_layers(n, 'A', CW, CH, 0, plane, &ent) != NEURONTE_OK || ent != 0)
            FAIL("coverage_layers on a distance glyph");
        neuronte_coverage(n, 'A', CW, CH, 0, cov);
        if (memcmp(plane, cov, sizeof plane) != 0)
            FAIL("coverage_layers and coverage disagree on A");
    }
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
    advance_checks(bundled ? NULL : data, len);

    neuronte_close(n);
    free(copy);
    free(data);
    puts(failed ? "test_api: FAILED" : "test_api: passed");
    return failed;
}
