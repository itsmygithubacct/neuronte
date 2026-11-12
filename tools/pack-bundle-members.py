"""Repack a bundle and its standalone members once per source model."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train'))
import pack

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('out',type=Path);p.add_argument('nets',nargs='+')
a=p.parse_args()
reserved={Path(path).resolve() for path in a.nets}|{Path(path).with_suffix('.nrt').resolve() for path in a.nets}
if a.out.resolve() in reserved:p.error('bundle output must be distinct from source and standalone member files')
images=[pack.pack(path) for path in a.nets]
data,_=pack._bundle_images(a.nets,images)
for source,image in zip(a.nets,images):
    path=Path(source).with_suffix('.nrt');path.write_bytes(image)
    print(path,len(image),'bytes')
a.out.write_bytes(data)
print(a.out,len(data),'bytes')
