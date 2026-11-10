/* UTF-8 decoding cases. No weights needed. MIT licence. */
#include "neuronte.h"

#include <stdio.h>
#include <string.h>

static int failed;

static void check(const char *name, const char *s, size_t len, uint32_t want, size_t want_len)
{
    uint32_t got = 0x12345678;
    size_t n = neuronte_utf8_decode(s, len, &got);
    if (got != want || n != want_len) {
        printf("FAIL %s: got U+%04X after %zu bytes, want U+%04X after %zu\n", name, (unsigned)got, n,
               (unsigned)want, want_len);
        failed = 1;
    }
}

/* Count the scalars a whole string decodes to, and check each one. */
static void sequence(const char *name, const char *s, size_t len, const uint32_t *want, int count)
{
    size_t off = 0;
    int i = 0;
    while (off < len) {
        uint32_t got;
        off += neuronte_utf8_decode(s + off, len - off, &got);
        if (i >= count || got != want[i]) {
            printf("FAIL %s: scalar %d is U+%04X\n", name, i, (unsigned)got);
            failed = 1;
            return;
        }
        i++;
    }
    if (i != count) {
        printf("FAIL %s: %d scalars, want %d\n", name, i, count);
        failed = 1;
    }
}

int main(void)
{
    check("ASCII A", "A", 1, 0x41, 1);
    check("NUL", "\0", 1, 0, 1);
    check("DEL", "\x7f", 1, 0x7F, 1);
    check("two bytes", "\xc3\xa9", 2, 0xE9, 2);
    check("three bytes", "\xe4\xb8\xad", 3, 0x4E2D, 3);
    check("four bytes", "\xf0\x9f\x98\x80", 4, 0x1F600, 4);
    check("last scalar", "\xf4\x8f\xbf\xbf", 4, 0x10FFFF, 4);
    check("U+FFFD itself", "\xef\xbf\xbd", 3, 0xFFFD, 3);
    check("empty", "", 0, NEURONTE_REPLACEMENT, 0);
    check("lone continuation", "\x80", 1, NEURONTE_REPLACEMENT, 1);
    check("overlong C0", "\xc0\xaf", 2, NEURONTE_REPLACEMENT, 1);
    check("overlong E0", "\xe0\x80\xaf", 3, NEURONTE_REPLACEMENT, 1);
    check("overlong F0", "\xf0\x80\x80\xaf", 4, NEURONTE_REPLACEMENT, 1);
    check("surrogate", "\xed\xa0\x80", 3, NEURONTE_REPLACEMENT, 1);
    check("above U+10FFFF", "\xf4\x90\x80\x80", 4, NEURONTE_REPLACEMENT, 1);
    check("F5 lead", "\xf5\x80\x80\x80", 4, NEURONTE_REPLACEMENT, 1);
    check("FF", "\xff", 1, NEURONTE_REPLACEMENT, 1);
    check("truncated three", "\xe4\xb8", 2, NEURONTE_REPLACEMENT, 2);
    check("truncated four", "\xf0\x9f\x98", 3, NEURONTE_REPLACEMENT, 3);
    check("bad second byte", "\xe4\x41", 2, NEURONTE_REPLACEMENT, 1);
    check("bad third byte", "\xe4\xb8\x41", 3, NEURONTE_REPLACEMENT, 2);
    {
        /* A bad byte must not swallow the character after it. */
        static const uint32_t want[] = {0x41, 0xFFFD, 0x42, 0xFFFD, 0x4E2D, 0xFFFD};
        sequence("mixed", "A\xff" "B\xe4\xb8" "\xe4\xb8\xad\x80", 9, want, 6);
    }
    {
        /* The byte 0x41 and the UTF-8 encoding of U+0041 are the same input. */
        uint32_t a, b;
        neuronte_utf8_decode("A", 1, &a);
        neuronte_utf8_decode("\x41", 1, &b);
        if (a != b) {
            printf("FAIL ASCII and UTF-8 differ\n");
            failed = 1;
        }
    }
    puts(failed ? "test_utf8: FAILED" : "test_utf8: passed");
    return failed;
}
