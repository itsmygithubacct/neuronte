/* Exercise the final four neurons of a width-12 distance model. */
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

int main(void)
{
    enum { H = 12, PARAMS = 2 * H * H + 94 * H + 1, BYTES = 204 + 4 * PARAMS };
    unsigned char image[BYTES] = {0};
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
    assert(neuronte_open(image, sizeof image, &net) == 0 && net);
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
    for (int h = 4; h <= 1028; h += 2) {
        if (h >= 8 && h <= 1024 && h % 4 == 0) continue;
        u32(image + 20, (uint32_t)h);
        net = (neuronte *)1;
        assert(neuronte_open(image, sizeof image, &net) < 0 && net == NULL);
    }
    u32(image + 20, H);
    assert(neuronte_open(image, sizeof image - 1, &net) < 0 && net == NULL);
    puts("test_widths: width 12, final-neuron inference, cold/warm drawing and malformed shapes passed");
    return 0;
}
