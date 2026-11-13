"""Pack spatial decomposition exports as an identity-mapped tiled expert.

MIT licence; see LICENSE.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train'))
import decompose
import pack


def build(paths):
    docs=[json.loads(Path(p).read_text()) for p in paths]
    if not docs:raise ValueError('no tile nets')
    parts=[]
    for doc in docs:
        info=doc['training']['experiment']
        parts.append(info)
        if doc['format']!='neuronte-weights' or doc['version']!=1:
            raise ValueError('expected distance nets')
    labels=parts[0]['scalars']
    if any(p['scalars']!=labels or p['seed']!=parts[0]['seed'] or
           p['identity']!=parts[0]['identity'] for p in parts):
        raise ValueError('tile training identities differ')
    cols=sorted({v for p in parts for v in p['region'][:2]})
    rows=sorted({v for p in parts for v in p['region'][2:]})
    expected=[[x0,x1,y0,y1] for y0,y1 in zip(rows,rows[1:]) for x0,x1 in zip(cols,cols[1:])]
    if [p['region'] for p in parts]!=expected or cols[0]!=0 or cols[-1]!=1 or rows[0]!=0 or rows[-1]!=2:
        raise ValueError('tiles must exactly cover the cell in row-major order')
    if any(abs(float(d['shape']['tau'])*(p['region'][1]-p['region'][0])-.15)>1e-7 for d,p in zip(docs,parts)):
        raise ValueError('tile distance scale differs')
    return {'format':'neuronte-tiled-weights','version':1,'first':'U+0000','last':'U+10FFFF',
            'columns':cols,'rows':rows,
            'tiles':[{'net':i,'mask':'0x1FFFFF','base':'U+0000','code':'place'} for i in range(len(docs))],
            'nets':docs,'training':{'set':parts[0]['identity']['teacher']['identity'].get('expert','ascii'),'labelled':' '.join(f'U+{c:04X}' for c in labels),
            'tile_sources':[{'file':Path(p).name,'sha256':decompose.digest(p)} for p in paths]}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('out',type=Path);p.add_argument('models',nargs='+',type=Path)
    a=p.parse_args()
    if a.out.resolve() in {x.resolve() for x in a.models}:p.error('output must be distinct from inputs')
    doc=build(a.models)
    a.out.write_text(json.dumps(doc)+'\n')
    a.out.with_suffix('.nrt').write_bytes(pack.pack(a.out))
    print(a.out)


if __name__=='__main__':main()
