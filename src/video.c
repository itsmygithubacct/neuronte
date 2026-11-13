/* Fused RGB24 composition through cached binary neural ink selections. */
#include "neuronte.h"
#include <string.h>

/* NRT_VIDEO_PORTABLE builds only the scalar paths, so tests can compare them. */
#if defined(__GNUC__) && (defined(__x86_64__) || defined(__i386__)) && !defined(NRT_VIDEO_PORTABLE)
#include <tmmintrin.h>
#define NRT_VIDEO_SSSE3 1
#endif

static int frame_span(int width, int height, size_t bytes_per_pixel, size_t stride, size_t *span)
{
    if (width <= 0 || height <= 0 || (size_t)width > SIZE_MAX / bytes_per_pixel)
        return 0;
    size_t row = (size_t)width * bytes_per_pixel;
    if (stride < row || (size_t)(height - 1) > (SIZE_MAX - row) / stride)
        return 0;
    *span = (size_t)(height - 1) * stride + row;
    return 1;
}

/* Byte ranges [a, a + a_len) and [b, b + b_len) share at least one byte, or
 * cannot be represented. */
static int overlaps(const void *a, size_t a_len, const void *b, size_t b_len)
{
    uintptr_t x = (uintptr_t)a, y = (uintptr_t)b;
    if (a_len > UINTPTR_MAX - x || b_len > UINTPTR_MAX - y)
        return 1;
    return x < y + b_len && y < x + a_len;
}

static int copy_indices(const uint8_t ink_indices[8], uint8_t indices[8])
{
    for (int i = 0; i < 8; ++i) {
        if (ink_indices[i] > 7)
            return 0;
        indices[i] = ink_indices[i];
    }
    return 1;
}

/* The source rows and column offsets that one output row takes, from the
 * actual learned selections; it is not replaced by a geometric identity
 * assumption. Palette rows use Gray labels 0,1,3,2. Rows past the bottom
 * edge clamp, as padding before encode/decode replicates them. */
struct row_selection { int y0, y1, x0, x1, copy; };

static struct row_selection select_row(const uint8_t indices[8], int y, int height)
{
    static const int row_of_ink[4] = {0, 1, 3, 2};
    struct row_selection s;
    int base_y = y - y % 4;
    int k0 = indices[(y % 4) * 2], k1 = indices[(y % 4) * 2 + 1];
    s.y0 = base_y + row_of_ink[k0 >> 1];
    s.y1 = base_y + row_of_ink[k1 >> 1];
    if (s.y0 >= height) s.y0 = height - 1;
    if (s.y1 >= height) s.y1 = height - 1;
    s.x0 = k0 & 1;
    s.x1 = k1 & 1;
    /* Both inks of this row come from one source row in column order. */
    s.copy = s.y0 == s.y1 && !s.x0 && s.x1;
    return s;
}

int neuronte_video_rgb24(const uint8_t *src, size_t src_bytes, size_t src_stride,
                        uint8_t *dst, size_t dst_bytes, size_t dst_stride,
                        int width, int height, const uint8_t ink_indices[8])
{
    size_t input, output;
    uint8_t indices[8];
    if (!src || !dst || !ink_indices ||
        !frame_span(width, height, 3, src_stride, &input) ||
        !frame_span(width, height, 3, dst_stride, &output) ||
        src_bytes < input || dst_bytes < output ||
        overlaps(src, input, dst, output) || !copy_indices(ink_indices, indices))
        return NEURONTE_ERR_ARG;

    for (int y = 0; y < height; ++y) {
        struct row_selection s = select_row(indices, y, height);
        const uint8_t *a = src + (size_t)s.y0 * src_stride;
        const uint8_t *b = src + (size_t)s.y1 * src_stride;
        uint8_t *out = dst + (size_t)y * dst_stride;
        if (s.copy) {
            /* The learned selections preserve this row's column order.
             * Row remapping still follows the model, including edge clamps. */
            memcpy(out, a, (size_t)width * 3);
            continue;
        }
        int x = 0;
        for (; x < width - 1; x += 2) {
            size_t at = (size_t)x * 3;
            const uint8_t *p = a + at + s.x0 * 3;
            const uint8_t *q = b + at + s.x1 * 3;
            out[at] = p[0]; out[at + 1] = p[1]; out[at + 2] = p[2];
            out[at + 3] = q[0]; out[at + 4] = q[1]; out[at + 5] = q[2];
        }
        if (x < width) {
            /* Edge replication agrees with padding before encode/decode. */
            size_t at = (size_t)x * 3;
            out[at] = a[at]; out[at + 1] = a[at + 1]; out[at + 2] = a[at + 2];
        }
    }
    return NEURONTE_OK;
}

static void interleave_scalar(uint8_t *restrict out, const uint8_t *restrict r,
                              const uint8_t *restrict g, const uint8_t *restrict b, int width)
{
    for (int x = 0; x < width; ++x) {
        out[3 * x] = r[x];
        out[3 * x + 1] = g[x];
        out[3 * x + 2] = b[x];
    }
}

#ifdef NRT_VIDEO_SSSE3
/* Byte positions of 16 R, G and B samples within 48 packed output bytes;
 * 0x80 leaves a byte for another channel. */
static const uint8_t interleave_mask[9][16] = {
    {0, 0x80, 0x80, 1, 0x80, 0x80, 2, 0x80, 0x80, 3, 0x80, 0x80, 4, 0x80, 0x80, 5},
    {0x80, 0, 0x80, 0x80, 1, 0x80, 0x80, 2, 0x80, 0x80, 3, 0x80, 0x80, 4, 0x80, 0x80},
    {0x80, 0x80, 0, 0x80, 0x80, 1, 0x80, 0x80, 2, 0x80, 0x80, 3, 0x80, 0x80, 4, 0x80},
    {0x80, 0x80, 6, 0x80, 0x80, 7, 0x80, 0x80, 8, 0x80, 0x80, 9, 0x80, 0x80, 10, 0x80},
    {5, 0x80, 0x80, 6, 0x80, 0x80, 7, 0x80, 0x80, 8, 0x80, 0x80, 9, 0x80, 0x80, 10},
    {0x80, 5, 0x80, 0x80, 6, 0x80, 0x80, 7, 0x80, 0x80, 8, 0x80, 0x80, 9, 0x80, 0x80},
    {0x80, 11, 0x80, 0x80, 12, 0x80, 0x80, 13, 0x80, 0x80, 14, 0x80, 0x80, 15, 0x80, 0x80},
    {0x80, 0x80, 11, 0x80, 0x80, 12, 0x80, 0x80, 13, 0x80, 0x80, 14, 0x80, 0x80, 15, 0x80},
    {10, 0x80, 0x80, 11, 0x80, 0x80, 12, 0x80, 0x80, 13, 0x80, 0x80, 14, 0x80, 0x80, 15},
};

__attribute__((target("ssse3")))
static void interleave_ssse3(uint8_t *restrict out, const uint8_t *restrict r,
                             const uint8_t *restrict g, const uint8_t *restrict b, int width)
{
    int x = 0;
    for (; x + 16 <= width; x += 16) {
        __m128i red = _mm_loadu_si128((const __m128i *)(const void *)(r + x));
        __m128i green = _mm_loadu_si128((const __m128i *)(const void *)(g + x));
        __m128i blue = _mm_loadu_si128((const __m128i *)(const void *)(b + x));
        for (int v = 0; v < 3; ++v) {
            const __m128i *mask = (const __m128i *)(const void *)interleave_mask[3 * v];
            __m128i bytes = _mm_or_si128(
                _mm_or_si128(_mm_shuffle_epi8(red, _mm_loadu_si128(mask)),
                             _mm_shuffle_epi8(green, _mm_loadu_si128(mask + 1))),
                _mm_shuffle_epi8(blue, _mm_loadu_si128(mask + 2)));
            _mm_storeu_si128((__m128i *)(void *)(out + (size_t)x * 3 + 16 * (size_t)v), bytes);
        }
    }
    interleave_scalar(out + (size_t)x * 3, r + x, g + x, b + x, width - x);
}
#endif

int neuronte_video_planes_rgb24(const uint8_t *red, const uint8_t *green, const uint8_t *blue,
                                size_t plane_bytes, size_t src_stride,
                                uint8_t *dst, size_t dst_bytes, size_t dst_stride,
                                int width, int height, const uint8_t ink_indices[8])
{
    size_t input, output;
    uint8_t indices[8];
    if (!red || !green || !blue || !dst || !ink_indices ||
        !frame_span(width, height, 1, src_stride, &input) ||
        !frame_span(width, height, 3, dst_stride, &output) ||
        plane_bytes < input || dst_bytes < output ||
        overlaps(red, input, dst, output) || overlaps(green, input, dst, output) ||
        overlaps(blue, input, dst, output) || !copy_indices(ink_indices, indices))
        return NEURONTE_ERR_ARG;

    void (*interleave)(uint8_t *restrict, const uint8_t *restrict, const uint8_t *restrict,
                       const uint8_t *restrict, int) = interleave_scalar;
#ifdef NRT_VIDEO_SSSE3
    if (__builtin_cpu_supports("ssse3"))
        interleave = interleave_ssse3;
#endif
    for (int y = 0; y < height; ++y) {
        struct row_selection s = select_row(indices, y, height);
        size_t a = (size_t)s.y0 * src_stride, b = (size_t)s.y1 * src_stride;
        uint8_t *out = dst + (size_t)y * dst_stride;
        if (s.copy) {
            /* The same learned column order as the packed copy: pack this
             * source row's planes in one pass. */
            interleave(out, red + a, green + a, blue + a, width);
            continue;
        }
        int x = 0;
        for (; x < width - 1; x += 2) {
            size_t at = (size_t)x * 3, p = a + (size_t)(x + s.x0), q = b + (size_t)(x + s.x1);
            out[at] = red[p]; out[at + 1] = green[p]; out[at + 2] = blue[p];
            out[at + 3] = red[q]; out[at + 4] = green[q]; out[at + 5] = blue[q];
        }
        if (x < width) {
            /* Edge replication agrees with padding before encode/decode. */
            size_t at = (size_t)x * 3, p = a + (size_t)x;
            out[at] = red[p]; out[at + 1] = green[p]; out[at + 2] = blue[p];
        }
    }
    return NEURONTE_OK;
}
