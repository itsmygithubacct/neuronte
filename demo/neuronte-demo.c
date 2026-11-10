/* neuronte-demo: every glyph on the screen drawn by the Neuronte net,
 * shown in a Kilix terminal through kitty-framebuffer.
 *
 *   neuronte-demo [WEIGHTS.nrt]
 *   neuronte-demo --snapshot OUT.ppm [WIDTH HEIGHT] [WEIGHTS.nrt]
 *
 * Type to draw text. Tab changes the size of the typed text, Backspace
 * deletes, Enter starts a new line, Esc or Ctrl-C quits. --snapshot draws
 * the first screen into a PPM file with no terminal. The default weights
 * are neuronte-full, else neuronte-ascii. With weights that know box
 * drawing, a panel of it, blocks, Braille and symbols is shown, with two
 * spinners that turn while the demo waits for keys. MIT licence. */
#define _POSIX_C_SOURCE 200809L
#include "neuronte.h"

#ifndef NEURONTE_DEMO_NO_TERMINAL
#include "kitty_framebuffer.h"
#endif

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define BG 0xFF11151Cu
#define INK 0xFFE9E6DFu
#define DIM 0xFF8A93A3u
#define ACCENT 0xFF7FB4FFu
#define RULE 0xFF2A3140u

static const int sizes[] = {8, 12, 16, 24, 32, 48};
#define NSIZES ((int)(sizeof sizes / sizeof sizes[0]))

struct screen {
    uint32_t *px;
    int w, h;
};

struct state {
    char text[4096];
    size_t len;
    int size_index;
    double last_ms;
    int full;  /* the weights draw box drawing, blocks and Braille */
    int frame; /* spinner frame */
};

static double now_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec * 1e-6;
}

static void fill(struct screen *s, int x0, int y0, int x1, int y1, uint32_t c)
{
    int x, y;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > s->w) x1 = s->w;
    if (y1 > s->h) y1 = s->h;
    for (y = y0; y < y1; y++)
        for (x = x0; x < x1; x++)
            s->px[(size_t)y * s->w + x] = c;
}

/* Draw text with wrapping at right; returns the y below the last line. */
static int text(neuronte *n, struct screen *s, int x, int y, int right, int cw, const char *t,
                size_t len, uint32_t color, int *caret_x, int *caret_y)
{
    size_t off = 0;
    int cx = x, ch = 2 * cw;
    while (off < len) {
        uint32_t sc;
        off += neuronte_utf8_decode(t + off, len - off, &sc);
        if (sc == '\n' || cx + cw > right) {
            cx = x;
            y += ch;
            if (sc == '\n')
                continue;
        }
        neuronte_draw_scalar(n, s->px, s->w, s->w, s->h, cx, y, cw, ch, sc, color);
        cx += cw;
    }
    if (caret_x) {
        if (cx + cw > right) {
            cx = x;
            y += ch;
        }
        *caret_x = cx;
        *caret_y = y;
    }
    return y + ch;
}

static int line(neuronte *n, struct screen *s, int x, int y, int cw, const char *t, uint32_t color)
{
    return text(n, s, x, y, s->w, cw, t, strlen(t), color, NULL, NULL);
}

/* The n-th UTF-8 character of t, copied into out. */
static void nth(const char *t, int k, char *out)
{
    size_t off = 0, len = strlen(t), step = 0;
    uint32_t sc;
    for (; k >= 0 && off < len; k--) {
        step = neuronte_utf8_decode(t + off, len - off, &sc);
        if (k > 0)
            off += step;
    }
    memcpy(out, t + off, step);
    out[step] = 0;
}

static const char *panel[] = {
    "\u256D\u2500\u2500\u2500\u2500\u252C\u2500\u2500\u2500\u2500\u256E "
    "\u250F\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2513 "
    "\u2554\u2550\u2550\u2550\u2550\u2566\u2550\u2550\u2550\u2550\u2557 "
    "\u250C\u2504\u2504\u2504\u2504\u2510  \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
    "\u2587\u2586\u2585\u2584\u2583\u2582\u2581  \u2880\u28C0\u28E4\u28F6\u28FF\u28FF\u28F6\u28E4\u28C0\u2840",
    "\u2502 ab \u2502 cd \u2502 \u2503 ef \u2503 gh \u2503 \u2551 ij \u2551 kl \u2551 "
    "\u2506 mn \u2506  \u258F\u258E\u258D\u258C\u258B\u258A\u2589\u2588  "
    "\u2596\u2597\u2598\u2599\u259A\u259B\u259C\u259D\u259E\u259F  \u2801\u2803\u2807\u2847\u28C7\u28E7\u28F7\u28FF",
    "\u2570\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u256F "
    "\u2517\u2501\u2501\u2501\u2501\u253B\u2501\u2501\u2501\u2501\u251B "
    "\u255A\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u255D "
    "\u2514\u2504\u2504\u2504\u2504\u2518  \u2580\u2594\u2590\u2595 \u2571\u2572\u2573\u2571\u2572  "
    "\u23BF done \u2714 \u2610 \u2612",
    "\u25CF \u25C6 \u25C8 \u25D0 \u25D1 \u25C9 \u25EF \u25B2 \u25BC \u25BE \u25B8 \u23F5 \u276F \u203A "
    "\u2190 \u2192 \u2191 \u2193 \u2197 \u21E3 \u273B \u2722 \u2736 \u273D \u2733 \u00B7 \u2022 "
    "\u2026 \u2014 \u2013 \u2018\u2019 \u201C\u201D \u00D7 \u2261 \u2248 \u00B0 \u00BD \u00A9 "
    "\u203B \u2059 \u2E2C",
};
static const char braille_spin[] = "\u280B\u2819\u2839\u2838\u283C\u2834\u2826\u2827\u2807\u280F";
static const char star_spin[] = "\u00B7\u2722\u2733\u2736\u273B\u273D\u273B\u2736\u2733\u2722";

/* "44,801" */
static void thousands(size_t v, char *out)
{
    char d[32];
    int len = snprintf(d, sizeof d, "%zu", v), i, o = 0;
    for (i = 0; i < len; i++) {
        if (i > 0 && (len - i) % 3 == 0)
            out[o++] = ',';
        out[o++] = d[i];
    }
    out[o] = 0;
}

/* Where the parts that change are. */
struct layout {
    int m, small, spin_y, dyn_y;
};

/* Everything that stays put: drawn once, and again after a resize. The
 * first time takes seconds, so show(), when given, presents each part as
 * it is done. */
static void draw_static(neuronte *n, struct screen *s, const struct state *st, struct layout *l,
                        void (*show)(const struct screen *))
{
    static const char sample[] = "The quick brown fox jumps over the lazy dog. 0123456789";
    char buf[160], count[32];
    int m = s->w / 40 < 12 ? 12 : s->w / 40, y = m, i;
    int small = s->w >= 1100 ? 10 : 8;

    fill(s, 0, 0, s->w, s->h, BG);
    y = line(n, s, m, y, s->w >= 1100 ? 40 : 28, st->full ? "Neuronte full" : "Neuronte", INK);
    thousands(neuronte_parameters(n), count);
    snprintf(buf, sizeof buf, "Every glyph on this screen is drawn by a %s-weight neural net. No font file.",
             count);
    y = line(n, s, m, y, small, buf, DIM);
    y += small;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;
    if (show)
        show(s);

    /* The same weights at four cell widths. */
    for (i = 0; i < 4; i++) {
        snprintf(buf, sizeof buf, "%2d px", sizes[i]);
        line(n, s, m, y + (2 * sizes[i] - 2 * small) / 2, small, buf, DIM);
        /* No wrap: a line too long for the screen is cut at the edge. */
        y = text(n, s, m + 7 * small, y, 1 << 20, sizes[i], sample, sizeof sample - 1, INK, NULL, NULL);
        y += sizes[i] / 3;
        if (show)
            show(s);
    }
    y += small / 2;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;

    /* All 95 printable ASCII characters. */
    {
        char all[96];
        for (i = 0; i < 95; i++)
            all[i] = (char)(32 + i);
        y = text(n, s, m, y, s->w - m, 16, all, 95, ACCENT, NULL, NULL);
    }
    y += small;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;
    if (show)
        show(s);

    /* Box drawing, blocks, Braille and symbols, cut at the screen edge. */
    l->spin_y = -1;
    if (st->full) {
        for (i = 0; i < (int)(sizeof panel / sizeof panel[0]); i++) {
            const char *row = panel[i];
            y = text(n, s, m, y, 1 << 20, 16, row, strlen(row), ACCENT, NULL, NULL);
            if (show)
                show(s);
        }
        l->spin_y = y + 4;
        y = line(n, s, m + 4 * 16, l->spin_y, 16, "these turn while the demo waits for keys", INK);
        y += small;
        fill(s, m, y, s->w - m, y + 1, RULE);
        y += small;
    }
    l->m = m;
    l->small = small;
    l->dyn_y = y;
}

/* The spinners, the typed text and the footer. */
static void draw_dynamic(neuronte *n, struct screen *s, const struct state *st, const struct layout *l)
{
    char buf[160];
    int m = l->m, small = l->small, y = l->dyn_y, cx, cy, cw = sizes[st->size_index];

    if (l->spin_y >= 0) {
        char a[8], b[8];
        nth(braille_spin, st->frame % 10, a);
        nth(star_spin, st->frame % 10, b);
        snprintf(buf, sizeof buf, "%s %s", a, b);
        fill(s, m, l->spin_y, m + 3 * 16, l->spin_y + 32, BG);
        line(n, s, m, l->spin_y, 16, buf, INK);
    }
    fill(s, 0, y, s->w, s->h, BG);
    snprintf(buf, sizeof buf, "Type here (%d px):", cw);
    y = line(n, s, m, y, small, buf, DIM) + small / 2;
    text(n, s, m, y, s->w - m, cw, st->text, st->len, INK, &cx, &cy);
    fill(s, cx, cy + 2 * cw - (cw > 12 ? 3 : 2), cx + cw, cy + 2 * cw, ACCENT);

    snprintf(buf, sizeof buf, "Tab: text size   Esc: quit   last frame %.1f ms", st->last_ms);
    line(n, s, m, s->h - 2 * small - m / 2, small, buf, DIM);
}

static void to_rgba(const struct screen *s, uint8_t *rgba)
{
    size_t i, count = (size_t)s->w * s->h;
    for (i = 0; i < count; i++) {
        uint32_t p = s->px[i];
        rgba[4 * i] = (uint8_t)(p >> 16);
        rgba[4 * i + 1] = (uint8_t)(p >> 8);
        rgba[4 * i + 2] = (uint8_t)p;
        rgba[4 * i + 3] = 255;
    }
}

static void erase_last(struct state *st)
{
    while (st->len > 0) {
        unsigned char c = (unsigned char)st->text[--st->len];
        if ((c & 0xC0) != 0x80)
            break;
    }
}

/* Apply one chunk of input. Returns 1 to quit. */
static int input(struct state *st, const unsigned char *b, size_t n)
{
    size_t i;
    for (i = 0; i < n; i++) {
        unsigned char c = b[i];
        if (c == 3)
            return 1;
        if (c == 0x1B) {
            if (i + 1 >= n)
                return 1; /* a lone Esc */
            /* Skip an escape sequence, such as an arrow key. */
            i++;
            if (b[i] == '[' || b[i] == 'O')
                while (i + 1 < n && !(b[i + 1] >= 0x40 && b[i + 1] <= 0x7E))
                    i++;
            i++;
            continue;
        }
        if (c == '\t') {
            st->size_index = (st->size_index + 1) % NSIZES;
        } else if (c == 127 || c == 8) {
            erase_last(st);
        } else if (c == '\r' || c == '\n') {
            if (st->len < sizeof st->text)
                st->text[st->len++] = '\n';
        } else if (c >= 32 && st->len < sizeof st->text) {
            st->text[st->len++] = (char)c;
        }
    }
    return 0;
}

/* Whether the weights were trained on blocks: a full block fills its cell. */
static int knows_blocks(neuronte *n)
{
    float c[8 * 16];
    int i;
    if (neuronte_coverage(n, 0x2588, 8, 16, 2, c) != NEURONTE_OK)
        return 0;
    for (i = 0; i < 8 * 16; i++)
        if (c[i] < 0.9f)
            return 0;
    return 1;
}

static int snapshot(neuronte *n, const char *out, int w, int h)
{
    struct screen s = {malloc((size_t)w * h * sizeof(uint32_t)), w, h};
    struct state st = {.size_index = 3, .full = knows_blocks(n), .frame = 2};
    const char typed[] = "Hello, Kilix!\nTyped text is drawn the same way.";
    struct layout l;
    double t0, first;
    FILE *f;
    int i;

    if (!s.px)
        return 1;
    memcpy(st.text, typed, sizeof typed - 1);
    st.len = sizeof typed - 1;
    t0 = now_ms();
    draw_static(n, &s, &st, &l, NULL);
    draw_dynamic(n, &s, &st, &l);
    first = now_ms() - t0;
    /* Again, as a keypress would, with the time of that frame shown. */
    t0 = now_ms();
    draw_dynamic(n, &s, &st, &l);
    st.last_ms = now_ms() - t0;
    draw_dynamic(n, &s, &st, &l);
    f = fopen(out, "wb");
    if (!f) {
        perror(out);
        return 1;
    }
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    for (i = 0; i < w * h; i++) {
        unsigned char rgb[3] = {(unsigned char)(s.px[i] >> 16), (unsigned char)(s.px[i] >> 8),
                                (unsigned char)s.px[i]};
        fwrite(rgb, 1, 3, f);
    }
    fclose(f);
    printf("%s: %dx%d, first draw %.1f ms, next %.1f ms\n", out, w, h, first, st.last_ms);
    free(s.px);
    return 0;
}

#ifndef NEURONTE_DEMO_NO_TERMINAL
static kittyfb_session session;
static uint8_t *rgba; /* the frame as kitty-framebuffer takes it */

static void show_now(const struct screen *s)
{
    to_rgba(s, rgba);
    kittyfb_present(&session, rgba, s->w, s->h);
}

static void on_fatal(int sig)
{
    kittyfb_emergency_restore(&session);
    _exit(128 + sig);
}

static int run(neuronte *n)
{
    kittyfb_options opt;
    struct sigaction sa;
    struct screen s;
    struct state st = {.size_index = 2, .full = knows_blocks(n)};
    struct layout l;
    int dirty = 1, fresh = 1, rc = 0;

    kittyfb_session_init(&session);
    kittyfb_options_init(&opt);
    if (kittyfb_start(&session, STDIN_FILENO, STDOUT_FILENO, &opt) != 0) {
        fprintf(stderr, errno == ENOTSUP ? "neuronte-demo: this terminal does not speak the Kitty graphics protocol\n"
                                         : "neuronte-demo: %s\n", strerror(errno));
        return 1;
    }
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_fatal;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    s.w = kittyfb_width(&session);
    s.h = kittyfb_height(&session);
    s.px = malloc((size_t)s.w * s.h * sizeof *s.px);
    rgba = malloc((size_t)s.w * s.h * 4);
    if (!s.px || !rgba) {
        rc = 1;
        goto out;
    }
    for (;;) {
        struct pollfd p = {STDIN_FILENO, POLLIN, 0};
        unsigned char b[256];
        ssize_t got;
        int nw, nh;

        if (kittyfb_check_resize(&session, &nw, &nh)) {
            uint32_t *px2 = realloc(s.px, (size_t)nw * nh * sizeof *px2);
            uint8_t *rgba2;
            if (!px2) {
                rc = 1;
                break;
            }
            s.px = px2;
            rgba2 = realloc(rgba, (size_t)nw * nh * 4);
            if (!rgba2) {
                rc = 1;
                break;
            }
            rgba = rgba2;
            s.w = nw;
            s.h = nh;
            dirty = fresh = 1;
        }
        if (dirty) {
            double t0 = now_ms();
            if (fresh)
                draw_static(n, &s, &st, &l, show_now);
            fresh = 0;
            draw_dynamic(n, &s, &st, &l);
            st.last_ms = now_ms() - t0;
            to_rgba(&s, rgba);
            if (!kittyfb_present(&session, rgba, s.w, s.h)) {
                rc = 1;
                break;
            }
            dirty = 0;
        }
        if (poll(&p, 1, 100) <= 0) {
            if (st.full) {
                st.frame++;
                dirty = 1;
            }
            continue;
        }
        got = read(STDIN_FILENO, b, sizeof b);
        if (got <= 0)
            continue;
        if (input(&st, b, (size_t)got))
            break;
        dirty = 1;
    }
out:
    kittyfb_stop(&session);
    free(s.px);
    free(rgba);
    return rc;
}
#endif

/* Open the named weights, or by default the full set, else ASCII. */
static int open_weights(const char *path, neuronte **n)
{
    int rc;
    if (path) {
        rc = neuronte_open_file(path, n);
    } else {
        path = "weights/neuronte-full-v0.nrt";
        rc = neuronte_open_file(path, n);
        if (rc != NEURONTE_OK) {
            path = "weights/neuronte-ascii-v0.nrt";
            rc = neuronte_open_file(path, n);
        }
    }
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
        if (w < 320 || h < 240 || w > 4096 || h > 4096) {
            fprintf(stderr, "snapshot size must be 320x240 .. 4096x4096\n");
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
#ifdef NEURONTE_DEMO_NO_TERMINAL
    fprintf(stderr, "built without kitty-framebuffer; only --snapshot works\n");
    rc = 2;
#else
    rc = run(n);
#endif
    neuronte_close(n);
    return rc;
}
