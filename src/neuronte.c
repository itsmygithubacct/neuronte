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
 * A weights file holds one net (version 1) or a bundle of several
 * (version 2) with a router: a table of scalar ranges, each drawn by one
 * net, and for scalars outside the table either a gate, a small net over
 * the same 64 code features that picks a net, or a fallback net. The
 * handle is the same either way; one net is a bundle of one.
 *
 * An advance table (version 4) is the pen step of each character of a
 * proportional face, regular and bold, in steps of a hundredth of an em.
 * A drawing file (version 5) is a directory of whole images: nets, at
 * most one advance table, and colour nets (version 3), which this
 * library does not read yet and leaves out.
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
#define MAX_H 1024 /* hidden widths are multiples of 8 up to this */
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
    unsigned long used;
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
    float mem[]; /* the arrays above point into this */
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
    int binary; /* the draw calls cut coverage at one half */
    unsigned long tick;
    struct entry cache[SETS][WAYS];
};

/* Weights and biases in a net of hidden width h. */
static size_t params(size_t h)
{
    return h * IN + h + 2 * (h * h + h) + h + 1;
}

/* The length of a one-net file of hidden width h, or 0 if no such width. */
static size_t file_len(uint32_t h)
{
    return h >= 8 && h <= MAX_H && h % 8 == 0 ? HEADER + 4 * params(h) : 0;
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
        if (len < HEADER || len > file_len(MAX_H))
            return 0;
        total += len;
    }
    return total;
}

static void free_handle(neuronte *n)
{
    int i, j;
    for (i = 0; i < n->nets; i++)
        free(n->net[i]);
    for (i = 0; i < SETS; i++)
        for (j = 0; j < WAYS; j++)
            free(n->cache[i][j].cov);
    free(n->ranges);
    free(n->gate);
    free(n->adv);
    free(n);
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
        if (r->first > r->last || r->last > 0x10FFFF || r->net >= k ||
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
        rc = net_open(p + off, nl, &n->net[i]);
        if (rc != NEURONTE_OK)
            return rc;
        n->nets++;
        off += nl;
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
        if (off != total || len < MIN_IMAGE || len > file_len(MAX_H))
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
        case 3: /* a colour net: not read by this library, and not drawn */
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
    uint32_t version;
    int rc;

    if (!out)
        return NEURONTE_ERR_ARG;
    *out = NULL;
    if (!data)
        return NEURONTE_ERR_ARG;
    if (len < MIN_IMAGE || memcmp(p, "NEURONTE", 8) != 0)
        return NEURONTE_ERR_FORMAT;
    version = rd32(p + 8);
    if (version != 1 && version != 2 && version != 4 && version != 5)
        return NEURONTE_ERR_FORMAT;
    n = calloc(1, sizeof *n);
    if (!n)
        return NEURONTE_ERR_NOMEM;
    if (version == 1) {
        rc = net_open(p, len, &n->net[0]);
        n->nets = rc == NEURONTE_OK;
    } else if (version == 2) {
        rc = bundle_open(p, len, n);
    } else if (version == 4) {
        rc = adv_open(p, len, n);
    } else {
        rc = drawing_open(p, len, n);
    }
    if (rc != NEURONTE_OK) {
        free_handle(n);
        return rc;
    }
    *out = n;
    return NEURONTE_OK;
}

/* Read exactly the bytes the file's header says it has, and one more,
 * which shows a file too long; never more than that. */
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
    for (i = 0; i < n->nets; i++)
        total += params((size_t)n->net[i]->h);
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

int neuronte_route(const neuronte *n, uint32_t scalar)
{
    return n && n->nets ? route(n, normalize(scalar)) : NEURONTE_ERR_ARG;
}

int neuronte_coverage(const neuronte *hd, uint32_t scalar, int cell_w, int cell_h,
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
    scalar = normalize(scalar);
    n = hd->net[route(hd, scalar)];
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

static const float *cached(neuronte *n, uint32_t s, int w, int h, int ss, int *rc)
{
    uint32_t k = s * 2654435761u ^ (uint32_t)w * 40503u ^ (uint32_t)h * 9973u ^ (uint32_t)ss;
    struct entry *set = n->cache[(k >> 8) % SETS], *e = set;
    float *cov;
    int i;

    for (i = 0; i < WAYS; i++) {
        struct entry *c = &set[i];
        if (c->cov && c->scalar == s && c->w == w && c->h == h && c->ss == ss) {
            c->used = ++n->tick;
            return c->cov;
        }
        if (!c->cov || (e->cov && c->used < e->used))
            e = c; /* an empty way, else the least recently used */
    }
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
    e->used = ++n->tick;
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

    if (!n || !n->nets || !pixels || width < 0 || height < 0 || stride < width || cell_w <= 0 ||
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
            float c = cov[(size_t)py * cell_w + px], a;
            if (n->binary)
                c = c > 0.5f ? 1.0f : 0.0f;
            a = c * alpha;
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

int neuronte_draw_text(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int em_px, int bold, const char *text, size_t len,
                       uint32_t color)
{
    float alpha = (float)(color >> 24) / 255.0f;
    int cw = em_px, ch = 2 * em_px, total, ss, px, py;
    size_t off = 0;

    if (!n || !n->nets || !pixels || width < 0 || height < 0 || stride < width || em_px <= 0 ||
        em_px > NEURONTE_MAX_CELL / 2)
        return NEURONTE_ERR_ARG;
    total = neuronte_text_width(n, text, len, bold, em_px);
    if (total < 0 || alpha <= 0.0f)
        return total;
    ss = n->samples ? n->samples : auto_samples(cw);
    while (off < len) {
        const struct advance *a;
        const float *cov;
        uint32_t s;
        int rc = NEURONTE_OK;

        off += neuronte_utf8_decode(text + off, len - off, &s);
        a = advance_of(n, s);
        /* One column more for bold, whose second strike is a pixel right. */
        if (x < width && y < height && x + cw + bold > 0 && y + ch > 0) {
            cov = cached(n, a->scalar, cw, ch, ss, &rc);
            if (!cov)
                return rc;
            for (py = y < 0 ? -y : 0; py < ch && y + py < height; py++)
                for (px = x < 0 ? -x : 0; px < cw + bold && x + px < width; px++) {
                    const float *row = cov + (size_t)py * cw;
                    float c = px < cw ? row[px] : 0.0f;
                    if (bold && px > 0 && row[px - 1] > c)
                        c = row[px - 1];
                    if (n->binary)
                        c = c > 0.5f ? 1.0f : 0.0f;
                    if (c * alpha > 0.0f) {
                        uint32_t *d = pixels + (size_t)(y + py) * stride + (x + px);
                        *d = blend(*d, color, c * alpha);
                    }
                }
        }
        x += (a->steps[bold] * em_px + 50) / 100;
    }
    return total;
}
