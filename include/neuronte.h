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
 * calls keep up to 1,024 cells inside it, dropping the least recently
 * used. A cell is keyed by its scalar, size, sample count and whether
 * snapping is on. The entry holds one coverage mask per layer and the
 * palette index of each layer. Theme and the caller's colour are applied
 * when those masks are composited, so changing them keeps the cache.
 * neuronte_coverage() and neuronte_coverage_layers() do not touch it.
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
 * scalar to one of them; the calls below work the same on it. */
int neuronte_open(const void *data, size_t len, neuronte **out);
int neuronte_open_file(const char *path, neuronte **out);
void neuronte_close(neuronte *n);

/* The number of weights and biases, over all nets and the router's gate,
 * or 0 for NULL. A colour net counts its trunk and its palette head. */
size_t neuronte_parameters(const neuronte *n);

/* How many nets the file holds: 1, or more for a bundle. 0 for NULL. */
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

/* The most layers a glyph in this file can have, at least 1. A file of
 * distance nets returns 1. 0 for NULL. */
int neuronte_layers(const neuronte *n);

/* 0 is the dark palette, 1 the light one. The handle starts on dark.
 * The masks do not depend on the theme, so the draw cache stays. */
int neuronte_set_theme(neuronte *n, int theme);

/* Snap the straight edges of a colour glyph when the cell is narrower
 * than below_px pixels. 0 turns snapping off. -1 restores the number
 * stored in the file, which is off for a file with no colour net. A
 * positive value replaces the threshold. The test is cell_w < threshold.
 * Letters and box drawing have no edge record, so they are not snapped. */
int neuronte_set_snap(neuronte *n, int below_px);

/* Copy one theme's palette into rgb, 32 entries of R, G, B. Entry 0 and
 * entry 1 are stored as 0, 0, 0: entry 0 is the caller's colour and entry
 * 1 is clear. A file with no colour net copies zeros. */
int neuronte_palette(const neuronte *n, int theme, uint8_t *rgb);

/* Coverage of one character's cell, cell_w * cell_h floats in 0..1,
 * row-major. samples_per_axis 0 is automatic as above. A surrogate or a
 * value above U+10FFFF is drawn as U+FFFD. The cell is the net's 1 x 2
 * design cell scaled to cell_w x cell_h; another aspect stretches it.
 * A colour glyph returns the alpha of its layers composited back to front. */
int neuronte_coverage(const neuronte *n, uint32_t scalar, int cell_w, int cell_h,
                      int samples_per_axis, float *coverage);

/* One mask per layer and one palette index per layer. masks holds
 * neuronte_layers() masks of cell_h * cell_w floats, layer 0 (the back)
 * first. entries holds that many indices. The caller sizes both from
 * neuronte_layers(). samples_per_axis 0 is automatic, as above.
 * A distance net fills mask 0 with the coverage neuronte_coverage()
 * returns, writes 0 in the other masks, and writes entry 0.
 * An index of 32 or more is not a colour; drawing paints it as entry 0.
 * This call does not use the draw cache. */
int neuronte_coverage_layers(const neuronte *n, uint32_t scalar, int cell_w, int cell_h,
                             int samples_per_axis, float *masks, uint8_t *entries);

/* Blend one character into the buffer in colour 0xAARRGGBB, with its cell's
 * top-left corner at (x, y). stride is in pixels. Pixels outside the buffer
 * are skipped, so a cell may hang off any edge. A colour glyph is composited
 * back to front first: entry 1 clears, entry 0 uses this call's RGB, and
 * any other entry uses the theme's palette. The call's alpha then scales
 * the whole glyph, and the pixel is blended as a distance glyph is. A pixel
 * the glyph left clear is not written. */
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
