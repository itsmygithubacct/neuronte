"""Create a separate video mask bundle with a narrower coverage transition.

The frozen field output is unchanged. Multiplying its coverage scale tau by
2 makes every 2x4 octant centre land beyond the coverage ramp, with a margin.
This is a video rendering calibration, NOT retraining or a claim that the
field is a newly fitted signed distance. Standard text assets remain intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pack


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights',type=Path,default=Path(__file__).resolve().parents[1]/'weights')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    output=[]
    for name in ['pixel-v1','ascii-v0']:
        parent=args.weights/f'neuronte-{name}.json'
        doc=json.loads(parent.read_text())
        old=doc['shape']['tau']; doc['shape']['tau']=old*2
        doc['video_calibration']=dict(version=1,parent=parent.name,parent_sha256=digest(parent),
             script_sha256=digest(__file__),coverage_scale_gain=2,
             original_tau=old,scope='video-only continuous coverage; no rounding; field layers unchanged',
             required_gate='all 256 octants, 2048 centres, 2x4 ss1, exact binary coverage')
        dest=args.output/f'neuronte-video-{name}.json'
        with dest.open('x') as stream: json.dump(doc,stream,separators=(',',':')); stream.write('\n')
        output.append(str(dest))
    data,_=pack.bundle(output,fallback=1)
    with (args.output/'neuronte-video-masks-v0.nrt').open('xb') as stream: stream.write(data)

if __name__=='__main__': main()
