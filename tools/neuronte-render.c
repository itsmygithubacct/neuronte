/* neuronte-render WEIGHTS CELL_W OUT.ppm LINE...
 *
 * Draws each LINE as one row of cells, CELL_W pixels wide and twice as
 * tall, dark ink on white, and writes a binary PPM. MIT licence. */
#include "neuronte.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    neuronte *n;
    uint32_t *px;
    int cw, ch, cols = 0, rows, w, h, i, rc;
    FILE *out;

    if (argc < 5) {
        fprintf(stderr, "usage: %s WEIGHTS CELL_W OUT.ppm LINE...\n", argv[0]);
        return 2;
    }
    cw = atoi(argv[2]);
    ch = 2 * cw;
    if (cw <= 0 || cw > 256) {
        fprintf(stderr, "CELL_W must be 1..256\n");
        return 2;
    }
    rc = neuronte_open_file(argv[1], &n);
    if (rc != NEURONTE_OK) {
        fprintf(stderr, "%s: cannot load weights (%d)\n", argv[1], rc);
        return 1;
    }
    rows = argc - 4;
    for (i = 4; i < argc; i++) {
        int cells = 0;
        size_t off = 0, len = strlen(argv[i]);
        while (off < len) {
            off += neuronte_utf8_decode(argv[i] + off, len - off, NULL);
            cells++;
        }
        if (cells > cols)
            cols = cells;
    }
    w = (cols + 2) * cw;
    h = rows * ch + ch / 2;
    px = malloc((size_t)w * h * sizeof *px);
    if (!px) {
        neuronte_close(n);
        return 1;
    }
    for (i = 0; i < w * h; i++)
        px[i] = 0xFFFFFFFFu;
    for (i = 4; i < argc; i++) {
        rc = neuronte_draw_utf8(n, px, w, w, h, cw, ch / 4 + (i - 4) * ch, cw, ch, argv[i],
                                strlen(argv[i]), 0xFF181C2Cu);
        if (rc < 0) {
            fprintf(stderr, "draw failed (%d)\n", rc);
            return 1;
        }
    }
    out = fopen(argv[3], "wb");
    if (!out) {
        perror(argv[3]);
        return 1;
    }
    fprintf(out, "P6\n%d %d\n255\n", w, h);
    for (i = 0; i < w * h; i++) {
        unsigned char rgb[3] = {(unsigned char)(px[i] >> 16), (unsigned char)(px[i] >> 8),
                                (unsigned char)px[i]};
        fwrite(rgb, 1, 3, out);
    }
    if (fclose(out) != 0) {
        perror(argv[3]);
        return 1;
    }
    free(px);
    neuronte_close(n);
    return 0;
}
