/* neuronte-demo: every glyph on the screen drawn by the Neuronte net,
 * shown in a Kilix terminal through kitty-framebuffer.
 *
 *   neuronte-demo [WEIGHTS.nrt]
 *   neuronte-demo --snapshot OUT.ppm [WIDTH HEIGHT] [WEIGHTS.nrt]
 *
 * Type to draw text. Tab changes the size of the typed text, Backspace
 * deletes, Enter starts a new line, Esc or Ctrl-C quits. --snapshot draws
 * the first screen into a PPM file with no terminal. MIT licence. */
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

static void draw(neuronte *n, struct screen *s, const struct state *st)
{
    static const char sample[] = "The quick brown fox jumps over the lazy dog. 0123456789";
    char buf[160];
    int m = s->w / 40 < 12 ? 12 : s->w / 40, y = m, i, cx, cy, cw = sizes[st->size_index];
    int small = s->w >= 1100 ? 10 : 8;

    fill(s, 0, 0, s->w, s->h, BG);
    y = line(n, s, m, y, s->w >= 1100 ? 40 : 28, "Neuronte", INK);
    y = line(n, s, m, y, small,
             "Every glyph on this screen is drawn by a 44,801-weight neural net. No font file.", DIM);
    y += small;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;

    /* The same weights at four cell widths. */
    for (i = 0; i < 4; i++) {
        snprintf(buf, sizeof buf, "%2d px", sizes[i]);
        line(n, s, m, y + (2 * sizes[i] - 2 * small) / 2, small, buf, DIM);
        /* No wrap: a line too long for the screen is cut at the edge. */
        y = text(n, s, m + 7 * small, y, 1 << 20, sizes[i], sample, sizeof sample - 1, INK, NULL, NULL);
        y += sizes[i] / 3;
    }
    y += small / 2;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;

    /* All 95 trained characters. */
    {
        char all[96];
        for (i = 0; i < 95; i++)
            all[i] = (char)(32 + i);
        y = text(n, s, m, y, s->w - m, 16, all, 95, ACCENT, NULL, NULL);
    }
    y += small;
    fill(s, m, y, s->w - m, y + 1, RULE);
    y += small;

    /* What was typed, with a caret. */
    snprintf(buf, sizeof buf, "Type here (%d px):", cw);
    y = line(n, s, m, y, small, buf, DIM) + small / 2;
    text(n, s, m, y, s->w - m, cw, st->text, st->len, INK, &cx, &cy);
    fill(s, cx, cy + 2 * cw - (cw > 12 ? 3 : 2), cx + cw, cy + 2 * cw, ACCENT);

    /* Footer. */
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

static int snapshot(neuronte *n, const char *out, int w, int h)
{
    struct screen s = {malloc((size_t)w * h * sizeof(uint32_t)), w, h};
    struct state st = {.size_index = 3};
    const char typed[] = "Hello, Kilix!\nTyped text is drawn the same way.";
    double t0;
    FILE *f;
    int i;

    if (!s.px)
        return 1;
    memcpy(st.text, typed, sizeof typed - 1);
    st.len = sizeof typed - 1;
    t0 = now_ms();
    draw(n, &s, &st);
    st.last_ms = now_ms() - t0;
    draw(n, &s, &st); /* again, with the cache warm and the time shown */
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
    printf("%s: %dx%d, first draw %.1f ms\n", out, w, h, st.last_ms);
    free(s.px);
    return 0;
}

#ifndef NEURONTE_DEMO_NO_TERMINAL
static kittyfb_session session;

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
    struct state st = {.size_index = 2};
    uint8_t *rgba;
    int dirty = 1, rc = 0;

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
            dirty = 1;
        }
        if (dirty) {
            double t0 = now_ms();
            draw(n, &s, &st);
            st.last_ms = now_ms() - t0;
            to_rgba(&s, rgba);
            if (!kittyfb_present(&session, rgba, s.w, s.h)) {
                rc = 1;
                break;
            }
            dirty = 0;
        }
        if (poll(&p, 1, 100) <= 0)
            continue;
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

int main(int argc, char **argv)
{
    const char *weights = "weights/neuronte-ascii-v0.nrt";
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
        if ((rc = neuronte_open_file(weights, &n)) != NEURONTE_OK) {
            fprintf(stderr, "%s: cannot load weights (%d)\n", weights, rc);
            return 1;
        }
        rc = snapshot(n, argv[2], w, h);
        neuronte_close(n);
        return rc;
    }
    if (argc == 2)
        weights = argv[1];
    if ((rc = neuronte_open_file(weights, &n)) != NEURONTE_OK) {
        fprintf(stderr, "%s: cannot load weights (%d)\n", weights, rc);
        return 1;
    }
#ifdef NEURONTE_DEMO_NO_TERMINAL
    fprintf(stderr, "built without kitty-framebuffer; only --snapshot works\n");
    rc = 2;
#else
    rc = run(n);
#endif
    neuronte_close(n);
    return rc;
}
