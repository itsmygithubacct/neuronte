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
 * calls keep up to 1,024 cells' coverage inside it, dropping the least
 * recently used. neuronte_coverage() does not touch that cache.
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
 * which the file states, and in which characters were trained. A file
 * may also be a bundle of several nets with a router that sends each
 * scalar to one of them; the calls below work the same on it.
 *
 * Two more kinds of file open the same way. An advance table holds the
 * pen steps of a proportional face and no net. A drawing file holds
 * nets and at most one advance table; a scalar is drawn by its first
 * net, and a colour net in it is left out, because this library does
 * not read one yet. */
int neuronte_open(const void *data, size_t len, neuronte **out);
int neuronte_open_file(const char *path, neuronte **out);
void neuronte_close(neuronte *n);

/* The number of weights and biases, over all nets and the router's gate,
 * or 0 for NULL. */
size_t neuronte_parameters(const neuronte *n);

/* How many nets the file holds: 1, or more for a bundle. 0 for NULL, and
 * for an advance table by itself, whose handle measures and cannot draw:
 * the route, coverage and draw calls return NEURONTE_ERR_ARG on it. */
int neuronte_nets(const neuronte *n);

/* Which net draws the scalar, from 0, after the same replacement the draw
 * calls make. NEURONTE_ERR_ARG for NULL. */
int neuronte_route(const neuronte *n, uint32_t scalar);

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

/* Advances, for a proportional face. An advance is how far the pen moves
 * after a character, side bearings included. The file stores it in steps
 * of a hundredth of an em, for a regular and a bold weight (bold 0 or 1).
 * A scalar with no record of its own is measured as the table's fallback
 * scalar, and the caller draws that scalar in its place, so a measured
 * line ends where the drawn one does. Nothing is kerned.
 *
 * neuronte_advances() is the number of records, 0 for a handle with no
 * table. The other calls return NEURONTE_ERR_ARG on such a handle, but
 * neuronte_advance_scalar(), which returns U+FFFD. */
int neuronte_advances(const neuronte *n);

/* The scalar that is measured and drawn for this one: itself, or the
 * fallback. */
uint32_t neuronte_advance_scalar(const neuronte *n, uint32_t scalar);

/* The advance in steps, 10 to 200. */
int neuronte_advance_steps(const neuronte *n, uint32_t scalar, int bold);

/* The advance in whole pixels for an em of em_px pixels, 1 to
 * NEURONTE_MAX_CELL: (steps * em_px + 50) / 100, the nearest pixel, with
 * a tie going to the wider count. */
int neuronte_advance(const neuronte *n, uint32_t scalar, int bold, int em_px);

/* The width of UTF-8 text in pixels: each character's pixel advance,
 * rounded by itself, summed. Ill-formed bytes measure as U+FFFD does. */
int neuronte_text_width(const neuronte *n, const char *text, size_t len, int bold, int em_px);

#ifdef __cplusplus
}
#endif

#endif
