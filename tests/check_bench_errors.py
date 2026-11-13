#!/usr/bin/env python3
"""A failed raster must never become a fast benchmark sample. MIT licence."""

import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STUB = r'''
#include "neuronte.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct neuronte { int bad; };
static int live, registered;
static void check_closed(void) {
    if (live) { fputs("unclosed benchmark handles\n", stderr); _Exit(99); }
}
int neuronte_open_file(const char *name, neuronte **out) {
    *out = NULL;
    if (!registered) { atexit(check_closed); registered = 1; }
    if (!strcmp(name, "open-fails")) return NEURONTE_ERR_FORMAT;
    *out = malloc(sizeof **out);
    if (!*out) return NEURONTE_ERR_NOMEM;
    (*out)->bad = !strcmp(name, "coverage-fails"); live++; return 0;
}
void neuronte_close(neuronte *n) { if (n) { live--; free(n); } }
int neuronte_coverage(const neuronte *n, uint32_t c, int w, int h, int ss, float *out) {
    (void)c; (void)ss;
    if (n->bad) return NEURONTE_ERR_ARG;
    memset(out, 0, (size_t)w * h * sizeof *out); return 0;
}
size_t neuronte_parameters(const neuronte *n) { (void)n; return 1; }
int neuronte_nets(const neuronte *n) { (void)n; return 1; }
int neuronte_route(const neuronte *n, uint32_t c) { (void)n; (void)c; return 0; }
size_t neuronte_utf8_decode(const char *s, size_t len, uint32_t *c) {
    if (!len) return 0; *c = (unsigned char)*s; return 1;
}
'''


class BenchmarkFailures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="neuronte-bench-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(cls.temporary.name)
        stub = root / "stub.c"
        stub.write_text(STUB)
        cls.binary = root / "bench"
        subprocess.run(shlex.split(os.environ.get("CC", "cc")) + [
            "-std=c11", "-O2", "-I", str(ROOT / "include"),
            str(ROOT / "tools/neuronte-bench.c"), str(stub), "-o", str(cls.binary)], check=True)

    def test_failures_close_handles_and_refuse_a_comparison(self):
        for names in [("coverage-fails",), ("good", "coverage-fails"),
                      ("coverage-fails", "good"), ("good", "open-fails")]:
            with self.subTest(names=names):
                run = subprocess.run([str(self.binary), *names], text=True, capture_output=True)
                self.assertEqual(run.returncode, 1, run.stderr)
                self.assertNotIn("unclosed", run.stderr)
                self.assertNotRegex(run.stdout, r"(?m)^ascii\s+95\s")
                self.assertTrue("coverage failed" in run.stderr or "cannot load" in run.stderr)

    def test_success_still_reports_and_closes_handles(self):
        for names in [("good",), ("good", "good")]:
            run = subprocess.run([str(self.binary), *names], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertFalse(run.stderr)
            self.assertIn("ms", run.stdout)


if __name__ == "__main__":
    unittest.main()
