"""Check a bundle with a replaced box-drawing expert through the public draw API.

usage: python3 tools/draw-api-check.py NEW.nrt OLD.nrt [--lib build/libneuronte.so]
           [--sizes 8x16,...] [--out REPORT.json]

For every box-drawing and shade scalar at every size, on a fresh handle:
cold neuronte_draw_scalar() (empty cache), then a warm one (cache hit),
must each give exactly the white-over-transparent ARGB composited from
neuronte_coverage() with the compositor's float rounding; a draw at an
odd offset hanging off the buffer edge must equal the clipped cell.
neuronte_draw_utf8() of box text must equal per-scalar draws.
Every scalar the OLD bundle's other members were trained on must give
bit-identical coverage in NEW, and every other expert keeps its index.
Unknown scalars: the route family check is tools/replace-bundle-expert.py's.
MIT licence; see LICENSE.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BOX = list(range(0x2500, 0x2580))+[0x2591, 0x2592, 0x2593]
P = ctypes.POINTER


def load(path):
    lib = ctypes.CDLL(str(Path(path).resolve()))
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, P(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_route.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.neuronte_nets.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int, P(ctypes.c_float)]
    lib.neuronte_draw_scalar.argtypes = [ctypes.c_void_p, P(ctypes.c_uint32), ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32]
    lib.neuronte_draw_utf8.argtypes = [ctypes.c_void_p, P(ctypes.c_uint32), ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t,
                                       ctypes.c_uint32]
    return lib


def handle(lib, path):
    h = ctypes.c_void_p()
    if lib.neuronte_open_file(str(path).encode(), ctypes.byref(h)) != 0:
        raise SystemExit(f'{path}: cannot open')
    return h


def coverage(lib, h, s, w, hh):
    out = np.zeros(w*hh, np.float32)
    if lib.neuronte_coverage(h, s, w, hh, 0, out.ctypes.data_as(P(ctypes.c_float))) != 0:
        raise SystemExit(f'coverage U+{s:04X}')
    return out.reshape(hh, w)


def reference(cov):
    a = (cov.astype(np.float32)*np.float32(255)).astype(np.float32)+np.float32(.5)
    alpha = a.astype(np.float32).astype(np.int64)
    return np.where(cov > 0, (alpha << 24) | 0xFFFFFF, 0).astype(np.uint32)


def draw(lib, h, buf, x, y, w, hh, s):
    bh, bw = buf.shape
    rc = lib.neuronte_draw_scalar(h, buf.ctypes.data_as(P(ctypes.c_uint32)), bw, bw, bh, x, y, w, hh, s, 0xFFFFFFFF)
    if rc != 0:
        raise SystemExit(f'draw U+{s:04X}: {rc}')


def members(blob):
    k, r, _, g = struct.unpack_from('<4I', blob, 12)
    lengths = struct.unpack_from(f'<{k}I', blob, 28)
    ranges = [struct.unpack_from('<3I', blob, 28+4*k+12*i) for i in range(r)]
    return k, ranges


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('new', type=Path)
    p.add_argument('old', type=Path)
    p.add_argument('--lib', default=str(ROOT/'build'/'libneuronte.so'))
    p.add_argument('--sizes', default='8x16,16x32,48x96,7x13,23x47,24x48,25x49,11x23,16x48,12x30,3x6')
    p.add_argument('--other-sizes', default='8x16,16x32')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    lib = load(a.lib)
    report = {'new': str(a.new), 'new_sha256': hashlib.sha256(a.new.read_bytes()).hexdigest(),
              'old': str(a.old), 'old_sha256': hashlib.sha256(a.old.read_bytes()).hexdigest(),
              'library_sha256': hashlib.sha256(Path(a.lib).read_bytes()).hexdigest(), 'draw': {}, 'others': {}}
    failures = []
    for size in a.sizes.split(','):
        w, hh = map(int, size.split('x'))
        h = handle(lib, a.new)
        bad = 0
        for s in BOX:
            want = reference(coverage(lib, h, s, w, hh))
            for state in ('cold', 'warm'):
                buf = np.zeros((hh, w), np.uint32)
                draw(lib, h, buf, 0, 0, w, hh, s)
                if not np.array_equal(buf, want):
                    bad += 1
                    failures.append(f'{size} U+{s:04X} {state}')
            buf = np.zeros((hh+3, w+5), np.uint32)
            draw(lib, h, buf, 5, -2, w, hh, s)
            if not np.array_equal(buf[:hh-2, 5:], want[2:, :]) or buf[:, :5].any() or buf[hh-2:].any():
                bad += 1
                failures.append(f'{size} U+{s:04X} clipped')
        text = '┌─┬─┐│ ├─┼─┤╔═╦═╗║ ╠═╬═╣╭─╮╰─╯╱╲╳░▒▓┄┅┆┇'
        enc = text.encode()
        buf = np.zeros((hh, w*len(text)), np.uint32)
        n = lib.neuronte_draw_utf8(h, buf.ctypes.data_as(P(ctypes.c_uint32)), buf.shape[1], buf.shape[1], hh, 0, 0, w, hh,
                                   enc, len(enc), 0xFFFFFFFF)
        one = np.zeros_like(buf)
        for i, ch in enumerate(text):
            draw(lib, h, one, i*w, 0, w, hh, ord(ch))
        utf8_ok = n == len(text) and np.array_equal(buf, one)
        if not utf8_ok:
            failures.append(f'{size} utf8')
        lib.neuronte_close(h)
        report['draw'][size] = {'glyphs': len(BOX), 'mismatches': bad, 'utf8_cells': n, 'utf8_equal': bool(utf8_ok)}
        print(size, report['draw'][size], flush=True)
    old_blob, new_blob = a.old.read_bytes(), a.new.read_bytes()
    k_old, ranges = members(old_blob)
    k_new, _ = members(new_blob)
    ho, hn = handle(lib, a.old), handle(lib, a.new)
    box_net = lib.neuronte_route(ho, 0x2500)
    for size in a.other_sizes.split(','):
        w, hh = map(int, size.split('x'))
        diff, count = 0, 0
        for first, last, net in ranges:
            if net == box_net:
                continue
            for s in range(first, last+1):
                count += 1
                if lib.neuronte_route(hn, s) != net:
                    failures.append(f'route U+{s:04X}')
                if not np.array_equal(coverage(lib, ho, s, w, hh), coverage(lib, hn, s, w, hh)):
                    diff += 1
        report['others'][size] = {'scalars': count, 'coverage_differences': diff}
        if diff:
            failures.append(f'{size} other experts differ: {diff}')
        print(size, 'other experts', report['others'][size], flush=True)
    report['nets'] = {'old': k_old, 'new': k_new}
    report['failures'] = failures
    report['passed'] = not failures
    if a.out:
        a.out.write_text(json.dumps(report, indent=1)+'\n')
    print('PASS' if not failures else f'FAIL {failures[:10]}')
    sys.exit(0 if not failures else 1)


if __name__ == '__main__':
    main()
