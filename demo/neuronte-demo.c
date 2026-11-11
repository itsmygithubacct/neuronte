/* neuronte-demo: every glyph on the screen drawn by the Neuronte net,
 * shown in a Kilix terminal through kitty-framebuffer.
 *
 *   neuronte-demo [WEIGHTS.nrt]
 *   neuronte-demo --snapshot OUT.ppm [WIDTH HEIGHT] [WEIGHTS.nrt]
 *
 * Type to draw text. Tab changes the size of the typed text, Backspace
 * deletes, Enter starts a new line, Esc or Ctrl-C quits. --snapshot draws
 * the first screen into a PPM file with no terminal. The default weights
 * are neuronte-split, else neuronte-full, else neuronte-ascii. With weights that know box
 * drawing, a panel of it, blocks, Braille and symbols is shown, with two
 * spinners that turn while the demo waits for keys. MIT licence. */
#define _POSIX_C_SOURCE 200809L
#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const int sizes[] = {8, 12, 16, 24, 32, 48};
#define NSIZES ((int)(sizeof sizes / sizeof sizes[0]))

struct state {
    struct typing typed;
    double last_ms;
    int full;  /* the weights draw box drawing, blocks and Braille */
    int frame; /* spinner frame */
};

static const char *panel[] = {
    "╭────┬────╮ "
    "┏━━━━┳━━━━┓ "
    "╔════╦════╗ "
    "┌┄┄┄┄┐  ▁▂▃▄▅▆▇█"
    "▇▆▅▄▃▂▁  ⢀⣀⣤⣶⣿⣿⣶⣤⣀⡀",
    "│ ab │ cd │ ┃ ef ┃ gh ┃ ║ ij ║ kl ║ "
    "┆ mn ┆  ▏▎▍▌▋▊▉█  "
    "▖▗▘▙▚▛▜▝▞▟  ⠁⠃⠇⡇⣇⣧⣷⣿",
    "╰────┴────╯ "
    "┗━━━━┻━━━━┛ "
    "╚════╩════╝ "
    "└┄┄┄┄┘  ▀▔▐▕ ╱╲╳╱╲  "
    "⎿ done ✔ ☐ ☒  ░░▒▒▓▓",
    "● ◆ ◈ ◐ ◑ ◉ ◯ ▲ ▼ ▾ ▸ ⏵ ❯ › "
    "← → ↑ ↓ ↗ ⇣ ✻ ✢ ✶ ✽ ✳ · • "
    "… — – ‘’ “” × ≡ ≈ ° ½ © "
    "※ ⁙ ⸬",
};

/* Where the parts that change are. */
struct layout {
    int m, small, spin_y, dyn_y;
};

/* Everything that stays put: drawn once, and again after a resize. The
 * first time takes seconds, so show(), when given, presents each part as
 * it is done. */
static void draw_static(neuronte *n, const struct screen *s, const struct state *st, struct layout *l,
                        int (*show)(const struct screen *))
{
    static const char sample[] = "The quick brown fox jumps over the lazy dog. 0123456789";
    char buf[160], count[32];
    int m = s->w / 40 < 12 ? 12 : s->w / 40, y = m, i;
    int small = s->w >= 1100 ? 10 : 8;

    fill(s, 0, 0, s->w, s->h, BG);
    y = line(n, s, m, y, s->w >= 1100 ? 40 : 28,
             neuronte_nets(n) > 1 ? "Neuronte split" : st->full ? "Neuronte full" : "Neuronte", INK);
    thousands(neuronte_parameters(n), count);
    if (neuronte_nets(n) > 1)
        snprintf(buf, sizeof buf, "Every glyph on this screen is drawn by %d neural nets, %s weights in all. No font file.",
                 neuronte_nets(n), count);
    else
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
        y = row(n, s, m + 7 * small, y, sizes[i], sample, INK);
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
            y = row(n, s, m, y, 16, panel[i], ACCENT);
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
static void draw_dynamic(neuronte *n, const struct screen *s, const struct state *st, const struct layout *l)
{
    const struct typing *t = &st->typed;
    char buf[160];
    int m = l->m, small = l->small, y = l->dyn_y, cx, cy, cw = sizes[t->size_index];

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
    text(n, s, m, y, s->w - m, cw, t->text, t->len, INK, &cx, &cy);
    fill(s, cx, cy + 2 * cw - (cw > 12 ? 3 : 2), cx + cw, cy + 2 * cw, ACCENT);

    snprintf(buf, sizeof buf, "Tab: text size   Esc: quit   last frame %.1f ms", st->last_ms);
    line(n, s, m, s->h - 2 * small - m / 2, small, buf, DIM);
}

static int snapshot(neuronte *n, const char *out, int w, int h)
{
    struct screen s = {malloc((size_t)w * h * sizeof(uint32_t)), w, h, w};
    struct state st = {.typed.size_index = 3, .full = knows_blocks(n), .frame = 2};
    const char typed[] = "Hello, Kilix!\nTyped text is drawn the same way.";
    struct layout l;
    double t0, first;
    int rc;

    if (!s.px)
        return 1;
    memcpy(st.typed.text, typed, sizeof typed - 1);
    st.typed.len = sizeof typed - 1;
    t0 = now_ms();
    draw_static(n, &s, &st, &l, NULL);
    draw_dynamic(n, &s, &st, &l);
    first = now_ms() - t0;
    /* Again, as a keypress would, with the time of that frame shown. */
    t0 = now_ms();
    draw_dynamic(n, &s, &st, &l);
    st.last_ms = now_ms() - t0;
    draw_dynamic(n, &s, &st, &l);
    rc = write_ppm(&s, out);
    if (rc == 0)
        printf("%s: %dx%d, first draw %.1f ms, next %.1f ms\n", out, w, h, first, st.last_ms);
    free(s.px);
    return rc == 0 ? 0 : 1;
}

static int run(neuronte *n)
{
    struct screen s;
    struct state st = {.typed.size_index = 2, .full = knows_blocks(n)};
    struct layout l;
    int dirty = 1, fresh = 1, rc = 0;

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
            dirty = fresh = 1;
        if (dirty) {
            double t0 = now_ms();
            if (fresh)
                draw_static(n, &s, &st, &l, term_show);
            fresh = 0;
            draw_dynamic(n, &s, &st, &l);
            st.last_ms = now_ms() - t0;
            if (term_show(&s) != 0) {
                rc = 1;
                break;
            }
            dirty = 0;
        }
        got = term_read(b, sizeof b, 100);
        if (got == 0) {
            if (st.full) {
                st.frame++;
                dirty = 1;
            }
            continue;
        }
        if (typing_input(&st.typed, NSIZES, b, (size_t)got))
            break;
        dirty = 1;
    }
    term_stop(&s);
    return rc;
}

/* Open the named weights, or by default the first of these that loads. */
static int open_weights(const char *path, neuronte **n)
{
    static const char *const defaults[] = {"weights/neuronte-split-v3.nrt", "weights/neuronte-full-v2.nrt",
                                           "weights/neuronte-ascii-v0.nrt"};
    int rc = NEURONTE_ERR_ARG;
    size_t i;
    if (path)
        rc = neuronte_open_file(path, n);
    for (i = 0; !path && i < sizeof defaults / sizeof defaults[0]; i++) {
        rc = neuronte_open_file(defaults[i], n);
        if (rc == NEURONTE_OK || i + 1 == sizeof defaults / sizeof defaults[0])
            path = defaults[i];
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
    rc = run(n);
    neuronte_close(n);
    return rc;
}
