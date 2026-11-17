/* Cells files: coverage a program would otherwise ask a net for at its
 * first use of a character, drawn once and kept in a file that every
 * process maps read-only.
 *
 * The library's own cache belongs to one handle in one process. A cells
 * file is the same floats neuronte_coverage_styled() writes, for the
 * characters, cells and styles its maker chose, so a hit is bit for bit
 * what a miss would compute and a caller may mix the two freely:
 *
 *     const float *kept = cells ? neuronte_cells_find(cells, scalar, w, h, 0, style,
 *                                                     NEURONTE_CELLS_SNAP_FILE) : NULL;
 *     if (!kept)
 *         return neuronte_coverage_styled(n, scalar, w, h, 0, style, out);
 *     memcpy(out, kept, (size_t)w * h * sizeof *out);
 *     return NEURONTE_OK;
 *
 * neuronte_coverage() writes what neuronte_coverage_styled() writes for
 * style 0, so the same file answers for it.
 *
 * What a cells file answers for. An entry's key is everything that changes
 * the bytes neuronte_coverage_styled() writes:
 *   - the scalar, after the U+FFFD replacement the library makes;
 *   - cell_w and cell_h;
 *   - samples per axis as the caller passes it (0, the library's own
 *     choice, is a key of its own: it is not matched with the number the
 *     library would choose);
 *   - the style bits;
 *   - the handle's snap threshold (neuronte_set_snap()). One file is made
 *     under one threshold, kept in its header, and neuronte_cells_find()
 *     answers only a caller that names the same one. A file made by
 *     neuronte-setup is made under the weight file's own threshold,
 *     NEURONTE_CELLS_SNAP_FILE: a handle neuronte_set_snap() was never
 *     called on, or was last called on with -1.
 * A file holds only characters its weight file is trained on
 * (neuronte_untrained() is 0), and those are drawn the same whatever
 * neuronte_set_untrained() says, so that setting is not in the key; the
 * untrained mark is never in a file. The other handle settings
 * (neuronte_set_binary(), neuronte_set_theme(), neuronte_set_samples())
 * change the draw calls only, not the coverage calls.
 *
 * A cells file belongs to one weight file. Its header holds that file's
 * size, modification time and SHA-256, and neuronte_cells_open() refuses a
 * cells file made from other weights.
 *
 * The file, version 1, kind 1 (coverage). Integers are little-endian.
 *     0   8  "NRTCELLS"
 *     8   4  version, 1
 *    12   4  kind, 1: one plane of coverage for each entry
 *    16   4  header bytes, 128
 *    20   4  entry bytes, 16
 *    24   8  entries
 *    32   8  floats in the data
 *    40   8  bytes in the whole file
 *    48   8  the weight file's bytes
 *    56   8  the weight file's modification time, seconds
 *    64   4  and nanoseconds
 *    68   4  the snap threshold it was made under, -1 for the weight file's
 *    72   4  the float 1.0 as the data stores floats (00 00 80 3F)
 *    76   4  zero
 *    80  32  the weight file's SHA-256
 *   112   8  a check of bytes 0..111 and the whole index: 64-bit FNV-1a
 *   120   8  zero
 *   128      the index: for each entry scalar (4), cell_w (2), cell_h (2),
 *            samples (1), style (1), zero (2), and the place of its first
 *            float in the data, counted in floats (4). Entries are in
 *            rising order of cell_w, cell_h, samples, style, scalar, no two
 *            alike, and their data follows in the same order with no gaps.
 *   then     the data: cell_w * cell_h floats for each entry, rows from the
 *            top, exactly as neuronte_coverage_styled() writes them.
 * Another kind (colour: for each half of a glyph, its layers and their
 * palette entries) would be another kind number with its own entry and
 * data layout; version 1 readers refuse a kind they do not know.
 *
 * MIT licence. See LICENSE. */
#ifndef NEURONTE_CELLS_H
#define NEURONTE_CELLS_H

#include <stddef.h>
#include <stdint.h>

#include "neuronte.h"

#ifdef __cplusplus
extern "C" {
#endif

#define NEURONTE_CELLS_VERSION 1
/* The snap threshold a weight file carries: what a handle has until
 * neuronte_set_snap() is called with another number. */
#define NEURONTE_CELLS_SNAP_FILE (-1)

/* Flags of neuronte_cells_open(). */
#define NEURONTE_CELLS_VERIFY 1u /* hash the weight file even when its size and time match */
#define NEURONTE_CELLS_COPY 2u   /* read the cells file into memory in place of mapping it */

typedef struct neuronte_cells neuronte_cells;

struct neuronte_cells_key {
    uint32_t scalar;
    uint16_t cell_w, cell_h;
    uint8_t samples; /* per axis, as passed to the coverage call; 0 is the library's choice */
    uint8_t style;   /* NEURONTE_STYLE_BOLD | NEURONTE_STYLE_ITALIC */
};

/* Open a cells file made from the weight file at weights_path.
 *
 * The header and the index are checked as a whole (a file with any byte
 * of them changed is refused), and every field and every entry is then
 * checked against the size of the file before anything is used, so no
 * later call reads outside the file whatever it holds. The floats
 * themselves are not read here: a changed float is not seen.
 *
 * The weight file is compared by size and modification time; only when
 * the time differs, or with NEURONTE_CELLS_VERIFY, is it hashed. A weight
 * file changed with its size and time kept is therefore found only with
 * NEURONTE_CELLS_VERIFY.
 *
 * The file is mapped read-only and shared with every other process that
 * maps it. It must be replaced by renaming a new file over it (as
 * neuronte_cells_write() does), never written in place.
 *
 * NEURONTE_OK; NEURONTE_ERR_IO when a file cannot be read;
 * NEURONTE_ERR_FORMAT for a file that is not a cells file of this version
 * and kind, or is damaged; NEURONTE_ERR_SHAPE for a cells file made from
 * other weights; NEURONTE_ERR_ARG; NEURONTE_ERR_NOMEM. On error *out is
 * NULL. */
int neuronte_cells_open(const char *cells_path, const char *weights_path, unsigned flags,
                        neuronte_cells **out);

/* The kept coverage for one call of neuronte_coverage_styled(n, scalar,
 * cell_w, cell_h, samples_per_axis, style, ...) on a handle whose snap
 * threshold is snap_below: cell_w * cell_h floats that stay valid until
 * neuronte_cells_close(). NULL when the file does not hold that entry, was
 * made under another snap threshold, or an argument is one the coverage
 * call would refuse. Safe to call from several threads at once. */
const float *neuronte_cells_find(const neuronte_cells *c, uint32_t scalar, int cell_w, int cell_h,
                                 int samples_per_axis, unsigned style, int snap_below);

/* How many entries the file holds, and entry number index (from 0, in the
 * file's order) with its key. NULL past the end. */
size_t neuronte_cells_count(const neuronte_cells *c);
const float *neuronte_cells_entry(const neuronte_cells *c, size_t index,
                                  struct neuronte_cells_key *key);

void neuronte_cells_close(neuronte_cells *c);

/* Write a cells file for the weight file at weights_path, which n was
 * opened from, beside its final name and then renamed over it.
 *
 * keys are count entries in any order. cells[i] is the coverage of
 * keys[i], cell_w * cell_h floats that neuronte_coverage_styled() wrote,
 * or cells is NULL and each entry is drawn here with n. snap_below is the
 * threshold n has (NEURONTE_CELLS_SNAP_FILE unless neuronte_set_snap() was
 * called on it). The same entries give the same bytes whatever their
 * order.
 *
 * NEURONTE_ERR_ARG for a key the coverage call would refuse, a scalar the
 * weight file is not trained on or that the library would replace, two
 * keys alike, or a float outside 0..1; NEURONTE_ERR_IO; NEURONTE_ERR_NOMEM.
 * On error the old file, if any, is left as it was. */
int neuronte_cells_write(const char *cells_path, const char *weights_path, const neuronte *n,
                         int snap_below, const struct neuronte_cells_key *keys,
                         const float *const *cells, size_t count);

#ifdef __cplusplus
}
#endif

#endif
