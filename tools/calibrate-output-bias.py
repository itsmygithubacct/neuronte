"""Derive a model with explicit, source-bound offsets to its output biases.

This changes signed-distance predictions. It does not change glyph targets,
coverage rules, palette heads or routes. Acceptance must be rerun on the packed
result; this tool does not assert quality or approval.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--offsets',required=True,help='one offset for all outputs, or comma-separated offsets per output')
    a=p.parse_args()
    if a.source.resolve()==a.out.resolve():p.error('output must preserve the original source file')
    raw=a.source.read_bytes();d=json.loads(raw)
    if d.get('format') not in ('neuronte-weights','neuronte-colour-weights') or d.get('version')!=1:
        p.error('expected a version1 Neuronte model')
    if 'output_bias_calibration' in d['training']:p.error('source already has output-bias calibration')
    layer=d['layers']['out'];count=layer['rows']
    try:offsets=[float(v) for v in a.offsets.split(',')]
    except ValueError:p.error('offsets must be finite numbers')
    if len(offsets)==1:offsets*=count
    if len(offsets)!=count or not all(math.isfinite(v) for v in offsets):
        p.error('provide one finite offset or one per output')
    before=np.asarray(layer['bias'],dtype=np.float32)
    if before.shape!=(count,):p.error('invalid output bias shape')
    after=before+np.asarray(offsets,dtype=np.float32)
    if not np.isfinite(after).all():p.error('calibration must retain finite weights')
    layer['bias']=[float(v) for v in after]
    d['training']['output_bias_calibration']={
        'version':1,'method':'add float32 offsets to output-layer biases',
        'source_sha256':hashlib.sha256(raw).hexdigest(),
        'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'offsets':offsets,'bias_before':[float(v) for v in before],
        'bias_after':layer['bias'],'units':'normalized signed distance; physical shift is tau times offset',
        'acceptance':'requires independent packed C and visual validation'}
    a.out.write_text(json.dumps(d)+'\n')
    print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),
                      'output_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'offsets':offsets}))


if __name__=='__main__':main()
