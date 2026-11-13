"""Check the set-generic split trainer against decompose.py and its partitions."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

import decompose as d
import glyphs
import split_expert as s


def analytic(directory, scalars, name):
    yy, xx = np.mgrid[0:17, 0:9]/8
    fields = np.stack([(.4-((xx-.5-.01*i)**2+(yy-1)**2)) for i in range(len(scalars))]).astype(np.float16)
    np.save(directory/'teacher.npy', fields)
    identity = {'grid': 8, 'sources': {}, 'pen': .075, 'set': name, 'scalars': scalars}
    (directory/'teacher.json').write_text(json.dumps({'sha256': d.digest(directory/'teacher.npy'), 'identity': identity}))


class SplitExpertTests(unittest.TestCase):
    def test_partitions(self):
        scalars = [ord(c) for c, _, _ in glyphs.charset('symbol')]
        self.assertEqual(len(scalars), 49)
        for partition in s.PARTITIONS:
            for count in (1, 2, 4, 8, 16):
                parts = s.specs('symbol', scalars, 'repertoire', count, partition)
                got = sorted(c for p in parts for c in p['scalars'])
                self.assertEqual(got, scalars)
                sizes = [len(p['scalars']) for p in parts]
                self.assertLessEqual(max(sizes)-min(sizes), 1)
                self.assertEqual(sum(p['width'] for p in parts), 128)
        for count in (2, 4, 8, 16):
            tiles = s.specs('symbol', scalars, 'spatial', count)
            self.assertAlmostEqual(sum((t['region'][1]-t['region'][0])*(t['region'][3]-t['region'][2]) for t in tiles), 2.)
            self.assertTrue(all(t['scalars'] == scalars for t in tiles))
        # The ASCII inventory is decompose.py's, member for member.
        ascii_ = list(range(32, 127))
        for mode in ('spatial', 'repertoire'):
            for count in d.COUNTS:
                ours = s.specs('ascii', ascii_, mode, count)
                theirs = d.specs(mode, count)
                strip = lambda rows: [{k: v for k, v in r.items() if k != 'name'} for r in rows]
                self.assertEqual(strip(ours), strip(theirs))

    def test_same_weights_as_decompose(self):
        # Same members, teacher, draws and loss: the exported weights must match exactly.
        ascii_ = list(range(32, 127))
        for mode, parts, start in (('repertoire', 4, 1), ('spatial', 4, 2)):
            with tempfile.TemporaryDirectory() as temp:
                a_dir, b_dir = Path(temp)/'a', Path(temp)/'b'
                a_dir.mkdir()
                b_dir.mkdir()
                analytic(a_dir, ascii_, 'ascii')
                analytic(b_dir, ascii_, 'ascii')
                common = dict(mode=mode, parts=parts, seeds='0,1', start=start, batch_models=3, steps=3, device='cpu',
                              unlabelled=1., compile=False, resume=False, log_every=1, checkpoint_every=2, stop_after=None)
                with contextlib.redirect_stdout(io.StringIO()):
                    d.train(argparse.Namespace(directory=a_dir, **common))
                    s.train(argparse.Namespace(directory=b_dir, partition='contiguous', budget=128, **common))
                theirs = sorted(a_dir.glob('ascii-*.json'))
                ours = sorted(b_dir.glob('ascii-*.json'))
                self.assertEqual(len(theirs), 3)
                self.assertEqual(len(ours), 3)
                for x, y in zip(theirs, ours):
                    self.assertEqual(json.loads(x.read_text())['layers'], json.loads(y.read_text())['layers'])
                    self.assertEqual(json.loads(x.read_text())['shape'], json.loads(y.read_text())['shape'])

    def test_interleaved_resume(self):
        scalars = [ord(c) for c, _, _ in glyphs.charset('symbol')]
        with tempfile.TemporaryDirectory() as temp:
            dirs = [Path(temp)/'full', Path(temp)/'cut']
            for directory in dirs:
                directory.mkdir()
                analytic(directory, scalars, 'symbol')
            a = argparse.Namespace(directory=dirs[0], mode='repertoire', partition='interleaved', parts=8, budget=128,
                                   seeds='0,1', start=6, batch_models=4, steps=4, device='cpu', unlabelled=1.,
                                   compile=False, resume=False, log_every=1, checkpoint_every=2, stop_after=None)
            b = argparse.Namespace(**{**vars(a), 'directory': dirs[1], 'stop_after': 2})
            with contextlib.redirect_stdout(io.StringIO()):
                s.train(a)
                s.train(b)
                self.assertFalse(list(dirs[1].glob('symbol-*.json')))
                b.stop_after, b.resume = None, True
                s.train(b)
                b.unlabelled = .5
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    s.train(b)
            first = sorted(dirs[0].glob('symbol-*.json'))
            self.assertEqual(len(first), 4)
            for path in first:
                self.assertEqual(path.read_bytes(), (dirs[1]/path.name).read_bytes())
                doc = json.loads(path.read_text())
                self.assertEqual(doc['shape']['hidden_width'], 16)
                self.assertEqual(doc['shape']['tau'], .15)

    def test_symbol_teacher(self):
        with tempfile.TemporaryDirectory() as temp:
            s.prepare(Path(temp), 'symbol')
            meta = json.loads((Path(temp)/'teacher.json').read_text())
            rows = glyphs.charset('symbol')
            self.assertEqual(meta['identity']['scalars'], [ord(c) for c, _, _ in rows])
            fields = np.load(Path(temp)/'teacher.npy')
            self.assertEqual(fields.shape, (49, 513, 257))
            for i in (0, 7, 48):
                np.testing.assert_array_equal(fields[i], glyphs.field(rows[i][2], 256, glyphs.PEN, .15).astype(np.float16))
            for w, h in s.SIZES:
                self.assertEqual(np.load(Path(temp)/f'truth-{w}x{h}.npy').shape, (49, h, w))
            with contextlib.redirect_stdout(io.StringIO()):
                s.prepare(Path(temp), 'symbol')


if __name__ == '__main__':
    unittest.main()
