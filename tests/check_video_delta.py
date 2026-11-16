"""Change-only output of the player's default pixels mode: --skip-threshold,
--partial-limit, --partial-rects and --refresh, on by default (threshold 4,
and in kitty or Kilix partial limit 0.25); --skip-threshold off sends every
frame whole, which the tests call today's picture.

Every playback test runs the real player and reads its output with a model
of the terminal (tests/kitty_model.py), then compares the picture the
terminal holds after every source frame with the true frame, decoded by the
player's own decoder command and drawn as the pixels mode draws it.
"""
import importlib.util
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
import neuronte_video as v
from kitty_model import KittyModel
spec = importlib.util.spec_from_file_location('neuronte_play', ROOT / 'tools/neuronte-play.py')
play = importlib.util.module_from_spec(spec); spec.loader.exec_module(play)

# 8 x 6 cells = 16 x 24 samples. A small square moves on every third frame
# (so two frames in three are identical) and the whole picture turns red for
# frames 25-34, counting from 0 (a change too large for a frame edit).
MOVING = ("color=c=gray:size=16x24:rate=30,format=rgb24[b];color=c=0x20c040:size=4x4:rate=30,format=rgb24[f];"
          "[b][f]overlay=x='mod(floor(n/3)*2,12)':y='if(lt(mod(n,40),20),2,14)'[m];"
          "color=c=red:size=16x24:rate=30,format=rgb24[r];[m][r]overlay=enable='between(n,25,34)'")
# Every sample one level brighter than in the frame before: a drift that never
# exceeds a small threshold between consecutive frames.
RAMP = "nullsrc=size=16x24:rate=30,format=rgb24,geq=r='min(255,N)':g='128':b='64'"
NEEDS = all(__import__('shutil').which(t) for t in ('ffmpeg', 'ffprobe'))


def reference(source, cols, rows, frames):
    """The true samples of each frame: the player's own decoder command."""
    w, h = cols * 2, rows * 4
    raw = subprocess.run(v.decoder_command(source, w, h, 30., lavfi=True, exact_pixels=False)[:-1]
                         + ['-frames:v', str(frames), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(frames, h, w, 3)


def run(source, *options, cols=8, rows=6, frames=60, env=None, keys=None):
    """Play untimed into the model terminal. Returns the model, the frame log and the summary."""
    with tempfile.TemporaryDirectory() as temp:
        log, stats = Path(temp) / 'log', Path(temp) / 'stats'
        cmd = [sys.executable, str(ROOT / 'tools/neuronte-play.py'), source, '--lavfi', '--cols', str(cols), '--rows', str(rows),
               '--no-status', '--untimed', '--frames', str(frames), '--log', str(log), '--stats', str(stats), *options]
        environment = dict(os.environ, COLUMNS='80', LINES='24'); environment.pop('KITTY_WINDOW_ID', None)
        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env=environment)
        model = KittyModel()
        try:
            while True:
                chunk = os.read(child.stdout.fileno(), 1 << 16)
                if not chunk: break
                model.feed(chunk)               # reads and unlinks shared memory as a terminal does
            err = child.stderr.read().decode(); child.wait(timeout=10)
        finally:
            if child.poll() is None: child.kill(); child.wait()
            for path in Path('/dev/shm').glob(f'neuronte-play-{child.pid}-*'): path.unlink()
        if child.returncode: raise AssertionError(err)
        records = [json.loads(line) for line in log.read_text().splitlines()]
        return model, records, json.loads(stats.read_text())


def held(model, records):
    """The picture held after each source frame. Every record with bytes is
    one synchronized update; one with none leaves the picture as it was."""
    pictures = iter(model.pictures); out = []; current = None
    for record in records:
        if record.get('bytes'): current = next(pictures)
        out.append(current)
    return out


def enlarge(samples):
    return np.repeat(np.repeat(samples, 4, axis=0), 4, axis=1)


@unittest.skipUnless(NEEDS, 'ffmpeg is not installed')
class Playback(unittest.TestCase):
    def test_threshold_zero_holds_todays_picture_after_every_frame(self):
        frames = 90
        for transport in ('shm', 'inline'):
            today = held(*run(MOVING, '--transport', transport, '--skip-threshold', 'off', frames=frames)[:2])
            truth = reference(MOVING, 8, 6, frames)
            for picture, samples in zip(today, truth):
                np.testing.assert_array_equal(picture, enlarge(samples))
            for options in (['--skip-threshold', '0'],
                            ['--skip-threshold', '0', '--partial-limit', '1'],
                            ['--skip-threshold', '0', '--partial-limit', '.3', '--partial-rects', '2']):
                with self.subTest(transport=transport, options=options):
                    model, records, summary = run(MOVING, '--transport', transport, *options, frames=frames)
                    pictures = held(model, records)
                    self.assertEqual(len(pictures), frames)
                    for n, (a, b) in enumerate(zip(pictures, today)):
                        self.assertTrue(np.array_equal(a, b), f'frame {n + 1} differs from today\'s picture')
                    counts = summary['delta']
                    self.assertGreater(counts['unchanged'], frames // 3)     # two frames in three are identical
                    self.assertEqual(counts['unchanged'] + counts['partial'] + counts['full'], frames)
                    self.assertEqual(sum(1 for r in records if r['bytes'] == 0), counts['unchanged'])
                    if '--partial-limit' in options:
                        self.assertGreater(counts['partial'], 0)
                        self.assertEqual(model.commands['T'], counts['full'])
                        rects = sum(r.get('rects', 0) for r in records)
                        self.assertEqual(model.commands['f'], rects)
                        self.assertLessEqual(max(r.get('rects', 0) for r in records), int(options[-1]) if '--partial-rects' in options else 1)
                    else:
                        self.assertEqual(model.commands['f'], 0)

    def test_threshold_bounds_the_error_and_does_not_drift(self):
        frames = 120
        truth = reference(RAMP, 8, 6, frames)
        for transport in ('shm', 'inline'):
            for options in (['--skip-threshold', '4'], ['--skip-threshold', '4', '--partial-limit', '.5']):
                with self.subTest(transport=transport, options=options):
                    model, records, summary = run(RAMP, '--transport', transport, *options, frames=frames)
                    worst = max(int(np.abs(p.astype(int) - enlarge(s)).max()) for p, s in zip(held(model, records), truth))
                    self.assertLessEqual(worst, 4)
                    # Each frame is one level from the one before. Compared with the
                    # previous frame nothing would ever be sent; compared with what
                    # was sent, the fifth frame after a send has moved every cell 5
                    # levels and is sent whole, and so is the frame after it (a
                    # change that large is followed by one frame sent uncompared).
                    sends = [n for n, r in enumerate(records) if r['bytes']]
                    self.assertEqual(sends, [0] + [n for k in range(0, frames, 6) for n in (5 + k, 6 + k) if n < frames])
                    self.assertTrue(all(r['delta'] == 'full' for r in records if r['bytes']))
            model, records, summary = run(MOVING, '--transport', transport, '--skip-threshold', '6', '--partial-limit', '.5', frames=frames)
            truth_moving = reference(MOVING, 8, 6, frames)
            worst = max(int(np.abs(p.astype(int) - enlarge(s)).max()) for p, s in zip(held(model, records), truth_moving))
            self.assertLessEqual(worst, 6)

    def test_fallback_sends_the_whole_picture(self):
        model, records, summary = run(MOVING, '--skip-threshold', '0', '--partial-limit', '.3', frames=60)
        kinds = [r['delta'] for r in records]
        self.assertEqual(kinds[0], 'full')                          # the first frame
        self.assertEqual(kinds[25], 'full'); self.assertEqual(kinds[35], 'full')   # all red, then back
        self.assertEqual(model.commands['T'], kinds.count('full'))
        self.assertEqual(model.commands['f'], kinds.count('partial'))
        # The refresh falls on the same frames of the file in every run.
        model, records, summary = run(MOVING, '--skip-threshold', '0', '--partial-limit', '.3', '--refresh', '.5', frames=60)
        full = [n for n, r in enumerate(records) if r['delta'] == 'full']
        self.assertEqual(full[:2], [0, 15])                     # half a second of video, not of the run
        self.assertTrue(all(b - a <= 15 for a, b in zip(full, full[1:] + [60])), full)
        again = [n for n, r in enumerate(run(MOVING, '--skip-threshold', '0', '--partial-limit', '.3', '--refresh', '.5', frames=60)[1])
                 if r['delta'] == 'full']
        self.assertEqual(full, again)
        model, records, summary = run(RAMP, '--skip-threshold', '0', '--partial-limit', '1', '--refresh', '0', frames=60)
        self.assertEqual([r['delta'] for r in records].count('full'), 1)

    def test_identical_frames_send_nothing_and_still_count_as_shown(self):
        model, records, summary = run('color=c=blue:size=16x24:rate=30', '--skip-threshold', '0', frames=30)
        self.assertEqual(summary['shown'], 30); self.assertEqual(summary['delta']['unchanged'], 29)
        self.assertEqual(model.commands, dict(T=1, f=0, d=2))   # placed once; both ids deleted at exit
        self.assertEqual(sum(r['bytes'] for r in records[1:]), 0)

    def test_busy_terminal_frames_are_resent_not_lost(self):
        """Timed playback skips frames the terminal has not taken; what was
        skipped was never sent, so the next frame carries its change."""
        delta = play.Delta(0, .5)
        a = np.zeros((24, 16, 3), np.uint8); b = a.copy(); b[:4, :2] = 9
        self.assertEqual(delta.plan(a, 6, 8, 0.), 'full'); delta.commit(a, 'full', 0.)
        self.assertEqual(delta.plan(b, 6, 8, .1), [(0, 0, 1, 1)])     # not committed: the terminal was busy
        self.assertEqual(delta.plan(b, 6, 8, .2), [(0, 0, 1, 1)])
        delta.commit(b, [(0, 0, 1, 1)], .2); self.assertIsNone(delta.plan(b, 6, 8, .3))


@unittest.skipUnless(NEEDS, 'ffmpeg is not installed')
class Controls(unittest.TestCase):
    """Seek, pause, resize and --loop with change-only output, in timed playback."""

    def clip(self, temp, seconds=8):
        path = Path(temp) / f'clip-{seconds}.mkv'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', MOVING + f',trim=duration={seconds}',
                        '-c:v', 'ffv1', str(path)], check=True)
        return str(path)

    def truth(self, source, records):
        """The true picture of the last frame shown or found unchanged."""
        last = [r for r in records if not r.get('dropped') and not r.get('skipped')][-1]
        raw = subprocess.run(v.decoder_command(source, 16, 24, 30., start=0., exact_pixels=False)[:-1] + ['-'],
                             capture_output=True, check=True).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, 24, 16, 3)
        # A resize restarts the decoder at the clock's position, between two
        # frames: the decoder then starts at the next frame, not the nearest.
        return enlarge(frames[math.ceil(last['pts'] * 30 - 1e-3)])

    def play_timed(self, source, *options, keys=(), signals=(), timeout=60):
        cmd = [sys.executable, str(ROOT / 'tools/neuronte-play.py'), source, '--cols', '8', '--rows', '6', '--no-status',
               '--no-audio', *options]
        environment = dict(os.environ, COLUMNS='80', LINES='24'); environment.pop('KITTY_WINDOW_ID', None)
        r, w = os.pipe()
        child = subprocess.Popen(cmd + ['--input-fd', str(r)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 stdin=subprocess.DEVNULL, env=environment, pass_fds=[r])
        os.close(r); model = KittyModel(); spawned = time.monotonic(); began = None
        events = sorted([(t, 'key', k) for t, k in keys] + [(t, 'signal', s) for t, s in signals])
        os.set_blocking(child.stdout.fileno(), False)
        try:
            import select
            while True:
                if began is None and model.updates: began = time.monotonic()    # keys are timed from the first picture
                now = time.monotonic() - began if began is not None else -1.
                while events and events[0][0] <= now:
                    _, kind, what = events.pop(0)
                    if kind == 'key': os.write(w, what)
                    else: child.send_signal(what)
                if select.select([child.stdout], [], [], .02)[0]:
                    chunk = os.read(child.stdout.fileno(), 1 << 16)
                    if not chunk: break
                    model.feed(chunk)
                if time.monotonic() - spawned > timeout: raise AssertionError('player did not finish')
            child.wait(timeout=5)
        finally:
            os.close(w)
            if child.poll() is None: child.kill(); child.wait()
            for path in Path('/dev/shm').glob(f'neuronte-play-{child.pid}-*'): path.unlink()
        return child.returncode, model, child.stderr.read().decode()

    def test_seek_pause_resize_and_loop_start_from_a_whole_picture(self):
        with tempfile.TemporaryDirectory() as temp:
            source = self.clip(temp, 20); stats = Path(temp) / 'stats'; log = Path(temp) / 'log'
            for transport in ('shm', 'inline'):
                with self.subTest(transport=transport):
                    code, model, err = self.play_timed(
                        source, '--transport', transport, '--skip-threshold', '0', '--partial-limit', '.5', '--stats', str(stats),
                        '--log', str(log), keys=[(1., b'\x1b[C'), (3., b' '), (3.5, b'\x1b[D'), (4.5, b' '), (8.5, b'q')],
                        signals=[(6., signal.SIGWINCH)])     # seconds apart: a restarted decoder can be slow to start
                    self.assertEqual(code, 0, err)
                    summary = json.loads(stats.read_text()); self.assertEqual(summary['seeks'], 2)
                    records = [json.loads(line) for line in log.read_text().splitlines()]
                    # After the start, every seek, the resize and every loop, the first frame
                    # sent is whole. A paused seek sends its whole picture before the loop,
                    # unlogged; the frame after it (logged as first) may then be an edit.
                    firsts = [n for n, r in enumerate(records) if r.get('first')]
                    kinds = [next((r['delta'] for r in records[n:] if r.get('bytes')), None) for n in firsts]
                    self.assertGreaterEqual(len(firsts), 3, firsts)
                    self.assertEqual(kinds[0], 'full')
                    self.assertLessEqual(sum(kind not in ('full', None) for kind in kinds), 1, kinds)
                    self.assertGreaterEqual(summary['delta']['full'], 3)
                    self.assertGreater(summary['delta']['partial'] + summary['delta']['unchanged'], 0)
                    # Every edit landed inside the picture shown (the model raises otherwise),
                    # and with threshold 0 the picture held at the end is the true last frame.
                    self.assertEqual(model.commands['f'], sum(1 for r in records if r.get('delta') == 'partial' and r.get('bytes')))
                    np.testing.assert_array_equal(model.pictures[-2], self.truth(source, records))
            code, model, err = self.play_timed(self.clip(temp, 2), '--skip-threshold', '0', '--partial-limit', '.5', '--loop',
                                               '--stats', str(stats), '--log', str(log), keys=[(5.5, b'q')], timeout=40)
            self.assertEqual(code, 0, err)
            records = [json.loads(line) for line in log.read_text().splitlines()]
            wraps = [n for n in range(1, len(records)) if records[n].get('first')]
            self.assertTrue(wraps, 'the clip did not loop')
            for n in wraps:
                first = next((r for r in records[n:] if r.get('bytes')), None)
                if first is not None: self.assertEqual(first['delta'], 'full')


class Units(unittest.TestCase):
    def test_threshold_is_exceeded_not_reached(self):
        delta = play.Delta(4, 1.)
        a = np.full((8, 4, 3), 100, np.uint8); delta.commit(a, 'full', 0.)
        b = a.copy(); b[1, 1, 2] = 104; b[5, 2, 0] = 96
        self.assertIsNone(delta.plan(b, 2, 2, 0.))
        b[5, 3, 1] = 105; self.assertEqual(delta.plan(b, 2, 2, 0.), [(1, 1, 2, 2)])
        b[0, 0, 0] = 95; self.assertEqual(delta.plan(b, 2, 2, 0.), [(0, 0, 2, 2)])
        self.assertEqual(play.Delta(4, .5).plan(b, 2, 2, 0.), 'full')   # no sent picture yet

    def test_rectangles_cover_every_change_and_merge_the_nearest(self):
        rng = np.random.default_rng(5)
        for _ in range(200):
            rows, cols = rng.integers(1, 20, 2)
            changed = rng.random((rows, cols)) < rng.choice([.02, .1, .4])
            if not changed.any(): continue
            for rects in (1, 2, 4):
                boxes = play.Delta(0, 1., rects).boxes(changed)
                self.assertLessEqual(len(boxes), rects)
                cover = np.zeros_like(changed)
                for x0, y0, x1, y1 in boxes:
                    self.assertTrue(0 <= x0 < x1 <= cols and 0 <= y0 < y1 <= rows)
                    cover[y0:y1, x0:x1] = True
                self.assertTrue(np.all(cover[changed]))
                for i, p in enumerate(boxes):           # disjoint: no cell is sent twice
                    for q in boxes[i + 1:]:
                        self.assertTrue(p[2] <= q[0] or q[2] <= p[0] or p[3] <= q[1] or q[3] <= p[1])

    def test_large_changes_stop_comparing_early(self):
        delta = play.Delta(0, .1)
        a = np.zeros((64 * 4, 10 * 2, 3), np.uint8); delta.commit(a, 'full', 0.)
        b = a + 1
        calls = []
        real = np.count_nonzero
        try:
            np.count_nonzero = lambda x: calls.append(1) or real(x)
            self.assertEqual(delta.plan(b, 64, 10, 0.), 'full')
        finally:
            np.count_nonzero = real
        self.assertEqual(len(calls), 1)                 # the first band is already over the limit

    def test_sent_samples_change_only_where_sent(self):
        delta = play.Delta(0, 1.)
        a = np.zeros((8, 4, 3), np.uint8); delta.commit(a, 'full', 0.)
        b = a + 7; delta.commit(b, [(1, 0, 2, 1)], .1)
        self.assertTrue(np.all(delta.sent[:4, 2:] == 7)); self.assertTrue(np.all(delta.sent[4:] == 0)); self.assertTrue(np.all(delta.sent[:4, :2] == 0))
        self.assertEqual(delta.counts, dict(unchanged=0, partial=1, full=1))
        delta.reset(); self.assertEqual(delta.plan(b, 2, 2, .2), 'full')

    def test_after_a_large_change_frames_go_whole_uncompared_for_a_while(self):
        delta = play.Delta(0, .25)
        a = np.zeros((8 * 4, 8 * 2, 3), np.uint8); delta.commit(a, 'full', 0.)
        calls = []; real = delta.changed
        delta.changed = lambda *x, **k: calls.append(1) or real(*x, **k)
        frame = 0; kinds = []
        def step(picture):
            nonlocal frame
            frame += 1; plan = delta.plan(picture, 8, 8, frame / 30); kinds.append(plan if plan in (None, 'full') else 'partial')
            delta.commit(picture, plan, frame / 30)
        for n in range(1, 80): step(a + (n % 2))                  # everything changes every frame
        compared = len(calls)
        self.assertEqual(kinds.count('full'), 79)
        self.assertLessEqual(compared, 9)                         # 1, 2, 4, ... 32 frames between comparisons
        self.assertEqual(delta.wait, play.Delta.WAIT)
        for n in range(40): step(a + (79 % 2))                    # then nothing changes
        self.assertIn(None, kinds[79:]); self.assertEqual(delta.wait, 0)
        self.assertEqual(kinds[-1], None)
        # a whole picture that was not kept (the terminal was busy) is never compared against
        delta = play.Delta(0, .25); delta.commit(a, 'full', 0.)
        self.assertEqual(delta.plan(a + 1, 8, 8, .1), 'full'); self.assertEqual(delta.rest, 1)
        self.assertEqual(delta.plan(a + 1, 8, 8, .2), 'full'); delta.commit(a + 1, 'full', .2)   # rest 0: kept
        self.assertTrue(delta.fresh); self.assertIsNone(delta.plan(a + 1, 8, 8, .3))
        delta.rest = 2; delta.commit(a + 2, 'full', .4); self.assertFalse(delta.fresh)
        self.assertEqual([delta.plan(a + 2, 8, 8, .5), delta.plan(a + 2, 8, 8, .6), delta.plan(a + 2, 8, 8, .7)], ['full'] * 3)

    def test_refresh_counts_video_time(self):
        delta = play.Delta(0, 1., refresh=2.)
        a = np.zeros((8, 4, 3), np.uint8); delta.commit(a, 'full', 10.)
        self.assertIsNone(delta.plan(a, 2, 2, 11.9)); self.assertEqual(delta.plan(a, 2, 2, 12.), 'full')
        self.assertIsNone(play.Delta(0, 1., refresh=0.).plan(a, 2, 2, 1e6) if False else None)

    def test_frame_edit_bytes(self):
        import base64, re, zlib
        for transport in ('shm', 'inline'):
            presenter = play.Presenter(None, transport, slots=6, transient=transport == 'shm')
            try:
                with self.assertRaises(ValueError): presenter.edit([(0, 0, np.zeros((16, 8, 3), np.uint8))])
                presenter.frame(np.zeros((32, 16, 3), np.uint8), 2, 2, 1, 1); presenter.sent()
                patch = np.arange(16 * 8 * 3, dtype=np.uint8).reshape(16, 8, 3)
                data = presenter.edit([(8, 16, patch), (0, 0, patch[:, ::-1])])
                self.assertTrue(data.startswith(b'\x1b[?2026h') and data.endswith(b'\x1b[?2026l'))
                self.assertNotIn(b'a=T', data); self.assertNotIn(b'a=d', data)
                hint = b',N=1' if transport == 'shm' else b''
                heads = re.findall(rb'\x1b_G(a=f,i=(\d+),r=1,x=(\d+),y=(\d+),s=8,v=16,f=24' + hint + rb',q=2)', data)
                self.assertEqual([(int(i), int(x), int(y)) for _, i, x, y in heads], [(presenter.current, 8, 16), (presenter.current, 0, 0)])
                model = KittyModel(); model.images[presenter.current] = np.zeros((32, 16, 3), np.uint8); model.shown = presenter.current
                model.feed(data)
                np.testing.assert_array_equal(model.pictures[-1][16:, 8:], patch)
                np.testing.assert_array_equal(model.pictures[-1][:16, :8], patch[:, ::-1])
                self.assertFalse(model.pictures[-1][:16, 8:].any())
                # Too few free objects: nothing is written, nothing is left behind.
                if transport == 'shm':
                    def unread(): return sum(os.path.exists('/dev/shm/' + n) for n in presenter.names)
                    self.assertEqual(unread(), 1)                   # the whole picture, which nothing read here
                    self.assertIsNone(presenter.edit([(0, 0, patch)] * 6)); self.assertEqual(unread(), 1)
                    self.assertIsNotNone(presenter.edit([(0, 0, patch)] * 3)); presenter.sent(); self.assertEqual(unread(), 4)
                    self.assertIsNone(presenter.edit([(0, 0, patch)] * 3)); self.assertEqual(unread(), 4)
                    self.assertEqual(presenter.skipped, 2)
                    current = presenter.current; self.assertIsNotNone(presenter.edit([(0, 0, patch)])); self.assertEqual(unread(), 5)
                    presenter.discard()                              # a seek cancelled it: its object goes
                    self.assertEqual(presenter.current, current); self.assertEqual(unread(), 4)
            finally:
                presenter.close(drain=0)

    @unittest.skipUnless(NEEDS, 'ffmpeg is not installed')
    def test_defaults(self):
        def settings(*options, kitty=False):
            with tempfile.TemporaryDirectory() as temp:
                stats = Path(temp) / 'stats'
                environment = dict(os.environ, COLUMNS='80', LINES='24'); environment.pop('KITTY_WINDOW_ID', None)
                if kitty: environment['KITTY_WINDOW_ID'] = '1'
                subprocess.run([sys.executable, str(ROOT / 'tools/neuronte-play.py'), 'color=c=gray:size=16x24:rate=30', '--lavfi',
                                '--no-status', '--untimed', '--frames', '5', '--transport', 'inline', '--stats', str(stats), *options],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, env=environment, check=True)
                delta = json.loads(stats.read_text()).get('delta')
                return delta and (delta['threshold'], delta['partial_limit'])
        self.assertEqual(settings('--cols', '8', '--rows', '6', kitty=True), (4, 0.25))      # kitty or Kilix: frame edits too
        self.assertEqual(settings('--cols', '8', '--rows', '6'), (4, None))                 # elsewhere: unchanged frames only
        self.assertEqual(settings('--cols', '8', '--rows', '6', '--partial-limit', '.5'), (4, 0.5))
        self.assertEqual(settings('--cols', '8', '--rows', '6', '--skip-threshold', '0', kitty=True), (0, 0.25))
        self.assertEqual(settings('--cols', '8', '--rows', '6', '--skip-threshold', 'off', kitty=True), None)
        self.assertEqual(settings('--cols', '8', '--rows', '6', '--skip-threshold', '4', '--partial-limit', 'off', kitty=True), (4, None))
        self.assertEqual(settings('--pixel-size', '16x24', kitty=True), None)
        self.assertEqual(settings('--cols', '8', '--rows', '6', '--mode', 'cells', kitty=True), None)

    def test_options_are_checked(self):
        for options, message in [(['--skip-threshold', '256'], b'from 0 to 255'), (['--skip-threshold', '-1'], b'from 0 to 255'),
                                 (['--skip-threshold', 'off', '--partial-limit', '.5'], b'requires --skip-threshold'),
                                 (['--skip-threshold', 'some'], b'whole number of levels or off'),
                                 (['--partial-limit', 'half'], b'a fraction or off'),
                                 (['--skip-threshold', '0', '--partial-limit', '0'], b'above 0'),
                                 (['--skip-threshold', '0', '--partial-limit', '1.5'], b'above 0'),
                                 (['--skip-threshold', '0', '--partial-rects', '0'], b'from 1 to 16'),
                                 (['--skip-threshold', '0', '--refresh', '-1'], b'nonnegative'),
                                 (['--skip-threshold', '0', '--mode', 'cells'], b'without --pixel-size'),
                                 (['--skip-threshold', '0', '--pixel-size', '16x16'], b'without --pixel-size')]:
            with self.subTest(options=options):
                out = subprocess.run([sys.executable, str(ROOT / 'tools/neuronte-play.py'), 'color', '--lavfi', *options],
                                     capture_output=True)
                self.assertEqual(out.returncode, 2); self.assertIn(message, out.stderr); self.assertNotIn(b'Traceback', out.stderr)


if __name__ == '__main__':
    unittest.main()
