"""Glyph partitions of the colour trainer: --group (contiguous runs in scalar order) and
--partition/--part (a partition file in the tree) select exactly their drawings, both halves
of a wide drawing stay together, the partition file's sha256 is recorded, and bad
combinations are rejected. Tiny CPU runs (grid 8, width 8, 2 steps)."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import strokes  # noqa: E402

env = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'CUDA_VISIBLE_DEVICES': ''}
common = ['--device', 'cpu', '--grid', '8', '--width', '8', '--head-width', '8', '--steps', '2', '--seed', '3', '--log-every', '0',
          '--drawing', 'font/emoji.txt', '--palette', 'font/emoji-palette.txt', '--wide', '--form', 'A']
order = sorted(ord(c) for c in strokes.parse_layers(str(ROOT / 'font/emoji.txt'), strokes.palette(str(ROOT / 'font/emoji-palette.txt'))))
PART = 'font/emoji-partition-balanced-12.json'


def run(out, args, ok=True):
    r = subprocess.run([sys.executable, str(ROOT / 'train/colour.py'), str(out), *common, *args], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    assert (r.returncode == 0) == ok, (args, r.returncode, r.stderr[-500:])
    return json.loads(Path(out).read_text())['training'] if ok else r.stderr


def labelled(t):
    return [int(x[2:], 16) for x in t['labelled'].split()]


with tempfile.TemporaryDirectory(prefix='neuronte-partition-') as d:
    d = Path(d)
    t = run(d / 'g.json', ['--group', '7/150'])
    want = order[len(order) * 7 // 150: len(order) * 8 // 150]
    assert sorted(labelled(t)) == sorted(want + [s + 0x110000 for s in want]), 'group selects a contiguous run, both halves'
    assert t['group'] == '7/150' and t['set'] == 'emoji-g7of150', t['set']
    groups = json.loads((ROOT / PART).read_text())['groups']
    t = run(d / 'p.json', ['--partition', PART, '--part', '5'])
    want = [int(x[2:], 16) for x in groups[5]]
    assert sorted(labelled(t)) == sorted(want + [s + 0x110000 for s in want]), 'partition selects its group, both halves'
    assert t['partition'] == PART and t['part'] == 5 and t['set'] == f'emoji-p5of{len(groups)}', t['set']
    assert t['sources_sha256'][PART] == hashlib.sha256((ROOT / PART).read_bytes()).hexdigest()
    assert 'different partitions' in run(d / 'x.json', ['--group', '0/3', '--shard', '0/3'], ok=False)
    assert 'go together' in run(d / 'y.json', ['--partition', PART], ok=False)
    assert 'not a group' in run(d / 'z.json', ['--partition', PART, '--part', str(len(groups))], ok=False)
print('colour partitions: --group and --partition select exactly their drawings; bad combinations rejected')
