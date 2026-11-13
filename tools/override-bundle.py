"""Append labelled experts to a bundle while preserving every unlabelled route.

The old members and gate outputs are retained byte for byte. New experts are
selected only by explicit scalar ranges. No existing model is overwritten.
MIT licence; see LICENSE.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'train'))
import pack


def override(base, additions):
    """Return a v2 bundle. additions holds (packed_member, scalar_set) pairs."""
    if len(base) < 28 or base[:8] != b'NEURONTE':
        raise ValueError('expected a packed bundle')
    version, count, nranges, fallback, width = struct.unpack_from('<5I', base, 8)
    if version != 2 or not 1 <= count <= 128 or fallback >= count or width > 256:
        raise ValueError('unsupported base bundle header')
    if not additions or count + len(additions) > 128:
        raise ValueError('invalid added member count')
    at = 28
    sizes = list(struct.unpack_from(f'<{count}I', base, at)); at += count * 4
    routes = {}
    for _ in range(nranges):
        first, last, net = struct.unpack_from('<3I', base, at); at += 12
        if first > last or last > 0x10ffff or net >= count:
            raise ValueError('invalid base route')
        for scalar in range(first, last + 1):
            if scalar in routes:
                raise ValueError('overlapping base routes')
            routes[scalar] = net
    gate = b''
    if width:
        masks = base[at:at+172]; at += 172
        hidden = base[at:at+4*65*width]; at += 4*65*width
        weights = base[at:at+4*count*width]; at += 4*count*width
        bias = base[at:at+4*count]; at += 4*count
        w1 = np.frombuffer(hidden, '<f4', count=width*64).reshape(width,64).astype(np.float64)
        b1 = np.frombuffer(hidden, '<f4', offset=4*width*64).astype(np.float64)
        wo = np.frombuffer(weights, '<f4').reshape(count,width).astype(np.float64)
        bo = np.frombuffer(bias, '<f4').astype(np.float64)
        # Every input feature is +/-1. Bound all old logits in magnitude,
        # with generous room for native float accumulation rounding.
        bound = np.max(np.abs(wo) @ (np.abs(w1).sum(1)+np.abs(b1)) + np.abs(bo))
        floor = np.float32(-2 * max(1., bound) - 1.)
        if not np.isfinite(bound) or not np.isfinite(floor):
            raise ValueError('gate cannot be safely extended')
        gate = masks + hidden + weights + bytes(4*len(additions)*width) + bias + struct.pack(f'<{len(additions)}f', *([floor]*len(additions)))
    members = []
    for size in sizes:
        member = base[at:at+size]; at += size
        if len(member) != size:
            raise ValueError('truncated member')
        members.append(member)
    if at != len(base):
        raise ValueError('base has trailing bytes')
    replaced = set()
    for image, scalars in additions:
        if not scalars or not set(scalars) <= routes.keys() or replaced.intersection(scalars):
            raise ValueError('overrides must be disjoint subsets of known base labels')
        if len(image) < 12 or image[:8] != b'NEURONTE' or struct.unpack_from('<I',image,8)[0] not in (1,3,6):
            raise ValueError('unsupported added member')
        for scalar in scalars:
            routes[scalar] = len(members)
        replaced.update(scalars); members.append(image)
    ranges = []
    for scalar in sorted(routes):
        net = routes[scalar]
        if ranges and ranges[-1][1]+1 == scalar and ranges[-1][2] == net:
            ranges[-1][1] = scalar
        else:
            ranges.append([scalar,scalar,net])
    header = b'NEURONTE' + struct.pack('<5I',2,len(members),len(ranges),fallback,width)
    lengths = struct.pack(f'<{len(members)}I', *(len(x) for x in members))
    table = b''.join(struct.pack('<3I',*r) for r in ranges)
    return header + lengths + table + gate + b''.join(members)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('models', nargs='+', type=Path, help='labelled weight JSON files')
    args = parser.parse_args()
    if args.out.resolve() in {args.base.resolve(), *(p.resolve() for p in args.models)}:
        parser.error('output must be a new, distinct model path')
    additions = [(pack.pack(path), pack.scalars(path)[1]) for path in args.models]
    args.out.write_bytes(override(args.base.read_bytes(), additions))
    print(args.out, args.out.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
