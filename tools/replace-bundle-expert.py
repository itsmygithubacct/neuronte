"""Pack a new bundle in which one expert is replaced by several routed members.

usage: python3 tools/replace-bundle-expert.py OUT.nrt --gate GATE.json --replace I
           --nets NET.json... --members MEMBER.json... [--gate-out NEW_GATE.json]
           [--reference OLD.nrt]

NETS are the original bundle's members in order and GATE its gate. Member I
is replaced by MEMBERS: the first takes index I, the others are appended
after the original members, so every other expert keeps its index. Each
member's labelled scalars are routed to it by the table; together they must
equal the replaced expert's labelled scalars exactly, so table routing is
unchanged for every other scalar.

The gate is extended rather than retrained: its hidden layer and its first
K outputs are copied, and each appended member gets an output with zero
weights and a bias of -1e30, which can never be the first highest output.
A scalar the old gate sent to expert I now goes to the first member; every
other gate decision is unchanged. The derived gate records its parent.

With --reference the old packed bundle is compared: every untouched member
image must be byte-identical, and every scalar from U+0000 to U+10FFFF
(surrogates included, as the library replaces them) must route to the same
expert, counting all replacement members as expert I. Needs build/libneuronte.so.
MIT licence; see LICENSE.
"""
import argparse
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'train'))
import pack  # noqa: E402

NEVER = -1e30


def sha(data):
    return hashlib.sha256(data).hexdigest()


def derive_gate(gate_path, names, replace, members, out_path):
    doc = json.loads(Path(gate_path).read_text())
    k, g = len(doc['nets']), doc['hidden_width']
    if doc['nets'][replace] is None or len(names) != k:
        raise SystemExit('gate and net list differ')
    new = copy.deepcopy(doc)
    new['nets'] = names[:replace]+[members[0]]+names[replace+1:]+members[1:]
    out = new['layers']['out']
    w = list(out['weight'])+[0.0]*(g*(len(members)-1))
    b = list(out['bias'])+[NEVER]*(len(members)-1)
    out.update(rows=len(new['nets']), weight=w, bias=b)
    new['derived'] = {'parent': Path(gate_path).name, 'parent_sha256': sha(Path(gate_path).read_bytes()),
                      'rule': f'copy of the parent; outputs {k}..{len(new["nets"])-1} have zero weights and bias {NEVER}, '
                              f'so they are never selected and every parent decision is kept; expert {replace} is now '
                              f'member {members[0]!r}',
                      'replaced_index': replace}
    new.pop('scores', None)
    Path(out_path).write_text(json.dumps(new)+'\n')
    return out_path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('out', type=Path)
    p.add_argument('--gate', required=True)
    p.add_argument('--replace', type=int, required=True)
    p.add_argument('--nets', nargs='+', required=True)
    p.add_argument('--members', nargs='+', required=True)
    p.add_argument('--gate-out', type=Path)
    p.add_argument('--reference', type=Path)
    p.add_argument('--lib', default=str(ROOT/'build'/'libneuronte.so'))
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    if not 0 <= a.replace < len(a.nets):
        p.error('--replace is not a member index')
    old = set(pack.scalars(a.nets[a.replace])[1])
    new = [set(pack.scalars(m)[1]) for m in a.members]
    if set().union(*new) != old or sum(map(len, new)) != len(old):
        raise SystemExit('replacement members must partition the replaced expert\'s scalars exactly')
    names = [pack.scalars(n)[0] for n in a.nets]
    member_names = [pack.scalars(m)[0] for m in a.members]
    if len(set(names[:a.replace]+names[a.replace+1:]+member_names)) != len(names)-1+len(member_names):
        raise SystemExit('member set names must be distinct')
    gate_out = a.gate_out or a.out.with_suffix('.gate.json')
    derive_gate(a.gate, names, a.replace, member_names, gate_out)
    order = a.nets[:a.replace]+[a.members[0]]+a.nets[a.replace+1:]+a.members[1:]
    data, ranges = pack.bundle(order, str(gate_out))
    a.out.write_bytes(data)
    report = {'bundle': str(a.out), 'sha256': sha(data), 'bytes': len(data), 'gate': str(gate_out),
              'gate_sha256': sha(Path(gate_out).read_bytes()), 'order': order, 'ranges': len(ranges),
              'replaced_index': a.replace, 'member_indices': [a.replace]+list(range(len(a.nets), len(order)))}
    if a.reference:
        ref = a.reference.read_bytes()
        k_old = struct.unpack_from('<I', ref, 12)[0]
        k_new = len(order)
        def images(blob, k):
            r, g = struct.unpack_from('<2I', blob, 16)[0], struct.unpack_from('<I', blob, 24)[0]
            lengths = struct.unpack_from(f'<{k}I', blob, 28)
            off = 28+4*k+12*r+((43+g*64+g+k*g+k)*4 if g else 0)
            out = []
            for n in lengths:
                out.append(blob[off:off+n])
                off += n
            if off != len(blob):
                raise SystemExit('bundle length mismatch')
            return out
        old_images, new_images = images(ref, k_old), images(data, k_new)
        same = [i for i in range(k_old) if i != a.replace and old_images[i] == new_images[i]]
        if len(same) != k_old-1:
            raise SystemExit('an untouched member image differs from the reference')
        lib = ctypes.CDLL(str(Path(a.lib).resolve()))
        lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        lib.neuronte_route.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        handles = []
        for path in (a.reference, a.out):
            h = ctypes.c_void_p()
            if lib.neuronte_open_file(str(path).encode(), ctypes.byref(h)) != 0:
                raise SystemExit(f'{path}: cannot open')
            handles.append(h)
        family = np.arange(k_new)
        family[k_old:] = a.replace
        counts = np.zeros(k_new, np.int64)
        mismatch = 0
        for s in range(0x110000):
            r_old, r_new = lib.neuronte_route(handles[0], s), lib.neuronte_route(handles[1], s)
            counts[r_new] += 1
            if family[r_new] != r_old:
                mismatch += 1
        if mismatch:
            raise SystemExit(f'{mismatch} scalars route to a different expert family')
        report['reference'] = {'path': str(a.reference), 'sha256': sha(ref), 'untouched_members_identical': same,
                               'scalars_checked': 0x110000, 'family_route_mismatches': 0,
                               'routes_per_member': counts.tolist()}
    text = json.dumps(report, indent=1)
    if a.report:
        a.report.write_text(text+'\n')
    print(text)


if __name__ == '__main__':
    main()
