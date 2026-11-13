/* The Neuronte net: load, evaluate, draw. MIT licence. See LICENSE.
 *
 * The net is four dense layers. Input is 26 position features of a point
 * (x, y) in the 1 x 2 design cell and 64 features of the character's
 * scalar (its 21 bits and 43 parity bits, each -1 or +1). Three hidden
 * layers use ReLU; their width is read from the weights file. The output f is a clamped signed distance to the
 * ink edge, scaled by 1/tau. A sample's coverage is a ramp one sample wide:
 * clamp(0.5 + f * tau * cell_w * samples, 0, 1).
 *
 * The first layer is a sum of an x part, a y part and a character part,
 * so those are computed once per sample column, sample row and cell. The
 * other layers are stored transposed so each multiply is an axpy over the
 * outputs, which skips the inputs ReLU set to zero.
 *
 * A weights file holds one distance net (version 1), a bundle of nets
 * (version 2) with a router, or one colour net (version 3). A bundle's
 * members are version 1 or version 3. The router is a table of scalar
 * ranges, each drawn by one net, and for scalars outside the table either
 * a gate, a small net over the same 64 code features that picks a net, or
 * a fallback net. The handle is the same either way; one net is a bundle
 * of one.
 *
 * A colour net has K distance outputs that share the hidden vector, a
 * palette head that runs once per glyph, and the straight edges of the
 * drawings. Snapping warps the sample positions. It does not change the
 * weights. The warp is the one in train/snap.py.
 *
 * An advance table (version 4) is the pen step of each character of a
 * proportional face, regular and bold, in steps of a hundredth of an em.
 * A drawing file (version 5) is a directory of whole images: nets, at
 * most one advance table, and colour nets.
 */
#include "neuronte.h"

#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define OCT 6
#define POS (2 + 4 * OCT)
#define CODE 64
#define NMASK (CODE - 21)
#define IN (POS + CODE)
#define LAYERS 3
#define HEADER (8 + 5 * 4 + 4 + NMASK * 4)
#define MAX_H 1024 /* distance widths are multiples of 4 up to this */
#define MAX_NETS 16
#define MAX_RANGES 65536
#define MAX_GATE 256 /* gate hidden width */
#define BUNDLE_HEAD 28
#define ADV_HEAD 32
#define ADV_RECORD 8
#define ADV_MAX 4096           /* records in an advance table */
#define ADV_LO 10              /* the least and the greatest advance, in steps */
#define ADV_HI 200
#define DRAWING_HEAD 16
#define MIN_IMAGE 12           /* a magic and a version */
#define SETS 256 /* the draw cache: SETS x WAYS cells, least recently used out */
#define WAYS 4
#define MAX_K 16
#define MAX_R 256
#define COLOUR_FIXED 420
#define MAX_E 65536
#define MAX_MEMBER (32u * 1024u * 1024u) /* a wide colour net, plus its edge table */

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
    float *cov;   /* layers masks, each w * h, layer 0 first */
    uint8_t *ent; /* one palette index per layer */
    uint32_t scalar;
    int w, h, ss, snap;
    unsigned long used;
};

struct one_edge {
    float pos;
    int rising;
};

struct layer_edges {
    int nx, ny;
    struct one_edge *x, *y;
};

struct glyph_rec {
    uint32_t scalar;
    struct layer_edges *layer;
};

struct colour {
    int k, r, snap_px;
    uint8_t dark[96], light[96];
    float *w_out, *b_out; /* K x H, and K bias */
    float *hw1, *hb1;     /* head h1, R x 64, and R bias */
    float *hw2, *hb2;     /* head out, (K*5) x R, and K*5 bias */
    float *mem;
    struct glyph_rec *recs;
    struct layer_edges *layers;
    struct one_edge *pool;
    int nrecs;
};

struct net {
    int h;          /* hidden width */
    float *w1_pos;  /* POS rows of h: column i of l1, as a row */
    float *w1_code; /* CODE rows of h */
    float *b1;
    float *w2; /* h rows of h: w2[i * h + o] = l2 weight (o, i) */
    float *b2;
    float *w3;
    float *b3;
    float *w4;
    float b4;
    float tau;
    uint32_t masks[NMASK];
    struct colour *col; /* set for a version 3 net, otherwise NULL */
    float mem[];        /* the arrays above point into this */
};

struct range {
    uint32_t first, last, net;
};

struct advance {
    uint32_t scalar;
    uint16_t steps[2]; /* regular, bold */
};

struct neuronte {
    struct advance *adv; /* sorted by scalar; NULL for no advance table */
    size_t nadv, adv_fallback; /* the record a scalar with none of its own takes */
    int nets;
    struct net *net[MAX_NETS];
    struct range *ranges; /* sorted, not overlapping */
    size_t nranges;
    uint32_t fallback; /* the net for scalars outside the table, with no gate */
    int gate_h;        /* the gate's hidden width, 0 for no gate */
    uint32_t gate_masks[NMASK];
    float *gate; /* CODE rows of gate_h (l1, transposed), gate_h bias, nets rows of gate_h, nets bias */
    int samples;
    int theme;      /* 0 dark, 1 light */
    int snap_below; /* snap a colour glyph when cell_w is below this; 0 is off */
    int snap_file;  /* the number -1 restores */
    int layers;     /* the largest K in the file, at least 1 */
    int binary;     /* distance-net draw calls cut coverage at one half */
    uint8_t dark[96], light[96];
    unsigned long tick;
    struct entry cache[SETS][WAYS];
};

/* Weights and biases in a net of hidden width h. */
static size_t params(size_t h)
{
    return h * IN + h + 2 * (h * h + h) + h + 1;
}

/* Trunk and palette-head weights of a colour net. Palette bytes and the
 * edge table are not weights. */
static size_t trunk_floats(size_t h, size_t k)
{
    return 2 * h * h + (93 + k) * h + k;
}

static size_t head_floats(size_t r, size_t k)
{
    return r * (65 + 5 * k) + 5 * k;
}

/* The length of a one-net file of hidden width h, or 0 if no such width. */
static size_t file_len(uint32_t h)
{
    return h >= 8 && h <= MAX_H && h % 4 == 0 ? HEADER + 4 * params(h) : 0;
}

static size_t gate_params(size_t g, size_t k)
{
    return g * CODE + g + k * g + k;
}

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

static int finite_run(const unsigned char *p, size_t count)
{
    size_t i;
    for (i = 0; i < count; i++)
        if (!isfinite(rdf(p + 4 * i)))
            return 0;
    return 1;
}

/* One net from a version 1 image. */
static int net_open(const unsigned char *p, size_t len, struct net **out)
{
    struct net *n;
    size_t off, len_want;
    float *m;
    int i, o, h;

    if (len < 28 || memcmp(p, "NEURONTE", 8) != 0 || rd32(p + 8) != 1)
        return NEURONTE_ERR_FORMAT;
    len_want = file_len(rd32(p + 20));
    if (rd32(p + 12) != OCT || rd32(p + 16) != CODE || len_want == 0 || rd32(p + 24) != LAYERS)
        return NEURONTE_ERR_SHAPE;
    if (len != len_want)
        return NEURONTE_ERR_FORMAT;

    h = (int)rd32(p + 20);
    n = malloc(sizeof *n + (params((size_t)h) - 1) * sizeof *n->mem);
    if (!n)
        return NEURONTE_ERR_NOMEM;
    n->col = NULL;
    m = n->mem;
    n->h = h;
    n->w1_pos = m;
    n->w1_code = m += POS * h;
    n->b1 = m += CODE * h;
    n->w2 = m += h;
    n->b2 = m += (size_t)h * h;
    n->w3 = m += h;
    n->b3 = m += (size_t)h * h;
    n->w4 = m += h;
    n->tau = rdf(p + 28);
    if (!isfinite(n->tau) || n->tau <= 0)
        goto bad;
    for (i = 0; i < NMASK; i++) {
        n->masks[i] = rd32(p + 32 + 4 * i);
        if (n->masks[i] == 0 || n->masks[i] >= 1u << 21)
            goto bad;
    }
    if (!finite_run(p + HEADER, (len - HEADER) / 4))
        goto bad;

    off = HEADER;
#define NEXT() (off += 4, rdf(p + off - 4))
    for (o = 0; o < h; o++)
        for (i = 0; i < IN; i++) {
            float v = NEXT();
            if (i < POS)
                n->w1_pos[(size_t)i * h + o] = v;
            else
                n->w1_code[(size_t)(i - POS) * h + o] = v;
        }
    for (o = 0; o < h; o++)
        n->b1[o] = NEXT();
    for (o = 0; o < h; o++)
        for (i = 0; i < h; i++)
            n->w2[(size_t)i * h + o] = NEXT();
    for (o = 0; o < h; o++)
        n->b2[o] = NEXT();
    for (o = 0; o < h; o++)
        for (i = 0; i < h; i++)
            n->w3[(size_t)i * h + o] = NEXT();
    for (o = 0; o < h; o++)
        n->b3[o] = NEXT();
    for (i = 0; i < h; i++)
        n->w4[i] = NEXT();
    n->b4 = NEXT();
#undef NEXT
    *out = n;
    return NEURONTE_OK;
bad:
    free(n);
    return NEURONTE_ERR_FORMAT;
}

/* The bytes a bundle needs before its nets, or 0 if the header is bad. */
static size_t bundle_prefix(const unsigned char *p)
{
    uint32_t k = rd32(p + 12), r = rd32(p + 16), fb = rd32(p + 20), g = rd32(p + 24);
    if (k < 1 || k > MAX_NETS || r > MAX_RANGES || fb >= k || g > MAX_GATE)
        return 0;
    return BUNDLE_HEAD + 4 * (size_t)k + 12 * (size_t)r + (g ? 4 * (NMASK + gate_params(g, k)) : 0);
}

/* The length of a bundle from its first bundle_prefix() bytes, or 0. */
static size_t bundle_len(const unsigned char *p)
{
    size_t total = bundle_prefix(p), i;
    for (i = 0; total && i < rd32(p + 12); i++) {
        uint32_t len = rd32(p + BUNDLE_HEAD + 4 * i);
        /* A colour member is longer than a distance net of the same width.
         * The cap is the largest colour image this reader will load. */
        if (len < HEADER || len > MAX_MEMBER)
            return 0;
        total += len;
    }
    return total;
}

static void colour_free(struct colour *c)
{
    if (!c)
        return;
    free(c->mem);
    free(c->recs);
    free(c->layers);
    free(c->pool);
    free(c);
}

static void net_free(struct net *n)
{
    if (!n)
        return;
    colour_free(n->col);
    free(n);
}

static void free_handle(neuronte *n)
{
    int i, j;
    for (i = 0; i < n->nets; i++)
        net_free(n->net[i]);
    for (i = 0; i < SETS; i++)
        for (j = 0; j < WAYS; j++) {
            free(n->cache[i][j].cov);
            free(n->cache[i][j].ent);
        }
    free(n->ranges);
    free(n->gate);
    free(n->adv);
    free(n);
}

static uint32_t rd16(const unsigned char *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8;
}

/* 1 when the fixed header names a colour net this reader can size.
 * A version 1 image with the version word overwritten fails here, and
 * the caller reports it as a damaged file. */
static int colour_sizes(const unsigned char *p, size_t *weights, uint32_t *k_out, uint32_t *e_out)
{
    uint32_t h = rd32(p + 20), k = rd32(p + 32), r = rd32(p + 44), e = rd32(p + 48);
    size_t trunk, head;

    if (rd32(p + 12) != OCT || rd32(p + 16) != CODE || rd32(p + 24) != LAYERS)
        return 0;
    if (rd32(p + 36) != 32 || rd32(p + 40) != 5 || k < 1 || k > MAX_K || e > MAX_E)
        return 0;
    if (h < 8 || h > MAX_H || h % 8 != 0 || r < 8 || r > MAX_R || r % 8 != 0)
        return 0;
    trunk = trunk_floats(h, k);
    head = head_floats(r, k);
    *weights = 4 * (trunk + head);
    *k_out = k;
    *e_out = e;
    return 1;
}

/* One form A colour net from a version 3 image. */
static int colour_open(const unsigned char *p, size_t len, struct net **out)
{
    struct net *n;
    struct colour *c;
    size_t weights, off, count, used;
    float *m;
    uint32_t k, rbits, e, snap, prev;
    int h, r, i, o, layer;

    if (len < COLOUR_FIXED || memcmp(p, "NEURONTE", 8) != 0 || rd32(p + 8) != 3)
        return NEURONTE_ERR_FORMAT;
    /* K before the shape checks: a distance file with its version word set
     * to 3 has a parity mask there, not a layer count, and that is a
     * damaged file rather than a net of a different shape. */
    k = rd32(p + 32);
    if (k < 1 || k > MAX_K)
        return NEURONTE_ERR_FORMAT;
    if (rd32(p + 36) != 32 || rd32(p + 40) != 5)
        return NEURONTE_ERR_SHAPE;
    if (rd32(p + 12) != OCT || rd32(p + 16) != CODE || rd32(p + 24) != LAYERS)
        return NEURONTE_ERR_SHAPE;
    if (!colour_sizes(p, &weights, &k, &e))
        return NEURONTE_ERR_SHAPE;
    snap = rd32(p + 52);
    if (snap > 65535)
        return NEURONTE_ERR_FORMAT;
    if (len < COLOUR_FIXED + weights || !finite_run(p + COLOUR_FIXED, weights / 4))
        return NEURONTE_ERR_FORMAT;

    h = (int)rd32(p + 20);
    r = (int)rd32(p + 44);
    n = malloc(sizeof *n + (params((size_t)h) - 1) * sizeof *n->mem);
    c = calloc(1, sizeof *c);
    if (!n || !c) {
        free(n);
        free(c);
        return NEURONTE_ERR_NOMEM;
    }
    n->col = c;
    m = n->mem;
    n->h = h;
    n->w1_pos = m;
    n->w1_code = m += POS * h;
    n->b1 = m += CODE * h;
    n->w2 = m += h;
    n->b2 = m += (size_t)h * h;
    n->w3 = m += h;
    n->b3 = m += (size_t)h * h;
    n->w4 = m += h;
    n->tau = rdf(p + 28);
    if (!isfinite(n->tau) || n->tau <= 0)
        goto bad;
    for (i = 0; i < NMASK; i++) {
        n->masks[i] = rd32(p + 56 + 4 * i);
        if (n->masks[i] == 0 || n->masks[i] >= 1u << 21)
            goto bad;
    }
    c->k = (int)k;
    c->r = r;
    c->snap_px = (int)snap;
    memcpy(c->dark, p + 228, 96);
    memcpy(c->light, p + 324, 96);
    /* Trunk hidden weights live in n->mem. What remains is the K outputs
     * and the palette head. */
    {
        size_t hidden = (size_t)(2 * h * h + 93 * h);
        size_t rest = weights / 4 - hidden;
        float *cm;

        c->mem = malloc(rest * sizeof *c->mem);
        if (!c->mem)
            goto nomem;
        cm = c->mem;
        c->w_out = cm;
        c->b_out = cm += (size_t)k * h;
        c->hw1 = cm += k;
        c->hb1 = cm += (size_t)r * 64;
        c->hw2 = cm += r;
        c->hb2 = cm += (size_t)k * 5 * r;
        (void)cm;
    }

    off = COLOUR_FIXED;
#define NEXT() (off += 4, rdf(p + off - 4))
    for (o = 0; o < h; o++)
        for (i = 0; i < IN; i++) {
            float v = NEXT();
            if (i < POS)
                n->w1_pos[(size_t)i * h + o] = v;
            else
                n->w1_code[(size_t)(i - POS) * h + o] = v;
        }
    for (o = 0; o < h; o++)
        n->b1[o] = NEXT();
    for (o = 0; o < h; o++)
        for (i = 0; i < h; i++)
            n->w2[(size_t)i * h + o] = NEXT();
    for (o = 0; o < h; o++)
        n->b2[o] = NEXT();
    for (o = 0; o < h; o++)
        for (i = 0; i < h; i++)
            n->w3[(size_t)i * h + o] = NEXT();
    for (o = 0; o < h; o++)
        n->b3[o] = NEXT();
    for (layer = 0; layer < (int)k; layer++)
        for (i = 0; i < h; i++)
            c->w_out[(size_t)layer * h + i] = NEXT();
    for (layer = 0; layer < (int)k; layer++)
        c->b_out[layer] = NEXT();
    for (o = 0; o < r; o++)
        for (i = 0; i < CODE; i++)
            c->hw1[(size_t)o * CODE + i] = NEXT();
    for (o = 0; o < r; o++)
        c->hb1[o] = NEXT();
    rbits = k * 5;
    for (o = 0; o < (int)rbits; o++)
        for (i = 0; i < r; i++)
            c->hw2[(size_t)o * r + i] = NEXT();
    for (o = 0; o < (int)rbits; o++)
        c->hb2[o] = NEXT();
#undef NEXT

    /* One pass to check the edge table, one to keep it. */
    count = 0;
    prev = 0;
    {
        size_t at = off;
        for (e = 0; e < rd32(p + 48); e++) {
            uint32_t scalar, nk;
            if (at + 4 > len)
                goto bad;
            scalar = rd32(p + at);
            at += 4;
            if (scalar > 0x1FFFFF || (e > 0 && scalar <= prev))
                goto bad;
            prev = scalar;
            for (nk = 0; nk < k; nk++) {
                uint32_t nx, ny, t;
                if (at + 4 > len)
                    goto bad;
                nx = rd16(p + at);
                ny = rd16(p + at + 2);
                at += 4;
                if (at + (size_t)(nx + ny) * 8 > len)
                    goto bad;
                for (t = 0; t < nx + ny; t++) {
                    float pos = rdf(p + at);
                    uint32_t side = rd32(p + at + 4);
                    if (!isfinite(pos) || side > 1)
                        goto bad;
                    at += 8;
                }
                count += (size_t)nx + ny;
            }
        }
        if (at != len)
            goto bad;
    }
    c->nrecs = (int)rd32(p + 48);
    if (c->nrecs) {
        c->recs = calloc((size_t)c->nrecs, sizeof *c->recs);
        c->layers = calloc((size_t)c->nrecs * k, sizeof *c->layers);
        if (!c->recs || !c->layers)
            goto nomem;
    }
    if (count) {
        c->pool = calloc(count, sizeof *c->pool);
        if (!c->pool)
            goto nomem;
    }
    used = 0;
    for (e = 0; e < (uint32_t)c->nrecs; e++) {
        uint32_t nk;
        c->recs[e].scalar = rd32(p + off);
        off += 4;
        c->recs[e].layer = c->layers + (size_t)e * k;
        for (nk = 0; nk < k; nk++) {
            struct layer_edges *le = &c->recs[e].layer[nk];
            uint32_t t;
            le->nx = (int)rd16(p + off);
            le->ny = (int)rd16(p + off + 2);
            off += 4;
            le->x = c->pool + used;
            for (t = 0; t < (uint32_t)le->nx; t++, off += 8, used++) {
                c->pool[used].pos = rdf(p + off);
                c->pool[used].rising = (int)rd32(p + off + 4);
            }
            le->y = c->pool + used;
            for (t = 0; t < (uint32_t)le->ny; t++, off += 8, used++) {
                c->pool[used].pos = rdf(p + off);
                c->pool[used].rising = (int)rd32(p + off + 4);
            }
        }
    }
    *out = n;
    return NEURONTE_OK;
nomem:
    net_free(n);
    return NEURONTE_ERR_NOMEM;
bad:
    net_free(n);
    return NEURONTE_ERR_FORMAT;
}

static int member_open(const unsigned char *p, size_t len, struct net **out)
{
    if (len < 12 || memcmp(p, "NEURONTE", 8) != 0)
        return NEURONTE_ERR_FORMAT;
    if (rd32(p + 8) == 1)
        return net_open(p, len, out);
    if (rd32(p + 8) == 3)
        return colour_open(p, len, out);
    return NEURONTE_ERR_FORMAT;
}

static int bundle_open(const unsigned char *p, size_t len, neuronte *n)
{
    size_t prefix, off, i;
    uint32_t k;
    int rc;

    if (len < BUNDLE_HEAD || (prefix = bundle_prefix(p)) == 0 || len < prefix || bundle_len(p) != len)
        return NEURONTE_ERR_FORMAT;
    k = rd32(p + 12);
    n->nranges = rd32(p + 16);
    n->fallback = rd32(p + 20);
    n->gate_h = (int)rd32(p + 24);
    off = BUNDLE_HEAD + 4 * (size_t)k;
    if (n->nranges) {
        n->ranges = malloc(n->nranges * sizeof *n->ranges);
        if (!n->ranges)
            return NEURONTE_ERR_NOMEM;
    }
    for (i = 0; i < n->nranges; i++, off += 12) {
        struct range *r = &n->ranges[i];
        r->first = rd32(p + off);
        r->last = rd32(p + off + 4);
        r->net = rd32(p + off + 8);
        if (r->first > r->last || r->last > 0x1FFFFF || r->net >= k ||
            (i > 0 && r->first <= n->ranges[i - 1].last))
            return NEURONTE_ERR_FORMAT;
    }
    if (n->gate_h) {
        size_t g = (size_t)n->gate_h, count = gate_params(g, k), c, o;
        const unsigned char *w;
        for (i = 0; i < NMASK; i++, off += 4) {
            n->gate_masks[i] = rd32(p + off);
            if (n->gate_masks[i] == 0 || n->gate_masks[i] >= 1u << 21)
                return NEURONTE_ERR_FORMAT;
        }
        if (!finite_run(p + off, count))
            return NEURONTE_ERR_FORMAT;
        n->gate = malloc(count * sizeof *n->gate);
        if (!n->gate)
            return NEURONTE_ERR_NOMEM;
        /* l1 is stored g rows of CODE; keep it as CODE rows of g. */
        w = p + off;
        for (o = 0; o < g; o++)
            for (c = 0; c < CODE; c++)
                n->gate[c * g + o] = rdf(w + 4 * (o * CODE + c));
        for (i = g * CODE; i < count; i++)
            n->gate[i] = rdf(w + 4 * i);
        off += 4 * count;
    }
    for (i = 0; i < k; i++) {
        size_t nl = rd32(p + BUNDLE_HEAD + 4 * i);
        rc = member_open(p + off, nl, &n->net[i]);
        if (rc != NEURONTE_OK)
            return rc;
        n->nets++;
        off += nl;
    }
    return NEURONTE_OK;
}

/* Copy the first colour net's palette and snap threshold onto the handle.
 * A later colour net with a different palette or threshold is a damaged
 * bundle. A file of distance nets keeps a zero palette and snapping off. */
static int adopt(neuronte *n)
{
    int i, seen = 0;

    n->layers = 1;
    n->snap_file = 0;
    n->snap_below = 0;
    memset(n->dark, 0, sizeof n->dark);
    memset(n->light, 0, sizeof n->light);
    for (i = 0; i < n->nets; i++) {
        struct colour *c = n->net[i]->col;
        if (!c)
            continue;
        if (!seen) {
            memcpy(n->dark, c->dark, 96);
            memcpy(n->light, c->light, 96);
            n->snap_file = c->snap_px;
            n->snap_below = c->snap_px;
            seen = 1;
        } else if (memcmp(n->dark, c->dark, 96) != 0 || memcmp(n->light, c->light, 96) != 0 ||
                   c->snap_px != n->snap_file) {
            return NEURONTE_ERR_FORMAT;
        }
        if (c->k > n->layers)
            n->layers = c->k;
    }
    return NEURONTE_OK;
}

/* The length of an advance table from its first 28 bytes, or 0. */
static size_t adv_len(const unsigned char *p)
{
    uint32_t count = rd32(p + 24);
    return count >= 1 && count <= ADV_MAX ? ADV_HEAD + ADV_RECORD * (size_t)count : 0;
}

/* The advance table from a version 4 image. Nothing in it is repaired. */
static int adv_open(const unsigned char *p, size_t len, neuronte *n)
{
    uint32_t fallback;
    size_t count, i;
    int found = 0;

    if (n->adv || len < ADV_HEAD || memcmp(p, "NEURONTE", 8) != 0 || rd32(p + 8) != 4 ||
        rd32(p + 12) != 10 || rd32(p + 16) != 10 || rd32(p + 20) != 2 || adv_len(p) != len)
        return NEURONTE_ERR_FORMAT;
    count = rd32(p + 24);
    fallback = rd32(p + 28);
    n->adv = malloc(count * sizeof *n->adv);
    if (!n->adv)
        return NEURONTE_ERR_NOMEM;
    n->nadv = count;
    for (i = 0; i < count; i++) {
        const unsigned char *r = p + ADV_HEAD + ADV_RECORD * i;
        struct advance *a = &n->adv[i];
        int w;
        a->scalar = rd32(r);
        if (a->scalar > 0x10FFFF || (a->scalar >= 0xD800 && a->scalar <= 0xDFFF) ||
            (i > 0 && a->scalar <= n->adv[i - 1].scalar))
            return NEURONTE_ERR_FORMAT;
        for (w = 0; w < 2; w++) {
            a->steps[w] = (uint16_t)(r[4 + 2 * w] | r[5 + 2 * w] << 8);
            if (a->steps[w] < ADV_LO || a->steps[w] > ADV_HI)
                return NEURONTE_ERR_FORMAT;
        }
        if (a->scalar == fallback) {
            n->adv_fallback = i;
            found = 1;
        }
    }
    return found ? NEURONTE_OK : NEURONTE_ERR_FORMAT;
}

/* The bytes a drawing file needs before its members, or 0 if the header is bad. */
static size_t drawing_prefix(const unsigned char *p)
{
    uint32_t m = rd32(p + 12);
    return m >= 1 && m <= MAX_NETS ? DRAWING_HEAD + 8 * (size_t)m : 0;
}

/* The length of a drawing file from its first drawing_prefix() bytes, or 0.
 * Members follow the directory in its order, with nothing between them. */
static size_t drawing_len(const unsigned char *p)
{
    size_t total = drawing_prefix(p), i;
    for (i = 0; total && i < rd32(p + 12); i++) {
        uint32_t off = rd32(p + DRAWING_HEAD + 8 * i), len = rd32(p + DRAWING_HEAD + 8 * i + 4);
        if (off != total || len < MIN_IMAGE || len > MAX_MEMBER)
            return 0;
        total += len;
    }
    return total;
}

static int drawing_open(const unsigned char *p, size_t len, neuronte *n)
{
    size_t prefix, off, i;

    if (len < DRAWING_HEAD || (prefix = drawing_prefix(p)) == 0 || len < prefix || drawing_len(p) != len)
        return NEURONTE_ERR_FORMAT;
    for (i = 0, off = prefix; i < rd32(p + 12); i++) {
        size_t ml = rd32(p + DRAWING_HEAD + 8 * i + 4);
        const unsigned char *m = p + off;
        int rc = NEURONTE_OK;
        if (memcmp(m, "NEURONTE", 8) != 0)
            return NEURONTE_ERR_FORMAT;
        switch (rd32(m + 8)) {
        case 1:
            rc = net_open(m, ml, &n->net[n->nets]);
            n->nets += rc == NEURONTE_OK;
            break;
        case 3:
            rc = colour_open(m, ml, &n->net[n->nets]);
            n->nets += rc == NEURONTE_OK;
            break;
        case 4:
            rc = adv_open(m, ml, n); /* a second table is refused there */
            break;
        default: /* a bundle or a drawing file inside one, or a later kind */
            rc = NEURONTE_ERR_FORMAT;
        }
        if (rc != NEURONTE_OK)
            return rc;
        off += ml;
    }
    return NEURONTE_OK;
}

int neuronte_open(const void *data, size_t len, neuronte **out)
{
    const unsigned char *p = data;
    neuronte *n;
    uint32_t ver;
    int rc;

    if (!out)
        return NEURONTE_ERR_ARG;
    *out = NULL;
    if (!data)
        return NEURONTE_ERR_ARG;
    if (len < MIN_IMAGE || memcmp(p, "NEURONTE", 8) != 0)
        return NEURONTE_ERR_FORMAT;
    ver = rd32(p + 8);
    if (ver != 1 && ver != 2 && ver != 3 && ver != 4 && ver != 5)
        return NEURONTE_ERR_FORMAT;
    n = calloc(1, sizeof *n);
    if (!n)
        return NEURONTE_ERR_NOMEM;
    if (ver == 1) {
        rc = net_open(p, len, &n->net[0]);
        n->nets = rc == NEURONTE_OK;
    } else if (ver == 2) {
        rc = bundle_open(p, len, n);
    } else if (ver == 3) {
        rc = colour_open(p, len, &n->net[0]);
        n->nets = rc == NEURONTE_OK;
    } else if (ver == 4) {
        rc = adv_open(p, len, n);
    } else {
        rc = drawing_open(p, len, n);
    }
    if (rc == NEURONTE_OK)
        rc = adopt(n);
    if (rc != NEURONTE_OK) {
        free_handle(n);
        return rc;
    }
    *out = n;
    return NEURONTE_OK;
}

/* Append n bytes. 1 means the file ended early: *len is what was read,
 * and the caller lets neuronte_open report the short file. A count that
 * would pass MAX_MEMBER is refused before the read. */
static int colour_append(FILE *f, unsigned char **buf, size_t *len, size_t *cap, size_t n)
{
    size_t got;
    unsigned char *grown;

    if (n > MAX_MEMBER || *len > MAX_MEMBER - n)
        return NEURONTE_ERR_FORMAT;
    if (*len + n + 1 > *cap) {
        grown = realloc(*buf, *len + n + 1);
        if (!grown)
            return NEURONTE_ERR_NOMEM;
        *buf = grown;
        *cap = *len + n + 1;
    }
    got = fread(*buf + *len, 1, n, f);
    *len += got;
    if (ferror(f))
        return NEURONTE_ERR_IO;
    return got == n ? NEURONTE_OK : 1;
}

/* A version 3 image: fixed header, weights, edge table, and one extra
 * byte so a file that runs on is rejected. */
static int slurp_colour(FILE *f, const unsigned char *fixed, unsigned char **out, size_t *out_len)
{
    size_t weights, len, cap;
    uint32_t k, e, rec, layer;
    unsigned char *buf;
    int rc;

    if (!colour_sizes(fixed, &weights, &k, &e) || COLOUR_FIXED + weights > MAX_MEMBER) {
        buf = malloc(COLOUR_FIXED);
        if (!buf)
            return NEURONTE_ERR_NOMEM;
        memcpy(buf, fixed, COLOUR_FIXED);
        *out = buf;
        *out_len = COLOUR_FIXED;
        return NEURONTE_OK;
    }
    cap = COLOUR_FIXED + weights + 1;
    buf = malloc(cap);
    if (!buf)
        return NEURONTE_ERR_NOMEM;
    memcpy(buf, fixed, COLOUR_FIXED);
    len = COLOUR_FIXED;
    rc = colour_append(f, &buf, &len, &cap, weights);
    if (rc == 1)
        goto done;
    if (rc != NEURONTE_OK)
        goto fail;
    for (rec = 0; rec < e; rec++) {
        rc = colour_append(f, &buf, &len, &cap, 4);
        if (rc == 1)
            goto done;
        if (rc != NEURONTE_OK)
            goto fail;
        for (layer = 0; layer < k; layer++) {
            size_t at = len;
            uint32_t nx, ny;
            rc = colour_append(f, &buf, &len, &cap, 4);
            if (rc == 1)
                goto done;
            if (rc != NEURONTE_OK)
                goto fail;
            nx = rd16(buf + at);
            ny = rd16(buf + at + 2);
            rc = colour_append(f, &buf, &len, &cap, (size_t)(nx + ny) * 8);
            if (rc == 1)
                goto done;
            if (rc != NEURONTE_OK)
                goto fail;
        }
    }
    rc = colour_append(f, &buf, &len, &cap, 1);
    if (rc == 1 || rc == NEURONTE_OK)
        goto done;
fail:
    free(buf);
    return rc;
done:
    *out = buf;
    *out_len = len;
    return NEURONTE_OK;
}

/* Read exactly the bytes the file's header says it has, and one more,
 * which shows a file too long; never more than that. A version 3 file's
 * length is the edge table's, so that table is walked with the same cap. */
int neuronte_open_file(const char *path, neuronte **out)
{
    unsigned char head[BUNDLE_HEAD], *buf = NULL;
    size_t got, want = 0, prefix = 0;
    size_t (*whole)(const unsigned char *) = bundle_len;
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
    got = fread(head, 1, sizeof head, f);
    if (got == sizeof head && rd32(head + 8) == 3) {
        unsigned char fixed[COLOUR_FIXED];
        size_t more;
        memcpy(fixed, head, sizeof head);
        more = fread(fixed + sizeof head, 1, COLOUR_FIXED - sizeof head, f);
        if (ferror(f)) {
            fclose(f);
            return NEURONTE_ERR_IO;
        }
        got = sizeof head + more;
        if (got < COLOUR_FIXED) {
            rc = neuronte_open(fixed, got, out);
            fclose(f);
            return rc;
        }
        rc = slurp_colour(f, fixed, &buf, &got);
        if (rc != NEURONTE_OK) {
            fclose(f);
            return rc;
        }
        rc = neuronte_open(buf, got, out);
        fclose(f);
        free(buf);
        return rc;
    }
    if (got == sizeof head && rd32(head + 8) == 1)
        want = file_len(rd32(head + 20));
    else if (got == sizeof head && rd32(head + 8) == 2)
        prefix = bundle_prefix(head);
    else if (got == sizeof head && rd32(head + 8) == 4)
        want = adv_len(head);
    else if (got == sizeof head && rd32(head + 8) == 5) {
        prefix = drawing_prefix(head);
        whole = drawing_len;
    }
    if (prefix) {
        /* A drawing file of one member has a prefix shorter than the head
         * already read. */
        if (prefix < sizeof head)
            prefix = sizeof head;
        buf = malloc(prefix);
        if (!buf) {
            fclose(f);
            return NEURONTE_ERR_NOMEM;
        }
        memcpy(buf, head, sizeof head);
        got = sizeof head + fread(buf + sizeof head, 1, prefix - sizeof head, f);
        want = got == prefix ? whole(buf) : 0;
        if (want == 0) {
            rc = ferror(f) ? NEURONTE_ERR_IO : NEURONTE_ERR_FORMAT;
            fclose(f);
            free(buf);
            return rc;
        }
    }
    if (ferror(f) || want == 0) {
        /* Too short or a bad header: let neuronte_open say which. */
        rc = ferror(f) ? NEURONTE_ERR_IO : neuronte_open(head, got, out);
        fclose(f);
        free(buf);
        return rc;
    }
    {
        unsigned char *all = realloc(buf, want + 1);
        if (!all) {
            free(buf);
            fclose(f);
            return NEURONTE_ERR_NOMEM;
        }
        buf = all;
    }
    if (!prefix) {
        memcpy(buf, head, sizeof head);
        prefix = sizeof head;
    }
    got = prefix + fread(buf + prefix, 1, want + 1 - prefix, f);
    rc = ferror(f) ? NEURONTE_ERR_IO : neuronte_open(buf, got, out);
    fclose(f);
    free(buf);
    return rc;
}

size_t neuronte_parameters(const neuronte *n)
{
    size_t total = 0;
    int i;
    if (!n)
        return 0;
    for (i = 0; i < n->nets; i++) {
        struct colour *c = n->net[i]->col;
        if (c)
            total += trunk_floats((size_t)n->net[i]->h, (size_t)c->k) +
                     head_floats((size_t)c->r, (size_t)c->k);
        else
            total += params((size_t)n->net[i]->h);
    }
    return total + (n->gate_h ? gate_params((size_t)n->gate_h, (size_t)n->nets) : 0);
}

int neuronte_nets(const neuronte *n)
{
    return n ? n->nets : 0;
}

void neuronte_close(neuronte *n)
{
    if (n)
        free_handle(n);
}

int neuronte_set_samples(neuronte *n, int per_axis)
{
    if (!n || per_axis < 0 || per_axis > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    n->samples = per_axis;
    return NEURONTE_OK;
}

int neuronte_layers(const neuronte *n)
{
    return n ? n->layers : 0;
}

int neuronte_set_theme(neuronte *n, int theme)
{
    if (!n || (theme != 0 && theme != 1))
        return NEURONTE_ERR_ARG;
    n->theme = theme;
    return NEURONTE_OK;
}

int neuronte_set_snap(neuronte *n, int below_px)
{
    if (!n || below_px < -1)
        return NEURONTE_ERR_ARG;
    n->snap_below = below_px < 0 ? n->snap_file : below_px;
    return NEURONTE_OK;
}

int neuronte_palette(const neuronte *n, int theme, uint8_t *rgb)
{
    if (!n || !rgb || (theme != 0 && theme != 1))
        return NEURONTE_ERR_ARG;
    memcpy(rgb, theme ? n->light : n->dark, 96);
    return NEURONTE_OK;
}

int neuronte_set_binary(neuronte *n, int on)
{
    if (!n || on < 0 || on > 1)
        return NEURONTE_ERR_ARG;
    n->binary = on;
    return NEURONTE_OK;
}

static uint32_t normalize(uint32_t s)
{
    return (s > 0x10FFFF || (s >= 0xD800 && s <= 0xDFFF)) ? NEURONTE_REPLACEMENT : s;
}

static int half_code(uint32_t scalar, int half, uint32_t *code)
{
    if (scalar != normalize(scalar) || half < 0 || half > 1 ||
        (half && scalar > 0xEFFFF))
        return NEURONTE_ERR_ARG;
    *code = scalar + (half ? 0x110000u : 0);
    return NEURONTE_OK;
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

/* The 64 code features of s, each -1 or +1. */
static void code_of(uint32_t s, const uint32_t *masks, float *v)
{
    int i;
    for (i = 0; i < CODE; i++)
        v[i] = (i < 21 ? (s >> i) & 1 : (uint32_t)parity(s & masks[i - 21])) ? 1.0f : -1.0f;
}

/* The net the gate picks for s: the first of the highest outputs. */
static int gate_pick(const neuronte *n, uint32_t s)
{
    float v[CODE], hid[MAX_GATE], best = 0.0f;
    const float *b1, *w2, *b2;
    int g = n->gate_h, i, o, pick = 0;

    code_of(s, n->gate_masks, v);
    b1 = n->gate + (size_t)g * CODE;
    w2 = b1 + g;
    b2 = w2 + (size_t)n->nets * g;
    memcpy(hid, b1, (size_t)g * sizeof *hid);
    for (i = 0; i < CODE; i++)
        for (o = 0; o < g; o++)
            hid[o] += v[i] * n->gate[(size_t)i * g + o];
    for (i = 0; i < n->nets; i++) {
        float z = b2[i];
        for (o = 0; o < g; o++)
            z += w2[(size_t)i * g + o] * (hid[o] > 0.0f ? hid[o] : 0.0f);
        if (i == 0 || z > best) {
            best = z;
            pick = i;
        }
    }
    return pick;
}

static int route(const neuronte *n, uint32_t s)
{
    size_t lo = 0, hi = n->nranges;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (n->ranges[mid].last < s)
            lo = mid + 1;
        else
            hi = mid;
    }
    if (lo < n->nranges && n->ranges[lo].first <= s)
        return (int)n->ranges[lo].net;
    return n->gate_h ? gate_pick(n, s) : (int)n->fallback;
}

/* l1 bias plus the character's columns of l1. */
static void char_part(const struct net *n, uint32_t s, float *c)
{
    int i, o, h = n->h;
    memcpy(c, n->b1, (size_t)h * sizeof *c);
    for (i = 0; i < CODE; i++) {
        int bit = i < 21 ? (int)((s >> i) & 1) : parity(s & n->masks[i - 21]);
        float v = bit ? 1.0f : -1.0f;
        const float *w = n->w1_code + (size_t)i * h;
        for (o = 0; o < h; o++)
            c[o] += v * w[o];
    }
}

/* One axis's columns of l1 at coordinate t: axis 0 is x in 0..1, axis 1
 * is y in 0..2. Feature 0 is 2x - 1 and feature 1 is y - 1. For octave k
 * features 2+4k and 3+4k are sin(w x) and sin(w y), 4+4k and 5+4k are
 * cos(w x) and cos(w y), with w = 2 pi 2^k. */
static void axis_part(const struct net *n, int axis, double t, float *out)
{
    const double two_pi = 6.283185307179586476925286766559;
    float v = axis == 0 ? (float)(2.0 * t - 1.0) : (float)(t - 1.0);
    int k, o, h = n->h;
    for (o = 0; o < h; o++)
        out[o] = v * n->w1_pos[(size_t)axis * h + o];
    for (k = 0; k < OCT; k++) {
        double w = two_pi * (double)(1 << k);
        float sv = (float)sin(w * t), cv = (float)cos(w * t);
        const float *ws = n->w1_pos + (size_t)(2 + 4 * k + axis) * h;
        const float *wc = n->w1_pos + (size_t)(4 + 4 * k + axis) * h;
        for (o = 0; o < h; o++)
            out[o] += sv * ws[o] + cv * wc[o];
    }
}

HOT static void dense(const float *restrict w, const float *restrict b, const float *restrict in,
                      float *restrict out, int h)
{
    int i, o;
    memcpy(out, b, (size_t)h * sizeof *out);
    for (i = 0; i < h; i++) {
        float a = in[i];
        if (a != 0.0f) {
            const float *restrict row = w + (size_t)i * h;
            for (o = 0; o < h; o++)
                out[o] += a * row[o];
        }
    }
    for (o = 0; o < h; o++)
        if (!(out[o] > 0.0f))
            out[o] = 0.0f;
}

/* The field at one sample. scratch holds 3 h floats. */
HOT static float field(const struct net *n, const float *c, const float *xp, const float *yp,
                       float *scratch)
{
    int o, h = n->h;
    float *h1 = scratch, *h2 = scratch + h, *h3 = scratch + 2 * h, f;
    for (o = 0; o < h; o++) {
        float v = c[o] + xp[o] + yp[o];
        h1[o] = v > 0.0f ? v : 0.0f;
    }
    dense(n->w2, n->b2, h1, h2, h);
    dense(n->w3, n->b3, h2, h3, h);
    f = n->b4;
    for (o = 0; o < h; o++)
        f += n->w4[o] * h3[o];
    return f;
}

static int auto_samples(int cell_w)
{
    return cell_w < 24 ? 2 : 1;
}

struct warp_pair {
    double p, t;
};

static int cmp_edge(const void *a, const void *b)
{
    const struct one_edge *x = a, *y = b;
    if (x->pos < y->pos)
        return -1;
    if (x->pos > y->pos)
        return 1;
    return x->rising - y->rising;
}

static int cmp_pair(const void *a, const void *b)
{
    const struct warp_pair *x = a, *y = b;
    if (x->p < y->p)
        return -1;
    if (x->p > y->p)
        return 1;
    if (x->t < y->t)
        return -1;
    if (x->t > y->t)
        return 1;
    return 0;
}

/* Nearest whole pixel. A value on n + 0.5 moves toward centre. */
static double round_half(double v, double centre)
{
    double f = floor(v);
    if (v - f == 0.5)
        return v > centre ? f : f + 1.0;
    return floor(v + 0.5);
}

static double interp_knots(double u, const double *xp, const double *fp, int n)
{
    int i;
    if (n <= 1 || u <= xp[0])
        return fp[0];
    if (u >= xp[n - 1])
        return fp[n - 1];
    for (i = 1; i < n; i++) {
        if (u <= xp[i]) {
            double span = xp[i] - xp[i - 1];
            if (span == 0.0)
                return fp[i - 1];
            return fp[i - 1] + (u - xp[i - 1]) * (fp[i] - fp[i - 1]) / span;
        }
    }
    return fp[n - 1];
}

/* Knots for one axis, matching train/snap.py. orig is the original pixel
 * position and snapped is where it lands. Both run from 0 to extent. */
static int build_knots(const struct glyph_rec *rec, int k, int axis, double scale, double extent,
                       double **orig_out, double **snap_out, int *n_out)
{
    struct warp_pair *pairs = NULL, *kn;
    double *orig, *snapped;
    int total = 0, np = 0, nk, layer, i;

    for (layer = 0; layer < k; layer++)
        total += axis == 0 ? rec->layer[layer].nx : rec->layer[layer].ny;
    if (total) {
        pairs = malloc((size_t)total * sizeof *pairs);
        if (!pairs)
            return NEURONTE_ERR_NOMEM;
    }
    for (layer = 0; layer < k; layer++) {
        struct layer_edges *le = &rec->layer[layer];
        struct one_edge *src = axis == 0 ? le->x : le->y;
        struct one_edge *ed;
        int n = axis == 0 ? le->nx : le->ny;
        int e;
        if (!n)
            continue;
        ed = malloc((size_t)n * sizeof *ed);
        if (!ed) {
            free(pairs);
            return NEURONTE_ERR_NOMEM;
        }
        memcpy(ed, src, (size_t)n * sizeof *ed);
        qsort(ed, (size_t)n, sizeof *ed, cmp_edge);
        for (e = 0; e < n;) {
            double p = (double)ed[e].pos * scale;
            if (ed[e].rising && e + 1 < n && !ed[e + 1].rising) {
                double q = (double)ed[e + 1].pos * scale;
                double w = ceil(q - p - 0.5);
                double left;
                if (w < 1.0)
                    w = 1.0;
                left = round_half((p + q) / 2.0 - w / 2.0, extent / 2.0 - w / 2.0);
                pairs[np].p = p;
                pairs[np++].t = left;
                pairs[np].p = q;
                pairs[np++].t = left + w;
                e += 2;
            } else {
                pairs[np].p = p;
                pairs[np++].t = round_half(p, extent / 2.0);
                e++;
            }
        }
        free(ed);
    }
    if (np > 1)
        qsort(pairs, (size_t)np, sizeof *pairs, cmp_pair);
    kn = malloc((size_t)(np + 2) * sizeof *kn);
    if (!kn) {
        free(pairs);
        return NEURONTE_ERR_NOMEM;
    }
    kn[0].p = 0;
    kn[0].t = 0;
    nk = 1;
    for (i = 0; i < np; i++) {
        double p = pairs[i].p, t = pairs[i].t, lp = kn[nk - 1].p, lt = kn[nk - 1].t;
        if (p - lp < 0.5 || p >= extent)
            continue;
        if (t < lt + 1.0)
            t = lt + 1.0;
        if (t >= extent)
            break;
        kn[nk].p = p;
        kn[nk].t = t;
        nk++;
    }
    kn[nk].p = extent;
    kn[nk].t = extent;
    nk++;
    free(pairs);
    orig = malloc((size_t)nk * sizeof *orig);
    snapped = malloc((size_t)nk * sizeof *snapped);
    if (!orig || !snapped) {
        free(orig);
        free(snapped);
        free(kn);
        return NEURONTE_ERR_NOMEM;
    }
    for (i = 0; i < nk; i++) {
        orig[i] = kn[i].p;
        snapped[i] = kn[i].t;
    }
    free(kn);
    *orig_out = orig;
    *snap_out = snapped;
    *n_out = nk;
    return NEURONTE_OK;
}

static int axis_samples(const struct glyph_rec *rec, int k, int axis, int n_px, int ss, double scale,
                        double extent, double *out)
{
    double *orig = NULL, *snapped = NULL;
    int n = n_px * ss, nk = 0, i, rc = NEURONTE_OK;

    if (rec) {
        rc = build_knots(rec, k, axis, scale, extent, &orig, &snapped, &nk);
        if (rc != NEURONTE_OK)
            return rc;
    }
    for (i = 0; i < n; i++) {
        double u = ((double)i + 0.5) / (double)ss;
        out[i] = (rec ? interp_knots(u, snapped, orig, nk) : u) / scale;
    }
    free(orig);
    free(snapped);
    return NEURONTE_OK;
}

static const struct glyph_rec *find_rec(const struct colour *c, uint32_t s)
{
    int lo = 0, hi = c->nrecs;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (c->recs[mid].scalar < s)
            lo = mid + 1;
        else
            hi = mid;
    }
    if (lo < c->nrecs && c->recs[lo].scalar == s)
        return &c->recs[lo];
    return NULL;
}

/* Snapping is on only for a colour glyph that has an edge record, and only
 * when the cell is narrower than the threshold. */
static int snap_on(const neuronte *hd, const struct net *net, uint32_t s, int cell_w)
{
    return net->col && hd->snap_below > 0 && cell_w < hd->snap_below && find_rec(net->col, s) != NULL;
}

static void colour_hidden(const struct net *n, const float *c, const float *xp, const float *yp,
                          float *scratch)
{
    int o, h = n->h;
    float *h1 = scratch, *h2 = scratch + h, *h3 = scratch + 2 * h;
    for (o = 0; o < h; o++) {
        float v = c[o] + xp[o] + yp[o];
        h1[o] = v > 0.0f ? v : 0.0f;
    }
    dense(n->w2, n->b2, h1, h2, h);
    dense(n->w3, n->b3, h2, h3, h);
}

static void palette_index(const struct net *n, uint32_t s, uint8_t *entries)
{
    const struct colour *c = n->col;
    float code[CODE], hid[MAX_R];
    int r = c->r, k = c->k, i, o, layer;

    code_of(s, n->masks, code);
    memcpy(hid, c->hb1, (size_t)r * sizeof *hid);
    for (i = 0; i < CODE; i++)
        for (o = 0; o < r; o++)
            hid[o] += code[i] * c->hw1[(size_t)o * CODE + i];
    for (o = 0; o < r; o++)
        if (!(hid[o] > 0.0f))
            hid[o] = 0.0f;
    for (layer = 0; layer < k; layer++) {
        int bits = 0, b;
        for (b = 0; b < 5; b++) {
            int row = layer * 5 + b;
            float z = c->hb2[row];
            for (o = 0; o < r; o++)
                z += c->hw2[(size_t)row * r + o] * hid[o];
            if (z > 0.0f)
                bits |= 1 << b;
        }
        entries[layer] = (uint8_t)bits;
    }
}

/* K coverage masks and K palette indices. masks has room for K planes of
 * cell_h * cell_w, and the caller has zeroed any planes past K. */
static int eval_colour(const neuronte *hd, const struct net *net, uint32_t scalar, int cell_w, int cell_h,
                       int ss, float *masks, uint8_t *entries)
{
    const struct colour *col = net->col;
    const struct glyph_rec *rec;
    double *pos;
    float *mem, *part, *scratch, *xp, *yp, slope;
    int k = col->k, h = net->h, sw = cell_w * ss, sh = cell_h * ss;
    int i, j, px, py, layer, rc;
    size_t plane = (size_t)cell_w * cell_h;

    rec = snap_on(hd, net, scalar, cell_w) ? find_rec(col, scalar) : NULL;
    pos = malloc(((size_t)sw + (size_t)sh) * sizeof *pos);
    mem = malloc(((size_t)sw + (size_t)sh + 4) * (size_t)h * sizeof *mem);
    if (!pos || !mem) {
        free(pos);
        free(mem);
        return NEURONTE_ERR_NOMEM;
    }
    rc = axis_samples(rec, k, 0, cell_w, ss, cell_w, cell_w, pos);
    if (rc == NEURONTE_OK)
        rc = axis_samples(rec, k, 1, cell_h, ss, (double)cell_h / 2.0, cell_h, pos + sw);
    if (rc != NEURONTE_OK) {
        free(pos);
        free(mem);
        return rc;
    }
    part = mem;
    scratch = part + h;
    xp = scratch + 3 * h;
    yp = xp + (size_t)sw * h;
    char_part(net, scalar, part);
    for (i = 0; i < sw; i++)
        axis_part(net, 0, pos[i], xp + (size_t)i * h);
    for (j = 0; j < sh; j++)
        axis_part(net, 1, pos[sw + j], yp + (size_t)j * h);
    palette_index(net, scalar, entries);
    slope = net->tau * (float)cell_w * (float)ss;
    for (py = 0; py < cell_h; py++)
        for (px = 0; px < cell_w; px++) {
            float acc[MAX_K];
            memset(acc, 0, sizeof acc);
            for (j = 0; j < ss; j++)
                for (i = 0; i < ss; i++) {
                    const float *h3;
                    colour_hidden(net, part, xp + (size_t)(px * ss + i) * h,
                                  yp + (size_t)(py * ss + j) * h, scratch);
                    h3 = scratch + 2 * h;
                    for (layer = 0; layer < k; layer++) {
                        const float *w = col->w_out + (size_t)layer * h;
                        float f = col->b_out[layer], v;
                        int o;
                        for (o = 0; o < h; o++)
                            f += w[o] * h3[o];
                        v = 0.5f + slope * f;
                        acc[layer] += v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
                    }
                }
            for (layer = 0; layer < k; layer++)
                masks[(size_t)layer * plane + (size_t)py * cell_w + px] = acc[layer] / (float)(ss * ss);
        }
    free(pos);
    free(mem);
    return NEURONTE_OK;
}

static float cover_alpha(const float *masks, const uint8_t *ent, int k, size_t plane, size_t px)
{
    float a = 0.0f;
    int layer;
    for (layer = 0; layer < k; layer++) {
        float c = masks[(size_t)layer * plane + px];
        if (ent[layer] == 1)
            a *= 1.0f - c;
        else
            a = c + a * (1.0f - c);
    }
    return a;
}

int neuronte_route(const neuronte *n, uint32_t scalar)
{
    return n && n->nets ? route(n, normalize(scalar)) : NEURONTE_ERR_ARG;
}

int neuronte_route_half(const neuronte *n, uint32_t scalar, int half)
{
    uint32_t code;
    if (!n || !n->nets || half_code(scalar, half, &code) != NEURONTE_OK)
        return NEURONTE_ERR_ARG;
    return route(n, code);
}

static int coverage_code(const neuronte *hd, uint32_t scalar, int cell_w, int cell_h,
                          int samples_per_axis, float *coverage)
{
    const struct net *n;
    float *mem, *c, *scratch, *xp, *yp, slope;
    int ss = samples_per_axis, sw, sh, i, j, px, py;
    size_t h;

    if (!hd || !hd->nets || !coverage || cell_w <= 0 || cell_h <= 0 || cell_w > NEURONTE_MAX_CELL ||
        cell_h > NEURONTE_MAX_CELL || ss < 0 || ss > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    if (ss == 0)
        ss = auto_samples(cell_w);
    n = hd->net[route(hd, scalar)];
    if (n->col) {
        size_t plane = (size_t)cell_w * cell_h;
        int k = n->col->k, rc;
        float *masks = calloc(plane * (size_t)k, sizeof *masks);
        uint8_t ent[MAX_K];
        size_t px;
        if (!masks)
            return NEURONTE_ERR_NOMEM;
        rc = eval_colour(hd, n, scalar, cell_w, cell_h, ss, masks, ent);
        if (rc == NEURONTE_OK)
            for (px = 0; px < plane; px++)
                coverage[px] = cover_alpha(masks, ent, k, plane, px);
        free(masks);
        return rc;
    }
    sw = cell_w * ss;
    sh = cell_h * ss;
    h = (size_t)n->h;
    mem = malloc(((size_t)sw + (size_t)sh + 4) * h * sizeof *mem);
    if (!mem)
        return NEURONTE_ERR_NOMEM;
    c = mem;
    scratch = c + h;
    xp = scratch + 3 * h;
    yp = xp + (size_t)sw * h;
    char_part(n, scalar, c);
    for (i = 0; i < sw; i++)
        axis_part(n, 0, (i + 0.5) / sw, xp + (size_t)i * h);
    for (j = 0; j < sh; j++)
        axis_part(n, 1, (j + 0.5) / sh * 2.0, yp + (size_t)j * h);
    slope = n->tau * (float)cell_w * (float)ss;
    for (py = 0; py < cell_h; py++)
        for (px = 0; px < cell_w; px++) {
            float acc = 0.0f;
            for (j = 0; j < ss; j++)
                for (i = 0; i < ss; i++) {
                    float v = 0.5f + slope * field(n, c, xp + (size_t)(px * ss + i) * h,
                                                   yp + (size_t)(py * ss + j) * h, scratch);
                    acc += v < 0.0f ? 0.0f : v > 1.0f ? 1.0f : v;
                }
            coverage[(size_t)py * cell_w + px] = acc / (float)(ss * ss);
        }
    free(mem);
    return NEURONTE_OK;
}

int neuronte_coverage(const neuronte *hd, uint32_t scalar, int cell_w, int cell_h,
                      int samples_per_axis, float *coverage)
{
    return coverage_code(hd, normalize(scalar), cell_w, cell_h, samples_per_axis, coverage);
}

int neuronte_coverage_half(const neuronte *hd, uint32_t scalar, int half, int cell_w, int cell_h,
                           int samples_per_axis, float *coverage)
{
    uint32_t code;
    if (half_code(scalar, half, &code) != NEURONTE_OK)
        return NEURONTE_ERR_ARG;
    return coverage_code(hd, code, cell_w, cell_h, samples_per_axis, coverage);
}

static int coverage_layers_code(const neuronte *hd, uint32_t scalar, int cell_w, int cell_h,
                                 int samples_per_axis, float *masks, uint8_t *entries)
{
    const struct net *n;
    int ss = samples_per_axis, layers, rc;
    size_t plane;

    if (!hd || !hd->nets || !masks || !entries || cell_w <= 0 || cell_h <= 0 ||
        cell_w > NEURONTE_MAX_CELL || cell_h > NEURONTE_MAX_CELL || ss < 0 || ss > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    if (ss == 0)
        ss = auto_samples(cell_w);
    n = hd->net[route(hd, scalar)];
    layers = hd->layers;
    plane = (size_t)cell_w * cell_h;
    memset(entries, 0, (size_t)layers);
    memset(masks, 0, plane * (size_t)layers * sizeof *masks);
    if (!n->col)
        return coverage_code(hd, scalar, cell_w, cell_h, ss, masks);
    rc = eval_colour(hd, n, scalar, cell_w, cell_h, ss, masks, entries);
    return rc;
}

int neuronte_coverage_layers(const neuronte *hd, uint32_t scalar, int cell_w, int cell_h,
                             int samples_per_axis, float *masks, uint8_t *entries)
{
    return coverage_layers_code(hd, normalize(scalar), cell_w, cell_h, samples_per_axis, masks, entries);
}

int neuronte_coverage_layers_half(const neuronte *hd, uint32_t scalar, int half, int cell_w, int cell_h,
                                  int samples_per_axis, float *masks, uint8_t *entries)
{
    uint32_t code;
    if (half_code(scalar, half, &code) != NEURONTE_OK)
        return NEURONTE_ERR_ARG;
    return coverage_layers_code(hd, code, cell_w, cell_h, samples_per_axis, masks, entries);
}

static const struct entry *cached(neuronte *n, uint32_t s, int w, int h, int ss, int *rc)
{
    const struct net *net = n->net[route(n, s)];
    int snap = snap_on(n, net, s, w);
    uint32_t key = s * 2654435761u ^ (uint32_t)w * 40503u ^ (uint32_t)h * 9973u ^ (uint32_t)ss;
    struct entry *set, *e;
    float *cov;
    uint8_t *ent;
    int i;

    if (snap)
        key ^= 0x9E3779B9u;
    set = n->cache[(key >> 8) % SETS];
    e = set;
    for (i = 0; i < WAYS; i++) {
        struct entry *c = &set[i];
        if (c->cov && c->scalar == s && c->w == w && c->h == h && c->ss == ss && c->snap == snap) {
            c->used = ++n->tick;
            return c;
        }
        if (!c->cov || (e->cov && c->used < e->used))
            e = c; /* an empty way, else the least recently used */
    }
    cov = calloc((size_t)n->layers * (size_t)w * (size_t)h, sizeof *cov);
    ent = calloc((size_t)n->layers, 1);
    if (!cov || !ent) {
        free(cov);
        free(ent);
        *rc = NEURONTE_ERR_NOMEM;
        return NULL;
    }
    if (!net->col)
        *rc = coverage_code(n, s, w, h, ss, cov);
    else
        *rc = eval_colour(n, net, s, w, h, ss, cov, ent);
    if (*rc != NEURONTE_OK) {
        free(cov);
        free(ent);
        return NULL;
    }
    free(e->cov);
    free(e->ent);
    e->cov = cov;
    e->ent = ent;
    e->scalar = s;
    e->w = w;
    e->h = h;
    e->ss = ss;
    e->snap = snap;
    e->used = ++n->tick;
    return e;
}

static int byte_chan(float v)
{
    if (!(v > 0.0f))
        return 0;
    if (v >= 255.0f)
        return 255;
    return (int)(v + 0.5f);
}

/* Premultiplied composite, back to front, then scaled by the call's alpha. */
static void over_pixel(const float *masks, const uint8_t *ent, int k, size_t plane, size_t px,
                       const uint8_t *pal, uint32_t color, float *or, float *og, float *ob, float *oa)
{
    float r = 0.0f, g = 0.0f, b = 0.0f, a = 0.0f;
    float cr = (float)((color >> 16) & 255), cg = (float)((color >> 8) & 255), cb = (float)(color & 255);
    float ca = (float)(color >> 24) / 255.0f;
    int layer;

    for (layer = 0; layer < k; layer++) {
        float c = masks[(size_t)layer * plane + px];
        float keep = 1.0f - c;
        int entry = ent[layer];
        if (entry == 1) {
            r *= keep;
            g *= keep;
            b *= keep;
            a *= keep;
        } else {
            float ir, ig, ib;
            if (entry >= 2 && entry <= 31) {
                ir = pal[entry * 3];
                ig = pal[entry * 3 + 1];
                ib = pal[entry * 3 + 2];
            } else {
                ir = cr;
                ig = cg;
                ib = cb;
            }
            r = ir * c + r * keep;
            g = ig * c + g * keep;
            b = ib * c + b * keep;
            a = c + a * keep;
        }
    }
    *or = r * ca;
    *og = g * ca;
    *ob = b * ca;
    *oa = a * ca;
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

/* Rightward dilation of a row, including every offset so thick weights have
 * no holes. Both ends can lie outside the original row. */
static float stroked(const float *row, int width, int x, int stroke)
{
    int lo = x > stroke ? x - stroke : 0;
    int hi = x < width ? x : width - 1;
    float c = 0.0f;
    int i;
    for (i = lo; i <= hi; i++)
        if (row[i] > c)
            c = row[i];
    return c;
}

static int italic_shift(int row, int w, int h)
{
    /* Exact rational form of (0.675 - (row + 0.5) / h) * w / 2.
     * Avoid a float-dependent rounding decision at half-pixel ties. */
    int64_t num = (27LL * h - 40LL * row - 20) * w;
    int64_t den = 80LL * h;
    return num >= 0 ? (int)((num + den / 2) / den) : -(int)((-num + den / 2) / den);
}

int neuronte_coverage_styled(const neuronte *n, uint32_t scalar, int cell_w, int cell_h,
                             int samples_per_axis, unsigned style, float *coverage)
{
    float *base;
    int x, y, stroke, rc;
    if (style & ~(NEURONTE_STYLE_BOLD | NEURONTE_STYLE_ITALIC))
        return NEURONTE_ERR_ARG;
    if (!n || !n->nets || !coverage || cell_w <= 0 || cell_h <= 0 ||
        cell_w > NEURONTE_MAX_CELL || cell_h > NEURONTE_MAX_CELL ||
        samples_per_axis < 0 || samples_per_axis > NEURONTE_MAX_SAMPLES)
        return NEURONTE_ERR_ARG;
    scalar = normalize(scalar);
    if (!style || n->net[route(n, scalar)]->col)
        return coverage_code(n, scalar, cell_w, cell_h, samples_per_axis, coverage);
    base = malloc((size_t)cell_w * cell_h * sizeof *base);
    if (!base)
        return NEURONTE_ERR_NOMEM;
    rc = coverage_code(n, scalar, cell_w, cell_h, samples_per_axis, base);
    if (rc == NEURONTE_OK) {
        stroke = style & NEURONTE_STYLE_BOLD ? (cell_w + 16) / 32 : 0;
        if ((style & NEURONTE_STYLE_BOLD) && stroke == 0)
            stroke = 1;
        for (y = 0; y < cell_h; y++) {
            int shift = style & NEURONTE_STYLE_ITALIC ? italic_shift(y, cell_w, cell_h) : 0;
            for (x = 0; x < cell_w; x++)
                coverage[(size_t)y * cell_w + x] = stroked(base + (size_t)y * cell_w,
                                                          cell_w, x - shift, stroke);
        }
    }
    free(base);
    return rc;
}

static int draw_code(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                      int x, int y, int cell_w, int cell_h, uint32_t scalar,
                      uint32_t color, unsigned style)
{
    const struct entry *cell;
    const struct net *net;
    float alpha = (float)(color >> 24) / 255.0f;
    int rc = NEURONTE_OK, ss, px, py;

    if (!n || !n->nets || !pixels || width < 0 || height < 0 || stride < width || cell_w <= 0 ||
        cell_h <= 0 || cell_w > NEURONTE_MAX_CELL || cell_h > NEURONTE_MAX_CELL ||
        (style & ~(NEURONTE_STYLE_BOLD | NEURONTE_STYLE_ITALIC)))
        return NEURONTE_ERR_ARG;
    /* A cell may start at INT_MAX. The sums are wider than int so a clipped
     * edge is skipped instead of overflowing. */
    if (alpha <= 0.0f || (int64_t)x >= width || (int64_t)y >= height ||
        (int64_t)x + cell_w <= 0 || (int64_t)y + cell_h <= 0)
        return NEURONTE_OK;
    ss = n->samples ? n->samples : auto_samples(cell_w);
    cell = cached(n, scalar, cell_w, cell_h, ss, &rc);
    if (!cell)
        return rc;
    net = n->net[route(n, scalar)];
    if (!net->col) {
        int stroke = style & NEURONTE_STYLE_BOLD ? (cell_w + 16) / 32 : 0;
        if ((style & NEURONTE_STYLE_BOLD) && stroke == 0)
            stroke = 1;
        for (py = y < 0 ? (int)(-(int64_t)y) : 0; py < cell_h && (int64_t)y + py < height; py++) {
            const float *row = cell->cov + (size_t)py * cell_w;
            int shift = style & NEURONTE_STYLE_ITALIC ? italic_shift(py, cell_w, cell_h) : 0;
            for (px = x < 0 ? (int)(-(int64_t)x) : 0; px < cell_w && (int64_t)x + px < width; px++) {
                float c = stroked(row, cell_w, px - shift, stroke), a;
                if (n->binary)
                    c = c > 0.5f ? 1.0f : 0.0f;
                a = c * alpha;
                if (a > 0.0f) {
                    uint32_t *d = pixels + (size_t)((int64_t)y + py) * (size_t)stride +
                                  (size_t)((int64_t)x + px);
                    *d = blend(*d, color, a);
                }
            }
        }
        return NEURONTE_OK;
    }
    {
        const uint8_t *pal = n->theme ? n->light : n->dark;
        int k = net->col->k;
        size_t plane = (size_t)cell_w * cell_h;
        for (py = y < 0 ? (int)(-(int64_t)y) : 0; py < cell_h && (int64_t)y + py < height; py++)
            for (px = x < 0 ? (int)(-(int64_t)x) : 0; px < cell_w && (int64_t)x + px < width; px++) {
                float pr, pg, pb, pa;
                over_pixel(cell->cov, cell->ent, k, plane, (size_t)py * cell_w + px, pal, color, &pr, &pg,
                           &pb, &pa);
                if (pa > 0.0f) {
                    uint32_t src = (uint32_t)byte_chan(pr / pa) << 16 | (uint32_t)byte_chan(pg / pa) << 8 |
                                   (uint32_t)byte_chan(pb / pa);
                    uint32_t *d = pixels + (size_t)((int64_t)y + py) * (size_t)stride +
                                  (size_t)((int64_t)x + px);
                    *d = blend(*d, src, pa);
                }
            }
    }
    return NEURONTE_OK;
}

int neuronte_draw_scalar_styled(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                                int x, int y, int cell_w, int cell_h, uint32_t scalar,
                                uint32_t color, unsigned style)
{
    return draw_code(n, pixels, stride, width, height, x, y, cell_w, cell_h,
                     normalize(scalar), color, style);
}

int neuronte_draw_half(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int cell_w, int cell_h, uint32_t scalar, int half,
                       uint32_t color)
{
    uint32_t code;
    if (half_code(scalar, half, &code) != NEURONTE_OK)
        return NEURONTE_ERR_ARG;
    return draw_code(n, pixels, stride, width, height, x, y, cell_w, cell_h, code, color, 0);
}

int neuronte_draw_scalar(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                         int x, int y, int cell_w, int cell_h, uint32_t scalar, uint32_t color)
{
    return neuronte_draw_scalar_styled(n, pixels, stride, width, height, x, y, cell_w, cell_h,
                                       scalar, color, 0);
}

int neuronte_draw_utf8(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int cell_w, int cell_h, const char *text, size_t len,
                       uint32_t color)
{
    size_t off = 0;
    int cells = 0;
    int64_t pen = x;

    if (!text && len)
        return NEURONTE_ERR_ARG;
    while (off < len) {
        uint32_t s;
        int rc;
        off += neuronte_utf8_decode(text + off, len - off, &s);
        /* A pen past INT_MAX is off any buffer this call can name. */
        if (pen <= INT_MAX) {
            rc = neuronte_draw_scalar(n, pixels, stride, width, height, (int)pen, y, cell_w, cell_h, s,
                                      color);
            if (rc != NEURONTE_OK)
                return rc;
        }
        if (cell_w > 0 && pen > INT64_MAX - cell_w)
            pen = INT64_MAX;
        else
            pen += cell_w;
        cells++;
    }
    return cells;
}

/* The record that measures the scalar: its own, or the fallback's. */
static const struct advance *advance_of(const neuronte *n, uint32_t scalar)
{
    size_t lo = 0, hi = n->nadv;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (n->adv[mid].scalar < scalar)
            lo = mid + 1;
        else
            hi = mid;
    }
    return lo < n->nadv && n->adv[lo].scalar == scalar ? &n->adv[lo] : &n->adv[n->adv_fallback];
}

int neuronte_advances(const neuronte *n)
{
    return n && n->adv ? (int)n->nadv : 0;
}

uint32_t neuronte_advance_scalar(const neuronte *n, uint32_t scalar)
{
    return n && n->adv ? advance_of(n, scalar)->scalar : NEURONTE_REPLACEMENT;
}

int neuronte_advance_steps(const neuronte *n, uint32_t scalar, int bold)
{
    if (!n || !n->adv || bold < 0 || bold > 1)
        return NEURONTE_ERR_ARG;
    return advance_of(n, scalar)->steps[bold];
}

int neuronte_advance(const neuronte *n, uint32_t scalar, int bold, int em_px)
{
    int steps = neuronte_advance_steps(n, scalar, bold);
    if (steps < 0 || em_px <= 0 || em_px > NEURONTE_MAX_CELL)
        return NEURONTE_ERR_ARG;
    return (steps * em_px + 50) / 100; /* to the nearest pixel, a tie going up */
}

int neuronte_text_width(const neuronte *n, const char *text, size_t len, int bold, int em_px)
{
    size_t off = 0;
    int total = 0;

    if (!text && len)
        return NEURONTE_ERR_ARG;
    if (neuronte_advance(n, 0x20, bold, em_px) < 0)
        return NEURONTE_ERR_ARG;
    while (off < len) {
        uint32_t s;
        int px;
        off += neuronte_utf8_decode(text + off, len - off, &s);
        px = neuronte_advance(n, s, bold, em_px);
        if (px > INT_MAX - total)
            return NEURONTE_ERR_ARG;
        total += px;
    }
    return total;
}

int neuronte_text_width_stroke(const neuronte *n, const char *text, size_t len,
                               int stroke_px, int em_px)
{
    size_t off = 0;
    int total = neuronte_text_width(n, text, len, 0, em_px);
    if (total < 0 || stroke_px < 0 || stroke_px > em_px)
        return NEURONTE_ERR_ARG;
    while (off < len) {
        uint32_t s;
        off += neuronte_utf8_decode(text + off, len - off, &s);
        if (stroke_px > INT_MAX - total)
            return NEURONTE_ERR_ARG;
        total += stroke_px;
    }
    return total;
}

/* stroke_px == -1 is the unchanged packed-bold advance policy. */
static int draw_text(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                     int x, int y, int em_px, int bold, int stroke_px, const char *text, size_t len,
                     uint32_t color)
{
    float alpha = (float)(color >> 24) / 255.0f;
    int cw, ch, total, ss, px, py, stroke;
    int64_t pen;
    size_t off = 0;

    /* Check em before doubling it. Past INT_MAX / 2 the height overflows. */
    if (!n || !n->nets || !pixels || width < 0 || height < 0 || stride < width || em_px <= 0 ||
        em_px > NEURONTE_MAX_CELL / 2 || stroke_px < -1 || stroke_px > em_px)
        return NEURONTE_ERR_ARG;
    cw = em_px;
    ch = em_px * 2;
    total = stroke_px < 0 ? neuronte_text_width(n, text, len, bold, em_px) :
                           neuronte_text_width_stroke(n, text, len, stroke_px, em_px);
    if (total < 0 || alpha <= 0.0f)
        return total;
    stroke = stroke_px < 0 ? bold : stroke_px;
    ss = n->samples ? n->samples : auto_samples(cw);
    pen = x;
    while (off < len) {
        const struct advance *a;
        const struct entry *cell;
        const float *cov;
        uint32_t s;
        int rc = NEURONTE_OK;
        int ix;
        int64_t adv;

        off += neuronte_utf8_decode(text + off, len - off, &s);
        a = advance_of(n, s);
        /* Room for every offset of the rightward stroke.
         * The pen is wider than int: a clipped character may start at
         * INT_MAX, and its advance still has to be added. */
        ix = pen > INT_MAX ? INT_MAX : (int)pen;
        if (pen <= INT_MAX && (int64_t)ix < width && (int64_t)y < height &&
            pen + (int64_t)cw + stroke > 0 && (int64_t)y + ch > 0) {
            cell = cached(n, a->scalar, cw, ch, ss, &rc);
            if (!cell)
                return rc;
            if (n->net[route(n, a->scalar)]->col)
                return NEURONTE_ERR_ARG;
            cov = cell->cov;
            for (py = y < 0 ? (int)(-(int64_t)y) : 0; py < ch && (int64_t)y + py < height; py++)
                for (px = ix < 0 ? (int)(-(int64_t)ix) : 0; px < cw + stroke && (int64_t)ix + px < width; px++) {
                    const float *row = cov + (size_t)py * cw;
                    float c = stroked(row, cw, px, stroke);
                    if (n->binary)
                        c = c > 0.5f ? 1.0f : 0.0f;
                    if (c * alpha > 0.0f) {
                        uint32_t *d = pixels + (size_t)((int64_t)y + py) * (size_t)stride +
                                      (size_t)((int64_t)ix + px);
                        *d = blend(*d, color, c * alpha);
                    }
                }
        }
        adv = stroke_px < 0 ? ((int64_t)a->steps[bold] * em_px + 50) / 100 :
                             ((int64_t)a->steps[0] * em_px + 50) / 100 + stroke_px;
        if (adv > 0 && pen > INT64_MAX - adv)
            pen = INT64_MAX;
        else
            pen += adv;
    }
    return total;
}

int neuronte_draw_text(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int em_px, int bold, const char *text, size_t len,
                       uint32_t color)
{
    return draw_text(n, pixels, stride, width, height, x, y, em_px, bold, -1, text, len, color);
}

int neuronte_draw_text_stroke(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                              int x, int y, int em_px, int stroke_px, const char *text, size_t len,
                              uint32_t color)
{
    if (stroke_px < 0)
        return NEURONTE_ERR_ARG;
    return draw_text(n, pixels, stride, width, height, x, y, em_px, 0, stroke_px, text, len, color);
}
