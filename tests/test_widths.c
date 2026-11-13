/* Exercise the last neuron at scalar, vector and tail widths. */
#include "neuronte.h"
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void u32(unsigned char *p, uint32_t value)
{
    for (int i = 0; i < 4; i++) p[i] = (unsigned char)(value >> (8 * i));
}

static void f32(unsigned char *p, float value)
{
    uint32_t bits;
    memcpy(&bits, &value, sizeof bits);
    u32(p, bits);
}

static void check_width(int H)
{
    size_t BYTES = 204 + 4 * (2 * H * H + 94 * H + 1);
    unsigned char *image = calloc(BYTES, 1);
    assert(image);
    neuronte *net = NULL;
    float coverage[128];
    uint32_t canvas[130];
    memcpy(image, "NEURONTE", 8);
    u32(image + 8, 1); u32(image + 12, 6); u32(image + 16, 64);
    u32(image + 20, H); u32(image + 24, 3); f32(image + 28, .15f);
    for (int i = 0; i < 43; i++) u32(image + 32 + 4*i, (uint32_t)i + 1);
    size_t offset = 204 + 4 * H * 90;
    f32(image + offset + 4 * (H-1), 1.f); /* l1 bias */
    offset += 4 * H;
    f32(image + offset + 4 * (H*H-1), 1.f); /* l2 last diagonal */
    offset += 4 * (H*H + H);
    f32(image + offset + 4 * (H*H-1), 1.f); /* l3 last diagonal */
    offset += 4 * (H*H + H);
    f32(image + offset + 4 * (H-1), .125f); /* output last neuron */
    assert(neuronte_open(image, BYTES, &net) == 0 && net);
    for (int samples = 1; samples <= 2; samples++) {
        assert(neuronte_coverage(net, 0x28ff, 8, 16, samples, coverage) == 0);
        float expected = .5f + .15f * 8 * samples * .125f;
        for (int i = 0; i < 128; i++) assert(fabsf(coverage[i] - expected) < 1e-6f);
    }
    assert(neuronte_set_samples(net, 1) == 0);
    for (int pass = 0; pass < 2; pass++) {
        memset(canvas, 0, sizeof canvas);
        canvas[0] = canvas[129] = 0x12345678;
        assert(neuronte_draw_scalar(net, canvas + 1, 8, 8, 16, 0, 0, 8, 16, 0x28ff, UINT32_MAX) == 0);
        for (int i = 1; i <= 128; i++) assert(canvas[i] == 0xa6ffffff);
        assert(canvas[0] == 0x12345678 && canvas[129] == 0x12345678);
    }
    neuronte_close(net);

    /* Exercise an empty active list and a completely full one. The latter
     * reaches the compaction buffer's last slot at the largest block width. */
    size_t l1_bias = 204 + 4 * H * 90;
    size_t l2_weights = l1_bias + 4 * H;
    size_t l3_weights = l2_weights + 4 * (H*H + H);
    for (int active = 0; active <= 1; active++) {
        for (int i = 0; i < H; i++) {
            f32(image + l1_bias + 4 * i, active ? 1.f : 0.f);
            f32(image + l2_weights + 4 * (i*H + i), 1.f);
            f32(image + l3_weights + 4 * (i*H + i), 1.f);
        }
        assert(neuronte_open(image, BYTES, &net) == 0 && net);
        assert(neuronte_coverage(net, 0x28ff, 8, 16, 1, coverage) == 0);
        float expected = active ? .65f : .5f;
        for (int i = 0; i < 128; i++) assert(fabsf(coverage[i] - expected) < 1e-6f);
        neuronte_close(net);
    }
    if (H >= 2) {
        /* Finite weights can overflow into opposing infinities. ReLU must
         * clear the resulting NaN before it reaches the next layer. */
        for (int i = 0; i < H; i++)
            f32(image + l1_bias + 4 * i, i < 2 ? 1e30f : 0.f);
        f32(image + l2_weights + 4 * ((H-1)*H), 1e30f);
        f32(image + l2_weights + 4 * ((H-1)*H + 1), -1e30f);
        assert(neuronte_open(image, BYTES, &net) == 0 && net);
        assert(neuronte_coverage(net, 0x28ff, 8, 16, 1, coverage) == 0);
        for (int i = 0; i < 128; i++) assert(coverage[i] == .5f);
        neuronte_close(net);
    }
    for (int h = 0; h <= 1028; h++) {
        if (h >= 1 && h <= 1024) continue;
        u32(image + 20, (uint32_t)h);
        net = (neuronte *)1;
        assert(neuronte_open(image, BYTES, &net) < 0 && net == NULL);
    }
    u32(image + 20, H);
    assert(neuronte_open(image, BYTES - 1, &net) < 0 && net == NULL);
    free(image);
}

int main(void)
{
    const int widths[] = {1, 2, 3, 4, 6, 8, 12, 15, 17, 20, 48, 63, 64, 65, 128, 192, 255, 256, 257, 1024};
    for (size_t i = 0; i < sizeof widths / sizeof *widths; i++) check_width(widths[i]);
    puts("test_widths: scalar/vector/tail widths, final-neuron inference, cold/warm drawing and malformed shapes passed");
    return 0;
}
