/* Fused RGB24 composition through cached binary neural ink selections. */
#include "neuronte.h"
#include <string.h>

static int frame_span(int width, int height, size_t stride, size_t *span)
{
    if (width <= 0 || height <= 0 || (size_t)width > SIZE_MAX / 3)
        return 0;
    size_t row = (size_t)width * 3;
    if (stride < row || (size_t)(height - 1) > (SIZE_MAX - row) / stride)
        return 0;
    *span = (size_t)(height - 1) * stride + row;
    return 1;
}

int neuronte_video_rgb24(const uint8_t *src, size_t src_bytes, size_t src_stride,
                        uint8_t *dst, size_t dst_bytes, size_t dst_stride,
                        int width, int height, const uint8_t ink_indices[8])
{
    size_t input, output;
    if (!src || !dst || !ink_indices ||
        !frame_span(width, height, src_stride, &input) ||
        !frame_span(width, height, dst_stride, &output) ||
        src_bytes < input || dst_bytes < output)
        return NEURONTE_ERR_ARG;
    uintptr_t s = (uintptr_t)src, d = (uintptr_t)dst;
    if (input > UINTPTR_MAX - s || output > UINTPTR_MAX - d ||
        (s < d + output && d < s + input))
        return NEURONTE_ERR_ARG;
    uint8_t indices[8];
    for (int i = 0; i < 8; ++i) {
        if (ink_indices[i] > 7)
            return NEURONTE_ERR_ARG;
        indices[i] = ink_indices[i];
    }

    /* Palette rows use Gray labels 0,1,3,2. The map comes from the actual
     * neural masks; it is not replaced by a geometric identity assumption. */
    static const int row_of_ink[4] = {0, 1, 3, 2};
    for (int y = 0; y < height; ++y) {
        int base_y = y - y % 4;
        int k0 = indices[(y % 4) * 2], k1 = indices[(y % 4) * 2 + 1];
        int y0 = base_y + row_of_ink[k0 >> 1];
        int y1 = base_y + row_of_ink[k1 >> 1];
        if (y0 >= height) y0 = height - 1;
        if (y1 >= height) y1 = height - 1;
        const uint8_t *a = src + (size_t)y0 * src_stride;
        const uint8_t *b = src + (size_t)y1 * src_stride;
        uint8_t *out = dst + (size_t)y * dst_stride;
        if (y0 == y1 && !(k0 & 1) && (k1 & 1)) {
            /* The learned selections preserve this row's column order.
             * Row remapping still follows the model, including edge clamps. */
            memcpy(out, a, (size_t)width * 3);
            continue;
        }
        int x = 0;
        for (; x < width - 1; x += 2) {
            size_t at = (size_t)x * 3;
            const uint8_t *p = a + at + (k0 & 1) * 3;
            const uint8_t *q = b + at + (k1 & 1) * 3;
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
