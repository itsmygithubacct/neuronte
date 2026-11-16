"""Append known-only experts while preserving a bundle's original unknown routing.

The original members remain byte-identical. replace_known reassigns only the
table entries belonging to the selected expert; add_known gives table rows to
scalars that had none. New gate outputs are constant and below
a conservative lower bound on the winning original output, for every code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
import pack


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _parse(base, appended):
    """Split a version 2 bundle and build its gate with `appended` suppressed outputs."""
    if len(base)<28 or base[:8]!=b'NEURONTE':
        raise ValueError('expected a complete version 2 bundle')
    version,nets,nranges,fallback,g=struct.unpack_from('<5I',base,8)
    if version!=2 or not 1<=nets<=128 or not 0<=fallback<nets or not 0<=g<=256:
        raise ValueError('invalid original bundle header')
    if not appended or nets+appended>128:
        raise ValueError('replacement count exceeds bundle limits')
    lengths=struct.unpack_from(f'<{nets}I',base,28)
    off=28+4*nets
    ranges=[struct.unpack_from('<3I',base,off+12*i) for i in range(nranges)]
    if any(a>b or b>0x1fffff or n>=nets or (i and a<=ranges[i-1][1])
           for i,(a,b,n) in enumerate(ranges)):
        raise ValueError('invalid original range table')
    off+=12*nranges
    gate_bytes=b'';bound=None;winning_floor=None
    if g:
        count=43+g*64+g+nets*g+nets
        raw=base[off:off+4*count]
        if len(raw)!=4*count:raise ValueError('truncated original gate')
        floats=np.frombuffer(raw[172:],'<f4').astype(np.float64)
        if not np.isfinite(floats).all():raise ValueError('nonfinite original gate')
        w=floats[:g*64].reshape(g,64);b=floats[g*64:g*65]
        out=floats[g*65:g*65+nets*g].reshape(nets,g);bias=floats[-nets:]
        # Every input is +/-1; ReLU is nonnegative. The wide margin also
        # covers float32 accumulation error, including subnormals.
        hidden_bound=np.abs(b)+np.abs(w).sum(1)+1
        if float(hidden_bound.max())>=1e20:
            raise ValueError('cannot establish a safe hidden activation bound')
        magnitude=np.abs(bias)+np.abs(out)@hidden_bound*2
        bound=float(magnitude.max())
        winning_floor=-float(magnitude.min())
        # All original outputs stay finite, and at least one original row
        # exceeds the newly suppressed outputs. Existing suppressed rows
        # therefore remain valid when several expert replacements are composed.
        if not np.isfinite(magnitude).all() or bound>=1e35 or winning_floor<=-1e20:
            raise ValueError('cannot establish a safe original gate-output bound')
        first=172+4*g*65;last=first+4*nets*g
        gate_bytes=(raw[:last]+bytes(4*appended*g)+raw[last:]+
                    struct.pack(f'<{appended}f',*([-1e30]*appended)))
        off+=len(raw)
    members=[]
    for size in lengths:
        member=base[off:off+size]
        if size<12 or len(member)!=size or member[:8]!=b'NEURONTE' or struct.unpack_from('<I',member,8)[0] not in (1,3,6):
            raise ValueError('invalid original member')
        members.append(member);off+=size
    if off!=len(base):raise ValueError('original bundle length mismatch')
    return nets,ranges,fallback,g,gate_bytes,bound,winning_floor,members


def _member(path):
    path=Path(path);codes=pack.scalars(str(path))[1]
    if not codes:raise ValueError('replacement has no labelled scalars')
    image=pack.pack(str(path))
    if struct.unpack_from('<I',image,8)[0] not in (1,3,6):
        raise ValueError('replacement is not a supported bundle member')
    return codes,image,{'file':path.name,'source_sha256':digest(path.read_bytes()),
                        'packed_sha256':digest(image),'scalars':sorted(codes)}


def _assemble(members,rewritten,fallback,g,gate_bytes):
    total=len(members)
    result=bytearray(b'NEURONTE'+struct.pack('<5I',2,total,len(rewritten),fallback,g))
    result+=struct.pack(f'<{total}I',*map(len,members))
    for row in rewritten:result+=struct.pack('<3I',*row)
    result+=gate_bytes+b''.join(members)
    return bytes(result)


def _merge(rows):
    """Sorted, disjoint (a, b, n) rows with neighbours of one net joined."""
    out=[]
    for a,b,n in sorted(rows):
        if out and out[-1][1]+1==a and out[-1][2]==n:out[-1][1]=b
        else:out.append([a,b,n])
    return out


def replace_known(base, replacements, expert, allow_partial=False):
    """Return packed bytes and a provenance record; replacements are weight JSON paths."""
    nets,ranges,fallback,g,gate_bytes,bound,winning_floor,members=_parse(base,len(replacements))
    if not 0<=expert<nets:
        raise ValueError('invalid original bundle header')
    owner={};sources=[]
    for i,path in enumerate(replacements):
        codes,image,source=_member(path)
        for c in codes:
            if c in owner:raise ValueError('replacement repertoires overlap')
            if not any(a<=c<=b and n==expert for a,b,n in ranges):
                raise ValueError('replacement scalar is outside the selected expert table')
            owner[c]=nets+i
        members.append(image);sources.append(source)
    old_count=sum(b-a+1 for a,b,n in ranges if n==expert)
    if not allow_partial and len(owner)!=old_count:
        raise ValueError('replacement does not cover the complete selected expert')
    rewritten=[]
    def add(a,b,n):
        if a>b:return
        if rewritten and rewritten[-1][1]+1==a and rewritten[-1][2]==n:
            rewritten[-1][1]=b
        else:rewritten.append([a,b,n])
    selected=sorted(owner)
    for a,b,n in ranges:
        cursor=a
        for c in selected:
            if a<=c<=b:
                add(cursor,c-1,n);add(c,c,owner[c]);cursor=c+1
        add(cursor,b,n)
    result=_assemble(members,rewritten,fallback,g,gate_bytes)
    return result,{'schema':'neuronte.known-expert-bundle/v1','base_sha256':digest(base),
        'sha256':digest(result),'bytes':len(result),'original_members':nets,'members':len(members),
        'expert':expert,'partial':allow_partial,'replaced_scalars':len(owner),
        'sources':sources,'ranges':rewritten,'gate_original_magnitude_bound':bound,
        'gate_original_winning_floor':winning_floor,
        'original_member_sha256':[digest(m) for m in members[:nets]],
        'unknown_policy':'original gate outputs and original member bytes retained; appended outputs suppressed'}


def add_known(base, additions):
    """Append nets for scalars that are in no table row yet; return bytes and a record.

    The original members, gate rows and table rows stay as they were; table
    rows are added for the new scalars only, so every other scalar, known or
    unknown, routes exactly as before. The new gate outputs are suppressed,
    as replace_known does, so the gate never picks a new net."""
    nets,ranges,fallback,g,gate_bytes,bound,winning_floor,members=_parse(base,len(additions))
    owner={};sources=[]
    for i,path in enumerate(additions):
        codes,image,source=_member(path)
        for c in codes:
            if c in owner:raise ValueError('addition repertoires overlap')
            if not 0<=c<=0x10ffff or 0xd800<=c<=0xdfff:raise ValueError('addition scalar is not a Unicode scalar value')
            if any(a<=c<=b for a,b,n in ranges):
                raise ValueError('addition scalar is already in the table')
            owner[c]=nets+i
        members.append(image);sources.append(source)
    rewritten=_merge([list(r) for r in ranges]+[[c,c,n] for c,n in owner.items()])
    if [r for r in rewritten if r[2]<nets]!=_merge([list(r) for r in ranges]):
        raise ValueError('original table rows changed')
    result=_assemble(members,rewritten,fallback,g,gate_bytes)
    return result,{'schema':'neuronte.known-addition-bundle/v1','base_sha256':digest(base),
        'sha256':digest(result),'bytes':len(result),'original_members':nets,'members':len(members),
        'added_scalars':len(owner),'sources':sources,'ranges':rewritten,
        'gate_original_magnitude_bound':bound,'gate_original_winning_floor':winning_floor,
        'original_member_sha256':[digest(m) for m in members[:nets]],
        'unknown_policy':'original table rows, gate outputs and member bytes retained; added scalars get table rows; appended outputs suppressed'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('base',type=Path);p.add_argument('output',type=Path)
    p.add_argument('replacements',nargs='+',type=Path);p.add_argument('--expert',type=int,required=True)
    p.add_argument('--allow-partial',action='store_true')
    a=p.parse_args()
    image,record=replace_known(a.base.read_bytes(),a.replacements,a.expert,a.allow_partial)
    a.output.write_bytes(image)
    a.output.with_suffix('.provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'output':a.output.name,'sha256':record['sha256'],'bytes':len(image)}))
