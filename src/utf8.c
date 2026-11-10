/* UTF-8 to one Unicode scalar. MIT licence. See LICENSE. */
#include "neuronte.h"

size_t neuronte_utf8_decode(const char *s, size_t len, uint32_t *scalar)
{
    const unsigned char *p = (const unsigned char *)s;
    uint32_t cp;
    unsigned lo = 0x80, hi = 0xBF, c;
    size_t need, i;

    if (!s || len == 0) {
        if (scalar)
            *scalar = NEURONTE_REPLACEMENT;
        return 0;
    }
    c = p[0];
    if (c < 0x80) {
        if (scalar)
            *scalar = c;
        return 1;
    }
    /* Lead bytes and the range allowed for the second byte, from the
     * well-formed sequences table of the Unicode standard (3-7). */
    if (c >= 0xC2 && c <= 0xDF) {
        need = 1; cp = c & 0x1F;
    } else if (c == 0xE0) {
        need = 2; cp = c & 0x0F; lo = 0xA0;
    } else if ((c >= 0xE1 && c <= 0xEC) || c == 0xEE || c == 0xEF) {
        need = 2; cp = c & 0x0F;
    } else if (c == 0xED) {
        need = 2; cp = c & 0x0F; hi = 0x9F; /* no surrogates */
    } else if (c == 0xF0) {
        need = 3; cp = c & 0x07; lo = 0x90;
    } else if (c >= 0xF1 && c <= 0xF3) {
        need = 3; cp = c & 0x07;
    } else if (c == 0xF4) {
        need = 3; cp = c & 0x07; hi = 0x8F; /* nothing above U+10FFFF */
    } else {
        if (scalar)
            *scalar = NEURONTE_REPLACEMENT;
        return 1;
    }
    for (i = 1; i <= need; i++) {
        unsigned b;
        if (i >= len) {
            if (scalar)
                *scalar = NEURONTE_REPLACEMENT;
            return i;
        }
        b = p[i];
        if (b < lo || b > hi) {
            if (scalar)
                *scalar = NEURONTE_REPLACEMENT;
            return i;
        }
        lo = 0x80;
        hi = 0xBF;
        cp = (cp << 6) | (b & 0x3F);
    }
    if (scalar)
        *scalar = cp;
    return need + 1;
}
