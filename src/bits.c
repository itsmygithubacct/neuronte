/* Packed text masks: 32-bit pixels to 1-bit or 8-bit rows, and kept 1-bit
 * letters laid into a line. No net runs here. MIT licence. See LICENSE. */
#include <string.h>

#include "neuronte.h"

static int sized(int stride, int width, int height)
{
    return width > 0 && height > 0 && stride >= width && width <= NEURONTE_MAX_CELL * 64 &&
           height <= NEURONTE_MAX_CELL;
}

int neuronte_bits_pack(const uint32_t *pixels, int stride, int width, int height, uint8_t *out,
                       size_t out_len)
{
    size_t row_bytes;
    int x, y;

    if (!pixels || !out || !sized(stride, width, height))
        return NEURONTE_ERR_ARG;
    row_bytes = ((size_t)width + 7) / 8;
    if (out_len < row_bytes * (size_t)height)
        return NEURONTE_ERR_ARG;
    memset(out, 0, row_bytes * (size_t)height);
    for (y = 0; y < height; y++) {
        const uint32_t *src = pixels + (size_t)y * (size_t)stride;
        uint8_t *dst = out + (size_t)y * row_bytes;
        for (x = 0; x < width; x++)
            if (src[x])
                dst[x >> 3] |= (uint8_t)(0x80u >> (x & 7));
    }
    return NEURONTE_OK;
}

int neuronte_alpha_pack(const uint32_t *pixels, int stride, int width, int height, uint8_t *out,
                        size_t out_len)
{
    int x, y;

    if (!pixels || !out || !sized(stride, width, height))
        return NEURONTE_ERR_ARG;
    if (out_len < (size_t)width * (size_t)height)
        return NEURONTE_ERR_ARG;
    for (y = 0; y < height; y++) {
        const uint32_t *src = pixels + (size_t)y * (size_t)stride;
        uint8_t *dst = out + (size_t)y * (size_t)width;
        for (x = 0; x < width; x++)
            dst[x] = (uint8_t)(src[x] >> 24);
    }
    return NEURONTE_OK;
}

/* OR one letter's rows into the line with its left edge at column pen. */
static void lay(uint8_t *out, size_t out_row, const uint8_t *cell, int width, int rows, int pen)
{
    size_t cell_row = ((size_t)width + 7) / 8, first = (size_t)pen >> 3, j;
    unsigned shift = (unsigned)pen & 7u;
    /* Bits past the letter's width in its last byte are not ink. */
    uint8_t last = (uint8_t)(0xFFu << ((8u - ((unsigned)width & 7u)) & 7u));
    int y;

    for (y = 0; y < rows; y++) {
        const uint8_t *src = cell + (size_t)y * cell_row;
        uint8_t *dst = out + (size_t)y * out_row + first;
        for (j = 0; j < cell_row; j++) {
            unsigned v = src[j];
            if (j + 1 == cell_row)
                v &= last;
            if (!v)
                continue;
            dst[j] |= (uint8_t)(v >> shift);
            if (shift && (uint8_t)(v << (8u - shift)))
                dst[j + 1] |= (uint8_t)(v << (8u - shift));
        }
    }
}

int neuronte_bits_compose(uint8_t *out, size_t out_len, int out_width, int rows,
                          const uint8_t *atlas, size_t atlas_len, const neuronte_bits_cell *cells,
                          size_t cell_count, const uint32_t *text, size_t text_len, int bold)
{
    size_t out_row, i;
    long pen = 0;

    if (!out || out_width <= 0 || rows <= 0 || out_width > NEURONTE_MAX_CELL * 64 ||
        rows > NEURONTE_MAX_CELL || (!text && text_len) || (!cells && cell_count) ||
        (!atlas && atlas_len))
        return NEURONTE_ERR_ARG;
    out_row = ((size_t)out_width + 7) / 8;
    if (out_len < out_row * (size_t)rows)
        return NEURONTE_ERR_ARG;
    /* Check the whole string first, so that an error writes nothing. */
    for (i = 0; i < text_len; i++) {
        const neuronte_bits_cell *c;
        size_t bytes;
        if (text[i] >= cell_count)
            return NEURONTE_ERR_ARG;
        c = &cells[text[i]];
        bytes = (((size_t)c->width + 7) / 8) * (size_t)rows;
        if (c->width && (c->offset > atlas_len || bytes > atlas_len - c->offset ||
                         pen + c->width + (bold ? 1 : 0) > out_width))
            return NEURONTE_ERR_ARG;
        pen += bold ? c->bold_advance : c->advance;
        if (pen > out_width)
            return NEURONTE_ERR_ARG;
    }
    memset(out, 0, out_row * (size_t)rows);
    pen = 0;
    for (i = 0; i < text_len; i++) {
        const neuronte_bits_cell *c = &cells[text[i]];
        if (c->width) {
            lay(out, out_row, atlas + c->offset, c->width, rows, (int)pen);
            if (bold)
                lay(out, out_row, atlas + c->offset, c->width, rows, (int)pen + 1);
        }
        pen += bold ? c->bold_advance : c->advance;
    }
    return (int)pen;
}
