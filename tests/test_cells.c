/* Tests of the cells file (include/neuronte_cells.h, src/cells.c).
 *
 *   test_cells WEIGHTS OTHER_WEIGHTS SCRATCH_DIR
 *
 * WEIGHTS is a bundle with a table of its trained characters; OTHER_WEIGHTS
 * is any other weight file. Files are written in SCRATCH_DIR only.
 *
 * 1. Every entry of a written file is bit for bit what
 *    neuronte_coverage_styled() computes, on a handle with its settings
 *    untouched and on one with the untrained mark, binary letters, the
 *    light theme and a sample count set: those settings do not change
 *    coverage, and a file holds trained characters only. For style 0 it is
 *    also what neuronte_coverage() computes.
 * 2. The writer gives the same bytes whatever the order of its entries and
 *    whether it draws them or is handed them; it refuses an untrained
 *    scalar, two keys alike, a float outside 0..1 and a key the coverage
 *    call would refuse, and then leaves the old file as it was.
 * 3. A find for anything the file does not hold is NULL, as is a find
 *    under another snap threshold.
 * 4. A cells file is refused for other weights, for weights changed with a
 *    new time, and (only with NEURONTE_CELLS_VERIFY) for weights changed
 *    with size and time kept.
 * 5. Damaged files: every byte of the header and the index changed to
 *    several values, every cut length, files made longer, random changes
 *    and headers that claim other counts. None of them opens. Then the
 *    same again with the header's check made right for the damaged bytes,
 *    as a file written wrongly would be: the check no longer stops them,
 *    and each one that opens is read through, every float of every entry.
 *    Built with AddressSanitizer (make test does) a read outside the file
 *    stops the test, because the file is then in memory of exactly its
 *    size.
 * MIT licence. See LICENSE. */
#define _POSIX_C_SOURCE 200809L
#include "neuronte.h"
#include "neuronte_cells.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int checks, fails;

static void is(int ok, const char *what)
{
    checks++;
    if (!ok) {
        fails++;
        fprintf(stderr, "test_cells: FAILED: %s\n", what);
    }
}

/* The example in neuronte_cells.h: one cell's coverage, from the cells
 * file when it holds it and from the net when it does not. */
static int cell(const neuronte *n, const neuronte_cells *cells, uint32_t scalar, int w, int h,
                unsigned style, float *out)
{
    const float *kept = cells ? neuronte_cells_find(cells, scalar, w, h, 0, style,
                                                    NEURONTE_CELLS_SNAP_FILE) : NULL;
    if (!kept)
        return neuronte_coverage_styled(n, scalar, w, h, 0, style, out);
    memcpy(out, kept, (size_t)w * h * sizeof *out);
    return NEURONTE_OK;
}

static uint8_t *slurp(const char *path, size_t *len)
{
    FILE *f = fopen(path, "rb");
    uint8_t *buf;
    long size;
    if (!f || fseek(f, 0, SEEK_END) || (size = ftell(f)) < 0) {
        fprintf(stderr, "test_cells: cannot read %s\n", path);
        exit(2);
    }
    rewind(f);
    buf = malloc(size ? (size_t)size : 1);
    if (!buf || fread(buf, 1, (size_t)size, f) != (size_t)size)
        exit(2);
    fclose(f);
    *len = (size_t)size;
    return buf;
}

static void spill(const char *path, const uint8_t *buf, size_t len)
{
    FILE *f = fopen(path, "wb");
    if (!f || fwrite(buf, 1, len, f) != len || fclose(f)) {
        fprintf(stderr, "test_cells: cannot write %s\n", path);
        exit(2);
    }
}

static void same_time(const char *from, const char *to)
{
    struct stat st;
    struct timespec t[2];
    if (stat(from, &st))
        exit(2);
    t[0] = st.st_atim;
    t[1] = st.st_mtim;
    if (utimensat(AT_FDCWD, to, t, 0))
        exit(2);
}

static uint32_t rng = 0x9E3779B9u;

static uint32_t next(void)
{
    rng ^= rng << 13;
    rng ^= rng >> 17;
    rng ^= rng << 5;
    return rng;
}

static void wr32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

/* Make the header's check right for the bytes as they are now. */
static void recheck(uint8_t *buf, size_t len)
{
    uint64_t h = 0xcbf29ce484222325u, entries = 0;
    size_t i, end;
    for (i = 0; i < 8 && len >= 128; i++)
        entries |= (uint64_t)buf[24 + i] << (8 * i);
    if (len < 128 || entries > (len - 128) / 16)
        return;
    end = 128 + (size_t)entries * 16;
    for (i = 0; i < end; i++) {
        if (i == 112)
            i = 128;
        if (i < end)
            h = (h ^ buf[i]) * 0x100000001b3u;
    }
    for (i = 0; i < 8; i++)
        buf[112 + i] = (uint8_t)(h >> (8 * i));
}

static volatile float sink;

/* Open a damaged file; when it opens, read all of it through the calls.
 * Returns 1 when it opened. */
static int probe(const char *path, const char *weights, const uint8_t *buf, size_t len,
                 unsigned flags)
{
    neuronte_cells *c = NULL;
    struct neuronte_cells_key k;
    size_t i, p, count;
    float sum = 0.0f;
    spill(path, buf, len);
    if (neuronte_cells_open(path, weights, flags, &c) != NEURONTE_OK) {
        if (c)
            is(0, "a refused file still gave a handle");
        return 0;
    }
    count = neuronte_cells_count(c);
    for (i = 0; i < count; i++) {
        const float *f = neuronte_cells_entry(c, i, &k), *g;
        size_t area = (size_t)k.cell_w * k.cell_h;
        for (p = 0; p < area; p++)
            sum += f[p];
        for (int snap = -1; snap < 3; snap++) {
            g = neuronte_cells_find(c, k.scalar, k.cell_w, k.cell_h, k.samples, k.style, snap);
            if (g && g != f)
                is(0, "a find in a damaged file gave another entry's floats");
        }
    }
    neuronte_cells_find(c, 'A', 9, 18, 0, 0, -1);
    sink = sum;
    neuronte_cells_close(c);
    return 1;
}

int main(int argc, char **argv)
{
    static const int boxes[][3] = { /* cell_w, cell_h, samples */
        { 9, 18, 0 }, { 8, 17, 0 }, { 5, 9, 0 }, { 9, 18, 2 }, { 18, 36, 0 } };
    char a[1024], b[1024], d[1024], w2[1024], bad[1024];
    neuronte *n = NULL, *m = NULL, *s = NULL;
    neuronte_cells *c = NULL, *copy = NULL, *other = NULL;
    struct neuronte_cells_key *keys, k;
    const float **ref;
    float *got, *scratch;
    uint32_t chars[512], untrained = 0;
    size_t nchars = 0, nkeys = 0, i, j, len, lenb, extra = 0;
    uint8_t *bytes, *bytesb, *mut;
    unsigned style;
    int wrong_plain = 0, wrong_set = 0, wrong_cov = 0, missing = 0;

    if (argc != 4) {
        fprintf(stderr, "usage: test_cells WEIGHTS OTHER_WEIGHTS SCRATCH_DIR\n");
        return 2;
    }
    mkdir(argv[3], 0755);
    snprintf(a, sizeof a, "%s/a.cells", argv[3]);
    snprintf(b, sizeof b, "%s/b.cells", argv[3]);
    snprintf(d, sizeof d, "%s/snap.cells", argv[3]);
    snprintf(w2, sizeof w2, "%s/weights-copy.nrt", argv[3]);
    snprintf(bad, sizeof bad, "%s/damaged.cells", argv[3]);

    if (neuronte_open_file(argv[1], &n) || neuronte_open_file(argv[1], &m) ||
        neuronte_open_file(argv[1], &s)) {
        fprintf(stderr, "test_cells: cannot open %s\n", argv[1]);
        return 2;
    }
    if (neuronte_untrained(n, 0x10FFFF) != 1) {
        fprintf(stderr, "test_cells: %s has no table of trained characters\n", argv[1]);
        return 2;
    }
    /* A handle with every setting that is not in the key changed. */
    is(neuronte_set_untrained(m, 1) == NEURONTE_OK && neuronte_set_binary(m, 1) == NEURONTE_OK &&
       neuronte_set_theme(m, 1) == NEURONTE_OK && neuronte_set_samples(m, 3) == NEURONTE_OK,
       "the settings of the second handle");

    /* ASCII, Latin-1, U+FFFD and the first trained characters after them. */
    for (uint32_t ch = 0x20; ch <= 0x10FFFF && nchars < 512; ch++) {
        int basic = (ch >= 0x20 && ch <= 0x7E) || (ch >= 0xA0 && ch <= 0xFF) || ch == 0xFFFD;
        if (ch >= 0xD800 && ch <= 0xDFFF)
            continue;
        if (neuronte_untrained(n, ch) == 1) {
            if (!untrained && ch > 0xFF)
                untrained = ch;
            continue;
        }
        if (basic || (ch > 0xFF && extra < 24)) {
            chars[nchars++] = ch;
            extra += !basic;
        }
        if (ch > 0xFFFD && extra >= 24 && untrained)
            break;
    }
    keys = calloc(nchars * 20, sizeof *keys);
    ref = calloc(nchars * 20, sizeof *ref);
    if (!keys || !ref)
        return 2;
    for (j = 0; j < sizeof boxes / sizeof boxes[0]; j++)
        for (style = 0; style < 4; style++)
            for (i = 0; i < nchars; i++) {
                float *f;
                /* The larger boxes cost more: fewer characters and styles there. */
                if ((boxes[j][2] == 2 && (style == 1 || style == 2)) ||
                    (boxes[j][0] == 18 && (style || i % 6)))
                    continue;
                keys[nkeys].scalar = chars[i];
                keys[nkeys].cell_w = (uint16_t)boxes[j][0];
                keys[nkeys].cell_h = (uint16_t)boxes[j][1];
                keys[nkeys].samples = (uint8_t)boxes[j][2];
                keys[nkeys].style = (uint8_t)style;
                f = malloc((size_t)boxes[j][0] * boxes[j][1] * sizeof *f);
                if (!f || neuronte_coverage_styled(n, chars[i], boxes[j][0], boxes[j][1], boxes[j][2],
                                                   style, f) != NEURONTE_OK)
                    return 2;
                ref[nkeys++] = f;
            }
    got = malloc(64 * 64 * sizeof *got);
    scratch = malloc(64 * 64 * sizeof *scratch);
    if (!got || !scratch)
        return 2;

    /* 2: drawn by the writer, and handed over in the opposite order. */
    remove(a);
    remove(b);
    is(neuronte_cells_write(a, argv[1], n, NEURONTE_CELLS_SNAP_FILE, keys, NULL, nkeys) == NEURONTE_OK,
       "write, the writer drawing");
    {
        struct neuronte_cells_key *rk = malloc(nkeys * sizeof *rk);
        const float **rr = malloc(nkeys * sizeof *rr);
        if (!rk || !rr)
            return 2;
        for (i = 0; i < nkeys; i++) {
            rk[i] = keys[nkeys - 1 - i];
            rr[i] = ref[nkeys - 1 - i];
        }
        is(neuronte_cells_write(b, argv[1], n, NEURONTE_CELLS_SNAP_FILE, rk, rr, nkeys) == NEURONTE_OK,
           "write, handed the cells in the opposite order");
        free(rk);
        free(rr);
    }
    bytes = slurp(a, &len);
    bytesb = slurp(b, &lenb);
    is(len == lenb && !memcmp(bytes, bytesb, len), "the two written files are the same bytes");

    /* 1 */
    is(neuronte_cells_open(a, argv[1], 0, &c) == NEURONTE_OK && c, "open");
    is(neuronte_cells_open(a, argv[1], NEURONTE_CELLS_COPY | NEURONTE_CELLS_VERIFY, &copy) == NEURONTE_OK,
       "open, read into memory and the weights hashed");
    is(neuronte_cells_count(c) == nkeys && neuronte_cells_count(copy) == nkeys, "the count of entries");
    for (i = 0; i < nkeys; i++) {
        size_t bytes_in = (size_t)keys[i].cell_w * keys[i].cell_h * sizeof(float);
        const float *f = neuronte_cells_find(c, keys[i].scalar, keys[i].cell_w, keys[i].cell_h,
                                             keys[i].samples, keys[i].style, -1);
        const float *g = neuronte_cells_find(copy, keys[i].scalar, keys[i].cell_w, keys[i].cell_h,
                                             keys[i].samples, keys[i].style, -1);
        if (!f || !g) {
            missing++;
            continue;
        }
        wrong_plain += memcmp(f, ref[i], bytes_in) != 0 || memcmp(g, ref[i], bytes_in) != 0;
        if (neuronte_coverage_styled(m, keys[i].scalar, keys[i].cell_w, keys[i].cell_h,
                                     keys[i].samples, keys[i].style, got) != NEURONTE_OK ||
            memcmp(f, got, bytes_in))
            wrong_set++;
        if (!keys[i].style &&
            (neuronte_coverage(n, keys[i].scalar, keys[i].cell_w, keys[i].cell_h, keys[i].samples,
                               got) != NEURONTE_OK || memcmp(f, got, bytes_in)))
            wrong_cov++;
    }
    is(missing == 0, "every entry is found");
    is(wrong_plain == 0, "every entry is the bytes neuronte_coverage_styled() writes");
    is(wrong_set == 0, "the same with the untrained mark, binary letters, the light theme and samples set");
    is(wrong_cov == 0, "every style 0 entry is the bytes neuronte_coverage() writes");
    {
        uint64_t last = 0;
        int ordered = 1, agree = 1;
        for (i = 0; i < nkeys; i++) {
            const float *f = neuronte_cells_entry(c, i, &k);
            uint64_t at = (uint64_t)k.cell_w << 40 | (uint64_t)k.cell_h << 27 |
                          (uint64_t)k.samples << 23 | (uint64_t)k.style << 21 | k.scalar;
            ordered &= !i || at > last;
            last = at;
            agree &= f && f == neuronte_cells_find(c, k.scalar, k.cell_w, k.cell_h, k.samples,
                                                   k.style, -1);
        }
        is(ordered, "the entries are in the stated order");
        is(agree, "entry and find give the same floats");
        is(neuronte_cells_entry(c, nkeys, &k) == NULL, "entry past the end");
    }

    /* 3 */
    is(untrained && neuronte_cells_find(c, untrained, 9, 18, 0, 0, -1) == NULL, "an untrained character");
    is(neuronte_cells_find(c, 'A', 9, 19, 0, 0, -1) == NULL, "a cell the file does not hold");
    is(neuronte_cells_find(c, 'A', 9, 18, 1, 0, -1) == NULL, "a sample count the file does not hold");
    is(neuronte_cells_find(c, 'A', 9, 18, 0, 0, -1) != NULL, "the same with the one it holds");
    is(neuronte_cells_find(c, 'A', 9, 18, 0, 0, 12) == NULL, "another snap threshold");
    is(neuronte_cells_find(c, 'A', 9, 18, 0, 4, -1) == NULL && neuronte_cells_find(c, 'A', 0, 18, 0, 0, -1) == NULL &&
       neuronte_cells_find(c, 'A', 9, -1, 0, 0, -1) == NULL && neuronte_cells_find(c, 'A', 4097, 18, 0, 0, -1) == NULL &&
       neuronte_cells_find(c, 'A', 9, 18, 9, 0, -1) == NULL && neuronte_cells_find(NULL, 'A', 9, 18, 0, 0, -1) == NULL,
       "arguments the coverage call would refuse");
    if (neuronte_untrained(n, 0xFFFD) == 0) {
        const float *f = neuronte_cells_find(c, 0xFFFD, 9, 18, 0, 0, -1);
        is(f && neuronte_cells_find(c, 0xD800, 9, 18, 0, 0, -1) == f &&
           neuronte_cells_find(c, 0x110000, 9, 18, 0, 0, -1) == f &&
           neuronte_coverage_styled(n, 0xD800, 9, 18, 0, 0, got) == NEURONTE_OK &&
           !memcmp(f, got, 9 * 18 * sizeof *got),
           "a scalar the library replaces finds U+FFFD, as the library draws it");
    }
    /* The example: a hit, a miss in the file, and no file. */
    is(cell(n, c, 'g', 9, 18, 3, got) == NEURONTE_OK &&
       neuronte_coverage_styled(n, 'g', 9, 18, 0, 3, scratch) == NEURONTE_OK &&
       !memcmp(got, scratch, 9 * 18 * sizeof *got), "the example, a character the file holds");
    is(cell(n, c, 'g', 11, 22, 1, got) == NEURONTE_OK &&
       neuronte_coverage_styled(n, 'g', 11, 22, 0, 1, scratch) == NEURONTE_OK &&
       !memcmp(got, scratch, 11 * 22 * sizeof *got), "the example, a cell the file does not hold");
    is(cell(n, NULL, 'g', 9, 18, 0, got) == NEURONTE_OK &&
       !memcmp(got, neuronte_cells_find(c, 'g', 9, 18, 0, 0, -1), 9 * 18 * sizeof *got),
       "the example, no cells file");

    /* 2: what the writer refuses, and that the old file stays. */
    {
        struct neuronte_cells_key two[2] = { keys[0], keys[0] }, one = keys[0];
        float high[5 * 9], *hp = high;
        const float *const *hand = (const float *const *)&hp;
        uint8_t *after;
        size_t lena;
        is(neuronte_cells_write(a, argv[1], n, -1, two, NULL, 2) == NEURONTE_ERR_ARG, "two keys alike");
        one.scalar = untrained;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "an untrained scalar");
        one.scalar = 0xD800;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "a surrogate");
        one = keys[0];
        one.cell_w = 0;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "a cell of no width");
        one = keys[0];
        one.samples = 9;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "too many samples");
        one = keys[0];
        one.style = 4;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "a style that is none");
        one = keys[0];
        one.cell_w = 5;
        one.cell_h = 9;
        for (i = 0; i < 45; i++)
            high[i] = 0.5f;
        high[44] = 1.5f;
        is(neuronte_cells_write(a, argv[1], n, -1, &one, hand, 1) == NEURONTE_ERR_ARG, "a float above 1");
        memset(&high[44], 0xFF, sizeof high[44]); /* a NaN */
        is(neuronte_cells_write(a, argv[1], n, -1, &one, hand, 1) == NEURONTE_ERR_ARG, "a float that is no number");
        is(neuronte_cells_write(a, "/nonexistent/weights.nrt", n, -1, &one, NULL, 1) == NEURONTE_ERR_IO,
           "weights that cannot be read");
        is(neuronte_cells_write("/nonexistent/dir/x.cells", argv[1], n, -1, &one, NULL, 1) == NEURONTE_ERR_IO,
           "a place that cannot be written");
        is(neuronte_cells_write(a, argv[1], NULL, -1, &one, NULL, 1) == NEURONTE_ERR_ARG, "no handle");
        after = slurp(a, &lena);
        is(lena == len && !memcmp(after, bytes, len), "a refused write leaves the old file as it was");
        free(after);
        snprintf(w2, sizeof w2, "%s/a.cells.%ld.tmp", argv[3], (long)getpid());
        is(access(w2, F_OK) != 0, "and leaves no file beside it");
        snprintf(w2, sizeof w2, "%s/weights-copy.nrt", argv[3]);
    }
    /* A file made under another snap threshold answers only for that one. */
    is(neuronte_set_snap(s, 12) == NEURONTE_OK &&
       neuronte_cells_write(d, argv[1], s, 12, keys, NULL, 40) == NEURONTE_OK &&
       neuronte_cells_open(d, argv[1], 0, &other) == NEURONTE_OK, "a file made under snap 12");
    if (other) {
        const float *f = neuronte_cells_find(other, keys[0].scalar, keys[0].cell_w, keys[0].cell_h,
                                             keys[0].samples, keys[0].style, 12);
        is(neuronte_cells_find(other, keys[0].scalar, keys[0].cell_w, keys[0].cell_h, keys[0].samples,
                               keys[0].style, -1) == NULL, "it does not answer the weight file's own threshold");
        is(f && neuronte_coverage_styled(s, keys[0].scalar, keys[0].cell_w, keys[0].cell_h,
                                         keys[0].samples, keys[0].style, got) == NEURONTE_OK &&
           !memcmp(f, got, (size_t)keys[0].cell_w * keys[0].cell_h * sizeof *got),
           "it answers threshold 12 with what that handle draws");
        neuronte_cells_close(other);
        other = NULL;
    }
    /* An empty file is a file. */
    is(neuronte_cells_write(d, argv[1], n, -1, NULL, NULL, 0) == NEURONTE_OK &&
       neuronte_cells_open(d, argv[1], 0, &other) == NEURONTE_OK && neuronte_cells_count(other) == 0 &&
       neuronte_cells_find(other, 'A', 9, 18, 0, 0, -1) == NULL, "a file of no entries");
    neuronte_cells_close(other);
    other = NULL;

    /* 4 */
    is(neuronte_cells_open(a, argv[2], 0, &other) == NEURONTE_ERR_SHAPE && !other, "other weights");
    {
        size_t wlen;
        uint8_t *wb = slurp(argv[1], &wlen);
        spill(w2, wb, wlen);
        is(neuronte_cells_open(a, w2, 0, &other) == NEURONTE_OK, "the same weights with another time (hashed)");
        neuronte_cells_close(other);
        other = NULL;
        wb[wlen / 2] ^= 1;
        spill(w2, wb, wlen);
        is(neuronte_cells_open(a, w2, 0, &other) == NEURONTE_ERR_SHAPE, "weights changed, with another time");
        same_time(argv[1], w2);
        is(neuronte_cells_open(a, w2, 0, &other) == NEURONTE_OK,
           "weights changed with size and time kept are not seen without VERIFY (the stated limit)");
        neuronte_cells_close(other);
        other = NULL;
        is(neuronte_cells_open(a, w2, NEURONTE_CELLS_VERIFY, &other) == NEURONTE_ERR_SHAPE,
           "and are refused with VERIFY");
        spill(w2, wb, wlen - 1);
        is(neuronte_cells_open(a, w2, 0, &other) == NEURONTE_ERR_SHAPE, "weights of another size");
        free(wb);
    }
    is(neuronte_cells_open("/nonexistent/x.cells", argv[1], 0, &other) == NEURONTE_ERR_IO, "no cells file");
    is(neuronte_cells_open(a, "/nonexistent/x.nrt", 0, &other) == NEURONTE_ERR_IO, "no weight file");
    is(neuronte_cells_open(argv[1], argv[1], 0, &other) == NEURONTE_ERR_FORMAT, "a weight file as a cells file");
    is(neuronte_cells_open(NULL, argv[1], 0, &other) == NEURONTE_ERR_ARG &&
       neuronte_cells_open(a, NULL, 0, &other) == NEURONTE_ERR_ARG &&
       neuronte_cells_open(a, argv[1], 0, NULL) == NEURONTE_ERR_ARG &&
       neuronte_cells_open(a, argv[1], 4, &other) == NEURONTE_ERR_ARG, "arguments open refuses");
    neuronte_cells_close(NULL);
    is(neuronte_cells_count(NULL) == 0, "count of nothing");

    /* 5: a small file, damaged every way. */
    {
        struct neuronte_cells_key small[40];
        size_t ns = 0, slen, idx, tried = 0, raw_opened = 0, opened = 0, total;
        uint8_t *sb;
        for (j = 0; j < 2; j++)
            for (style = 0; style < 2; style++)
                for (i = 0; i < 10; i++) {
                    small[ns].scalar = chars[i * 7 % nchars];
                    small[ns].cell_w = (uint16_t)(5 + j);
                    small[ns].cell_h = (uint16_t)(9 + 2 * j);
                    small[ns].samples = 0;
                    small[ns++].style = (uint8_t)style;
                }
        is(neuronte_cells_write(d, argv[1], n, -1, small, NULL, ns) == NEURONTE_OK, "the small file");
        sb = slurp(d, &slen);
        idx = 128 + 16 * ns;
        mut = malloc(slen + 8192);
        if (!mut)
            return 2;
        is(probe(bad, argv[1], sb, slen, NEURONTE_CELLS_COPY) == 1, "the small file, not damaged, opens");
        memcpy(mut, sb, slen);
        recheck(mut, slen);
        is(!memcmp(mut, sb, slen), "the test's own check value is the writer's");
/* Try the bytes in mut as they are, then with the check made right. */
#define TRY(length) \
    do { \
        unsigned how = tried % 16 ? NEURONTE_CELLS_COPY : 0; \
        tried++; \
        if ((length) != slen || memcmp(mut, sb, slen)) { \
            raw_opened += (size_t)probe(bad, argv[1], mut, (length), how); \
            recheck(mut, (length)); \
            opened += (size_t)probe(bad, argv[1], mut, (length), how); \
        } \
    } while (0)
        /* Every byte of the header and the index, to several values. */
        for (i = 0; i < idx; i++) {
            const uint8_t to[6] = { 0x00, 0x01, 0x7F, 0x80, 0xFF, (uint8_t)(sb[i] ^ 0x04) };
            for (j = 0; j < 6; j++) {
                memcpy(mut, sb, slen);
                mut[i] = to[j];
                TRY(slen);
            }
        }
        /* Cut short and made longer. */
        for (i = 0; i < slen; i += i < idx + 64 ? 1 : 251) {
            memcpy(mut, sb, slen);
            TRY(i);
        }
        for (i = 1; i <= 8192; i *= 2) {
            memcpy(mut, sb, slen);
            memset(mut + slen, 0, 8192);
            TRY(slen + i);
        }
        /* Random changes to the header and the index. */
        for (i = 0; i < 3000; i++) {
            int changes = 1 + (int)(next() % 4);
            memcpy(mut, sb, slen);
            while (changes--)
                mut[next() % idx] = (uint8_t)next();
            TRY(slen);
        }
        /* Headers that claim other counts of entries and floats, the sizes
         * agreeing with the length of the file, so that the index is read. */
        for (i = 0; i < 3000; i++) {
            size_t most, e;
            total = slen + (next() % 3 ? 0 : (next() % 64) * 4);
            most = (total - 128) / 16;
            e = next() % 4 ? next() % (ns + 9) : next() % (most + 1);
            if (e > most)
                e = most;
            memcpy(mut, sb, slen);
            memset(mut + slen, 0, 8192);
            wr32(mut + 24, (uint32_t)e);
            wr32(mut + 32, (uint32_t)((total - 128 - 16 * e) / 4));
            wr32(mut + 40, (uint32_t)total);
            if (next() % 2)
                mut[128 + next() % (16 * (e ? e : 1))] = (uint8_t)next();
            TRY(total);
        }
#undef TRY
        is(raw_opened == 0, "no damaged file opens");
        is(opened > 0, "some damaged files open once their check is made right, and are read through");
        printf("test_cells: %zu damaged files, none opened; with the check made right for the damage, "
               "%zu opened and were read through\n", tried, opened);
        free(sb);
        free(mut);
    }

    for (i = 0; i < nkeys; i++)
        free((void *)(uintptr_t)ref[i]);
    free(ref);
    free(keys);
    free(got);
    free(scratch);
    free(bytes);
    free(bytesb);
    neuronte_cells_close(c);
    neuronte_cells_close(copy);
    neuronte_close(n);
    neuronte_close(m);
    neuronte_close(s);
    remove(a);
    remove(b);
    remove(d);
    remove(w2);
    remove(bad);
    printf("test_cells: %zu entries of %zu characters compared; %d checks, %d failed\n", nkeys, nchars,
           checks, fails);
    return fails != 0;
}
