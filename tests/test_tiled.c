/* Tiled nets, version 6: exact dispatch and code mapping, bundles, drawing,
 * and a corpus of malformed files that must all be refused.
 *
 * The nets here are built by hand so that a sample's coverage is exactly
 * 1 when bit 0 of its code input is set and 0 when it is not. The expected
 * pixels are then worked out from the format's definition, one sample at a
 * time, without the library's tile arithmetic. */
#define _POSIX_C_SOURCE 200809L
#include "neuronte.h"
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define H 2
#define NET_BYTES (204 + 4 * (2 * H * H + 94 * H + 1))

static void u32(unsigned char *p, uint32_t v)
{
    for (int i = 0; i < 4; i++) p[i] = (unsigned char)(v >> (8 * i));
}

static void f32(unsigned char *p, float v)
{
    uint32_t bits;
    memcpy(&bits, &v, sizeof bits);
    u32(p, bits);
}

/* Output +1/2 when code bit `obs` is set, -1/2 when not; tau large enough
 * that every sample clamps to 1 or 0. sign -1 flips it. */
static void put_net(unsigned char *p, int sign, int obs)
{
    memset(p, 0, NET_BYTES);
    memcpy(p, "NEURONTE", 8);
    u32(p + 8, 1); u32(p + 12, 6); u32(p + 16, 64); u32(p + 20, H); u32(p + 24, 3);
    f32(p + 28, 64.f);
    for (int i = 0; i < 43; i++) u32(p + 32 + 4 * i, 1u << (i % 21));
    size_t o = 204;
    f32(p + o + 4 * (26 + obs), (float)sign); /* l1 row 0: code bit obs as +-1 */
    o += 4 * (90 * H + H);
    f32(p + o, 1.f);                        /* l2 [0][0] */
    o += 4 * (H * H + H);
    f32(p + o, 1.f);                        /* l3 [0][0] */
    o += 4 * (H * H + H);
    f32(p + o, 1.f);                        /* out weight 0 */
    f32(p + o + 4 * H, -.5f);
}

struct spec {
    int cols, rows, nets;
    uint32_t first, last;
    float xe[18], ye[18]; /* one spare, for the 17-edge refusals */
    uint32_t tile[256][4];
    int sign[65], obs[65];
};

static size_t image(const struct spec *s, unsigned char **out)
{
    size_t len = 32 + 4 * (s->cols + 1 + s->rows + 1) + 16 * (size_t)(s->cols * s->rows) +
                 4 * (size_t)s->nets + (size_t)s->nets * NET_BYTES;
    unsigned char *p = calloc(len, 1), *q;
    assert(p);
    memcpy(p, "NEURONTE", 8);
    u32(p + 8, 6); u32(p + 12, (uint32_t)s->cols); u32(p + 16, (uint32_t)s->rows);
    u32(p + 20, (uint32_t)s->nets); u32(p + 24, s->first); u32(p + 28, s->last);
    q = p + 32;
    for (int i = 0; i <= s->cols; i++, q += 4) f32(q, s->xe[i]);
    for (int i = 0; i <= s->rows; i++, q += 4) f32(q, s->ye[i]);
    for (int k = 0; k < s->cols * s->rows; k++)
        for (int f = 0; f < 4; f++, q += 4) u32(q, s->tile[k][f]);
    for (int i = 0; i < s->nets; i++, q += 4) u32(q, NET_BYTES);
    for (int i = 0; i < s->nets; i++, q += NET_BYTES) put_net(q, s->sign[i], s->obs[i]);
    assert((size_t)(q - p) == len);
    *out = p;
    return len;
}

static uint32_t code_of(const struct spec *s, const uint32_t *t, uint32_t scalar)
{
    uint32_t b = scalar - s->first, v = 0;
    int bit = 0;
    if (!t[3]) return t[2] | (b & t[1]);
    for (int i = 0; i < 32; i++)
        if (t[1] >> i & 1) v |= (b >> i & 1u) << bit++;
    return t[2] + v;
}

static uint32_t normal(uint32_t s)
{
    return s > 0x10FFFF || (s >= 0xD800 && s <= 0xDFFF) ? 0xFFFD : s;
}

/* Pixel coverage from the definition: each sample's tile, its code's bit 0. */
static void expect(const struct spec *s, uint32_t scalar, int w, int h, int ss, float *out)
{
    int sw = w * ss, sh = h * ss;
    scalar = normal(scalar);
    for (int py = 0; py < h; py++)
        for (int px = 0; px < w; px++) {
            int on = 0;
            for (int j = py * ss; j < py * ss + ss; j++)
                for (int i = px * ss; i < px * ss + ss; i++) {
                    double x = (i + .5) / sw, y = (j + .5) / sh * 2;
                    int c = 0, r = 0;
                    while (c + 1 < s->cols && x >= s->xe[c + 1]) c++;
                    while (r + 1 < s->rows && y >= s->ye[r + 1]) r++;
                    const uint32_t *t = s->tile[r * s->cols + c];
                    int bit = code_of(s, t, scalar) >> s->obs[t[0]] & 1;
                    on += s->sign[t[0]] > 0 ? bit : !bit;
                }
            out[py * w + px] = (float)on / (float)(ss * ss);
        }
}

static void check_cov(neuronte *n, const struct spec *s, uint32_t scalar, int w, int h, int ss)
{
    float *got = malloc(sizeof(float) * (size_t)w * h), *want = malloc(sizeof(float) * (size_t)w * h);
    assert(got && want);
    assert(neuronte_coverage(n, scalar, w, h, ss, got) == NEURONTE_OK);
    expect(s, scalar, w, h, ss ? ss : (w < 24 ? 2 : 1), want);
    for (size_t i = 0; i < (size_t)w * h; i++)
        if (fabsf(got[i] - want[i]) > 1e-6f) {
            fprintf(stderr, "U+%04X %dx%d ss %d pixel %zu: got %g want %g\n", scalar, w, h, ss, i, got[i], want[i]);
            abort();
        }
    free(got);
    free(want);
}

static int opens(const unsigned char *p, size_t len)
{
    neuronte *n = (neuronte *)1;
    int rc = neuronte_open(p, len, &n);
    if (rc == NEURONTE_OK) {
        assert(n);
        neuronte_close(n);
        return 1;
    }
    assert(n == NULL);
    return 0;
}

static int opens_file(const unsigned char *p, size_t len)
{
    char path[] = "/tmp/neuronte-tiled-XXXXXX";
    int fd = mkstemp(path);
    assert(fd >= 0);
    assert(write(fd, p, len) == (ssize_t)len);
    close(fd);
    neuronte *n = (neuronte *)1;
    int rc = neuronte_open_file(path, &n);
    unlink(path);
    if (rc == NEURONTE_OK) {
        neuronte_close(n);
        return 1;
    }
    assert(n == NULL);
    return 0;
}

/* A mutated copy must be refused, from memory and from a file. */
static int refused;
static void refuse(const struct spec *s, const char *what)
{
    unsigned char *p;
    size_t len = image(s, &p);
    if (opens(p, len) || opens_file(p, len)) {
        fprintf(stderr, "accepted: %s\n", what);
        abort();
    }
    refused++;
    free(p);
}

static void refuse_bytes(unsigned char *p, size_t len, const char *what)
{
    if (opens(p, len) || opens_file(p, len)) {
        fprintf(stderr, "accepted: %s\n", what);
        abort();
    }
    refused++;
}

static struct spec dots(void)
{
    /* Braille's 2 x 4 grid with uneven edges. Odd tiles extract their dot's
     * bit to bit 0 for nets 0 and 1, of opposite sign, which both see
     * bit 0. Even tiles place their bits, each with its own net that sees
     * the tile's dot bit where it lies. */
    struct spec s = {2, 4, 6, 0x2800, 0x28FF, {0, .375f, 1}, {0, .5f, 1, 1.25f, 2}, {{0}},
                     {1, -1, 1, 1, -1, 1}, {0, 0, 0, 1, 2, 6}};
    static const uint32_t mask[8] = {0x01, 0x08, 0x02, 0x10, 0x04, 0x20, 0x40, 0x80};
    for (int k = 0; k < 8; k++) {
        s.tile[k][1] = mask[k];
        if (k % 2) {
            s.tile[k][0] = (uint32_t)(k % 4 == 3);
            s.tile[k][2] = 0x2800;
            s.tile[k][3] = 1;
        } else {
            s.tile[k][0] = (uint32_t)(2 + k / 2);
            s.tile[k][1] |= 0x30;
            s.tile[k][2] = 0x2800;
        }
    }
    return s;
}

int main(void)
{
    struct spec s = dots();
    unsigned char *p;
    size_t len = image(&s, &p);
    neuronte *n = NULL;

    /* Valid: memory and file, counts, exact dispatch and codes. */
    assert(neuronte_open(p, len, &n) == NEURONTE_OK && n);
    assert(opens_file(p, len));
    assert(neuronte_nets(n) == 1);
    assert(neuronte_parameters(n) == 6 * (size_t)(2 * H * H + 94 * H + 1));
    assert(neuronte_route(n, 0x2800) == 0);
    static const int cells[][2] = {{1, 1}, {1, 2}, {2, 4}, {3, 6}, {5, 10}, {7, 13}, {8, 16}, {9, 17},
                                   {16, 32}, {23, 47}, {24, 48}, {25, 49}, {33, 61}, {48, 96}};
    for (uint32_t c = 0x27FE; c <= 0x2901; c++)
        for (size_t k = 0; k < sizeof cells / sizeof *cells; k++)
            for (int ss = 0; ss <= 3; ss++)
                check_cov(n, &s, c, cells[k][0], cells[k][1], ss);
    check_cov(n, &s, 0xD800, 8, 16, 2);
    check_cov(n, &s, 0x110000, 8, 16, 2);
    /* Past the keep limit, every sample is evaluated where it is summed. */
    check_cov(n, &s, 0x28A5, 2048, 1024, 2);
    check_cov(n, &s, 0x285A, 4096, 4, 8);

    /* Drawing: cold, warm and binary are the coverage. */
    {
        uint32_t canvas[2][25 * 49];
        float cov[25 * 49];
        assert(neuronte_set_samples(n, 0) == 0);
        for (int pass = 0; pass < 2; pass++) {
            memset(canvas[pass], 0, sizeof canvas[pass]);
            assert(neuronte_draw_scalar(n, canvas[pass], 25, 25, 49, 0, 0, 25, 49, 0x28C3, 0xFFFFFFFF) == 0);
        }
        assert(memcmp(canvas[0], canvas[1], sizeof canvas[0]) == 0);
        assert(neuronte_coverage(n, 0x28C3, 25, 49, 0, cov) == 0);
        for (int i = 0; i < 25 * 49; i++)
            assert((canvas[0][i] >> 24) == (uint32_t)(cov[i] * 255.f + .5f));
    }
    neuronte_close(n);

    /* In a bundle: alone, and beside a plain net. */
    {
        size_t blen = 28 + 4 + 12 + len;
        unsigned char *b = calloc(blen, 1);
        memcpy(b, "NEURONTE", 8);
        u32(b + 8, 2); u32(b + 12, 1); u32(b + 16, 1); u32(b + 20, 0); u32(b + 24, 0);
        u32(b + 28, (uint32_t)len);
        u32(b + 32, 0x2800); u32(b + 36, 0x28FF); u32(b + 40, 0);
        memcpy(b + 44, p, len);
        assert(neuronte_open(b, blen, &n) == NEURONTE_OK);
        check_cov(n, &s, 0x28C3, 23, 47, 0);
        neuronte_close(n);
        free(b);

        size_t two = 28 + 8 + 24 + NET_BYTES + len;
        b = calloc(two, 1);
        memcpy(b, "NEURONTE", 8);
        u32(b + 8, 2); u32(b + 12, 2); u32(b + 16, 2); u32(b + 20, 0); u32(b + 24, 0);
        u32(b + 28, NET_BYTES); u32(b + 32, (uint32_t)len);
        u32(b + 36, 0x20); u32(b + 40, 0x7E); u32(b + 44, 0);
        u32(b + 48, 0x2800); u32(b + 52, 0x28FF); u32(b + 56, 1);
        put_net(b + 60, 1, 0);
        memcpy(b + 60 + NET_BYTES, p, len);
        assert(neuronte_open(b, two, &n) == NEURONTE_OK);
        assert(neuronte_nets(n) == 2 && neuronte_route(n, 0x41) == 0 && neuronte_route(n, 0x2801) == 1);
        check_cov(n, &s, 0x2801, 9, 17, 0);
        neuronte_close(n);
        free(b);
    }

    /* A range that does not start on a mask boundary: codes come from
     * scalar - first, not from the scalar's own bits. */
    {
        struct spec o = {1, 2, 2, 0x2803, 0x28FF, {0, 1}, {0, 1, 2},
                         {{0, 0x0F, 0x2800, 0}, {1, 0x07, 0x40, 0}}, {1, -1}, {1, 2}};
        unsigned char *q;
        size_t ql = image(&o, &q);
        assert(neuronte_open(q, ql, &n) == NEURONTE_OK);
        for (uint32_t c = 0x27F0; c < 0x2820; c++) {
            check_cov(n, &o, c, 8, 16, 0);
            check_cov(n, &o, c, 5, 9, 3);
        }
        neuronte_close(n);
        free(q);
    }

    /* 64 nets with the identity mapping, as an ASCII split uses. */
    {
        struct spec a = {16, 4, 64, 0, 0x7F, {0}, {0, .5f, 1, 1.5f, 2}, {{0}}, {0}, {0}};
        for (int i = 0; i <= 16; i++) a.xe[i] = (float)i / 16;
        for (int k = 0; k < 64; k++) {
            a.tile[k][0] = (uint32_t)k;
            a.tile[k][1] = 0x1FFFFF;
            a.sign[k] = k % 3 ? 1 : -1;
            a.obs[k] = k % 7;
        }
        unsigned char *q;
        size_t ql = image(&a, &q);
        assert(neuronte_open(q, ql, &n) == NEURONTE_OK);
        for (uint32_t c = 0x20; c < 0x7F; c += 3) check_cov(n, &a, c, 16, 32, 0);
        check_cov(n, &a, 0x10FFFF, 17, 35, 0);
        neuronte_close(n);
        free(q);
        struct spec b = a;
        b.rows = 5; b.ye[0] = 0; b.ye[1] = .5f; b.ye[2] = 1; b.ye[3] = 1.5f; b.ye[4] = 1.75f; b.ye[5] = 2;
        b.nets = 65;
        for (int k = 64; k < 80; k++) b.tile[k][0] = (uint32_t)(k == 64 ? 64 : 0), b.tile[k][1] = 0x1FFFFF;
        refuse(&b, "65 nets");
    }

    /* Every truncation, and one byte too many. */
    for (size_t cut = 0; cut < len; cut++) {
        assert(!opens(p, cut));
        if (cut % 37 == 0 || cut + 8 > len) assert(!opens_file(p, cut));
        refused++;
    }
    {
        unsigned char *q = calloc(len + 1, 1);
        memcpy(q, p, len);
        refuse_bytes(q, len + 1, "a trailing byte");
        free(q);
    }

    /* Header, edges and tiles. */
#define BAD(field, value, what) do { struct spec m = dots(); m.field = value; refuse(&m, what); } while (0)
    BAD(cols, 0, "no columns");
    BAD(rows, 0, "no rows");
    BAD(nets, 0, "no nets");
    BAD(first, 0x2900, "first after last");
    BAD(last, 0x200000, "last past U+1FFFFF");
    BAD(xe[0], .125f, "first column edge not 0");
    BAD(xe[2], .875f, "last column edge not 1");
    BAD(ye[4], 1.75f, "last row edge not 2");
    BAD(xe[1], 0.f, "repeated column edge");
    BAD(ye[2], .25f, "falling row edge");
    BAD(xe[1], NAN, "NaN column edge");
    BAD(ye[1], NAN, "NaN row edge");
    BAD(ye[4], INFINITY, "infinite row edge");
    BAD(tile[5][0], 6, "tile net past the nets");
    BAD(tile[5][1], 0x200000, "mask past 21 bits");
    BAD(tile[5][2], 0x200000, "base past 21 bits");
    BAD(tile[5][3], 2, "extract not 0 or 1");
    {
        struct spec m = dots();
        m.tile[5][1] = 1; m.tile[5][2] = 0x1FFFFF; m.tile[5][3] = 1;
        refuse(&m, "extracted codes past U+1FFFFF");
        m.tile[5][2] = 0x1FFFFE;
        unsigned char *q;
        size_t ql = image(&m, &q);
        assert(opens(q, ql));
        free(q);
        m = dots();
        for (int k = 0; k < 8; k++) m.tile[k][0] = 0;
        refuse(&m, "a net that draws no tile");
        m = dots();
        m.cols = 17;
        refuse(&m, "17 columns");
        m = dots();
        m.rows = 17;
        refuse(&m, "17 rows");
        m = dots();
        m.nets = 9;
        refuse(&m, "more nets than tiles");
    }
    {
        /* The version, the member lengths and the members themselves. */
        size_t at_lengths = 32 + 4 * (3 + 5) + 16 * 8, first_net = at_lengths + 4 * 6;
        unsigned char *q = malloc(len);
        static const struct { size_t off; uint32_t value; const char *what; } words[] = {
            {8, 7, "version 7"}, {8, 5, "version 5 header"},
            {0, 0, "a member length of 0"}, {0, 203, "a member length under the header"},
            {0, NET_BYTES - 4, "a short member length"}, {0, NET_BYTES + 4, "a long member length"},
            {0, 0xFFFFFFFF, "a huge member length"},
            {1, 6, "a member that is itself tiled"}, {1, 2, "a member that is a bundle"},
            {1, 3, "a member that is a colour net"}, {2, 0, "a member of width 0"},
            {3, 0x54554E45, "a member without the magic"},
        };
        for (size_t i = 0; i < sizeof words / sizeof *words; i++) {
            memcpy(q, p, len);
            size_t off = words[i].off;
            if (i >= 2 && i <= 6) off = at_lengths;
            else if (words[i].off == 1) off = first_net + 8;
            else if (words[i].off == 2) off = first_net + 20;
            else if (words[i].off == 3) off = first_net;
            u32(q + off, words[i].value);
            refuse_bytes(q, len, words[i].what);
        }
        free(q);
    }
    free(p);
    printf("test_tiled: exact dispatch and codes at %zu cell sizes, keep and stream paths, bundles, "
           "64 identity nets, drawing and %d malformed files passed\n",
           sizeof cells / sizeof *cells, refused);
    return 0;
}
