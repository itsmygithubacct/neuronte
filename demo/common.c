/* What the Neuronte demos share. MIT licence. See common.h. */
#define _POSIX_C_SOURCE 200809L
#include "common.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

const char braille_spin[] = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
const char star_spin[] = "·✢✳✶✻✽✻✶✳✢";

struct screen sub_screen(const struct screen *s, int x, int w)
{
    struct screen v = *s;
    if (x < 0) {
        w += x;
        x = 0;
    }
    if (x > s->w)
        x = s->w;
    if (w > s->w - x)
        w = s->w - x;
    v.px = s->px + x;
    v.w = w < 0 ? 0 : w;
    return v;
}

double now_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec * 1e3 + (double)t.tv_nsec * 1e-6;
}

void fill(const struct screen *s, int x0, int y0, int x1, int y1, uint32_t c)
{
    int x, y;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > s->w) x1 = s->w;
    if (y1 > s->h) y1 = s->h;
    for (y = y0; y < y1; y++)
        for (x = x0; x < x1; x++)
            s->px[(size_t)y * s->stride + x] = c;
}

int text(neuronte *n, const struct screen *s, int x, int y, int right, int cw, const char *t,
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
        neuronte_draw_scalar(n, s->px, s->stride, s->w, s->h, cx, y, cw, ch, sc, color);
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

int line(neuronte *n, const struct screen *s, int x, int y, int cw, const char *t, uint32_t color)
{
    return text(n, s, x, y, s->w, cw, t, strlen(t), color, NULL, NULL);
}

int row(neuronte *n, const struct screen *s, int x, int y, int cw, const char *t, uint32_t color)
{
    return text(n, s, x, y, 1 << 20, cw, t, strlen(t), color, NULL, NULL);
}

void nth(const char *t, int k, char *out)
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

void thousands(size_t v, char *out)
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

int knows_blocks(neuronte *n)
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

static void erase_last(struct typing *t)
{
    while (t->len > 0) {
        unsigned char c = (unsigned char)t->text[--t->len];
        if ((c & 0xC0) != 0x80)
            break;
    }
}

int typing_input(struct typing *t, int nsizes, const unsigned char *b, size_t n)
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
            t->size_index = (t->size_index + 1) % nsizes;
        } else if (c == 127 || c == 8) {
            erase_last(t);
        } else if (c == '\r' || c == '\n') {
            if (t->len < sizeof t->text)
                t->text[t->len++] = '\n';
        } else if (c >= 32 && t->len < sizeof t->text) {
            t->text[t->len++] = (char)c;
        }
    }
    return 0;
}

int write_ppm(const struct screen *s, const char *path)
{
    FILE *f = fopen(path, "wb");
    int x, y;
    if (!f) {
        perror(path);
        return -1;
    }
    fprintf(f, "P6\n%d %d\n255\n", s->w, s->h);
    for (y = 0; y < s->h; y++)
        for (x = 0; x < s->w; x++) {
            uint32_t p = s->px[(size_t)y * s->stride + x];
            unsigned char rgb[3] = {(unsigned char)(p >> 16), (unsigned char)(p >> 8), (unsigned char)p};
            fwrite(rgb, 1, 3, f);
        }
    return fclose(f) == 0 ? 0 : -1;
}

#ifndef NEURONTE_DEMO_NO_TERMINAL
#include "kitty_framebuffer.h"

static kittyfb_session session;
static uint8_t *rgba; /* the frame as kitty-framebuffer takes it */

static void on_fatal(int sig)
{
    kittyfb_emergency_restore(&session);
    _exit(128 + sig);
}

static int alloc(struct screen *s, int w, int h)
{
    uint32_t *px = realloc(s->px, (size_t)w * h * sizeof *px);
    uint8_t *rgb;
    if (!px)
        return -1;
    s->px = px;
    rgb = realloc(rgba, (size_t)w * h * 4);
    if (!rgb)
        return -1;
    rgba = rgb;
    s->w = s->stride = w;
    s->h = h;
    return 0;
}

int term_start(struct screen *s)
{
    kittyfb_options opt;
    struct sigaction sa;

    kittyfb_session_init(&session);
    kittyfb_options_init(&opt);
    if (kittyfb_start(&session, STDIN_FILENO, STDOUT_FILENO, &opt) != 0) {
        if (errno == ENOTSUP)
            fprintf(stderr, "this terminal does not speak the Kitty graphics protocol\n");
        else
            fprintf(stderr, "%s\n", strerror(errno));
        return -1;
    }
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_fatal;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);
    s->px = NULL;
    if (alloc(s, kittyfb_width(&session), kittyfb_height(&session)) != 0) {
        term_stop(s);
        return -1;
    }
    return 0;
}

int term_resized(struct screen *s)
{
    int w, h;
    if (!kittyfb_check_resize(&session, &w, &h))
        return 0;
    return alloc(s, w, h) == 0 ? 1 : -1;
}

int term_show(const struct screen *s)
{
    size_t i, count = (size_t)s->w * s->h;
    for (i = 0; i < count; i++) {
        uint32_t p = s->px[i];
        rgba[4 * i] = (uint8_t)(p >> 16);
        rgba[4 * i + 1] = (uint8_t)(p >> 8);
        rgba[4 * i + 2] = (uint8_t)p;
        rgba[4 * i + 3] = 255;
    }
    return kittyfb_present(&session, rgba, s->w, s->h) ? 0 : -1;
}

int term_read(unsigned char *b, size_t cap, int timeout_ms)
{
    struct pollfd p = {STDIN_FILENO, POLLIN, 0};
    ssize_t got;
    if (poll(&p, 1, timeout_ms) <= 0)
        return 0;
    got = read(STDIN_FILENO, b, cap);
    return got > 0 ? (int)got : 0;
}

void term_stop(struct screen *s)
{
    kittyfb_stop(&session);
    free(s->px);
    free(rgba);
    s->px = NULL;
    rgba = NULL;
}

#else

int term_start(struct screen *s)
{
    (void)s;
    fprintf(stderr, "built without kitty-framebuffer; only --snapshot works\n");
    return -1;
}
int term_resized(struct screen *s) { (void)s; return -1; }
int term_show(const struct screen *s) { (void)s; return -1; }
int term_read(unsigned char *b, size_t cap, int timeout_ms) { (void)b; (void)cap; (void)timeout_ms; return 0; }
void term_stop(struct screen *s) { (void)s; }

#endif
