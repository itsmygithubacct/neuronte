/* The Neuronte net: load, evaluate, draw. MIT licence. See LICENSE.
 *
 * The net is four dense layers. Input is 26 position features of a point
 * (x, y) in the 1 x 2 design cell and 64 features of the character's
 * scalar (its 21 bits and 43 parity bits, each -1 or +1). Three hidden
 * layers of 128 use ReLU. The output f is a clamped signed distance to the
 * ink edge, scaled by 1/tau. A sample's coverage is a ramp one sample wide:
 * clamp(0.5 + f * tau * cell_w * samples, 0, 1).
 *
 * The first layer is a sum of an x part, a y part and a character part,
 * so those are computed once per sample column, sample row and cell. The
 * other layers are stored transposed so each multiply is an axpy over the
 * outputs, which skips the inputs ReLU set to zero.
 */
#include "neuronte.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define OCT 6
#define POS (2 + 4 * OCT)
#define CODE 64
#define NMASK (CODE - 21)
#define IN (POS + CODE)
#define H 128
#define LAYERS 3
#define HEADER (8 + 5 * 4 + 4 + NMASK * 4)
#define NFLOAT (H * IN + H + 2 * (H * H + H) + H + 1)
#define FILE_LEN ((size_t)HEADER + 4 * (size_t)NFLOAT)
#define CACHE 256

/* On x86-64 with GCC or Clang, build the inner loops twice, plain and
 * AVX2, and let the loader pick by CPU at run time. Built as ISO C, the
 * compiler does not fuse multiply-adds, so both paths round alike.
 * Define NEURONTE_NO_CLONES to build one portable path only. */
#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__)) && \
    !defined(NEURONTE_NO_CLONES) && defined(__ELF__)
#define HOT __attribute__((target_clones("avx2", "default")))
#else
#define HOT
#endif

struct entry {
    float *cov;
    uint32_t scalar;
    int w, h, ss;
};

struct neuronte {
    float w1_pos[POS][H]; /* column i of l1, as a row */
    float w1_code[CODE][H];
    float b1[H];
    float w2[H][H]; /* w2[i][o] = l2 weight (o, i) */
    float b2[H];
    float w3[H][H];
    float b3[H];
    float w4[H];
    float b4;
    float tau;
    uint32_t masks[NMASK];
    int samples;
    struct entry cache[CACHE];
};

static uint32_t rd32(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static float rdf(const unsigned char *p)
{
    uint32_t u = rd32(p);
    float f;
    memcpy(&f, &u, sizeof f);
    return f;
}

int neuronte_open(const void *data, size_t len, neuronte **out)
{
    const unsigned char *p = data;
    neuronte *n;
    size_t off;
    int i, o;

    if (!out)
        return NEURONTE_ERR_ARG;
    *out = NULL;
    if (!data)
        return NEURONTE_ERR_ARG;
    if (len < 28 || memcmp(p, "NEURONTE", 8) != 0 || rd32(p + 8) != 1)
        return NEURONTE_ERR_FORMAT;
    if (rd32(p + 12) != OCT || rd32(p + 16) != CODE || rd32(p + 20) != H || rd32(p + 24) != LAYERS)
        return NEURONTE_ERR_SHAPE;
    if (len != FILE_LEN)
        return NEURONTE_ERR_FORMAT;

    n = calloc(1, sizeof *n);
    if (!n)
        return NEURONTE_ERR_NOMEM;
    n->tau = rdf(p + 28);
    if (!isfinite(n->tau) || n->tau <= 0)
        goto bad;
    for (i = 0; i < NMASK; i++) {
        n->masks[i] = rd32(p + 32 + 4 * i);
        if (n->masks[i] == 0 || n->masks[i] >= 1u << 21)
            goto bad;
    }
    for (off = HEADER; off < FILE_LEN; off += 4)
        if (!isfinite(rdf(p + off)))
            goto bad;

    off = HEADER;
#define NEXT() (off += 4, rdf(p + off - 4))
    for (o = 0; o < H; o++)
        for (i = 0; i < IN; i++) {
            float v = NEXT();
            if (i < POS)
                n->w1_pos[i][o] = v;
            else
                n->w1_code[i - POS][o] = v;
        }
    for (o = 0; o < H; o++)
        n->b1[o] = NEXT();
    for (o = 0; o < H; o++)
        for (i = 0; i < H; i++)
            n->w2[i][o] = NEXT();
    for (o = 0; o < H; o++)
        n->b2[o] = NEXT();
    for (o = 0; o < H; o++)
        for (i = 0; i < H; i++)
            n->w3[i][o] = NEXT();
    for (o = 0; o < H; o++)
        n->b3[o] = NEXT();
    for (i = 0; i < H; i++)
        n->w4[i] = NEXT();
    n->b4 = NEXT();
#undef NEXT
    *out = n;
    return NEURONTE_OK;
bad:
    free(n);
    return NEURONTE_ERR_FORMAT;
}

int neuronte_open_file(const char *path, neuronte **out)
{
    unsigned char *buf;
    size_t got;
    FILE *f;
    int rc;

    if (!out)
        return NEURONTE_ERR_ARG;
    *out = NULL;
    if (!path)
        return NEURONTE_ERR_ARG;
    f = fopen(path, "rb");
    if (!f)
        return NEURONTE_ERR_IO;
    buf = malloc(FILE_LEN + 1);
    if (!buf) {
        fclose(f);
        return NEURONTE_ERR_NOMEM;
    }
    got = fread(buf, 1, FILE_LEN + 1, f); /* one byte more shows a file too long */
    rc = ferror(f) ? NEURONTE_ERR_IO : neuronte_open(buf, got, out);
    fclose(f);
    free(buf);
    return rc;
}

void neuronte_close(neuronte *n)
{
    int i;
    if (!n)
        return;
    for (i = 0; i < CACHE; i++)
        free(n->cache[i].cov);
    free(n);
}

int neuronte_set_samples(neuronte *n, int per_axis)
{
    if (!n || per_axis < 0 || per_axis > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    n->samples = per_axis;
    return NEURONTE_OK;
}

static uint32_t normalize(uint32_t s)
{
    return (s > 0x10FFFF || (s >= 0xD800 && s <= 0xDFFF)) ? NEURONTE_REPLACEMENT : s;
}

static int parity(uint32_t v)
{
    v ^= v >> 16;
    v ^= v >> 8;
    v ^= v >> 4;
    v ^= v >> 2;
    v ^= v >> 1;
    return (int)(v & 1);
}

/* l1 bias plus the character's columns of l1. */
static void char_part(const neuronte *n, uint32_t s, float *c)
{
    int i, o;
    memcpy(c, n->b1, sizeof n->b1);
    for (i = 0; i < CODE; i++) {
        int bit = i < 21 ? (int)((s >> i) & 1) : parity(s & n->masks[i - 21]);
        float v = bit ? 1.0f : -1.0f;
        for (o = 0; o < H; o++)
            c[o] += v * n->w1_code[i][o];
    }
}

/* One axis's columns of l1 at coordinate t: axis 0 is x in 0..1, axis 1
 * is y in 0..2. Feature 0 is 2x - 1 and feature 1 is y - 1. For octave k
 * features 2+4k and 3+4k are sin(w x) and sin(w y), 4+4k and 5+4k are
 * cos(w x) and cos(w y), with w = 2 pi 2^k. */
static void axis_part(const neuronte *n, int axis, double t, float *out)
{
    const double two_pi = 6.283185307179586476925286766559;
    float v = axis == 0 ? (float)(2.0 * t - 1.0) : (float)(t - 1.0);
    int k, o;
    for (o = 0; o < H; o++)
        out[o] = v * n->w1_pos[axis][o];
    for (k = 0; k < OCT; k++) {
        double w = two_pi * (double)(1 << k);
        float sv = (float)sin(w * t), cv = (float)cos(w * t);
        const float *ws = n->w1_pos[2 + 4 * k + axis], *wc = n->w1_pos[4 + 4 * k + axis];
        for (o = 0; o < H; o++)
            out[o] += sv * ws[o] + cv * wc[o];
    }
}

HOT static void dense(const float (*w)[H], const float *b, const float *in, float *out)
{
    int i, o;
    memcpy(out, b, H * sizeof *out);
    for (i = 0; i < H; i++) {
        float a = in[i];
        if (a != 0.0f) {
            const float *row = w[i];
            for (o = 0; o < H; o++)
                out[o] += a * row[o];
        }
    }
    for (o = 0; o < H; o++)
        if (!(out[o] > 0.0f))
            out[o] = 0.0f;
}

HOT static float field(const neuronte *n, const float *c, const float *xp, const float *yp)
{
    float h1[H], h2[H], h3[H], f;
    int o;
    for (o = 0; o < H; o++) {
        float v = c[o] + xp[o] + yp[o];
        h1[o] = v > 0.0f ? v : 0.0f;
    }
    dense((const float (*)[H])n->w2, n->b2, h1, h2);
    dense((const float (*)[H])n->w3, n->b3, h2, h3);
    f = n->b4;
    for (o = 0; o < H; o++)
        f += n->w4[o] * h3[o];
    return f;
}

static int auto_samples(int cell_w)
{
    return cell_w < 24 ? 2 : 1;
}

int neuronte_coverage(const neuronte *n, uint32_t scalar, int cell_w, int cell_h,
                      int samples_per_axis, float *coverage)
{
    float c[H], *xp, *yp, slope;
    int ss = samples_per_axis, sw, sh, i, j, px, py;

    if (!n || !coverage || cell_w <= 0 || cell_h <= 0 || cell_w > NEURONTE_MAX_CELL ||
        cell_h > NEURONTE_MAX_CELL || ss < 0 || ss > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    if (ss == 0)
        ss = auto_samples(cell_w);
    sw = cell_w * ss;
    sh = cell_h * ss;
    xp = malloc((size_t)sw * H * sizeof *xp);
    yp = malloc((size_t)sh * H * sizeof *yp);
    if (!xp || !yp) {
        free(xp);
        free(yp);
        return NEURONTE_ERR_NOMEM;
    }
    char_part(n, normalize(scalar), c);
    for (i = 0; i < sw; i++)
        axis_part(n, 0, (i + 0.5) / sw, xp + (size_t)i * H);
    for (j = 0; j < sh; j++)
        axis_part(n, 1, (j + 0.5) / sh * 2.0, yp + (size_t)j * H);
    slope = n->tau * (float)cell_w * (float)ss;
    for (py = 0; py < cell_h; py++)
        for (px = 0; px < cell_w; px++) {
            float acc = 0.0f;
            for (j = 0; j < ss; j++)
                for (i = 0; i < ss; i++) {
                    float v = 0.5f + slope * field(n, c, xp + (size_t)(px * ss + i) * H,
                                                   yp + (size_t)(py * ss + j) * H);
                    acc += v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
                }
            coverage[(size_t)py * cell_w + px] = acc / (float)(ss * ss);
        }
    free(xp);
    free(yp);
    return NEURONTE_OK;
}

static const float *cached(neuronte *n, uint32_t s, int w, int h, int ss, int *rc)
{
    uint32_t k = s * 2654435761u ^ (uint32_t)w * 40503u ^ (uint32_t)h * 9973u ^ (uint32_t)ss;
    struct entry *e = &n->cache[k % CACHE];
    float *cov;

    if (e->cov && e->scalar == s && e->w == w && e->h == h && e->ss == ss)
        return e->cov;
    cov = malloc((size_t)w * h * sizeof *cov);
    if (!cov) {
        *rc = NEURONTE_ERR_NOMEM;
        return NULL;
    }
    *rc = neuronte_coverage(n, s, w, h, ss, cov);
    if (*rc != NEURONTE_OK) {
        free(cov);
        return NULL;
    }
    free(e->cov);
    e->cov = cov;
    e->scalar = s;
    e->w = w;
    e->h = h;
    e->ss = ss;
    return cov;
}

static uint32_t blend(uint32_t dst, uint32_t color, float a)
{
    float da = (float)(dst >> 24) / 255.0f, oa = a + da * (1.0f - a), ch[3];
    int i;
    if (oa <= 0.0f)
        return 0;
    for (i = 0; i < 3; i++) {
        int sh = 16 - 8 * i;
        float sc = (float)((color >> sh) & 0xFF), dc = (float)((dst >> sh) & 0xFF);
        ch[i] = (sc * a + dc * da * (1.0f - a)) / oa;
    }
    return (uint32_t)(oa * 255.0f + 0.5f) << 24 | (uint32_t)(ch[0] + 0.5f) << 16 |
           (uint32_t)(ch[1] + 0.5f) << 8 | (uint32_t)(ch[2] + 0.5f);
}

int neuronte_draw_scalar(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                         int x, int y, int cell_w, int cell_h, uint32_t scalar, uint32_t color)
{
    const float *cov;
    float alpha = (float)(color >> 24) / 255.0f;
    int rc = NEURONTE_OK, ss, px, py;

    if (!n || !pixels || width < 0 || height < 0 || stride < width || cell_w <= 0 ||
        cell_h <= 0 || cell_w > NEURONTE_MAX_CELL || cell_h > NEURONTE_MAX_CELL)
        return NEURONTE_ERR_ARG;
    if (alpha <= 0.0f || x >= width || y >= height || x + cell_w <= 0 || y + cell_h <= 0)
        return NEURONTE_OK;
    ss = n->samples ? n->samples : auto_samples(cell_w);
    cov = cached(n, normalize(scalar), cell_w, cell_h, ss, &rc);
    if (!cov)
        return rc;
    for (py = y < 0 ? -y : 0; py < cell_h && y + py < height; py++)
        for (px = x < 0 ? -x : 0; px < cell_w && x + px < width; px++) {
            float a = cov[(size_t)py * cell_w + px] * alpha;
            if (a > 0.0f) {
                uint32_t *d = pixels + (size_t)(y + py) * stride + (x + px);
                *d = blend(*d, color, a);
            }
        }
    return NEURONTE_OK;
}

int neuronte_draw_utf8(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int cell_w, int cell_h, const char *text, size_t len,
                       uint32_t color)
{
    size_t off = 0;
    int cells = 0;

    if (!text && len)
        return NEURONTE_ERR_ARG;
    while (off < len) {
        uint32_t s;
        int rc;
        off += neuronte_utf8_decode(text + off, len - off, &s);
        rc = neuronte_draw_scalar(n, pixels, stride, width, height, x, y, cell_w, cell_h, s, color);
        if (rc != NEURONTE_OK)
            return rc;
        x += cell_w;
        cells++;
    }
    return cells;
}
