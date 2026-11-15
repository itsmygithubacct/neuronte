"""A model of the picture a kitty-graphics terminal holds, for the player's tests.

It reads the player's output as a terminal would: 24-bit images placed with
a=T (shared memory, t=s, or zlib-compressed inline chunks, o=z), frame data
loaded into frame 1 of an existing image (a=f, r=1, x/y offsets) and image
deletion (a=d, d=I). Shared-memory objects are read and unlinked as soon as
their command arrives, which is the acknowledgement the player waits for.
After every synchronized update (CSI ? 2026 l) the picture now shown, the
most recently placed image that still exists, is recorded.
"""
import base64
import os
import zlib
import numpy as np

START, END, SYNC = b'\x1b_G', b'\x1b\\', b'\x1b[?2026l'


class KittyModel:
    def __init__(self, keep=True):
        self.buffer = b''; self.images = {}; self.shown = None; self.loading = None
        self.keep = keep; self.pictures = []; self.updates = 0; self.commands = dict(T=0, f=0, d=0)

    def feed(self, data):
        self.buffer += data
        while True:
            g = self.buffer.find(START); s = self.buffer.find(SYNC)
            if s >= 0 and (g < 0 or s < g):
                self.buffer = self.buffer[s + len(SYNC):]; self.sync(); continue
            if g < 0:
                self.buffer = self.buffer[-(len(SYNC) - 1):] if len(self.buffer) >= len(SYNC) else self.buffer
                return
            e = self.buffer.find(END, g)
            if e < 0:
                self.buffer = self.buffer[g:]; return
            self.command(self.buffer[g + len(START):e]); self.buffer = self.buffer[e + len(END):]

    def sync(self):
        self.updates += 1
        picture = self.picture()
        self.pictures.append(picture.copy() if self.keep and picture is not None else picture)

    def picture(self):
        return None if self.shown is None or self.shown not in self.images else self.images[self.shown]

    @staticmethod
    def fields(control):
        return {k: v for k, v in (item.split(b'=', 1) for item in control.split(b',') if item)}

    def payload(self, f, data):
        if f.get(b't') == b's':
            path = '/dev/shm/' + base64.standard_b64decode(data).decode()
            with open(path, 'rb') as stream: raw = stream.read()
            os.unlink(path); return raw
        return base64.standard_b64decode(data)

    def command(self, packet):
        control, _, data = packet.partition(b';')
        f = self.fields(control)
        if self.loading is not None:                    # a continuation chunk of an inline transfer
            head, parts = self.loading; parts.append(data)
            if f.get(b'm', b'0') == b'1': return
            self.loading = None; self.apply(head, zlib.decompress(base64.standard_b64decode(b''.join(parts))))
            return
        action = f.get(b'a', b't')
        if action == b'd':
            self.commands['d'] += 1
            if f.get(b'd') == b'I': self.images.pop(int(f[b'i']), None)
            return
        if f.get(b't', b'd') == b'd' and f.get(b'm', b'0') == b'1':
            self.loading = (f, [data]); return
        raw = self.payload(f, data)
        if f.get(b'o') == b'z': raw = zlib.decompress(raw)
        self.apply(f, raw)

    def apply(self, f, raw):
        action = f.get(b'a', b't'); w, h = int(f[b's']), int(f[b'v'])
        if f.get(b'f') != b'24': raise ValueError('only 24-bit pictures are modelled')
        pixels = np.frombuffer(raw, np.uint8)
        if pixels.size < w * h * 3: raise ValueError(f'insufficient image data {pixels.size} < {w * h * 3}')
        pixels = pixels[:w * h * 3].reshape(h, w, 3)
        image = int(f[b'i'])
        if action == b'T':
            self.commands['T'] += 1
            self.images[image] = pixels.copy(); self.shown = image
        elif action == b'f':
            self.commands['f'] += 1
            if f.get(b'r') != b'1': raise ValueError('only edits of frame 1 are modelled')
            target = self.images[image]; x, y = int(f.get(b'x', 0)), int(f.get(b'y', 0))
            if x + w > target.shape[1] or y + h > target.shape[0]: raise ValueError('frame edit outside the image')
            target[y:y + h, x:x + w] = pixels
        else:
            raise ValueError(f'unmodelled action {action!r}')
