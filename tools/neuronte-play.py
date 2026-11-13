#!/usr/bin/env python3
"""Play a video in the terminal, drawn by Neuronte. See neuronte-video.md.

ffmpeg decodes and scales the file, inside the player through
libneuronte-media when it is built, else as a separate ffmpeg process; each
frame is fitted to terminal cells with the nets' own coverage masks. Sound is played by mpv (kilix-mpv when it
is installed), and its playback position is the clock the picture follows,
so seeking and pausing move both together. Frames that cannot be shown in
time are dropped instead of slowing playback down.

  pixels  (default) every cell is split into 2 x 4 blocks with eight
          colours, mixed by three Neuronte masks drawn at 8 x 16 pixels a
          cell; the result is sent with the kitty graphics protocol, so it
          needs a terminal that has it. --pixel-size instead draws at 2 x 4
          pixels a cell, retaining each decoded sample at natural size.
  cells   one character and two colours per cell, written as ordinary
          truecolour text, so the terminal's own font draws it. This is an
          exhaustive search and shows a few frames a second at best.

Keys: q quit, space pause, left/right 5 s, down/up 60 s, home restart,
m mute, 9 and 0 volume.
"""
import argparse
import base64
import ctypes
import fcntl
import json
import os
import secrets
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import termios
import time
import tty
import zlib
import numpy as np
# Installed payloads are verified source trees. Keep runtime imports from
# adding __pycache__ files that would make the next upgrade see local changes.
sys.dont_write_bytecode = True
from neuronte_video import TwoInk, MultiInk, MediaDecoder, decoder_command, ROOT, cell_bundle

try: LIBC = ctypes.CDLL(None)        # loaded now, so a child has nothing to load between fork and exec
except OSError: LIBC = None
PLAYER_PID = os.getpid()
CELL = (8, 16)                      # pixels drawn per terminal cell
BLOCKS = (2, 4)                     # colours fitted per cell in pixels mode, across and down
KEYS = {b'\x1b[C': 'right', b'\x1b[D': 'left', b'\x1b[A': 'up', b'\x1b[B': 'down', b'\x1b[H': 'home',
        b'\x1b[1~': 'home', b'\x1bOC': 'right', b'\x1bOD': 'left', b'\x1bOA': 'up', b'\x1bOB': 'down',
        b'\x1bOH': 'home', b' ': 'pause', b'q': 'quit', b'\x03': 'quit', b'm': 'mute', b'9': 'quieter', b'0': 'louder'}
SEEK = {'right': 5, 'left': -5, 'up': 60, 'down': -60}


def with_us():
    """Run in a child before it starts: ask the kernel to end it when the
    player dies, however the player dies. Without this a killed player leaves
    the sound playing."""
    try: LIBC.prctl(1, signal.SIGTERM)                      # PR_SET_PDEATHSIG
    except Exception: pass
    # The signal is not retroactive: the player may have died after fork,
    # before the child registered it. Do not launch an orphan in that case.
    if os.getppid() != PLAYER_PID: os._exit(0)


class LibraryFrames:
    """Poll the in-process decoder without blocking playback controls."""
    kind = 'libav'

    def __init__(self, stream, direct=False):
        self.stream, self.direct, self.buffer = stream, direct, None

    def read(self, size, wait=.05):
        frame = self.stream.read(wait_ms=round(wait * 1000))
        if frame is None or frame == b'': return frame
        planes = self.stream.planes(frame) if self.direct else None
        if planes is not None: return planes
        if size != self.stream.width * self.stream.height * 3:
            raise ValueError('decoded frame size does not match the player')
        if self.buffer is None:
            shape = ((3, self.stream.height, self.stream.width) if self.stream.planar else
                     (self.stream.height, self.stream.width, 3))
            self.buffer = np.empty(shape, np.uint8)
        self.stream.copy(frame, self.buffer)
        return memoryview(self.buffer).cast('B')

    def failure(self): return self.stream.failure

    def close(self): self.stream.close()


def probe(path, lavfi):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,chroma_location:format=duration', '-of', 'json']
    out = subprocess.run(cmd + (['-f', 'lavfi'] if lavfi else []) + [path], capture_output=True, text=True)
    try:
        doc = json.loads(out.stdout)
        stream = next(s for s in doc['streams'] if s.get('codec_type') == 'video')
        num, den = map(int, stream['r_frame_rate'].split('/'))
        duration = float(doc.get('format', {}).get('duration') or 0)
        sound = any(s.get('codec_type') == 'audio' for s in doc['streams'])
        chroma = stream.get('chroma_location')
        if chroma not in ('left', 'center', 'topleft', 'top', 'bottomleft', 'bottom'): chroma = None
        return int(stream['width']), int(stream['height']), num / den, duration, sound, chroma
    except (KeyError, IndexError, ValueError, ZeroDivisionError, StopIteration):
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


def pixel_size(value):
    try:
        width, height = map(int, value.lower().split('x'))
        if width > 0 and height > 0:
            return width, height
    except ValueError:
        pass
    raise argparse.ArgumentTypeError('pixel size must be positive WIDTHxHEIGHT')


def pad_cells(frame, fitter):
    """Complete edge cells without resizing or discarding source samples."""
    height, width = frame.shape[:2]
    bottom, right = -height % fitter.height, -width % fitter.width
    if bottom or right:
        return np.pad(frame, ((0, bottom), (0, right), (0, 0)), mode='edge')
    return frame


def shared_memory_reaches_terminal():
    """True when the terminal is a local kitty or Kilix that can read /dev/shm."""
    if os.environ.get('SSH_CONNECTION') or os.environ.get('TMUX'): return False
    return bool(os.environ.get('KITTY_WINDOW_ID')) and os.access('/dev/shm', os.W_OK)


class Presenter:
    """Sends pictures the way kilix-mpv and kitty-framebuffer do: the new
    image is complete under its own id before the previous one is deleted,
    inside one synchronized update, so the terminal never shows a gap."""

    def __init__(self, out, transport):
        self.out, self.transport = out, transport
        base = 0x4e520000 | secrets.randbelow(0x7fff) << 1
        self.ids = (base, base + 1); self.current = None
        self.names = [f'neuronte-play-{os.getpid()}-{secrets.token_hex(6)}-{i}' for i in range(3)]
        self.slot = 0; self.skipped = 0; self.pending = None

    def frame(self, frame, cols, rows, left, top, natural=False):
        """The bytes that replace the picture, or None when the terminal has
        not yet taken the earlier frames (shared memory only)."""
        h, w = frame.shape[:2]
        new = self.ids[0] if self.current != self.ids[0] else self.ids[1]
        span = '' if natural else f'c={cols},r={rows},'
        head = f'a=T,f=24,s={w},v={h},i={new},p=1,{span}z=-1,C=1,q=2'
        out = [b'\x1b[?2026h', f'\x1b[{top};{left}H'.encode()]
        name = None
        if self.transport == 'shm':
            for tries in range(3):              # the terminal unlinks a name once it has read it
                candidate = self.names[(self.slot + tries) % 3]
                try:
                    fd = os.open('/dev/shm/' + candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError:
                    continue
                # Cropping an odd-width picture leaves strided rows. NumPy's
                # strided tobytes walks individual elements; a contiguous
                # buffer uses row copies and can be written without another copy.
                with os.fdopen(fd, 'wb') as f: f.write(memoryview(np.ascontiguousarray(frame)))
                name = candidate; self.slot = (self.slot + tries + 1) % 3; break
            if name is None:
                self.skipped += 1; return None
            out.append(f'\x1b_G{head},t=s;'.encode() + base64.standard_b64encode(name.encode()) + b'\x1b\\')
        else:
            data = base64.standard_b64encode(zlib.compress(memoryview(np.ascontiguousarray(frame)), 1))
            for start in range(0, len(data), 4096):
                more = int(start + 4096 < len(data))
                out.append(b'\x1b_G' + (head + ',o=z,' if not start else '').encode() + f'm={more};'.encode() + data[start:start+4096] + b'\x1b\\')
        if self.current is not None: out.append(f'\x1b_Ga=d,d=I,i={self.current},q=2;\x1b\\'.encode())
        out.append(b'\x1b[?2026l'); self.pending = (self.current, name); self.current = new
        return b''.join(out)

    def sent(self):
        self.pending = None

    def discard(self):
        """A seek/resize can cancel a packed picture before it reaches the terminal."""
        if self.pending is not None:
            self.current, name = self.pending
            if name is not None:
                try: os.unlink('/dev/shm/' + name)
                except FileNotFoundError: pass
            self.pending = None

    def close(self, drain=.2):
        self.discard()
        # A flushed graphics command can still be waiting in the terminal's
        # input queue. Give it a bounded chance to read/unlink the last image
        # before removing unread objects, including after --frames completes.
        if self.transport == 'shm':
            deadline = time.monotonic() + drain
            while any(os.path.exists('/dev/shm/' + name) for name in self.names):
                if time.monotonic() >= deadline: break
                time.sleep(.001)
        tail = b''.join(f'\x1b_Ga=d,d=I,i={i},q=2;\x1b\\'.encode() for i in self.ids)
        for name in self.names:
            try: os.unlink('/dev/shm/' + name)
            except OSError: pass
        return tail


def text(renderer, cells, previous, left, top):
    """The changed cells as cursor-addressed truecolour text, in one synchronized update."""
    out = ['\x1b[?2026h']
    for y, x in np.ndindex(cells['indices'].shape):
        i = cells['indices'][y, x]; c = cells['colours'][y, x]
        if previous is not None and i == previous['indices'][y, x] and np.array_equal(c, previous['colours'][y, x]): continue
        bg, fg = c
        out.append(f'\x1b[{y+top};{x+left}H\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m' + chr(int(renderer.scalars[i])))
    return (''.join(out) + '\x1b[0m\x1b[?2026l').encode()


class Decoder:
    """Read one frame incrementally while draining a bounded diagnostic tail.

    A quiet or damaged source must not prevent the player from handling keys.
    read() returns b'' while waiting, a complete frame, or None after exit.
    Complete frames share one buffer and remain valid until the next read().
    """
    kind = 'ffmpeg'

    def __init__(self, command):
        self.child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      bufsize=0, preexec_fn=with_us)
        self.readers = [self.child.stdout, self.child.stderr]
        self.buffer = None; self.filled = 0; self.errors = bytearray()
        for stream in self.readers: os.set_blocking(stream.fileno(), False)

    def read(self, size, wait=.05):
        if size <= 0: raise ValueError('frame size must be positive')
        if self.buffer is None or len(self.buffer) != size:
            if self.filled: raise ValueError('cannot resize a partial frame')
            self.buffer = memoryview(bytearray(size))
        ready = select.select(self.readers, [], [], wait)[0]
        for stream in ready:
            if stream is self.child.stdout:
                amount = os.readv(stream.fileno(), [self.buffer[self.filled:]])
                self.filled += amount
            else:
                chunk = os.read(stream.fileno(), 65536)
                amount = len(chunk)
                self.errors.extend(chunk)
                del self.errors[:-65536]
            if not amount:
                self.readers.remove(stream)
                stream.close()
        if self.filled == size:
            self.filled = 0
            return self.buffer
        if not self.readers and self.child.poll() is not None:
            if self.filled and not self.child.returncode:
                raise ValueError('truncated RGB frame')
            return None
        return b''

    def failure(self):
        return (self.errors.decode(errors='replace').strip() or f'exit status {self.child.returncode}') if self.child.returncode else ''

    def close(self):
        if self.child.poll() is None: self.child.kill()
        self.child.wait()
        for stream in self.readers: stream.close()
        self.readers.clear()


class Keys:
    """Named keys from the terminal (or --input-fd), without echo; nothing off a tty."""
    def __init__(self, fd=None):
        self.fd = self.saved = None; self.owned = fd is None
        try:
            self.fd = os.open('/dev/tty', os.O_RDONLY) if fd is None else fd
            if os.isatty(self.fd):
                self.saved = termios.tcgetattr(self.fd); tty.setcbreak(self.fd)
        except OSError:
            self.fd = None

    def read(self, wait=0):
        if self.fd is None:
            if wait: time.sleep(wait)
            return []
        if not select.select([self.fd], [], [], wait)[0]: return []
        data = os.read(self.fd, 64)
        if not data:                            # a closed pipe: stop asking
            self.fd = None; return []
        found = []
        while data:
            for seq in sorted(KEYS, key=len, reverse=True):
                if data.startswith(seq):
                    found.append(KEYS[seq]); data = data[len(seq):]; break
            else:
                data = data[1:]
        return found

    def close(self):
        if self.fd is not None and self.saved is not None: termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
        if self.fd is not None and self.owned: os.close(self.fd)
        self.fd = None


class WallClock:
    """The position when nothing plays sound: time since the start, less pauses."""
    volume = None
    def __init__(self, start=0.): self.base = time.perf_counter() - start; self.held = None
    def time(self): return (self.held if self.held is not None else time.perf_counter()) - self.base
    def pause(self, on):
        if on and self.held is None: self.held = time.perf_counter()
        elif not on and self.held is not None: self.base += time.perf_counter() - self.held; self.held = None
    def seek(self, position): self.base = (self.held if self.held is not None else time.perf_counter()) - position
    def mute(self): pass
    def louder(self, step): pass
    def close(self): pass


class Sound:
    """mpv playing the file's sound with no picture. Its playback position is
    the clock; pausing and seeking it moves the picture with it."""
    def __init__(self, player, path, start, loop, output, delay, held=False):
        self.dir = tempfile.mkdtemp(prefix='neuronte-play-'); self.path = os.path.join(self.dir, 'mpv.sock')
        cmd = [player, '--no-config', '--no-video', '--no-terminal', '--really-quiet', f'--input-ipc-server={self.path}',
               f'--start={start}', '--keep-open=no', '--audio-display=no'] + (['--pause'] if held else []) + (['--loop-file=inf'] if loop else []) \
            + ([f'--ao={output}'] if output else []) + ['--', path]
        self.child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=with_us)
        self.sock = None; self.buffer = b''; self.delay = delay; self.last = start; self.request = 0; self.volume = 100
        self.offsets = []; self.offset = None; self.checked = 0.; self.held = start if held else None
        end = time.perf_counter() + 5
        while time.perf_counter() < end and self.child.poll() is None:
            try:
                s = socket.socket(socket.AF_UNIX); s.connect(self.path); s.settimeout(.5); self.sock = s; break
            except OSError:
                s.close(); time.sleep(.02)
        if self.sock is None: self.close(); raise OSError(f'{player} did not start')
        end = time.perf_counter() + 5           # the position is unknown until the sound is open
        while time.perf_counter() < end and self.ask('get_property', 'time-pos') is None and self.alive(): time.sleep(.02)

    def alive(self): return self.sock is not None and self.child.poll() is None

    def ask(self, *command):
        if self.sock is None: return None
        self.request += 1
        try:
            self.sock.sendall(json.dumps(dict(command=list(command), request_id=self.request)).encode() + b'\n')
            while True:
                while b'\n' not in self.buffer:
                    part = self.sock.recv(65536)
                    if not part: raise OSError('closed')
                    self.buffer += part
                line, self.buffer = self.buffer.split(b'\n', 1)
                reply = json.loads(line)
                if reply.get('request_id') == self.request: return reply.get('data') if reply.get('error') == 'success' else None
        except (OSError, ValueError):
            try: self.sock.close()
            except OSError: pass
            self.sock = None; return None

    def time(self):
        """The sound's position, read off a steady local clock that is kept
        in step with it. mpv reports its position in jumps of tens of
        milliseconds, far too coarse to time pictures by; between those
        jumps the true position runs ahead of the reported one, so the
        largest recent difference is the one to follow."""
        if self.held is not None: return self.held - self.delay
        now = time.perf_counter()
        if self.offset is None or now - self.checked >= .1:
            before = time.perf_counter(); position = self.ask('get_property', 'time-pos'); after = time.perf_counter()
            self.checked = after; now = after
            if position is not None:
                self.offsets = (self.offsets + [position - (before + after) / 2])[-20:]
                best = max(self.offsets)
                if self.offset is None or abs(best - self.offset) > .25: self.offset = best; self.offsets = [best]   # a jump: follow at once
                else: self.offset += .1 * (best - self.offset)
            elif self.offset is None: return self.last
        self.last = now + self.offset - self.delay
        return self.last

    def pause(self, on):
        if on and self.held is None: self.held = self.time() + self.delay
        self.ask('set_property', 'pause', bool(on))
        if not on and self.held is not None:
            self.offset = self.held - time.perf_counter(); self.offsets = [self.offset]; self.checked = time.perf_counter(); self.held = None
    def mute(self): self.ask('cycle', 'mute')
    def louder(self, step):
        self.volume = max(0, min(130, self.volume + step)); self.ask('set_property', 'volume', self.volume)

    def seek(self, position):
        self.ask('seek', position, 'absolute+exact'); end = time.perf_counter() + 2
        while time.perf_counter() < end and self.alive():      # wait for it to land, so the picture is not judged against the old position
            now = self.ask('get_property', 'time-pos')
            if now is not None and abs(now - position) < .5 and not self.ask('get_property', 'seeking'): break
            time.sleep(.01)
        self.last = position - self.delay
        if self.held is not None: self.held = position
        else: self.offset = position - time.perf_counter(); self.offsets = [self.offset]; self.checked = time.perf_counter()

    def close(self):
        if self.sock is not None:
            self.ask('quit')
            if self.sock is not None: self.sock.close()
            self.sock = None
        if self.child.poll() is None:
            try: self.child.wait(timeout=1)
            except subprocess.TimeoutExpired: self.child.terminate()
        shutil.rmtree(self.dir, ignore_errors=True)


def clock_text(seconds):
    seconds = max(0, int(seconds)); return f'{seconds // 3600}:{seconds // 60 % 60:02}:{seconds % 60:02}' if seconds >= 3600 else f'{seconds // 60}:{seconds % 60:02}'


def status(position, duration, paused, volume, cols, row):
    """One row of text under the picture: state, position, a bar, the volume."""
    left = ('paused ' if paused else '') + clock_text(position) + (' / ' + clock_text(duration) if duration else '')
    right = f'vol {volume}' if volume is not None else ''
    room = cols - len(left) - len(right) - 4
    bar = ''
    if duration and room >= 8:
        done = min(room, max(0, round(room * position / duration)))
        bar = ' ' + '━' * done + '─' * (room - done) + ' '
    line = (' ' + left + bar + right)[:cols]
    return f'\x1b[{row};1H\x1b[0;38;2;200;200;200;48;2;24;24;24m{line.ljust(cols)}\x1b[0m'.encode()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('video', help='a file or URL ffmpeg can read')
    p.add_argument('--mode', choices=['pixels', 'cells'], default='pixels')
    p.add_argument('--cols', type=int, help='grid width in cells; default: fit the terminal')
    p.add_argument('--rows', type=int)
    p.add_argument('--pixel-size', type=pixel_size, metavar='WIDTHxHEIGHT',
                   help='pixels mode: retain this many RGB samples and display at natural pixel size')
    p.add_argument('--fps', type=float, help='default: the file\'s own rate')
    p.add_argument('--filter-threads', type=int, default=1, help='scaling workers (default: 1; 0 lets ffmpeg choose)')
    p.add_argument('--decoder-threads', type=int, default=0, help='codec workers (default: 0 lets ffmpeg choose; fewer use less memory)')
    p.add_argument('--decoded-format', choices=['auto', 'rgb24', 'gbrp'], default='auto',
                   help='--pixel-size: the RGB layout ffmpeg writes; auto takes planar gbrp when the native compositor packs it')
    p.add_argument('--decoder', choices=['auto', 'libav', 'ffmpeg'], default='auto',
                   help='libav decodes local files inside the player with the same frames as the ffmpeg command; '
                        'auto uses it when build/libneuronte-media.so loads and accepts the file')
    p.add_argument('--start', type=float, default=0, help='begin at this many seconds')
    p.add_argument('--frames', type=int, help='stop after this many source frames')
    p.add_argument('--untimed', action='store_true', help='benchmark: process every frame as fast as possible, without sound')
    p.add_argument('--loop', action='store_true')
    p.add_argument('--no-audio', action='store_true', help='play no sound and keep time by the wall clock')
    p.add_argument('--audio-output', help='mpv audio output, such as pulse or null')
    p.add_argument('--audio-delay', type=float, default=0, help='seconds the picture runs behind the sound\'s position')
    p.add_argument('--transport', choices=['auto', 'shm', 'inline'], default='auto',
                   help='pixels mode: shared memory for a local kitty or Kilix, else inline')
    p.add_argument('--no-status', action='store_true', help='no row of text under the picture')
    p.add_argument('--characters', choices=['portable', 'full'], default='portable',
                   help='cells mode: the 328 block characters, or every character of the bundle (slower)')
    p.add_argument('--helper', action='store_true', help='cells mode with --characters full: use the learned speed helper')
    p.add_argument('--lavfi', action='store_true', help='the video argument is an ffmpeg lavfi source, such as testsrc2; no sound')
    p.add_argument('--input-fd', type=int, help='read keys from this descriptor instead of the terminal')
    p.add_argument('--log', help='write one JSON line of timings per source frame')
    p.add_argument('--stats', help='write a JSON summary at the end')
    p.add_argument('--weights'); p.add_argument('--library')
    a = p.parse_args()
    if a.pixel_size and (a.mode != 'pixels' or a.cols is not None or a.rows is not None):
        p.error('--pixel-size requires pixels mode and cannot be combined with --cols or --rows')
    if a.decoded_format != 'auto' and not a.pixel_size: p.error('--decoded-format requires --pixel-size')
    if a.filter_threads < 0: p.error('--filter-threads must be nonnegative')
    if a.decoder_threads < 0: p.error('--decoder-threads must be nonnegative')
    for tool in ['ffmpeg', 'ffprobe']:
        if not shutil.which(tool): p.error(f'{tool} is required and was not found')
    if a.helper and (a.mode != 'cells' or a.characters != 'full'): p.error('--helper requires --mode cells --characters full')
    if a.decoder == 'libav' and (a.lavfi or not os.path.isfile(a.video)): p.error('--decoder libav requires a local file')
    library = a.library or ROOT / 'build/libneuronte.so'
    if not os.path.exists(library): p.error(f'{library} is missing; run make first, or pass --library')
    width, height, rate, duration, has_sound, chroma = probe(a.video, a.lavfi)
    fps = a.fps or rate
    if not 0 < fps <= 240: p.error('frame rate must be above 0 and at most 240')
    if a.start < 0 or (duration and a.start >= duration): p.error('--start is outside the file')
    transport = a.transport if a.transport != 'auto' else ('shm' if shared_memory_reaches_terminal() else 'inline')
    player = next((x for x in ('kilix-mpv', 'mpv') if shutil.which(x)), None)
    notes = []
    if not a.no_audio and not a.lavfi and has_sound and player is None: notes.append('no sound: neither kilix-mpv nor mpv is installed')
    media = None
    if a.decoder != 'ffmpeg' and not a.lavfi and os.path.isfile(a.video):
        # Local files only: a network stream could block the player itself.
        try: media = MediaDecoder()
        except OSError as exc:
            if a.decoder == 'libav': p.error(f'the in-process decoder is not available: {exc}')
            notes.append('decoder: ffmpeg command (build/libneuronte-media.so is not built)')

    helper = None
    if a.mode == 'pixels':
        # Each block receives one decoded sample. Explicit pixel sizing uses
        # the same 2 x 4 neural masks for drawing, with no block enlargement.
        fitter = MultiInk(a.weights, library, *BLOCKS)
        renderer = fitter if a.pixel_size else MultiInk(a.weights, library, *CELL)
    else:
        fitter = None
        # The speed helper is bound to the bundle it was trained on (split-v5);
        # without --weights, cells use that bundle when the helper is on.
        bundle = cell_bundle(a.weights, a.helper)
        renderer = TwoInk(a.characters, *CELL, bundle, library)
        if a.helper:
            import hashlib
            from neuronte_video_helpers import Helper, features
            helper = Helper(ROOT / 'weights/neuronte-video-speed-v1.json', 'speed', runtime=True)
            if helper.doc.get('scalar_bundle_sha256') != hashlib.sha256(open(bundle, 'rb').read()).hexdigest():
                p.error('the speed helper was trained against a different bundle')

    # Both layouts carry the same RGB samples; planes skip ffmpeg's slower
    # packed conversion and are packed by the compositor instead.
    decoded = 'rgb24'
    if a.pixel_size:
        decoded = fitter.natural_input_format() if a.decoded_format == 'auto' else a.decoded_format
    planar = decoded == 'gbrp'

    out = sys.stdout.buffer
    geometry = {}

    def layout():
        cols, rows, ratio = terminal()
        room = rows - (0 if a.no_status or rows < 4 else 1)
        if a.pixel_size:
            w, h = a.pixel_size
            geometry.update(cols=cols, rows=rows, c=(w+1)//2, r=(h+3)//4, w=w, h=h,
                            left=1, top=1, status=None if a.no_status or rows < 4 else rows)
            return
        grid_c, grid_r = fit(width, height, a.cols or cols, a.rows or room, ratio)
        if a.cols: grid_c = a.cols
        if a.rows: grid_r = a.rows
        unit = BLOCKS if a.mode == 'pixels' else CELL          # what ffmpeg scales one cell to
        geometry.update(cols=cols, rows=rows, c=grid_c, r=grid_r, w=grid_c * unit[0], h=grid_r * unit[1],
                        left=max(1, (cols - grid_c) // 2 + 1), top=max(1, (room - grid_r) // 2 + 1),
                        status=None if a.no_status or rows < 4 else rows)
    layout()
    if geometry['c'] < 1 or geometry['r'] < 1: p.error('--cols and --rows must be positive')

    used = set()

    def decoder(position):
        g = geometry
        options = dict(start=position, chroma=chroma, lavfi=a.lavfi, exact_pixels=bool(a.pixel_size),
                       filter_threads=a.filter_threads, decoder_threads=a.decoder_threads, pix_fmt=decoded)
        stream = media.open(a.video, g['w'], g['h'], fps, **options) if media else None
        if stream is None and a.decoder == 'libav': raise ValueError('the in-process decoder declined this file')
        if stream is None and media and 'libav-declined' not in used:
            used.add('libav-declined'); notes.append('decoder: ffmpeg command (the in-process decoder declined this file)')
        source = (LibraryFrames(stream, direct=planar and bool(a.pixel_size)) if stream else
                  Decoder(decoder_command(a.video, g['w'], g['h'], fps, **options)))
        used.add(source.kind)
        return source

    def draw_pixels(colours):
        picture = renderer.decode(colours)
        return picture[:geometry['h'], :geometry['w']] if a.pixel_size else picture

    def present_pixels(picture):
        return presenter.frame(picture, geometry['c'], geometry['r'], geometry['left'], geometry['top'],
                               natural=bool(a.pixel_size))

    output_frame = None

    def render_natural(frame):
        nonlocal output_frame
        shape = (geometry['h'], geometry['w'], 3)
        if output_frame is None or output_frame.shape != shape:
            output_frame = np.empty(shape, np.uint8)
        if isinstance(frame, tuple):
            return renderer.render_planes(*frame, geometry['w'], geometry['h'], output_frame)
        if planar: return renderer.render_gbrp(frame, out=output_frame)
        return renderer.render_rgb24(frame, out=output_frame)

    presenter = Presenter(out, transport)
    keys = None
    source = clock = None; shown = dropped = count = skipped = seeks = 0; failure = ''; resized = []
    # Opening a bad log path must fail before changing the terminal's input mode.
    log = open(a.log, 'w', buffering=1) if a.log else None; late = []; cost = dict(read=0., fit=0., draw=0., pack=0., write=0.); wire = 0
    for number in (signal.SIGTERM, signal.SIGHUP):          # leave through finally, so the terminal and the sound are put back
        signal.signal(number, lambda *_: sys.exit(0))
    signal.signal(signal.SIGWINCH, lambda *_: resized.append(1))
    began = time.perf_counter()
    try:
        keys = Keys(a.input_fd)
        out.write(b'\x1b[?1049h\x1b[?25l\x1b[2J'); out.flush()
        if not a.no_audio and not a.untimed and not a.lavfi and has_sound and player:
            try: clock = Sound(player, a.video, a.start, a.loop, a.audio_output, a.audio_delay, held=True)
            except OSError as exc: notes.append(f'no sound: {exc}')
        if clock is None: clock = WallClock(a.start); clock.pause(True)
        origin = a.start; index = 0; previous = None; paused = False; drawn = -1.
        pending = None; preview = False; read_time = 0.
        source = decoder(origin); waiting = True    # the clock is held until the first picture is in hand

        def restart(position):
            nonlocal source, origin, index, previous, waiting, pending, preview, read_time, dropped
            source.close()
            if pending is not None:
                dropped += 1
                pending['record'].update(dropped=True, interrupted=True)
                if log: log.write(json.dumps(pending['record']) + '\n')
            presenter.discard(); pending = None; read_time = 0.; preview = paused
            if not waiting and not paused: clock.pause(True)
            waiting = True
            origin = position; index = 0; previous = None; source = decoder(origin)

        while pending is not None or a.frames is None or count < a.frames:
            # Revisit controls throughout long frame intervals and decoder stalls.
            # Packed pictures stay pending until their full deadline, including
            # pauses and rates below one frame per second.
            wait = .05 if paused and not preview else 0.
            if a.untimed and pending is not None and pending['payload'] is None:
                wait = .001                        # retry backpressure without spinning or blocking controls
            if pending is not None and not paused and not a.untimed:
                wait = max(0., min(.05, pending['pts'] - clock.time()))
            for key in keys.read(wait):
                if key == 'quit': raise KeyboardInterrupt
                if key == 'pause':
                    paused = not paused; drawn = -1.
                    if not waiting: clock.pause(paused)
                elif key == 'mute': clock.mute()
                elif key in ('quieter', 'louder'): clock.louder(5 if key == 'louder' else -5); drawn = -1.
                elif (key in SEEK or key == 'home') and not a.lavfi:
                    target = 0. if key == 'home' else clock.time() + SEEK[key]
                    target = max(0., min(target, max(0., duration - 1)) if duration else target)
                    restart(target); clock.seek(target); seeks += 1; drawn = -1.
            if resized:
                del resized[:]; layout(); out.write(b'\x1b[2J'); restart(clock.time()); drawn = -1.
            now = clock.time()
            if geometry['status'] and int(now) != int(drawn):
                out.write(status(now, duration, paused, clock.volume, geometry['cols'], geometry['status'])); out.flush(); drawn = now
            if paused and not preview: continue
            if pending is None:
                t0 = time.perf_counter()
                raw = source.read(geometry['w'] * geometry['h'] * 3)
                t1 = time.perf_counter(); read_time += t1 - t0
                if raw == b'': continue
                if waiting:
                    waiting = False
                    if not paused: clock.pause(False)
                if raw is None:
                    failure = source.failure()
                    if failure: break
                    if not a.loop or paused: break
                    restart(0.); clock.seek(0.); continue
                shape = (3, geometry['h'], geometry['w']) if planar else (geometry['h'], geometry['w'], 3)
                frame = raw if isinstance(raw, tuple) else np.frombuffer(raw, np.uint8).reshape(shape)
                if preview and paused:                      # a paused seek/resize gets one picture, then holds
                    if a.mode == 'pixels':
                        picture = render_natural(frame) if a.pixel_size else draw_pixels(fitter.encode(pad_cells(frame, fitter)))
                        payload = present_pixels(picture)
                    else:
                        payload = text(renderer, renderer.fit(frame), None, geometry['left'], geometry['top'])
                    if payload: out.write(payload); out.flush(); presenter.sent()
                    index = 1; preview = False; read_time = 0.
                    continue
                preview = False
                pts = origin + index / fps; index += 1; count += 1
                now = clock.time(); record = dict(n=count, t=round(time.monotonic(), 6), pts=round(pts, 4), clock=round(now, 4), read_ms=round(read_time * 1e3, 3))
                if not a.untimed and now > pts + 1 / fps and shown:
                    dropped += 1; record['dropped'] = True; read_time = 0.
                    if log: log.write(json.dumps(record) + '\n')
                    continue
                if a.mode == 'pixels':
                    if a.pixel_size:
                        t2 = t1
                        picture = render_natural(frame)
                    else:
                        colours = fitter.encode(pad_cells(frame, fitter)); t2 = time.perf_counter()
                        picture = draw_pixels(colours)
                    t3 = time.perf_counter()
                    payload = present_pixels(picture)
                else:
                    if helper is not None:
                        k = helper.doc['inference']['candidates']
                        scores = helper(features(frame))
                        cells = renderer.fit(frame, np.argpartition(scores, -k, axis=1)[:, -k:].reshape(geometry['r'], geometry['c'], k))
                    else:
                        cells = renderer.fit(frame)
                    t2 = t3 = time.perf_counter()
                    payload = text(renderer, cells, previous, geometry['left'], geometry['top']); previous = cells
                t4 = time.perf_counter()
                pending = dict(payload=payload, pts=pts, record=record,
                               costs=(read_time, t2 - t1, t3 - t2, t4 - t3))
                if payload is None and a.untimed:
                    pending['picture'] = picture   # keep this frame until the consumer has space
                read_time = 0.
            if not a.untimed and clock.time() < pending['pts']: continue
            payload, pts, record = pending['payload'], pending['pts'], pending['record']
            if payload is None and a.untimed:
                retry = time.perf_counter()
                payload = present_pixels(pending['picture'])
                costs = pending['costs']
                pending['costs'] = (*costs[:3], costs[3] + time.perf_counter() - retry)
                if payload is None: continue
                pending['payload'] = payload
                del pending['picture']
            if payload is None:                             # the terminal is behind: skip, do not queue
                skipped += 1; record['skipped'] = True; pending = None
                if log: log.write(json.dumps(record) + '\n')
                continue
            lateness = (clock.time() - pts) * 1e3
            wrote = time.perf_counter()
            out.write(payload); out.flush(); presenter.sent(); t5 = time.perf_counter(); shown += 1; wire += len(payload); late.append(lateness)
            for name, value in zip(('read', 'fit', 'draw', 'pack'), pending['costs']):
                cost[name] += value
                record[name + '_ms'] = round(value * 1e3, 3)
            cost['write'] += t5 - wrote
            record.update(write_ms=round((t5 - wrote) * 1e3, 3), late_ms=round(lateness, 3),
                          bytes=len(payload), wall=round(t5 - began, 4), shown=round(time.monotonic(), 6))
            pending = None
            if log: log.write(json.dumps(record) + '\n')
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    except ValueError as exc:
        failure = str(exc)
    finally:
        for number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT): signal.signal(number, signal.SIG_IGN)   # a second signal must not cut this short
        elapsed = time.perf_counter() - began
        tail = presenter.close()                            # first: the pictures in /dev/shm are the one thing nobody else removes
        if source: source.close()
        if clock: clock.close()
        if keys: keys.close()
        if log: log.close()
        try:
            out.write(tail + b'\x1b[?2026l\x1b[0m\x1b[?25h\x1b[?1049l'); out.flush()
        except (OSError, ValueError):
            pass
    late = np.array(late or [0.])
    summary = dict(shown=shown, dropped=dropped, skipped_terminal_busy=skipped, source_frames=count, seeks=seeks, seconds=round(elapsed, 3),
                   shown_per_second=round(shown / elapsed, 2) if elapsed else 0, grid=[geometry['c'], geometry['r']], mode=a.mode,
                   transport=transport if a.mode == 'pixels' else 'text', sound=type(clock).__name__ == 'Sound' if clock else False,
                   late_ms=dict(median=round(float(np.median(late)), 2), p95=round(float(np.percentile(late, 95)), 2), max=round(float(late.max()), 2)),
                   mean_ms={k: round(v / shown * 1e3, 3) if shown else 0 for k, v in cost.items()}, wire_bytes=wire, notes=notes)
    summary.update(decoded_size=[geometry['w'], geometry['h']], decoded_format=decoded, decoder='+'.join(sorted(used - {'libav-declined'})),
                   image_size=(list(a.pixel_size) if a.pixel_size else
                               [geometry['c'] * CELL[0], geometry['r'] * CELL[1]]) if a.mode == 'pixels' else None)
    if a.stats:
        with open(a.stats, 'w') as f: f.write(json.dumps(summary, indent=1) + '\n')
    print(f'{shown} frames shown, {dropped} dropped, {skipped} skipped for a busy terminal, {summary["shown_per_second"]:.1f} per second; '
          f'{geometry["c"]} x {geometry["r"]} cells, {a.mode}, {summary["transport"]}, sound {"on" if summary["sound"] else "off"}'
          + ''.join('; ' + n for n in notes), file=sys.stderr)
    if failure:
        print(f'decoding stopped early: {failure}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except (ValueError, OSError) as exc: print(str(exc), file=sys.stderr); sys.exit(2)
