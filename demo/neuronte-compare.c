/* neuronte-compare: two weight files side by side, by default
 * neuronte-ascii on the left and neuronte-full on the right, on examples
 * picked to show where they differ. Each column is drawn only by its own
 * net, labels included, so a column shows what that net can do.
 *
 *   neuronte-compare [LEFT.nrt RIGHT.nrt]
 *   neuronte-compare --snapshot OUT.ppm [WIDTH HEIGHT [LEFT.nrt RIGHT.nrt]]
 *
 * Typing goes to both columns, Tab changes the size of the typed text,
 * Esc or Ctrl-C quits. Each column states its net's size and how long it
 * took: one cell, the whole column, and the last keypress. MIT licence. */
#define _POSIX_C_SOURCE 200809L
#include "common.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WARN 0xFFE3A95Cu

static const int sizes[] = {8, 12, 16, 24, 32};
#define NSIZES ((int)(sizeof sizes / sizeof sizes[0]))

struct side {
    neuronte *n;
    char name[64];
    int full;          /* trained on box drawing, blocks and Braille */
    int accents;       /* trained on accented letters */
    struct screen col; /* this side's column of the screen */
    int top, small;
    int info_y, spin_x, spin_y, dyn_y;
    double cell_ms, column_ms, typed_ms;
};

struct state {
    struct typing typed;
    int frame;
};

/* A TUI panel and a file tree, 12 px cells. Column 2 of the panel's
 * fourth row is left blank for the spinner. */
static const char *panel[] = {
    "╭─ build ──────────╮",
    "│ ✔ compile        │",
    "│ ✔ test           │",
    "│   package        │",
    "╰──────────────────╯",
};
static const char *tree[] = {
    "neuronte",
    "├── src",
    "│   ├── neuronte.c",
    "│   └── utf8.c",
    "└── README.md",
};
static const char bar[] =
    "▕██████▍  ▏ 70% ░▒▓█ "
    "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁";
/* ASCII beside the characters it stands in for. */
static const char punct[] = "- – — ─  ' ’  \" “ ”  ... …  * •";
static const char symbols[] =
    "← → ↑ ↓  ✔ ☐ ☒  ● ◆ ▲ ▼  "
    "× ½ © °  ✻ ✢ ✶ ✽ ✳";
static const char accented[] = "café naïve señor Ångström Łódź Dvořák ß";
static const char neither[] =
    "中 文  ∑ ∞  Ω Ж  \U0001F600";

/* A sine wave two Braille cells high and `cells` wide, as two UTF-8 rows. */
static void braille_wave(int cells, char rows[2][256])
{
    /* Bit of Braille dot (row, column) in a cell. */
    static const int bit[4][2] = {{0, 3}, {1, 4}, {2, 5}, {6, 7}};
    const double pi = 3.14159265358979323846;
    unsigned char cell[2][64] = {{0}};
    int x, r, prev = -1;

    if (cells > 64)
        cells = 64;
    for (x = 0; x < 2 * cells; x++) {
        int y = (int)lround(3.5 - 3.4 * sin(x * 2 * pi / 40.0)), a = y, b = y;
        if (prev >= 0 && prev < y - 1)
            a = prev + 1; /* join a steep step to the dot before */
        if (prev > y + 1)
            b = prev - 1;
        for (r = a; r <= b; r++)
            cell[r / 4][x / 2] |= (unsigned char)(1 << bit[r % 4][x % 2]);
        prev = y;
    }
    for (r = 0; r < 2; r++) {
        char *o = rows[r];
        for (x = 0; x < cells; x++) {
            *o++ = (char)0xE2;
            *o++ = (char)(0xA0 | cell[r][x] >> 6);
            *o++ = (char)(0x80 | (cell[r][x] & 0x3F));
        }
        *o = 0;
    }
}

/* A row's heading, and in colour whether this net was trained on it. */
static int heading(const struct side *d, int y, const char *what, int trained)
{
    char buf[96];
    snprintf(buf, sizeof buf, "%s: ", what);
    line(d->n, &d->col, 0, y, d->small, buf, DIM);
    line(d->n, &d->col, (int)strlen(buf) * d->small, y, d->small,
         trained ? "trained" : "not trained, so a mark of its own", trained ? ACCENT : WARN);
    return y + 2 * d->small + 3;
}

/* What stays put. show(), when given, presents each part as it is done,
 * so the time each net takes can be watched. */
static void draw_column(struct side *d, const struct screen *whole, int (*show)(const struct screen *))
{
    const struct screen *s = &d->col;
    neuronte *n = d->n;
    char buf[160], a[32], b[32], wave[2][256];
    int small = d->small, y = d->top, i;
    double t0 = now_ms();

    y = line(n, s, 0, y, 16, d->name, INK);
    thousands(neuronte_parameters(n), a);
    thousands(204 + 4 * neuronte_parameters(n), b);
    if (neuronte_nets(n) > 1)
        snprintf(buf, sizeof buf, "%s weights in %d nets, one picked per character.", a, neuronte_nets(n));
    else
        snprintf(buf, sizeof buf, "%s weights, %s bytes. Draws all of this column.", a, b);
    y = line(n, s, 0, y, small, buf, DIM);
    y = line(n, s, 0, y, small,
             d->full && d->accents ? "Trained on ASCII, drawing, symbols, accented letters."
             : d->full             ? "Trained on ASCII, box drawing, blocks, Braille, symbols."
                                   : "Trained on the 95 ASCII characters.", DIM);
    d->info_y = y;
    y += 2 * small + small / 2;
    fill(s, 0, y, s->w, y + 1, RULE);
    y += small;
    if (show)
        show(whole);

    y = heading(d, y, "ASCII at 8, 16 and 20 px", 1);
    y = row(n, s, 0, y, 8, "The quick brown fox jumps over the lazy dog. 0123456789", INK) + 4;
    y = row(n, s, 0, y, 16, "Sphinx of black quartz, judge my vow.", INK) + 4;
    y = row(n, s, 0, y, 20, "Ag&@ Rxy? 1lI0O", INK) + small;
    if (show)
        show(whole);

    y = heading(d, y, "Box drawing in a TUI", d->full);
    for (i = 0; i < 5; i++) {
        row(n, s, 0, y + 24 * i, 12, panel[i], INK);
        row(n, s, 21 * 12, y + 24 * i, 12, tree[i], INK);
    }
    d->spin_x = 2 * 12;
    d->spin_y = y + 3 * 24;
    y += 5 * 24 + small;
    if (show)
        show(whole);

    y = heading(d, y, "Blocks and Braille", d->full);
    y = row(n, s, 0, y, 16, bar, ACCENT) + 4;
    braille_wave(40, wave);
    y = row(n, s, 0, y, 12, wave[0], ACCENT);
    y = row(n, s, 0, y, 12, wave[1], ACCENT) + small;
    if (show)
        show(whole);

    y = heading(d, y, "Symbols past ASCII", d->full);
    y = row(n, s, 0, y, 16, punct, INK) + 4;
    y = row(n, s, 0, y, 12, symbols, INK) + small;
    if (show)
        show(whole);

    y = heading(d, y, "Accented letters", d->accents);
    y = row(n, s, 0, y, 12, accented, INK) + small;
    if (show)
        show(whole);

    y = line(n, s, 0, y, small, "In neither set: each net makes its own mark", DIM) + 3;
    y = row(n, s, 0, y, 12, neither, INK) + small;
    d->dyn_y = y;
    d->column_ms = now_ms() - t0;
    if (show)
        show(whole);
}

static void draw_spinner(const struct side *d, int frame)
{
    char a[8];
    nth(braille_spin, frame % 10, a);
    fill(&d->col, d->spin_x, d->spin_y, d->spin_x + 12, d->spin_y + 24, BG);
    line(d->n, &d->col, d->spin_x, d->spin_y, 12, a, ACCENT);
}

/* The typed text, then the timings, which include it. */
static void draw_typed(struct side *d, const struct typing *t)
{
    const struct screen *s = &d->col;
    char buf[160];
    int cw = sizes[t->size_index], y, cx, cy;
    double t0 = now_ms();

    fill(s, 0, d->dyn_y, s->w, s->h, BG);
    snprintf(buf, sizeof buf, "Type: both columns get it (%d px). Tab: size. Esc: quit.", cw);
    y = line(d->n, s, 0, d->dyn_y, d->small, buf, DIM) + d->small / 2;
    text(d->n, s, 0, y, s->w, cw, t->text, t->len, INK, &cx, &cy);
    fill(s, cx, cy + 2 * cw - (cw > 12 ? 3 : 2), cx + cw, cy + 2 * cw, ACCENT);
    d->typed_ms = now_ms() - t0;

    fill(s, 0, d->info_y, s->w, d->info_y + 2 * d->small, BG);
    snprintf(buf, sizeof buf, "16x32 cell %.1f ms, column %.0f ms, typing %.1f ms", d->cell_ms, d->column_ms,
             d->typed_ms);
    line(d->n, s, 0, d->info_y, d->small, buf, DIM);
}

/* Split the screen into the two columns. */
static void place(struct side d[2], const struct screen *s)
{
    int m = s->w / 40 < 12 ? 12 : s->w / 40, half = s->w / 2, w = half - m - m / 2, i;
    d[0].col = sub_screen(s, m, w);
    d[1].col = sub_screen(s, half + m / 2, w);
    for (i = 0; i < 2; i++) {
        d[i].top = m * 3 / 4;
        d[i].small = s->w >= 1100 ? 10 : 8;
    }
}

static void draw_all(struct side d[2], const struct screen *s, const struct state *st,
                     int (*show)(const struct screen *))
{
    int m = d[0].top, i;
    fill(s, 0, 0, s->w, s->h, BG);
    fill(s, s->w / 2, m, s->w / 2 + 1, s->h - m, RULE);
    for (i = 0; i < 2; i++)
        draw_column(&d[i], s, show);
    for (i = 0; i < 2; i++) {
        draw_spinner(&d[i], st->frame);
        draw_typed(&d[i], &st->typed);
    }
}

static int snapshot(struct side d[2], const char *out, int w, int h)
{
    struct screen s = {malloc((size_t)w * h * sizeof(uint32_t)), w, h, w};
    struct state st = {.typed.size_index = 2, .frame = 2};
    const char typed[] = "Typed in both: ASCII, é, ── and ✔.";
    int rc, i;

    if (!s.px)
        return 1;
    memcpy(st.typed.text, typed, sizeof typed - 1);
    st.typed.len = sizeof typed - 1;
    place(d, &s);
    draw_all(d, &s, &st, NULL);
    for (i = 0; i < 2; i++)
        draw_typed(&d[i], &st.typed); /* again, as a keypress would */
    rc = write_ppm(&s, out);
    if (rc == 0)
        printf("%s: %dx%d, columns %.0f and %.0f ms\n", out, w, h, d[0].column_ms, d[1].column_ms);
    free(s.px);
    return rc == 0 ? 0 : 1;
}

static int run(struct side d[2])
{
    struct screen s;
    struct state st = {.typed.size_index = 2};
    int fresh = 1, keys = 0, rc = 0, i;

    if (term_start(&s) != 0)
        return 1;
    for (;;) {
        unsigned char b[256];
        int got, r = term_resized(&s);

        if (r < 0) {
            rc = 1;
            break;
        }
        if (r > 0)
            fresh = 1;
        if (fresh) {
            place(d, &s);
            draw_all(d, &s, &st, term_show);
            fresh = keys = 0;
        } else if (keys) {
            for (i = 0; i < 2; i++)
                draw_typed(&d[i], &st.typed);
            keys = 0;
        } else {
            for (i = 0; i < 2; i++)
                draw_spinner(&d[i], st.frame);
        }
        if (term_show(&s) != 0) {
            rc = 1;
            break;
        }
        got = term_read(b, sizeof b, 100);
        if (got == 0) {
            st.frame++;
            continue;
        }
        if (typing_input(&st.typed, NSIZES, b, (size_t)got))
            break;
        keys = 1;
    }
    term_stop(&s);
    return rc;
}

static int open_side(struct side *d, const char *path)
{
    const char *base = strrchr(path, '/');
    size_t len;
    float c[16 * 32];
    double t0;
    int rc = neuronte_open_file(path, &d->n), i;

    if (rc != NEURONTE_OK) {
        fprintf(stderr, "%s: cannot load weights (%d)\n", path, rc);
        return rc;
    }
    base = base ? base + 1 : path;
    len = strlen(base);
    if (len > 4 && strcmp(base + len - 4, ".nrt") == 0)
        len -= 4;
    if (len >= sizeof d->name)
        len = sizeof d->name - 1;
    memcpy(d->name, base, len);
    d->name[len] = 0;
    d->full = knows_blocks(d->n);
    d->accents = knows_accents(d->n);
    /* One 16 x 32 cell, timed without the cache. */
    t0 = now_ms();
    for (i = 0; i < 3; i++)
        neuronte_coverage(d->n, (uint32_t)('g' + i), 16, 32, 0, c);
    d->cell_ms = (now_ms() - t0) / 3;
    return NEURONTE_OK;
}

int main(int argc, char **argv)
{
    const char *left = "weights/neuronte-ascii-v0.nrt", *right = "weights/neuronte-full-v1.nrt";
    struct side d[2];
    int snap = argc >= 3 && strcmp(argv[1], "--snapshot") == 0, w = 1280, h = 800, rc;

    memset(d, 0, sizeof d);
    if (snap) {
        if (argc != 3 && argc != 5 && argc != 7) {
            fprintf(stderr, "usage: %s --snapshot OUT.ppm [WIDTH HEIGHT [LEFT.nrt RIGHT.nrt]]\n", argv[0]);
            return 2;
        }
        if (argc >= 5) {
            w = atoi(argv[3]);
            h = atoi(argv[4]);
        }
        if (argc == 7) {
            left = argv[5];
            right = argv[6];
        }
        if (w < 320 || h < 240 || w > 4096 || h > 4096) {
            fprintf(stderr, "snapshot size must be 320x240 .. 4096x4096\n");
            return 2;
        }
    } else if (argc == 3) {
        left = argv[1];
        right = argv[2];
    } else if (argc != 1) {
        fprintf(stderr, "usage: %s [LEFT.nrt RIGHT.nrt]\n", argv[0]);
        return 2;
    }
    if (open_side(&d[0], left) != NEURONTE_OK || open_side(&d[1], right) != NEURONTE_OK) {
        neuronte_close(d[0].n);
        return 1;
    }
    rc = snap ? snapshot(d, argv[2], w, h) : run(d);
    neuronte_close(d[0].n);
    neuronte_close(d[1].n);
    return rc;
}
