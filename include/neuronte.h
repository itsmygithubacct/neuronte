/* Neuronte: a neural net that is its own font.
 *
 * A character goes in as a Unicode scalar, or as ASCII or UTF-8 text.
 * The net fills that character's cell in a pixel buffer the caller owns.
 * No font file, glyph table or atlas is consulted. The weights are the font.
 *
 * Pixels are row-major uint32_t, 0xAARRGGBB, the soft-raster layout.
 * Neuronte never allocates the screen, opens a window or takes a terminal.
 *
 * A handle is not safe to share between threads without a lock: the draw
 * calls fill a small coverage cache inside it. neuronte_coverage() does not
 * touch the cache.
 *
 * MIT licence. See LICENSE.
 */
#ifndef NEURONTE_H
#define NEURONTE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct neuronte neuronte;

enum {
    NEURONTE_OK = 0,
    NEURONTE_ERR_ARG = -1,    /* a null pointer or a size out of range */
    NEURONTE_ERR_FORMAT = -2, /* not a Neuronte weight file, or damaged */
    NEURONTE_ERR_SHAPE = -3,  /* a weight file for a different net shape */
    NEURONTE_ERR_NOMEM = -4,
    NEURONTE_ERR_IO = -5
};

#define NEURONTE_REPLACEMENT 0xFFFDu

/* The largest cell side, in pixels, and the most samples per pixel axis. */
#define NEURONTE_MAX_CELL 4096
#define NEURONTE_MAX_SAMPLES 8

/* Load weights from memory (the bytes are copied) or from a file. The
 * same calls load any of the weight files: they differ in hidden width,
 * which the file states, and in which characters were trained. */
int neuronte_open(const void *data, size_t len, neuronte **out);
int neuronte_open_file(const char *path, neuronte **out);
void neuronte_close(neuronte *n);

/* The number of weights and biases in the loaded net, or 0 for NULL. */
size_t neuronte_parameters(const neuronte *n);

/* Decode one Unicode scalar from the front of s. Returns the number of
 * bytes consumed, which is at least 1 when len > 0, and 0 when len is 0.
 * An ASCII byte decodes to itself. Ill-formed UTF-8 decodes to U+FFFD and
 * consumes the longest prefix that could have started a valid sequence
 * (Unicode's "maximal subpart" rule), so a bad byte never eats the next
 * character. Surrogates and values above U+10FFFF are ill-formed. */
size_t neuronte_utf8_decode(const char *s, size_t len, uint32_t *scalar);

/* Samples per pixel along each axis for the draw calls. 0 is automatic:
 * 2 when the cell is narrower than 24 pixels, else 1. */
int neuronte_set_samples(neuronte *n, int per_axis);

/* Coverage of one character's cell, cell_w * cell_h floats in 0..1,
 * row-major. samples_per_axis 0 is automatic as above. A surrogate or a
 * value above U+10FFFF is drawn as U+FFFD. The cell is the net's 1 x 2
 * design cell scaled to cell_w x cell_h; another aspect stretches it. */
int neuronte_coverage(const neuronte *n, uint32_t scalar, int cell_w, int cell_h,
                      int samples_per_axis, float *coverage);

/* Blend one character into the buffer in colour 0xAARRGGBB, with its cell's
 * top-left corner at (x, y). stride is in pixels. Pixels outside the buffer
 * are skipped, so a cell may hang off any edge. */
int neuronte_draw_scalar(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                         int x, int y, int cell_w, int cell_h, uint32_t scalar, uint32_t color);

/* Draw text left to right, one cell per scalar, starting at (x, y). ASCII
 * and UTF-8 give the same cells for the same scalars. Nothing is done about
 * line breaks or wide characters. Returns the number of cells, or an error. */
int neuronte_draw_utf8(neuronte *n, uint32_t *pixels, int stride, int width, int height,
                       int x, int y, int cell_w, int cell_h, const char *text, size_t len,
                       uint32_t color);

#ifdef __cplusplus
}
#endif

#endif
