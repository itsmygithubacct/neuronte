"""Difficulty-balanced partition of the 300 emoji into N experts of near-equal glyph count,
using v0's published per-layer 16 px IoUs (weights/neuronte-emoji-v0.quality.json, mean of
seeds 0 and 1) as the difficulty proxy. Greedy: largest deficit (sum of 1 - IoU) first, to the part whose
mean stays highest, among parts with room; then pairwise swaps that raise the worst part's mean. usage: balance.py N [OUT.json]"""
import json, sys
import numpy as np
from pathlib import Path
W = Path(__file__).resolve().parents[1]
N = int(sys.argv[1])
q = json.loads((W / 'weights/neuronte-emoji-v0.quality.json').read_text())['seeds']
order = sorted(int(g['scalar'][2:], 16) for g in json.loads((W / 'font/emoji-manifest.json').read_text())['glyphs'])
def per_glyph(sd):
    rows = {}
    for e in q[sd]['experts'].values():
        for r in e['sizes']['16']['layers']:
            if r['target_coverage'] > 0:
                c = int(r['code'][2:], 16); rows.setdefault(c - 0x110000 if c >= 0x110000 else c, []).append(r['iou'])
    return rows
s0, s1 = per_glyph('0'), per_glyph('1')
proxy = {s: [(a + b) / 2 for a, b in zip(s0[s], s1[s])] for s in order}
cap = [len(order) // N + (1 if i < len(order) % N else 0) for i in range(N)]
D = {s: sum(1 - x for x in proxy[s]) for s in order}; Lc = {s: len(proxy[s]) for s in order}
parts = [[] for _ in range(N)]; dsum = [0.] * N; lsum = [0] * N
# greedy: largest deficit first, to the part whose mean after adding stays highest
for s in sorted(order, key=lambda s: (-D[s], s)):
    i = min((i for i in range(N) if len(parts[i]) < cap[i]), key=lambda i: ((dsum[i] + D[s]) / (lsum[i] + Lc[s]), i))
    parts[i].append(s); dsum[i] += D[s]; lsum[i] += Lc[s]
# swap refinement: raise the worst part's mean while it improves (deterministic)
def worst():
    return max(range(N), key=lambda i: (dsum[i] / lsum[i], -i))
for _ in range(20000):
    w = worst(); cur = dsum[w] / lsum[w]; best = None
    for a in parts[w]:
        for j in range(N):
            if j == w: continue
            for b in parts[j]:
                nw = (dsum[w] - D[a] + D[b]) / (lsum[w] - Lc[a] + Lc[b]); nj = (dsum[j] - D[b] + D[a]) / (lsum[j] - Lc[b] + Lc[a])
                m = max(nw, nj)
                if m < cur - 1e-12 and (best is None or m < best[0]): best = (m, a, j, b)
    if best is None: break
    _, a, j, b = best
    parts[w].remove(a); parts[j].remove(b); parts[w].append(b); parts[j].append(a)
    dsum[w] += D[b] - D[a]; dsum[j] += D[a] - D[b]; lsum[w] += Lc[b] - Lc[a]; lsum[j] += Lc[a] - Lc[b]
parts = [sorted(p) for p in parts]
parts.sort(key=lambda p: p[0])
def means(rows): return [float(np.mean([x for s in p for x in rows[s]])) for p in parts]
m0, m1 = means(s0), means(s1)
print(N, 'parts; v0 seed0 per-part 16px mean min %.4f, seed1 min %.4f; glyphs %s; layers %s' % (
    min(m0), min(m1), sorted(set(map(len, parts))), [sum(len(proxy[s]) for s in p) for p in parts]))
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(json.dumps({'format': 'neuronte-emoji-partition', 'version': 1, 'parts': N,
        'method': __doc__.strip().splitlines()[0] + ' ' + ' '.join(__doc__.strip().splitlines()[1:]),
        'groups': [[f'U+{s:04X}' for s in p] for p in parts],
        'v0_proxy_part_means': {'seed0': m0, 'seed1': m1}}, indent=1) + '\n')
