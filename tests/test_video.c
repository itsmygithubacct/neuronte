#include "neuronte.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint32_t state = 20261113u;
static uint32_t next(void) { state = state * 1664525u + 1013904223u; return state >> 8; }

/* Split a packed RGB24 frame into three planes with their own row stride. */
static void split(const uint8_t *rgb, size_t rgb_stride, uint8_t *planes[3], size_t stride,
                  int width, int height)
{
    for (int y = 0; y < height; ++y)
        for (int x = 0; x < width; ++x)
            for (int c = 0; c < 3; ++c)
                planes[c][(size_t)y * stride + (size_t)x] = rgb[(size_t)y * rgb_stride + (size_t)x * 3 + (size_t)c];
}

/* Planar composition must equal packed composition of the same pixels for
 * any learned selection, size, stride and SIMD width or tail. */
static void planar_matches_packed(int width, int height, const uint8_t map[8])
{
    size_t rgb_stride = (size_t)width * 3 + next() % 7, stride = (size_t)width + next() % 5;
    size_t dst_stride = (size_t)width * 3 + next() % 6;
    size_t rgb_bytes = rgb_stride * (size_t)height, plane = stride * (size_t)height;
    size_t dst_bytes = dst_stride * (size_t)height;
    uint8_t *rgb = malloc(rgb_bytes), *buffer = malloc(3 * plane), *packed = malloc(dst_bytes), *planar = malloc(dst_bytes);
    assert(rgb && buffer && packed && planar);
    for (size_t i = 0; i < rgb_bytes; ++i) rgb[i] = (uint8_t)next();
    for (size_t i = 0; i < 3 * plane; ++i) buffer[i] = (uint8_t)next();   /* padding is junk */
    uint8_t *planes[3] = {buffer + 2 * plane, buffer, buffer + plane}; /* R, G, B in gbrp order */
    split(rgb, rgb_stride, planes, stride, width, height);
    memset(packed, 0x5a, dst_bytes);
    memset(planar, 0x5a, dst_bytes);
    assert(neuronte_video_rgb24(rgb, rgb_bytes, rgb_stride, packed, dst_bytes, dst_stride, width, height, map) == NEURONTE_OK);
    assert(neuronte_video_planes_rgb24(planes[0], planes[1], planes[2], plane, stride,
                                       planar, dst_bytes, dst_stride, width, height, map) == NEURONTE_OK);
    assert(memcmp(packed, planar, dst_bytes) == 0);  /* includes untouched row padding */
    for (int y = 0; y < height; ++y)
        for (size_t pad = (size_t)width * 3; pad < dst_stride; ++pad)
            assert(planar[(size_t)y * dst_stride + pad] == 0x5a);
    free(rgb); free(buffer); free(packed); free(planar);
}

int main(void)
{
    uint8_t src[4 * 16], dst[4 * 17], map[8] = {7, 0, 5, 2, 3, 6, 1, 4};
    for (size_t i = 0; i < sizeof(src); ++i) src[i] = (uint8_t)i;
    memset(dst, 0xa5, sizeof(dst));
    assert(neuronte_video_rgb24(src, sizeof(src), 16, dst, sizeof(dst), 17, 3, 3, map) == 0);
    /* Explicit source coordinates for this non-identity fixture, including
     * the odd right edge and bottom replication. No geometric identity. */
    const int x[3][3] = {{1,0,2}, {1,0,2}, {1,0,2}};
    const int y[3][3] = {{2,0,2}, {2,1,2}, {1,2,1}};
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col)
            assert(memcmp(dst + row*17 + col*3, src + y[row][col]*16 + x[row][col]*3, 3) == 0);
        for (int pad = 9; pad < 17; ++pad) assert(dst[row*17 + pad] == 0xa5);
    }
    for (size_t i = 3*17; i < sizeof(dst); ++i) assert(dst[i] == 0xa5);

    /* The same fixture from planes: each output channel comes from the same
     * explicit coordinate in its own plane. */
    uint8_t planes[3][4 * 5];
    for (int c = 0; c < 3; ++c)
        for (int row = 0; row < 4; ++row)
            for (int col = 0; col < 5; ++col)
                planes[c][row * 5 + col] = (uint8_t)(40 * c + 7 * row + col);
    uint8_t out[4 * 11];
    memset(out, 0xa5, sizeof(out));
    assert(neuronte_video_planes_rgb24(planes[0], planes[1], planes[2], sizeof(planes[0]), 5,
                                       out, sizeof(out), 11, 3, 3, map) == NEURONTE_OK);
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col)
            for (int c = 0; c < 3; ++c)
                assert(out[row * 11 + col * 3 + c] == planes[c][y[row][col] * 5 + x[row][col]]);
        for (int pad = 9; pad < 11; ++pad) assert(out[row * 11 + pad] == 0xa5);
    }
    for (size_t i = 3 * 11; i < sizeof(out); ++i) assert(out[i] == 0xa5);

    /* A gray source may pass one plane three times. */
    memset(out, 0, sizeof(out));
    const uint8_t learned[8] = {0, 1, 2, 3, 6, 7, 4, 5};
    assert(neuronte_video_planes_rgb24(planes[1], planes[1], planes[1], sizeof(planes[1]), 5,
                                       out, sizeof(out), 11, 3, 3, learned) == NEURONTE_OK);
    for (int row = 0; row < 3; ++row)
        for (int col = 0; col < 3; ++col)
            for (int c = 0; c < 3; ++c)
                assert(out[row * 11 + col * 3 + c] == planes[1][row * 5 + col]);

    /* Identity-preserving learned maps take the packed-row path; random maps
     * take the gather path. Widths cover SIMD blocks, tails and odd edges. */
    const int sizes[][2] = {{1, 1}, {1, 9}, {2, 5}, {15, 4}, {16, 4}, {17, 7}, {31, 3}, {32, 8},
                            {33, 13}, {47, 6}, {48, 5}, {49, 11}, {945, 531}};
    const uint8_t identity[8] = {0, 1, 2, 3, 6, 7, 4, 5};
    for (size_t s = 0; s < sizeof(sizes) / sizeof(sizes[0]); ++s) {
        planar_matches_packed(sizes[s][0], sizes[s][1], identity);
        planar_matches_packed(sizes[s][0], sizes[s][1], map);
        for (int trial = 0; trial < 6; ++trial) {
            uint8_t random_map[8];
            for (int i = 0; i < 8; ++i) random_map[i] = (uint8_t)(next() % 8);
            planar_matches_packed(sizes[s][0], sizes[s][1], random_map);
        }
    }

    memset(dst, 0xa5, sizeof(dst));
    assert(neuronte_video_rgb24(src, 1, 16, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), 8, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), SIZE_MAX, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), 16, src+1, sizeof(src)-1, 16, 3, 3, map) == NEURONTE_ERR_ARG);
    map[7] = 8;
    assert(neuronte_video_rgb24(src, sizeof(src), 16, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    for (size_t i = 0; i < sizeof(dst); ++i) assert(dst[i] == 0xa5);

    /* Planar rejections leave the output untouched. */
    map[7] = 4;
    memset(out, 0xa5, sizeof(out));
    const uint8_t *r = planes[0], *g = planes[1], *b = planes[2];
    assert(neuronte_video_planes_rgb24(NULL, g, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, NULL, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, NULL, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, NULL, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, 3, NULL) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, 2 * 5 + 2, 5, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);  /* one byte short */
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 2, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), SIZE_MAX, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, 2 * 11 + 8, 11, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, sizeof(out), 8, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 0, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, -1, map) == NEURONTE_ERR_ARG);
    map[3] = 9;
    assert(neuronte_video_planes_rgb24(r, g, b, sizeof(planes[0]), 5, out, sizeof(out), 11, 3, 3, map) == NEURONTE_ERR_ARG);
    map[3] = 2;
    for (size_t i = 0; i < sizeof(out); ++i) assert(out[i] == 0xa5);
    /* The output may not overlap any input plane, wherever it lies. */
    uint8_t shared[64 + 3 * 20];
    memset(shared, 0x33, sizeof(shared));
    for (int plane = 0; plane < 3; ++plane) {
        const uint8_t *p[3] = {shared + 64, shared + 64, shared + 64};
        p[plane] = shared + 30;   /* overlaps out = shared[0..31] */
        assert(neuronte_video_planes_rgb24(p[0], p[1], p[2], 20, 5, shared, 32, 11, 3, 3, map) == NEURONTE_ERR_ARG);
    }
    for (size_t i = 0; i < sizeof(shared); ++i) assert(shared[i] == 0x33);
    puts("video compositor: packed and planar odd edges, learned selection, strides, bounds and overlap passed");
    return 0;
}
