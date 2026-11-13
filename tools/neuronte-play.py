#!/usr/bin/env python3
"""Play a video in the terminal, drawn by Neuronte. See neuronte-video.md.

ffmpeg decodes and scales the file; each frame is fitted to terminal cells
with the nets' own coverage masks and shown at the file's frame rate.
Frames that cannot be shown in time are dropped, so playback keeps pace
with the clock (and with --audio) instead of slowing down.

  pixels  (default) every cell is split into 2 x 4 blocks with eight
          colours, mixed by three Neuronte masks drawn at 8 x 16 pixels a
          cell; the result is sent with the kitty graphics protocol, so it
          needs a terminal that has it. Real time at ordinary sizes.
  cells   one character and two colours per cell, written as ordinary
          truecolour text, so the terminal's own font draws it. This is an
          exhaustive search and shows a few frames a second at best.

Keys: q or Ctrl-C quits, space pauses.
"""
import argparse
import base64
import fcntl
import json
import os
import select
import shutil
import signal
import struct
import subprocess
import sys
import termios
import time
import tty
import zlib
import numpy as np
from neuronte_video import TwoInk, MultiInk, ROOT

CELL = (8, 16)                      # pixels drawn per terminal cell
BLOCKS = (2, 4)                     # colours fitted per cell in pixels mode, across and down
IMAGE_ID = 0x4e52                   # one kitty image, replaced every frame


def probe(path, lavfi):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
           'stream=width,height,r_frame_rate', '-of', 'json']
    out = subprocess.run(cmd + (['-f', 'lavfi'] if lavfi else []) + [path], capture_output=True, text=True)
    try:
        stream = json.loads(out.stdout)['streams'][0]
        num, den = map(int, stream['r_frame_rate'].split('/'))
        return int(stream['width']), int(stream['height']), num / den
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        raise ValueError(f'ffprobe found no video stream in {path}: {out.stderr.strip()}')


def terminal():
    """Columns, rows and the width/height ratio of one cell."""
    cols, rows = shutil.get_terminal_size((80, 24))
    ratio = CELL[0] / CELL[1]
    try:
        r, c, xp, yp = struct.unpack('HHHH', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, bytes(8)))
        if r and c and xp and yp: ratio = (xp / c) / (yp / r)
    except OSError:
        pass
    return cols, rows, ratio


def fit(width, height, cols, rows, ratio):
    """Largest grid no bigger than cols x rows with the picture's shape."""
    wide = width / height / ratio           # the picture's width in cells per row of height
    c = min(cols, max(1, round(rows * wide)))
    r = min(rows, max(1, round(c / wide)))
    return c, r


def graphics(frame, cols, rows, left, top):
    """One kitty graphics transmit-and-place, replacing the last frame."""
    h, w = frame.shape[:2]
    data = base64.standard_b64encode(zlib.compress(frame.tobytes(), 1))
    head = f'a=T,f=24,o=z,s={w},v={h},i={IMAGE_ID},p=1,c={cols},r={rows},C=1,q=2,'
    out = [f'\x1b[{top};{left}H'.encode()]
    for start in range(0, len(data), 4096):
        more = int(start + 4096 < len(data))
        out.append(b'\x1b_G' + (head if not start else '').encode() + f'm={more};'.encode() + data[start:start+4096] + b'\x1b\\')
    return b''.join(out)


def text(renderer, cells, previous, left, top):
    """The changed cells as cursor-addressed truecolour text."""
    out = []
    for y, x in np.ndindex(cells['indices'].shape):
        i = cells['indices'][y, x]; c = cells['colours'][y, x]
        if previous is not None and i == previous['indices'][y, x] and np.array_equal(c, previous['colours'][y, x]): continue
        bg, fg = c
        out.append(f'\x1b[{y+top};{x+left}H\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m' + chr(int(renderer.scalars[i])))
    return (''.join(out) + '\x1b[0m').encode()


def read_exact(stream, size):
    parts = []; remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part: return None
        parts.append(part); remaining -= len(part)
    return b''.join(parts)


class Keys:
    """q, Ctrl-C and space from the terminal, without echo; a no-op off a tty."""
    def __init__(self):
        self.fd = None
        try:
            fd = os.open('/dev/tty', os.O_RDONLY)
            self.saved = termios.tcgetattr(fd); tty.setcbreak(fd); self.fd = fd
        except OSError:
            pass

    def read(self, wait=0):
        if self.fd is None:
            if wait: time.sleep(wait)
            return b''
        return os.read(self.fd, 16) if select.select([self.fd], [], [], wait)[0] else b''

    def close(self):
        if self.fd is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved); os.close(self.fd); self.fd = None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('video', help='a file or URL ffmpeg can read')
    p.add_argument('--mode', choices=['pixels', 'cells'], default='pixels')
    p.add_argument('--cols', type=int, help='grid width in cells; default: fit the terminal')
    p.add_argument('--rows', type=int)
    p.add_argument('--fps', type=float, help='default: the file\'s own rate')
    p.add_argument('--frames', type=int, help='stop after this many source frames')
    p.add_argument('--loop', action='store_true')
    p.add_argument('--audio', action='store_true', help='also play the sound with ffplay; started together, not resynchronised')
    p.add_argument('--characters', choices=['portable', 'full'], default='portable',
                   help='cells mode: the 328 block characters, or every character of the bundle (slower)')
    p.add_argument('--helper', action='store_true', help='cells mode with --characters full: use the learned speed helper')
    p.add_argument('--lavfi', action='store_true', help='the video argument is an ffmpeg lavfi source, such as testsrc2')
    p.add_argument('--weights'); p.add_argument('--library')
    a = p.parse_args()
    for tool in ['ffmpeg', 'ffprobe'] + (['ffplay'] if a.audio else []):
        if not shutil.which(tool): p.error(f'{tool} is required and was not found')
    if a.helper and (a.mode != 'cells' or a.characters != 'full'): p.error('--helper requires --mode cells --characters full')
    library = a.library or ROOT / 'build/libneuronte.so'
    if not os.path.exists(library): p.error(f'{library} is missing; run make first, or pass --library')
    width, height, rate = probe(a.video, a.lavfi)
    fps = a.fps or rate
    if not 0 < fps <= 240: p.error('frame rate must be above 0 and at most 240')
    cols, rows, ratio = terminal()
    grid_c, grid_r = fit(width, height, a.cols or cols, a.rows or rows, ratio)
    if a.cols: grid_c = a.cols
    if a.rows: grid_r = a.rows
    if grid_c < 1 or grid_r < 1: p.error('--cols and --rows must be positive')
    unit = BLOCKS if a.mode == 'pixels' else CELL          # what ffmpeg scales one cell to
    w, h = grid_c * unit[0], grid_r * unit[1]
    left, top = max(1, (cols - grid_c) // 2 + 1), max(1, (rows - grid_r) // 2 + 1)

    helper = None
    if a.mode == 'pixels':
        # The file is scaled to one pixel a block, so fitting is exact; the
        # nets' masks then draw each block at the cell's real size.
        fitter = MultiInk(a.weights, library, *BLOCKS); renderer = MultiInk(a.weights, library, *CELL)
    else:
        renderer = TwoInk(a.characters, *CELL, a.weights, library)
        if a.helper:
            import hashlib
            from neuronte_video_helpers import Helper, features
            helper = Helper(ROOT / 'weights/neuronte-video-speed-v1.json', 'speed', runtime=True)
            bundle = a.weights or ROOT / 'weights/neuronte-split-v5.nrt'
            if helper.doc.get('scalar_bundle_sha256') != hashlib.sha256(open(bundle, 'rb').read()).hexdigest():
                p.error('the speed helper was trained against a different bundle')

    decode = ['ffmpeg', '-v', 'error', '-nostdin'] + (['-stream_loop', '-1'] if a.loop and not a.lavfi else []) \
        + (['-f', 'lavfi'] if a.lavfi else []) + ['-i', a.video, '-an', '-vf', f'fps={fps},scale={w}:{h}:flags=area',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    out = sys.stdout.buffer
    keys = Keys(); source = sound = None; shown = dropped = count = 0; failure = ''
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        out.write(b'\x1b[?1049h\x1b[?25l\x1b[2J'); out.flush()
        source = subprocess.Popen(decode, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if a.audio:
            sound = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'] + (['-loop', '0'] if a.loop else []) + [a.video],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        started = time.perf_counter(); previous = None
        while a.frames is None or count < a.frames:
            key = keys.read()
            if b' ' in key:                         # pause: hold the clock, and the sound with it
                paused = time.perf_counter()
                if sound: sound.send_signal(signal.SIGSTOP)
                while True:
                    key = keys.read(.1)
                    if key: break
                if sound: sound.send_signal(signal.SIGCONT)
                started += time.perf_counter() - paused
            if b'q' in key or b'\x03' in key: break
            raw = read_exact(source.stdout, w * h * 3)
            if raw is None:                         # the end, or ffmpeg gave up: say which
                if source.wait(): failure = source.stderr.read().decode(errors='replace').strip()
                break
            due = started + count / fps; count += 1
            now = time.perf_counter()
            if now > due + 1 / fps and shown:       # late: skip the work, keep the clock
                dropped += 1; continue
            frame = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
            if a.mode == 'pixels':
                payload = graphics(renderer.decode(fitter.encode(frame)), grid_c, grid_r, left, top)
            else:
                if helper is not None:
                    k = helper.doc['inference']['candidates']
                    scores = helper(features(frame))
                    cells = renderer.fit(frame, np.argpartition(scores, -k, axis=1)[:, -k:].reshape(grid_r, grid_c, k))
                else:
                    cells = renderer.fit(frame)
                payload = text(renderer, cells, previous, left, top); previous = cells
            wait = due - time.perf_counter()
            if wait > 0: time.sleep(wait)
            out.write(payload); out.flush(); shown += 1
        elapsed = time.perf_counter() - started
    except (KeyboardInterrupt, BrokenPipeError):
        elapsed = time.perf_counter() - started if 'started' in dir() else 0
    finally:
        for child in (source, sound):
            if child and child.poll() is None:
                child.send_signal(signal.SIGCONT); child.terminate()
        keys.close()
        try:
            out.write(f'\x1b_Ga=d,d=I,i={IMAGE_ID},q=2\x1b\\\x1b[0m\x1b[?25h\x1b[?1049l'.encode()); out.flush()
        except (BrokenPipeError, ValueError):
            pass
    print(f'{shown} frames shown, {dropped} dropped, {shown/elapsed if elapsed else 0:.1f} per second; '
          f'{grid_c} x {grid_r} cells, {a.mode}', file=sys.stderr)
    if failure:
        print(f'ffmpeg stopped early: {failure}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (ValueError, OSError) as exc: print(str(exc), file=sys.stderr); sys.exit(2)
