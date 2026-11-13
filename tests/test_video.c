#include "neuronte.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

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
    memset(dst, 0xa5, sizeof(dst));
    assert(neuronte_video_rgb24(src, 1, 16, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), 8, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), SIZE_MAX, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    assert(neuronte_video_rgb24(src, sizeof(src), 16, src+1, sizeof(src)-1, 16, 3, 3, map) == NEURONTE_ERR_ARG);
    map[7] = 8;
    assert(neuronte_video_rgb24(src, sizeof(src), 16, dst, sizeof(dst), 17, 3, 3, map) == NEURONTE_ERR_ARG);
    for (size_t i = 0; i < sizeof(dst); ++i) assert(dst[i] == 0xa5);
    puts("video compositor: odd edges, learned selection, strides, bounds and overlap passed");
    return 0;
}
