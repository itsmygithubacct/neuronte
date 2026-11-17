/* Cells files: see include/neuronte_cells.h for what they hold and the
 * layout of the file. This file uses the library only through neuronte.h.
 * MIT licence. See LICENSE. */
#if defined(__unix__) || defined(__APPLE__)
#define NEURONTE_CELLS_POSIX 1
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#endif

#include "neuronte_cells.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef NEURONTE_CELLS_POSIX
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

#define HEADER 128
#define ENTRY 16
#define KIND_COVERAGE 1
#define MAX_STYLE (NEURONTE_STYLE_BOLD | NEURONTE_STYLE_ITALIC)

static const uint8_t MAGIC[8] = { 'N', 'R', 'T', 'C', 'E', 'L', 'L', 'S' };

struct neuronte_cells {
    const uint8_t *data; /* the whole file */
    size_t len;
    int mapped;
    size_t entries;
    const uint8_t *index;
    const float *floats;
    int snap;
};

/* What a weight file is known by. */
struct weights_id {
    uint64_t size;
    int64_t sec;
    uint32_t nsec;
    int timed; /* 0 where the file's time cannot be read */
    uint8_t sha[32];
};

/* SHA-256 (FIPS 180-4). */
struct sha256 {
    uint32_t h[8];
    uint64_t bytes;
    uint8_t block[64];
    size_t fill;
};

static const uint32_t SHA_K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static uint32_t rotr(uint32_t x, int n)
{
    return x >> n | x << (32 - n);
}

static void sha_block(struct sha256 *s, const uint8_t *p)
{
    uint32_t w[64], a[8], t1, t2;
    int i;
    for (i = 0; i < 16; i++)
        w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 |
               (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (; i < 64; i++)
        w[i] = w[i - 16] + (rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ w[i - 15] >> 3) + w[i - 7] +
               (rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ w[i - 2] >> 10);
    memcpy(a, s->h, sizeof a);
    for (i = 0; i < 64; i++) {
        t1 = a[7] + (rotr(a[4], 6) ^ rotr(a[4], 11) ^ rotr(a[4], 25)) +
             ((a[4] & a[5]) ^ (~a[4] & a[6])) + SHA_K[i] + w[i];
        t2 = (rotr(a[0], 2) ^ rotr(a[0], 13) ^ rotr(a[0], 22)) +
             ((a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]));
        memmove(a + 1, a, 7 * sizeof a[0]);
        a[4] += t1;
        a[0] = t1 + t2;
    }
    for (i = 0; i < 8; i++)
        s->h[i] += a[i];
}

static void sha_start(struct sha256 *s)
{
    static const uint32_t h0[8] = { 0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                                    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19 };
    memcpy(s->h, h0, sizeof h0);
    s->bytes = 0;
    s->fill = 0;
}

static void sha_add(struct sha256 *s, const uint8_t *p, size_t n)
{
    s->bytes += n;
    while (n) {
        size_t take = 64 - s->fill < n ? 64 - s->fill : n;
        memcpy(s->block + s->fill, p, take);
        s->fill += take;
        p += take;
        n -= take;
        if (s->fill == 64) {
            sha_block(s, s->block);
            s->fill = 0;
        }
    }
}

static void sha_end(struct sha256 *s, uint8_t out[32])
{
    uint64_t bits = s->bytes * 8;
    uint8_t pad[72] = { 0x80 }, len[8];
    size_t n = (s->fill < 56 ? 56 : 120) - s->fill;
    int i;
    for (i = 0; i < 8; i++)
        len[i] = (uint8_t)(bits >> (56 - 8 * i));
    sha_add(s, pad, n);
    sha_add(s, len, 8);
    for (i = 0; i < 32; i++)
        out[i] = (uint8_t)(s->h[i / 4] >> (24 - 8 * (i % 4)));
}

static uint16_t rd16(const uint8_t *p)
{
    return (uint16_t)(p[0] | p[1] << 8);
}

static uint32_t rd32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t rd64(const uint8_t *p)
{
    return (uint64_t)rd32(p) | (uint64_t)rd32(p + 4) << 32;
}

static void wr16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void wr32(uint8_t *p, uint32_t v)
{
    wr16(p, (uint16_t)v);
    wr16(p + 2, (uint16_t)(v >> 16));
}

static void wr64(uint8_t *p, uint64_t v)
{
    wr32(p, (uint32_t)v);
    wr32(p + 4, (uint32_t)(v >> 32));
}

/* The order of the index, as one number: cell_w, cell_h, samples, style,
 * scalar. The fields are checked to fit before this is called. */
static uint64_t order(uint32_t scalar, unsigned w, unsigned h, unsigned samples, unsigned style)
{
    return (uint64_t)w << 40 | (uint64_t)h << 27 | (uint64_t)samples << 23 |
           (uint64_t)style << 21 | scalar;
}

static int key_fits(uint32_t scalar, int64_t w, int64_t h, int64_t samples, uint64_t style)
{
    return scalar <= 0x10FFFF && !(scalar >= 0xD800 && scalar <= 0xDFFF) && w >= 1 &&
           w <= NEURONTE_MAX_CELL && h >= 1 && h <= NEURONTE_MAX_CELL && samples >= 0 &&
           samples <= NEURONTE_MAX_SAMPLES && style <= MAX_STYLE;
}

/* 64-bit FNV-1a over the header before the check and the index. */
static uint64_t fnv(const uint8_t *head, const uint8_t *index, size_t index_len)
{
    uint64_t h = 0xcbf29ce484222325u;
    size_t i;
    for (i = 0; i < 112; i++)
        h = (h ^ head[i]) * 0x100000001b3u;
    for (i = 0; i < index_len; i++)
        h = (h ^ index[i]) * 0x100000001b3u;
    return h;
}

/* 1 when this machine keeps a float as the data does. */
static int float_layout(const uint8_t *probe)
{
    static const uint8_t one[4] = { 0x00, 0x00, 0x80, 0x3F };
    float f = 1.0f;
    return sizeof f == 4 && !memcmp(probe, one, 4) && !memcmp(&f, one, 4);
}

/* Size, time and SHA-256 of a weight file. hash = 0 leaves the hash out. */
static int identify(const char *path, int hash, struct weights_id *id)
{
    uint8_t buf[1 << 15];
    struct sha256 s;
    uint64_t total = 0;
    size_t got;
    FILE *f;
    memset(id, 0, sizeof *id);
#ifdef NEURONTE_CELLS_POSIX
    {
        struct stat st;
        if (stat(path, &st) || !S_ISREG(st.st_mode))
            return NEURONTE_ERR_IO;
        id->size = (uint64_t)st.st_size;
        id->sec = (int64_t)st.st_mtim.tv_sec;
        id->nsec = (uint32_t)st.st_mtim.tv_nsec;
        id->timed = 1;
        if (!hash)
            return NEURONTE_OK;
    }
#else
    (void)hash;
#endif
    f = fopen(path, "rb");
    if (!f)
        return NEURONTE_ERR_IO;
    sha_start(&s);
    while ((got = fread(buf, 1, sizeof buf, f)) > 0) {
        sha_add(&s, buf, got);
        total += got;
    }
    if (ferror(f)) {
        fclose(f);
        return NEURONTE_ERR_IO;
    }
    fclose(f);
    sha_end(&s, id->sha);
#ifdef NEURONTE_CELLS_POSIX
    {
        /* The file must be the one whose size and time were read. */
        struct stat st;
        if (stat(path, &st) || (uint64_t)st.st_size != id->size || total != id->size ||
            (int64_t)st.st_mtim.tv_sec != id->sec || (uint32_t)st.st_mtim.tv_nsec != id->nsec)
            return NEURONTE_ERR_IO;
    }
#else
    id->size = total;
#endif
    return NEURONTE_OK;
}

static void drop(const uint8_t *data, size_t len, int mapped)
{
    if (!data)
        return;
#ifdef NEURONTE_CELLS_POSIX
    if (mapped) {
        munmap((void *)(uintptr_t)data, len);
        return;
    }
#else
    (void)len;
    (void)mapped;
#endif
    free((void *)(uintptr_t)data);
}

/* The whole file: mapped read-only, or read into memory of exactly its
 * size. A file shorter than a header is NEURONTE_ERR_FORMAT. */
static int load(const char *path, int copy, const uint8_t **data, size_t *len, int *mapped)
{
    uint8_t *buf;
    size_t size, got = 0;
    FILE *f;
    *data = NULL;
    *mapped = 0;
#ifdef NEURONTE_CELLS_POSIX
    if (!copy) {
        struct stat st;
        void *p;
        int fd = open(path, O_RDONLY | O_CLOEXEC);
        if (fd < 0)
            return NEURONTE_ERR_IO;
        if (fstat(fd, &st) || !S_ISREG(st.st_mode)) {
            close(fd);
            return NEURONTE_ERR_IO;
        }
        if (st.st_size < HEADER || (uint64_t)st.st_size > SIZE_MAX) {
            close(fd);
            return NEURONTE_ERR_FORMAT;
        }
        p = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
        close(fd);
        if (p == MAP_FAILED)
            return NEURONTE_ERR_IO;
        *data = p;
        *len = (size_t)st.st_size;
        *mapped = 1;
        return NEURONTE_OK;
    }
#else
    (void)copy;
#endif
    f = fopen(path, "rb");
    if (!f)
        return NEURONTE_ERR_IO;
    if (fseek(f, 0, SEEK_END) || ftell(f) < 0) {
        fclose(f);
        return NEURONTE_ERR_IO;
    }
    size = (size_t)ftell(f);
    if (size < HEADER) {
        fclose(f);
        return NEURONTE_ERR_FORMAT;
    }
    rewind(f);
    buf = malloc(size);
    if (!buf) {
        fclose(f);
        return NEURONTE_ERR_NOMEM;
    }
    got = fread(buf, 1, size, f);
    fclose(f);
    if (got != size) {
        free(buf);
        return NEURONTE_ERR_IO;
    }
    *data = buf;
    *len = size;
    return NEURONTE_OK;
}

/* Check the header and the whole index against the size of the file.
 * After this, every entry's floats lie inside the data. */
static int check(const uint8_t *d, size_t len, neuronte_cells *c)
{
    uint64_t entries, floats, sum = 0, last = 0, room;
    size_t i;
    if (len < HEADER || memcmp(d, MAGIC, sizeof MAGIC) || rd32(d + 8) != NEURONTE_CELLS_VERSION ||
        rd32(d + 12) != KIND_COVERAGE || rd32(d + 16) != HEADER || rd32(d + 20) != ENTRY)
        return NEURONTE_ERR_FORMAT;
    entries = rd64(d + 24);
    floats = rd64(d + 32);
    if (rd64(d + 40) != (uint64_t)len || !float_layout(d + 72) || rd32(d + 76) ||
        (int32_t)rd32(d + 68) < -1 || rd32(d + 64) > 999999999u)
        return NEURONTE_ERR_FORMAT;
    if (rd64(d + 120))
        return NEURONTE_ERR_FORMAT;
    room = (uint64_t)len - HEADER;
    if (entries > room / ENTRY)
        return NEURONTE_ERR_FORMAT;
    if (rd64(d + 112) != fnv(d, d + HEADER, (size_t)entries * ENTRY))
        return NEURONTE_ERR_FORMAT;
    room -= entries * ENTRY;
    if (room % 4 || floats != room / 4 || floats > UINT32_MAX)
        return NEURONTE_ERR_FORMAT;
    for (i = 0; i < (size_t)entries; i++) {
        const uint8_t *e = d + HEADER + i * ENTRY;
        uint32_t scalar = rd32(e);
        unsigned w = rd16(e + 4), h = rd16(e + 6), samples = e[8], style = e[9];
        uint64_t at;
        if (!key_fits(scalar, w, h, samples, style) || rd16(e + 10) || rd32(e + 12) != sum)
            return NEURONTE_ERR_FORMAT;
        at = order(scalar, w, h, samples, style);
        if (i && at <= last)
            return NEURONTE_ERR_FORMAT;
        last = at;
        sum += (uint64_t)w * h;
        if (sum > floats)
            return NEURONTE_ERR_FORMAT;
    }
    if (sum != floats)
        return NEURONTE_ERR_FORMAT;
    c->entries = (size_t)entries;
    c->index = d + HEADER;
    c->floats = (const float *)(const void *)(d + HEADER + (size_t)entries * ENTRY);
    c->snap = (int32_t)rd32(d + 68);
    return NEURONTE_OK;
}

int neuronte_cells_open(const char *cells_path, const char *weights_path, unsigned flags,
                        neuronte_cells **out)
{
    struct weights_id id;
    neuronte_cells *c;
    const uint8_t *d;
    int rc, quick;
    if (out)
        *out = NULL;
    if (!cells_path || !weights_path || !out || (flags & ~(NEURONTE_CELLS_VERIFY | NEURONTE_CELLS_COPY)))
        return NEURONTE_ERR_ARG;
    c = calloc(1, sizeof *c);
    if (!c)
        return NEURONTE_ERR_NOMEM;
    rc = load(cells_path, (flags & NEURONTE_CELLS_COPY) != 0, &c->data, &c->len, &c->mapped);
    if (rc == NEURONTE_OK)
        rc = check(c->data, c->len, c);
    if (rc == NEURONTE_OK)
        rc = identify(weights_path, 0, &id);
    if (rc == NEURONTE_OK) {
        d = c->data;
        quick = id.timed && !(flags & NEURONTE_CELLS_VERIFY) && id.size == rd64(d + 48) &&
                id.sec == (int64_t)rd64(d + 56) && id.nsec == rd32(d + 64);
        if (id.timed && id.size != rd64(d + 48))
            rc = NEURONTE_ERR_SHAPE;
        else if (!quick) {
            rc = identify(weights_path, 1, &id);
            if (rc == NEURONTE_OK && (id.size != rd64(d + 48) || memcmp(id.sha, d + 80, 32)))
                rc = NEURONTE_ERR_SHAPE;
        }
    }
    if (rc != NEURONTE_OK) {
        neuronte_cells_close(c);
        return rc;
    }
    *out = c;
    return NEURONTE_OK;
}

void neuronte_cells_close(neuronte_cells *c)
{
    if (!c)
        return;
    drop(c->data, c->len, c->mapped);
    free(c);
}

size_t neuronte_cells_count(const neuronte_cells *c)
{
    return c ? c->entries : 0;
}

const float *neuronte_cells_entry(const neuronte_cells *c, size_t index,
                                  struct neuronte_cells_key *key)
{
    const uint8_t *e;
    if (!c || index >= c->entries)
        return NULL;
    e = c->index + index * ENTRY;
    if (key) {
        key->scalar = rd32(e);
        key->cell_w = rd16(e + 4);
        key->cell_h = rd16(e + 6);
        key->samples = e[8];
        key->style = e[9];
    }
    return c->floats + rd32(e + 12);
}

const float *neuronte_cells_find(const neuronte_cells *c, uint32_t scalar, int cell_w, int cell_h,
                                 int samples_per_axis, unsigned style, int snap_below)
{
    size_t lo = 0, hi;
    uint64_t want;
    if (!c || snap_below != c->snap)
        return NULL;
    /* The replacement the library makes before it draws. */
    if (scalar > 0x10FFFF || (scalar >= 0xD800 && scalar <= 0xDFFF))
        scalar = NEURONTE_REPLACEMENT;
    if (!key_fits(scalar, cell_w, cell_h, samples_per_axis, style))
        return NULL;
    want = order(scalar, (unsigned)cell_w, (unsigned)cell_h, (unsigned)samples_per_axis, style);
    hi = c->entries;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        const uint8_t *e = c->index + mid * ENTRY;
        uint64_t at = order(rd32(e), rd16(e + 4), rd16(e + 6), e[8], e[9]);
        if (at == want)
            return c->floats + rd32(e + 12);
        if (at < want)
            lo = mid + 1;
        else
            hi = mid;
    }
    return NULL;
}

struct slot {
    uint64_t at;
    size_t i;
};

static int by_order(const void *a, const void *b)
{
    const struct slot *x = a, *y = b;
    return x->at < y->at ? -1 : x->at > y->at;
}

static int put(FILE *f, const void *p, size_t n)
{
    return fwrite(p, 1, n, f) == n ? NEURONTE_OK : NEURONTE_ERR_IO;
}

int neuronte_cells_write(const char *cells_path, const char *weights_path, const neuronte *n,
                         int snap_below, const struct neuronte_cells_key *keys,
                         const float *const *cells, size_t count)
{
    struct weights_id id;
    struct slot *slots = NULL;
    uint8_t head[HEADER] = { 0 }, *index = NULL;
    float *scratch = NULL;
    char *tmp = NULL;
    FILE *f = NULL;
    uint64_t floats = 0, sum = 0;
    size_t i, most = 0, plen;
    int rc = NEURONTE_OK;

    if (!cells_path || !weights_path || !n || snap_below < -1 || (count && !keys) ||
        count > (SIZE_MAX - HEADER) / ENTRY)
        return NEURONTE_ERR_ARG;
    slots = malloc((count ? count : 1) * sizeof *slots);
    if (!slots)
        return NEURONTE_ERR_NOMEM;
    for (i = 0; i < count; i++) {
        const struct neuronte_cells_key *k = &keys[i];
        size_t area = (size_t)k->cell_w * k->cell_h;
        if (!key_fits(k->scalar, k->cell_w, k->cell_h, k->samples, k->style) ||
            neuronte_untrained(n, k->scalar) != 0 || (cells && !cells[i])) {
            rc = NEURONTE_ERR_ARG;
            goto done;
        }
        slots[i].at = order(k->scalar, k->cell_w, k->cell_h, k->samples, k->style);
        slots[i].i = i;
        floats += area;
        if (area > most)
            most = area;
    }
    if (floats > UINT32_MAX) {
        rc = NEURONTE_ERR_ARG;
        goto done;
    }
    qsort(slots, count, sizeof *slots, by_order);
    for (i = 1; i < count; i++)
        if (slots[i].at == slots[i - 1].at) {
            rc = NEURONTE_ERR_ARG;
            goto done;
        }
    rc = identify(weights_path, 1, &id);
    if (rc != NEURONTE_OK)
        goto done;
    scratch = malloc((most ? most : 1) * sizeof *scratch);
    index = calloc(count ? count : 1, ENTRY);
    plen = strlen(cells_path);
    tmp = malloc(plen + 40);
    if (!scratch || !tmp || !index) {
        rc = NEURONTE_ERR_NOMEM;
        goto done;
    }
#ifdef NEURONTE_CELLS_POSIX
    snprintf(tmp, plen + 40, "%s.%ld.tmp", cells_path, (long)getpid());
#else
    snprintf(tmp, plen + 40, "%s.tmp", cells_path);
#endif
    f = fopen(tmp, "wb");
    if (!f) {
        rc = NEURONTE_ERR_IO;
        goto done;
    }
    memcpy(head, MAGIC, sizeof MAGIC);
    wr32(head + 8, NEURONTE_CELLS_VERSION);
    wr32(head + 12, KIND_COVERAGE);
    wr32(head + 16, HEADER);
    wr32(head + 20, ENTRY);
    wr64(head + 24, count);
    wr64(head + 32, floats);
    wr64(head + 40, HEADER + (uint64_t)count * ENTRY + floats * 4);
    wr64(head + 48, id.size);
    wr64(head + 56, (uint64_t)id.sec);
    wr32(head + 64, id.nsec);
    wr32(head + 68, (uint32_t)snap_below);
    {
        float one = 1.0f;
        memcpy(head + 72, &one, 4);
        if (!float_layout(head + 72)) {
            rc = NEURONTE_ERR_ARG; /* this machine's floats are not the file's */
            goto done;
        }
    }
    memcpy(head + 80, id.sha, 32);
    for (i = 0; i < count; i++) {
        const struct neuronte_cells_key *k = &keys[slots[i].i];
        uint8_t *entry = index + i * ENTRY;
        wr32(entry, k->scalar);
        wr16(entry + 4, k->cell_w);
        wr16(entry + 6, k->cell_h);
        entry[8] = k->samples;
        entry[9] = k->style;
        wr32(entry + 12, (uint32_t)sum);
        sum += (uint64_t)k->cell_w * k->cell_h;
    }
    wr64(head + 112, fnv(head, index, count * ENTRY));
    rc = put(f, head, HEADER);
    if (rc == NEURONTE_OK)
        rc = put(f, index, count * ENTRY);
    for (i = 0; i < count && rc == NEURONTE_OK; i++) {
        const struct neuronte_cells_key *k = &keys[slots[i].i];
        size_t area = (size_t)k->cell_w * k->cell_h, p;
        const float *src = cells ? cells[slots[i].i] : scratch;
        if (!cells)
            rc = neuronte_coverage_styled(n, k->scalar, k->cell_w, k->cell_h, k->samples,
                                          k->style, scratch);
        for (p = 0; p < area && rc == NEURONTE_OK; p++)
            if (!(src[p] >= 0.0f && src[p] <= 1.0f))
                rc = NEURONTE_ERR_ARG;
        if (rc == NEURONTE_OK)
            rc = put(f, src, area * sizeof *src);
    }
    if (rc == NEURONTE_OK && fflush(f))
        rc = NEURONTE_ERR_IO;
#ifdef NEURONTE_CELLS_POSIX
    /* On the disk before it takes the name. */
    if (rc == NEURONTE_OK && fsync(fileno(f)))
        rc = NEURONTE_ERR_IO;
#endif
    if (fclose(f) && rc == NEURONTE_OK)
        rc = NEURONTE_ERR_IO;
    f = NULL;
    if (rc == NEURONTE_OK && rename(tmp, cells_path))
        rc = NEURONTE_ERR_IO;
    if (rc != NEURONTE_OK)
        remove(tmp);
done:
    if (f) {
        fclose(f);
        remove(tmp);
    }
    free(tmp);
    free(index);
    free(scratch);
    free(slots);
    return rc;
}
