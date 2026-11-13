"""Write the shipped video helper files from trained parents, or refuse.

Reads the parents from train/video.py and the results of
train/evaluate_video_helpers.py (run with --grid-seed). Both model seeds
must pass the speed and quality gates on the held-out clips and on the
640x384 clip; otherwise nothing is written and the exit status is 1.
Seed 0 is the one shipped. The gates are not options.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('parents',type=Path);p.add_argument('results',type=Path)
    p.add_argument('--training-results',type=Path,required=True,help='results.json written by train/video.py')
    p.add_argument('--weights',type=Path,default=ROOT/'weights/neuronte-split-v5.nrt')
    p.add_argument('--version',default='v1');p.add_argument('--output',type=Path,default=ROOT/'weights')
    a=p.parse_args()
    results=json.loads(a.results.read_text())
    if [r.get('seed') for r in results]!=[0,1]:raise SystemExit('results must hold model seeds 0 and 1')
    failed=[f"seed {r['seed']} {where} {gate}" for r in results for where in ('heldout','grid_80x24')
            for gate in ('speed_pass','quality_pass') if r.get(where,{}).get(gate) is not True]
    failed+=[f"seed {r['seed']} validation chose no K" for r in results if r.get('selection_pass') is not True]
    if failed:
        print('not adopted: '+'; '.join(failed));return 1
    bundle=sha(a.weights);k=results[0]['heldout']['k']
    acceptance=dict(protocol=2,heldout=[r['heldout'] for r in results],
                    selection='seed0, both seeds pass',grid_80x24=[r['grid_80x24'] for r in results])
    policies=dict(speed=dict(candidates=k),
                  quality=dict(local_ssim_loss_max=.0001,frame_ssim_loss_max=.001,proposal='learned temporal switch'))
    for kind,policy in policies.items():
        parent=a.parents/f'{kind}-seed0.json';doc=json.loads(parent.read_text())
        if doc.get('scalar_bundle_sha256')!=bundle:raise SystemExit(f'{parent} was not trained against {a.weights.name}')
        doc.update(parent_sha256=sha(parent),inference=policy,acceptance=acceptance)
        (a.output/f'neuronte-video-{kind}-{a.version}.json').write_text(json.dumps(doc,separators=(',',':'))+'\n')
    scores=dict(weights=a.weights.name,weights_sha256=bundle,parent_training=json.loads(a.training_results.read_text()),
                revised_final_runtime=results)
    (a.output/f'neuronte-video-helpers-{a.version}.scores.json').write_text(json.dumps(scores,indent=1)+'\n')
    print(f'adopted seed 0, K={k}');return 0

if __name__=='__main__':raise SystemExit(main())
