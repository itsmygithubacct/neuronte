/* neuronte-showcase: everything Neuronte draws so far, on two pages,
 * shown in a Kilix terminal through kitty-framebuffer.
 *
 *   neuronte-showcase [WEIGHTS.nrt]
 *   neuronte-showcase --snapshot OUT.ppm [WIDTH HEIGHT] [WEIGHTS.nrt]
 *
 * Page 1 is the font: every class of character the bundle draws, each with
 * the net that draws it, and the mosaics up close. Page 2 is pictures: a
 * moving scene made by code, shown as it is and through octant cells three
 * ways, each with its time and its PSNR against the scene:
 *
 *   level 1, one octant and two colours per 8 x 16 cell, the exact best
 *   fit over all 256 octant patterns, which any terminal can show;
 *   level 2, eight colours per 8 x 16 cell, three octants used as bit
 *   planes, which needs a screen Neuronte draws;
 *   level 2 at 2 x 4 cells, where each sub-cell is one pixel.
 *
 * Every cell shape comes from the net's coverage. Tab changes page, Esc or
 * Ctrl-C quits. --snapshot writes page 1 to OUT.ppm and page 2 to the same
 * name with "-pictures" before the extension. MIT licence. */
#define _POSIX_C_SOURCE 200809L
#include "common.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- Characters ---- */

/* The 26 octant patterns Unicode encodes outside U+1CD00..U+1CDE5. Bit
 * n - 1 is cell n of the lattice 1 2 / 3 4 / 5 6 / 7 8. */
static const uint32_t elsewhere[26][2] = {
    {0, 0x20},      {255, 0x2588},   {15, 0x2580},    {240, 0x2584},   {85, 0x258C},
    {170, 0x2590},  {192, 0x2582},   {252, 0x2586},   {80, 0x2596},    {160, 0x2597},
    {5, 0x2598},    {245, 0x2599},   {165, 0x259A},   {95, 0x259B},    {175, 0x259C},
    {10, 0x259D},   {90, 0x259E},    {250, 0x259F},   {3, 0x1FB82},    {63, 0x1FB85},
    {20, 0x1FBE6},  {40, 0x1FBE7},   {128, 0x1CEA0},  {64, 0x1CEA3},   {1, 0x1CEA8},
    {2, 0x1CEAB}};

/* An octant's code point is its pattern's rank among the 230 patterns not
 * encoded elsewhere. */
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

#define MAX_CLASS 256
struct cls {
    const char *name;
    uint32_t s[MAX_CLASS];
    int count;
};

static void add_range(struct cls *c, uint32_t lo, uint32_t hi)
{
    for (; lo <= hi && c->count < MAX_CLASS; lo++)
        c->s[c->count++] = lo;
}

static void add_utf8(struct cls *c, const char *t)
{
    size_t off = 0, len = strlen(t);
    while (off < len && c->count < MAX_CLASS)
        off += neuronte_utf8_decode(t + off, len - off, &c->s[c->count++]);
}

/* The classes of neuronte-split-v4, as the training sets define them. */
static int classes(struct cls *c)
{
    static const uint32_t subs[] = {0x1FB82, 0x1FB85, 0x1FBE6, 0x1FBE7, 0x1CEA0, 0x1CEA3, 0x1CEA8, 0x1CEAB};
    size_t i;
    memset(c, 0, 9 * sizeof *c);
    c[0].name = "ASCII";
    add_range(&c[0], 0x20, 0x7E);
    c[1].name = "accented";
    add_range(&c[1], 0xC0, 0xD6);
    add_range(&c[1], 0xD8, 0x17F);
    add_utf8(&c[1], "¨¯´¸ˆˇ˘˙˚˛˜˝");
    c[2].name = "symbols";
    add_utf8(&c[2], "\xc2\xa0©°·½×–—‘’“”•…›※⁙←↑→↓↗⇣≈≡⋅⎿⏵▲▸▼▾◆◈◉●◐◑◯☐☒✔✢✳✶✻✽❯⸬");
    c[3].name = "box drawing";
    add_range(&c[3], 0x2500, 0x257F);
    c[4].name = "blocks, shades";
    add_range(&c[4], 0x2580, 0x259F);
    c[5].name = "Braille";
    add_range(&c[5], 0x2800, 0x28FF);
    c[6].name = "sextants";
    add_range(&c[6], 0x1FB00, 0x1FB3B);
    c[7].name = "octants";
    add_range(&c[7], 0x1CD00, 0x1CDE5);
    c[8].name = "substitutes";
    for (i = 0; i < sizeof subs / sizeof subs[0]; i++)
        c[8].s[c[8].count++] = subs[i];
    return 9;
}

/* Draw scalars in cells cw x 2cw from (x, y), wrapping at right. Returns
 * the y below the last row. */
static int scalars(neuronte *n, const struct screen *s, int x, int y, int right, int cw, const uint32_t *list,
                   int count, uint32_t color)
{
    int i, cx = x;
    for (i = 0; i < count; i++) {
        if (cx + cw > right) {
            cx = x;
            y += 2 * cw;
        }
        neuronte_draw_scalar(n, s->px, s->stride, s->w, s->h, cx, y, cw, 2 * cw, list[i], color);
        cx += cw;
    }
    return y + 2 * cw;
}

/* ---- Page 1: the font ---- */

static void draw_font_page(neuronte *n, const struct screen *s, int (*show)(const struct screen *))
{
    static struct cls c[9];
    int m = s->w >= 1000 ? 24 : 12, y = m, k, nc = classes(c), label_w, cw = 10, right = s->w - m;
    char buf[256], num[32];

    fill(s, 0, 0, s->w, s->h, BG);
    y = row(n, s, m, y, 16, "Neuronte: everything it draws so far", INK);
    thousands(neuronte_parameters(n), num);
    snprintf(buf, sizeof buf,
             "%d nets, %s weights. Every glyph on this screen, labels included, is computed by a net "
             "when it is first needed.",
             neuronte_nets(n), num);
    y = line(n, s, m, y + 6, 8, buf, DIM);
    y = line(n, s, m, y, 8, "Tab: pictures in octant cells   Esc: quit", DIM) + m / 2;
    if (show)
        show(s);

    label_w = 26 * 8;
    for (k = 0; k < nc; k++) {
        snprintf(buf, sizeof buf, "%s, %d", c[k].name, c[k].count);
        row(n, s, m, y + 2, 8, buf, DIM);
        snprintf(buf, sizeof buf, "net %d", neuronte_route(n, c[k].s[c[k].count - 1]));
        row(n, s, m + label_w - 7 * 8, y + 2, 8, buf, DIM);
        y = scalars(n, s, m + label_w, y, right, cw, c[k].s, c[k].count, k >= 6 ? ACCENT : INK) + 4;
        if (show)
            show(s);
    }

    /* Up close: the blocks, with the three-quadrant ones square, and an
     * area chart in octants, 2 x 4 sub-cells per cell, joined across cells. */
    fill(s, m, y + m / 4, s->w - m, y + m / 4 + 1, RULE);
    y += m / 2;
    {
        static const char close[] = "▖▗▘▝▚▞▙▛▜▟ ▀▄▌▐█ ░▒▓ ⣀⣤⣶⣿";
        int big = 24, top = y, x0 = m + label_w, cells, r, col, rows = 3;
        row(n, s, m, y + 2, 8, "up close, 24 px wide", DIM);
        text(n, s, x0, y, right, big, close, strlen(close), INK, NULL, NULL);
        y += 2 * big + m / 2;
        row(n, s, m, y + 2, 8, "an area chart in octants", DIM);
        row(n, s, m, y + 22, 8, "3 cells tall, 12 px wide", DIM);
        cells = (right - x0) / 12;
        for (col = 0; col < cells; col++)
            for (r = 0; r < rows; r++) {
                int bits = 0, half, k2;
                for (half = 0; half < 2; half++) {
                    int j = 2 * col + half;
                    double v = 6.0 + 4.5 * sin(j * 0.11) + 1.4 * sin(j * 0.47);
                    int h = (int)lround(v);
                    for (k2 = 0; k2 < 4; k2++) {
                        int g = (rows - 1 - r) * 4 + (3 - k2); /* sub-rows from the bottom */
                        if (g < h)
                            bits |= 1 << (2 * k2 + half);
                    }
                }
                neuronte_draw_scalar(n, s->px, s->stride, s->w, s->h, x0 + 12 * col, y + 24 * r, 12, 24,
                                     octant_char(bits), ACCENT);
            }
        (void)top;
        y += 24 * rows;
    }
    if (show)
        show(s);
}

/* ---- Page 2: pictures ---- */

struct pics {
    int pw, ph, x[4], y[4], label_h;
    uint32_t *srcpx; /* the scene, pw x ph */
    float *r, *g, *b;
    float *m1, s1[256], s2[256], det[256]; /* 256 octant masks at 8 x 16 */
    float *w8, *w2;                        /* the eight label weights at 8 x 16 and at 2 x 4 */
    double ms[4], psnr[4], frame_ms;
};

static float coverage_or_zero(neuronte *n, uint32_t s, int cw, int ch, float *out)
{
    if (neuronte_coverage(n, s, cw, ch, 0, out) != NEURONTE_OK)
        memset(out, 0, (size_t)cw * ch * sizeof *out);
    return 0;
}

/* The label weights of the eight-colour cell. Three octants are the bit
 * planes: U+2590 (the right column), the octant with cells 3 4 5 6 and
 * U+2584 (the lower half). Sub-cell (row r, column c) then has the label
 * c + 2 * gray(r), gray = 0 1 3 2, so neighbouring sub-cells differ in one
 * bit and an edge mixes only their two colours. */
static float *label_weights(neuronte *n, int cw, int ch)
{
    int P = cw * ch, i, L;
    float *a = malloc((size_t)P * 3 * sizeof *a), *w = malloc((size_t)P * 8 * sizeof *w);
    if (!a || !w) {
        free(a);
        free(w);
        return NULL;
    }
    coverage_or_zero(n, 0x2590, cw, ch, a);
    coverage_or_zero(n, octant_char(0x3C), cw, ch, a + P);
    coverage_or_zero(n, 0x2584, cw, ch, a + 2 * P);
    for (L = 0; L < 8; L++)
        for (i = 0; i < P; i++) {
            float v = 1;
            int bit;
            for (bit = 0; bit < 3; bit++) {
                float mk = a[bit * P + i];
                v *= (L >> bit & 1) ? mk : 1 - mk;
            }
            w[L * P + i] = v;
        }
    free(a);
    return w;
}

static int pics_init(neuronte *n, struct pics *p, const struct screen *s)
{
    int m = s->w >= 1000 ? 16 : 8, top = 72, k, i, P = 8 * 16, avail_h, avail_w;
    memset(p, 0, sizeof *p);
    p->label_h = 36;
    avail_w = (s->w - 3 * m) / 2;
    avail_h = (s->h - top - 2 * p->label_h - 3 * m) / 2;
    p->ph = avail_h / 16 * 16;
    p->pw = p->ph * 16 / 9;
    if (p->pw > avail_w)
        p->pw = avail_w;
    p->pw = p->pw / 8 * 8;
    if (p->pw < 64 || p->ph < 32)
        return -1;
    for (k = 0; k < 4; k++) {
        p->x[k] = m + (k % 2) * (p->pw + m);
        p->y[k] = top + p->label_h + (k / 2) * (p->ph + p->label_h + m);
    }
    p->srcpx = malloc((size_t)p->pw * p->ph * sizeof *p->srcpx);
    p->r = malloc((size_t)p->pw * p->ph * 3 * sizeof *p->r);
    p->m1 = malloc((size_t)256 * P * sizeof *p->m1);
    if (!p->srcpx || !p->r || !p->m1)
        return -1;
    p->g = p->r + p->pw * p->ph;
    p->b = p->g + p->pw * p->ph;
    for (k = 0; k < 256; k++) {
        float *mk = p->m1 + k * P;
        double s1 = 0, s2 = 0, det;
        coverage_or_zero(n, octant_char(k), 8, 16, mk);
        for (i = 0; i < P; i++) {
            s1 += mk[i];
            s2 += (double)mk[i] * mk[i];
        }
        det = P * s2 - s1 * s1;
        p->s1[k] = (float)s1;
        p->s2[k] = (float)s2;
        p->det[k] = det < 1e-3 * P * P ? 0 : (float)det; /* blank or full: one colour */
    }
    p->w8 = label_weights(n, 8, 16);
    p->w2 = label_weights(n, 2, 4);
    return p->w8 && p->w2 ? 0 : -1;
}

static void pics_free(struct pics *p)
{
    free(p->srcpx);
    free(p->r);
    free(p->m1);
    free(p->w8);
    free(p->w2);
    memset(p, 0, sizeof *p);
}

static uint32_t pack(float r, float g, float b)
{
    int R = (int)lrintf(fminf(fmaxf(r, 0), 1) * 255), G = (int)lrintf(fminf(fmaxf(g, 0), 1) * 255),
        B = (int)lrintf(fminf(fmaxf(b, 0), 1) * 255);
    return 0xFF000000u | (uint32_t)R << 16 | (uint32_t)G << 8 | (uint32_t)B;
}

static void hsv(float h, float s, float v, float *r, float *g, float *b)
{
    float f = (h - floorf(h)) * 6, p = v * (1 - s), q, t;
    int i = (int)f;
    f -= (float)i;
    q = v * (1 - s * f);
    t = v * (1 - s * (1 - f));
    switch (i % 6) {
    case 0: *r = v; *g = t; *b = p; break;
    case 1: *r = q; *g = v; *b = p; break;
    case 2: *r = p; *g = v; *b = t; break;
    case 3: *r = p; *g = q; *b = v; break;
    case 4: *r = t; *g = p; *b = v; break;
    default: *r = v; *g = p; *b = q; break;
    }
}

static float smooth(float edge, float d) /* 1 inside (d < edge), a pixel-wide ramp */
{
    float v = edge - d + 0.5f;
    return v < 0 ? 0 : v > 1 ? 1 : v;
}

/* The scene at time t: a hue gradient, a dark disc with a light ring that
 * circles, a turning yellow bar, bars one to four pixels thick, a scrolling
 * checkerboard of 3-pixel squares, and a word the net draws. */
static void scene(neuronte *n, struct pics *p, double t)
{
    int W = p->pw, H = p->ph, x, y;
    float cxd = (float)(W * (0.30 + 0.10 * cos(t))), cyd = (float)(H * (0.45 + 0.16 * sin(t))),
          rad = 0.17f * (float)H, ang = (float)(1.1 + 0.25 * sin(t * 0.7)), ca = cosf(ang), sa = sinf(ang),
          bx = (float)W * 0.62f, by = (float)H * 0.5f;
    int scroll = (int)(t * 12);
    struct screen v = {p->srcpx, W, H, W};

    for (y = 0; y < H; y++)
        for (x = 0; x < W; x++) {
            float u = (float)x / W, w = (float)y / H, r, g, b, d, k;
            hsv(u * 0.8f + w * 0.2f + 0.05f * (float)sin(t * 0.5), 0.6f, 0.95f - 0.45f * w, &r, &g, &b);
            /* the turning bar */
            d = fabsf((x - bx) * ca + (y - by) * sa);
            k = smooth(3.0f, d);
            r += (1.0f - r) * k, g += (0.82f - g) * k, b += (0.2f - b) * k;
            /* disc and ring */
            d = hypotf(x - cxd, y - cyd);
            k = smooth(rad + 4, d) * (1 - smooth(rad, d));
            r += (0.92f - r) * k, g += (0.95f - g) * k, b += (0.86f - b) * k;
            k = smooth(rad, d);
            r += (0.12f - r) * k, g += (0.16f - g) * k, b += (0.40f - b) * k;
            /* bars 1 to 4 px thick, top right */
            if (x > W * 0.70f && x < W * 0.95f && y > H * 0.08f && y < H * 0.30f) {
                int yy = y - (int)(H * 0.08f), band = 0, start = 0;
                for (band = 1; band <= 4; band++) {
                    if (yy >= start && yy < start + band) {
                        r = g = b = 0.08f;
                        break;
                    }
                    start += band + 5;
                }
            }
            /* scrolling checkerboard, bottom right */
            if (x > W * 0.70f && x < W * 0.95f && y > H * 0.62f && y < H * 0.92f) {
                int c = (((x + scroll) / 3) + (y / 3)) & 1;
                r = g = b = c ? 0.95f : 0.1f;
            }
            p->srcpx[(size_t)y * W + x] = pack(r, g, b);
        }
    /* A word drawn by the net into the picture. */
    {
        int cw = W / 14 < 8 ? 8 : W / 14;
        row(n, &v, W / 20, H - 2 * cw - H / 20, cw, "Neuronte", 0xFFFFFFFFu);
    }
    for (y = 0; y < H * W; y++) {
        uint32_t c = p->srcpx[y];
        p->r[y] = (float)(c >> 16 & 255) / 255.0f;
        p->g[y] = (float)(c >> 8 & 255) / 255.0f;
        p->b[y] = (float)(c & 255) / 255.0f;
    }
}

/* Level 1: for each 8 x 16 cell the octant pattern and two colours that
 * fit the cell best in least squares, over all 256 patterns, drawn with
 * the net's own mask for that pattern. */
static void level1(const struct pics *p, uint32_t *out)
{
    enum { CW = 8, CH = 16, P = CW * CH };
    int cx, cy, i, k, c, W = p->pw;
    float r[P], g[P], b[P];
    for (cy = 0; cy + CH <= p->ph; cy += CH)
        for (cx = 0; cx + CW <= p->pw; cx += CW) {
            float sc[3] = {0, 0, 0}, best = -1e30f, fg[3], bgc[3];
            const float *m;
            int bk = 0;
            for (i = 0; i < P; i++) {
                size_t at = (size_t)(cy + i / CW) * W + cx + i % CW;
                r[i] = p->r[at], g[i] = p->g[at], b[i] = p->b[at];
                sc[0] += r[i], sc[1] += g[i], sc[2] += b[i];
            }
            for (k = 0; k < 256; k++) {
                float mr = 0, mg = 0, mb = 0, score = 0, smc[3];
                m = p->m1 + k * P;
                if (p->det[k] == 0) {
                    score = (sc[0] * sc[0] + sc[1] * sc[1] + sc[2] * sc[2]) / P;
                } else {
                    for (i = 0; i < P; i++) {
                        mr += m[i] * r[i];
                        mg += m[i] * g[i];
                        mb += m[i] * b[i];
                    }
                    smc[0] = mr, smc[1] = mg, smc[2] = mb;
                    for (c = 0; c < 3; c++) {
                        float base = (p->s2[k] * sc[c] - p->s1[k] * smc[c]) / p->det[k];
                        float a = (P * smc[c] - p->s1[k] * sc[c]) / p->det[k];
                        score += base * sc[c] + a * smc[c];
                    }
                }
                if (score > best) {
                    best = score;
                    bk = k;
                }
            }
            m = p->m1 + bk * P;
            if (p->det[bk] == 0) {
                for (c = 0; c < 3; c++)
                    fg[c] = bgc[c] = sc[c] / P;
            } else {
                float smc[3] = {0, 0, 0};
                for (i = 0; i < P; i++) {
                    smc[0] += m[i] * r[i];
                    smc[1] += m[i] * g[i];
                    smc[2] += m[i] * b[i];
                }
                for (c = 0; c < 3; c++) {
                    float base = (p->s2[bk] * sc[c] - p->s1[bk] * smc[c]) / p->det[bk];
                    float a = (P * smc[c] - p->s1[bk] * sc[c]) / p->det[bk];
                    bgc[c] = fminf(fmaxf(base, 0), 1);
                    fg[c] = fminf(fmaxf(base + a, 0), 1);
                }
            }
            for (i = 0; i < P; i++) {
                float mk = m[i];
                out[(size_t)(cy + i / CW) * W + cx + i % CW] =
                    pack(bgc[0] + (fg[0] - bgc[0]) * mk, bgc[1] + (fg[1] - bgc[1]) * mk,
                         bgc[2] + (fg[2] - bgc[2]) * mk);
            }
        }
}

/* Level 2: eight colours per cell, one per sub-cell, each the mean of the
 * picture under that sub-cell's weight, mixed back by the same weights. */
static void level2(const struct pics *p, const float *w, int CW, int CH, uint32_t *out)
{
    int P = CW * CH, cx, cy, i, L, W = p->pw;
    for (cy = 0; cy + CH <= p->ph; cy += CH)
        for (cx = 0; cx + CW <= p->pw; cx += CW) {
            float col[8][3];
            for (L = 0; L < 8; L++) {
                float sw = 0, sr = 0, sg = 0, sb = 0;
                const float *wl = w + L * P;
                for (i = 0; i < P; i++) {
                    size_t at = (size_t)(cy + i / CW) * W + cx + i % CW;
                    sw += wl[i];
                    sr += wl[i] * p->r[at];
                    sg += wl[i] * p->g[at];
                    sb += wl[i] * p->b[at];
                }
                col[L][0] = sw > 1e-6f ? sr / sw : 0;
                col[L][1] = sw > 1e-6f ? sg / sw : 0;
                col[L][2] = sw > 1e-6f ? sb / sw : 0;
            }
            for (i = 0; i < P; i++) {
                float rr = 0, gg = 0, bb = 0;
                for (L = 0; L < 8; L++) {
                    float wl = w[L * P + i];
                    rr += wl * col[L][0];
                    gg += wl * col[L][1];
                    bb += wl * col[L][2];
                }
                out[(size_t)(cy + i / CW) * W + cx + i % CW] = pack(rr, gg, bb);
            }
        }
}

static double psnr(const uint32_t *a, const uint32_t *b, size_t n)
{
    double se = 0;
    size_t i;
    for (i = 0; i < n; i++) {
        int sh;
        for (sh = 0; sh <= 16; sh += 8) {
            double d = (double)(int)(a[i] >> sh & 255) - (double)(int)(b[i] >> sh & 255);
            se += d * d;
        }
    }
    return se == 0 ? INFINITY : 10 * log10(255.0 * 255.0 / (se / (3.0 * (double)n)));
}

static void blit(const struct screen *s, int x0, int y0, const uint32_t *px, int w, int h)
{
    int y;
    for (y = 0; y < h && y0 + y < s->h; y++)
        memcpy(s->px + (size_t)(y0 + y) * s->stride + x0, px + (size_t)y * w,
               (size_t)(x0 + w <= s->w ? w : s->w - x0) * sizeof *px);
}

static void draw_pictures(neuronte *n, const struct screen *s, struct pics *p, uint32_t *tmp, double t)
{
    static const char *const title[4] = {
        "The scene, made by code",
        "Level 1: one octant and two colours per 8 x 16 cell",
        "Level 2: eight colours per 8 x 16 cell",
        "Level 2: eight colours per 2 x 4 cell",
    };
    int m = s->w >= 1000 ? 16 : 8, k;
    double t0 = now_ms(), t1;
    char buf[200];
    size_t np = (size_t)p->pw * p->ph;

    scene(n, p, t);
    blit(s, p->x[0], p->y[0], p->srcpx, p->pw, p->ph);
    for (k = 1; k < 4; k++) {
        t1 = now_ms();
        if (k == 1)
            level1(p, tmp);
        else
            level2(p, k == 2 ? p->w8 : p->w2, k == 2 ? 8 : 2, k == 2 ? 16 : 4, tmp);
        p->ms[k] = now_ms() - t1;
        p->psnr[k] = psnr(tmp, p->srcpx, np);
        blit(s, p->x[k], p->y[k], tmp, p->pw, p->ph);
    }
    for (k = 0; k < 4; k++) {
        int ly = p->y[k] - p->label_h;
        fill(s, p->x[k], ly, p->x[k] + p->pw, p->y[k], BG);
        row(n, s, p->x[k], ly, 8, title[k], INK);
        if (k == 0)
            snprintf(buf, sizeof buf, "%d x %d px; the panels are measured against it", p->pw, p->ph);
        else if (isinf(p->psnr[k]))
            snprintf(buf, sizeof buf, "%.0f ms a frame, identical to the scene%s", p->ms[k],
                     k == 1 ? ", any terminal" : "");
        else
            snprintf(buf, sizeof buf, "%.0f ms a frame, PSNR %.1f dB%s", p->ms[k], p->psnr[k],
                     k == 1 ? ", any terminal" : ", a screen Neuronte draws");
        row(n, s, p->x[k], ly + 17, 7, buf, DIM);
    }
    p->frame_ms = now_ms() - t0;
    fill(s, 0, s->h - 20 - m / 2, s->w, s->h, BG);
    snprintf(buf, sizeof buf, "Tab: the font   Esc: quit   frame %.0f ms", p->frame_ms);
    row(n, s, m, s->h - 18 - m / 2, 8, buf, DIM);
}

static void draw_pictures_static(neuronte *n, const struct screen *s)
{
    int m = s->w >= 1000 ? 16 : 8;
    fill(s, 0, 0, s->w, s->h, BG);
    row(n, s, m, m, 16, "Neuronte: pictures in octant cells", INK);
    row(n, s, m, m + 38, 8,
        "Every cell's shape is the net's coverage of an octant character. Level 1 fits any terminal; "
        "level 2 needs a screen Neuronte draws.",
        DIM);
}

/* ---- Running ---- */

static char *pictures_name(const char *out)
{
    size_t len = strlen(out);
    char *name = malloc(len + 16);
    if (!name)
        return NULL;
    if (len > 4 && strcmp(out + len - 4, ".ppm") == 0)
        snprintf(name, len + 16, "%.*s-pictures.ppm", (int)(len - 4), out);
    else
        snprintf(name, len + 16, "%s-pictures", out);
    return name;
}

static int snapshot(neuronte *n, const char *out, int w, int h)
{
    struct screen s = {malloc((size_t)w * h * sizeof(uint32_t)), w, h, w};
    struct pics p;
    uint32_t *tmp;
    char *second = pictures_name(out);
    double t0;
    int rc = 1;

    if (!s.px || !second)
        goto done;
    t0 = now_ms();
    draw_font_page(n, &s, NULL);
    printf("%s: font page %dx%d, %.0f ms\n", out, w, h, now_ms() - t0);
    if (write_ppm(&s, out) != 0)
        goto done;
    if (pics_init(n, &p, &s) != 0)
        goto done;
    tmp = malloc((size_t)p.pw * p.ph * sizeof *tmp);
    if (tmp) {
        draw_pictures_static(n, &s);
        draw_pictures(n, &s, &p, tmp, 1.0);
        draw_pictures(n, &s, &p, tmp, 1.0); /* again, with the labels' glyphs cached */
        printf("%s: level 1 %.0f ms %.1f dB, level 2 at 8x16 %.0f ms %.1f dB, at 2x4 %.0f ms %.1f dB\n", second,
               p.ms[1], p.psnr[1], p.ms[2], p.psnr[2], p.ms[3], p.psnr[3]);
        rc = write_ppm(&s, second) == 0 ? 0 : 1;
        free(tmp);
    }
    pics_free(&p);
done:
    free(second);
    free(s.px);
    return rc;
}

static int run(neuronte *n)
{
    struct screen s;
    struct pics p = {0};
    uint32_t *saved = NULL, *tmp = NULL;
    int page = 0, fresh = 1, rc = 0, have_pics = 0;
    double t_start = now_ms();

    if (term_start(&s) != 0)
        return 1;
    for (;;) {
        unsigned char b[64];
        int got, r = term_resized(&s);

        if (r < 0) {
            rc = 1;
            break;
        }
        if (r > 0) {
            fresh = 1;
            free(saved);
            saved = NULL;
            if (have_pics) {
                pics_free(&p);
                free(tmp);
                tmp = NULL;
                have_pics = 0;
            }
        }
        if (page == 0 && fresh) {
            if (saved) {
                memcpy(s.px, saved, (size_t)s.h * s.stride * sizeof *s.px);
            } else {
                draw_font_page(n, &s, term_show);
                saved = malloc((size_t)s.h * s.stride * sizeof *s.px);
                if (saved)
                    memcpy(saved, s.px, (size_t)s.h * s.stride * sizeof *s.px);
            }
            fresh = 0;
            if (term_show(&s) != 0) {
                rc = 1;
                break;
            }
        } else if (page == 1) {
            if (!have_pics) {
                if (pics_init(n, &p, &s) != 0 || !(tmp = malloc((size_t)p.pw * p.ph * sizeof *tmp))) {
                    rc = 1;
                    break;
                }
                have_pics = 1;
                fresh = 1;
            }
            if (fresh)
                draw_pictures_static(n, &s);
            fresh = 0;
            draw_pictures(n, &s, &p, tmp, (now_ms() - t_start) / 1000.0);
            if (term_show(&s) != 0) {
                rc = 1;
                break;
            }
        }
        got = term_read(b, sizeof b, page == 1 ? 1 : 200);
        if (got <= 0)
            continue;
        if ((got == 1 && b[0] == 27) || memchr(b, 3, (size_t)got))
            break;
        if (memchr(b, '\t', (size_t)got)) {
            page ^= 1;
            fresh = 1;
        }
    }
    if (have_pics)
        pics_free(&p);
    free(tmp);
    free(saved);
    term_stop(&s);
    return rc;
}

static int open_weights(const char *path, neuronte **n)
{
    int rc;
    if (!path)
        path = "weights/neuronte-split-v4.nrt";
    rc = neuronte_open_file(path, n);
    if (rc != NEURONTE_OK)
        fprintf(stderr, "%s: cannot load weights (%d)\n", path, rc);
    return rc;
}

int main(int argc, char **argv)
{
    const char *weights = NULL;
    neuronte *n;
    int rc;

    if (argc >= 3 && strcmp(argv[1], "--snapshot") == 0) {
        int w = argc >= 5 ? atoi(argv[3]) : 1280, h = argc >= 5 ? atoi(argv[4]) : 800;
        if (argc == 6 || argc == 4)
            weights = argv[argc - 1];
        if (w < 640 || h < 480 || w > 4096 || h > 4096) {
            fprintf(stderr, "snapshot size must be 640x480 .. 4096x4096\n");
            return 2;
        }
        if (open_weights(weights, &n) != NEURONTE_OK)
            return 1;
        rc = snapshot(n, argv[2], w, h);
        neuronte_close(n);
        return rc;
    }
    if (argc == 2)
        weights = argv[1];
    if (open_weights(weights, &n) != NEURONTE_OK)
        return 1;
    rc = run(n);
    neuronte_close(n);
    return rc;
}
