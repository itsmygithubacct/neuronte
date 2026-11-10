/* What the Neuronte demos share: drawing text into a view of a pixel
 * buffer, typing, PPM snapshots, and the terminal through
 * kitty-framebuffer. MIT licence. */
#ifndef NEURONTE_DEMO_COMMON_H
#define NEURONTE_DEMO_COMMON_H

#include <stddef.h>
#include <stdint.h>

#include "neuronte.h"

#define BG 0xFF11151Cu
#define INK 0xFFE9E6DFu
#define DIM 0xFF8A93A3u
#define ACCENT 0xFF7FB4FFu
#define RULE 0xFF2A3140u

/* w x h pixels, rows stride pixels apart. A view may be part of a wider
 * buffer; drawing in it is cut at its edges. */
struct screen {
    uint32_t *px;
    int w, h, stride;
};

/* Columns x .. x + w of s, cut to s. */
struct screen sub_screen(const struct screen *s, int x, int w);

/* What has been typed, and which of the sizes it is drawn at. */
struct typing {
    char text[4096];
    size_t len;
    int size_index;
};

/* Ten frames each. */
extern const char braille_spin[];
extern const char star_spin[];

double now_ms(void);
void fill(const struct screen *s, int x0, int y0, int x1, int y1, uint32_t c);

/* Draw UTF-8 text in cells cw x 2cw from (x, y), wrapping at right and at
 * newlines. Returns the y below the last line. caret_x and caret_y, if
 * given, get where the next cell would go. */
int text(neuronte *n, const struct screen *s, int x, int y, int right, int cw, const char *t,
         size_t len, uint32_t color, int *caret_x, int *caret_y);
/* One string, wrapped at the view's edge. */
int line(neuronte *n, const struct screen *s, int x, int y, int cw, const char *t, uint32_t color);
/* One string, never wrapped: what does not fit is cut at the edge. */
int row(neuronte *n, const struct screen *s, int x, int y, int cw, const char *t, uint32_t color);

void nth(const char *t, int k, char *out); /* the k-th UTF-8 character of t */
void thousands(size_t v, char *out);       /* 44801 -> "44,801" */

/* Whether the weights were trained on blocks: a full block fills its cell. */
int knows_blocks(neuronte *n);

/* Apply a chunk of terminal input. Tab steps through nsizes sizes.
 * Returns 1 for Esc or Ctrl-C. */
int typing_input(struct typing *t, int nsizes, const unsigned char *b, size_t n);

int write_ppm(const struct screen *s, const char *path);

/* The terminal. term_start takes it and gives s a buffer of its size.
 * term_resized returns 1 when the size changed and s was reallocated, 0
 * when not, -1 on failure. term_read waits up to timeout_ms and returns
 * the bytes read, 0 for none. All but term_stop return -1 on failure. */
int term_start(struct screen *s);
int term_resized(struct screen *s);
int term_show(const struct screen *s);
int term_read(unsigned char *b, size_t cap, int timeout_ms);
void term_stop(struct screen *s);

#endif
