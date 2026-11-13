#!/usr/bin/env python3
"""libneuronte-media against the ffmpeg command it reproduces.

build/neuronte-media-decode writes what the library decodes as raw frames.
For every input, start, size and layout its bytes must equal the bytes that
decoder_command makes ffmpeg write, to the end of the file. The inputs cover
two streams and one (constant-rate output with and without its initial
duplicates), B-frames, odd sizes, a start offset, irregular timestamps, a
rotation matrix, 10-bit HEVC, a size change mid-stream and the last frames.
Inputs the library must decline are declined, and the player then runs the
command. The sanitizer builds repeat the harder cases and exercise the API
(tests/test_media.c), and the player is compared with both decoders. Run by
make test-media.
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.dont_write_bytecode = True
import numpy as np
from neuronte_video import MediaDecoder, MultiInk, RGBFrameReader, decoder_command

HARNESS = ROOT / 'build/neuronte-media-decode'
SANITIZED = ROOT / 'build/sanitize/neuronte-media-decode'


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', *map(str, args)], check=True)


def rate(path):
    """The frame rate the player uses, ffprobe's r_frame_rate (25 without video)."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'V:0', '-show_entries',
                          'stream=r_frame_rate', '-of', 'json', str(path)], check=True, capture_output=True).stdout
    streams = json.loads(out).get('streams') or [{'r_frame_rate': '25/1'}]
    num, den = map(int, streams[0]['r_frame_rate'].split('/'))
    return num / den


class Media(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('ffmpeg') or not HARNESS.exists():
            raise unittest.SkipTest('needs ffmpeg and make media')
        cls.temp = tempfile.TemporaryDirectory()
        d = cls.dir = Path(cls.temp.name)
        x264 = ['-c:v', 'libx264', '-preset', 'veryfast']
        # H.264 with B-frames and AAC: two streams, so rawvideo is constant-rate
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=333x187:r=25:d=4', '-f', 'lavfi', '-i', 'sine=f=440:d=4',
               *x264, '-bf', '3', '-g', '30', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', d / 'av.mp4')
        # Long enough to seek in while playing
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=320x180:r=30:d=12', '-f', 'lavfi', '-i', 'sine=f=330:d=12',
               *x264, '-g', '60', '-c:a', 'aac', '-shortest', d / 'long.mp4')
        # One stream: the command does not duplicate frames before the first
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=320x180:r=30:d=3', *x264, '-bf', '2', '-g', '45', d / 'video.mp4')
        # Timestamps that start late
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=160x90:r=24:d=3', *x264, '-output_ts_offset', '1.3', d / 'offset.mp4')
        # A gap and a change of rate, kept as they are in Matroska
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=200x120:r=25:d=3', '-vf',
               "setpts='if(lt(N,30),N/25,N/25+0.37+(N-30)*0.013)/TB'", '-fps_mode', 'passthrough', *x264,
               d / 'vfr.mkv')
        # 10-bit HEVC, and the same stream displayed a quarter turn round
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=192x108:r=30:d=2', '-c:v', 'libx265', '-x265-params',
               'log-level=error', '-pix_fmt', 'yuv420p10le', d / 'hevc10.mp4')
        ffmpeg('-display_rotation', '90', '-i', d / 'hevc10.mp4', '-c', 'copy', d / 'rotated.mp4')
        # VP9 that changes size at a keyframe: the command rebuilds its filters
        vp9 = ['-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8', '-g', '10']
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=160x96:r=25:d=1.2', *vp9, d / 'a.webm')
        ffmpeg('-f', 'lavfi', '-i', 'smptebars=s=224x128:r=25:d=1.2', *vp9, d / 'b.webm')
        (d / 'list.txt').write_text(f"file '{d / 'a.webm'}'\nfile '{d / 'b.webm'}'\n")
        ffmpeg('-f', 'concat', '-safe', '0', '-i', d / 'list.txt', '-c', 'copy', d / 'sizes.mkv')
        # Formats with 32-bit timestamps, one of them starting late, and AVI
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=176x144:r=25:d=3', '-f', 'lavfi', '-i', 'sine=d=3',
               '-c:v', 'wmv2', '-c:a', 'wmav2', '-output_ts_offset', '1.7', d / 'late.wmv')
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=176x144:r=25:d=3', '-f', 'lavfi', '-i', 'sine=d=3',
               *x264, '-bf', '2', '-c:a', 'aac', d / 'av.flv')
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=176x144:r=25:d=3', '-c:v', 'mpeg4', '-bf', '1', d / 'video.avi')
        # Declined: MPEG-TS, a raw elementary stream, audio with a cover
        ffmpeg('-i', d / 'av.mp4', '-c', 'copy', d / 'av.ts')
        ffmpeg('-i', d / 'video.mp4', '-c', 'copy', '-bsf:v', 'h264_mp4toannexb', '-f', 'h264', d / 'raw.h264')
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=64x64', '-frames:v', '1', d / 'cover.png')
        ffmpeg('-f', 'lavfi', '-i', 'sine=d=1', '-i', d / 'cover.png', '-map', '0', '-map', '1', '-c:a', 'libmp3lame',
               '-c:v', 'png', '-disposition:v', 'attached_pic', d / 'cover.mp3')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def command(self, name, start, size, layout, exact=True, chroma=None, threads=(1, 0)):
        path = self.dir / name
        return path, decoder_command(path, *size, rate(path), start=start, chroma=chroma, exact_pixels=exact,
                                     filter_threads=threads[0], decoder_threads=threads[1], pix_fmt=layout)

    def check(self, name, start, size, layout, exact=True, chroma=None, harness=HARNESS, threads=(1, 0)):
        path, cmd = self.command(name, start, size, layout, exact, chroma, threads)
        expected = subprocess.run(cmd, check=True, capture_output=True).stdout
        value = lambda flag: cmd[cmd.index(flag) + 1]
        got = subprocess.run([harness, path, value('-ss'), value('-vf'), layout, value('-threads:v'),
                              value('-filter_threads')], capture_output=True)
        self.assertEqual(got.returncode, 0, got.stderr.decode(errors='replace')[-3000:])
        self.assertNotIn(b'runtime error', got.stderr)
        frame = size[0] * size[1] * 3
        self.assertEqual(len(got.stdout) % frame, 0)
        self.assertEqual(len(got.stdout) // frame, len(expected) // frame, 'frame counts differ')
        self.assertTrue(got.stdout == expected, 'decoded bytes differ')
        return len(expected) // frame

    def test_frames_equal_the_command_to_the_end(self):
        cases = [('av.mp4', [0, 1.2, 1.37, 2.96, 3.9, 4.5], (161, 91)),
                 ('video.mp4', [0, 0.5, 1.51, 2.9], (320, 180)),
                 ('offset.mp4', [0, 0.7, 2.5], (97, 55)),
                 ('vfr.mkv', [0, 1.1, 1.3, 2.2], (100, 60)),
                 ('hevc10.mp4', [0, 0.4, 1.9], (192, 108)),
                 ('rotated.mp4', [0, 0.9], (55, 97)),
                 ('sizes.mkv', [0, 0.9, 1.3, 2.3], (161, 91)),
                 ('late.wmv', [0, 1.33], (61, 37)),
                 ('av.flv', [0, 1.33], (61, 37)),     # from 0 the command's seek passes the keyframe: no frames
                 ('video.avi', [0, 1.33], (61, 37))]
        total = 0
        for name, starts, size in cases:
            for start in starts:
                for layout in ('gbrp', 'rgb24'):
                    with self.subTest(name=name, start=start, layout=layout):
                        total += self.check(name, start, size, layout)
        self.assertGreater(total, 1000)

    def test_cell_scaling_threads_and_chroma_also_match(self):
        self.check('av.mp4', 1.37, (96, 64), 'rgb24', exact=False)
        self.check('av.mp4', 0.5, (161, 91), 'gbrp', chroma='left')
        self.check('video.mp4', 1.0, (319, 181), 'gbrp', threads=(0, 1))
        self.check('video.mp4', 1.0, (319, 181), 'gbrp', threads=(2, 3))

    def test_declined_inputs_need_the_command(self):
        for name in ('av.ts', 'raw.h264', 'cover.mp3'):
            with self.subTest(name=name):
                path, cmd = self.command(name, 0, (32, 32), 'gbrp')
                got = subprocess.run([HARNESS, path, '0.000', cmd[cmd.index('-vf') + 1], 'gbrp', '0', '1'],
                                     capture_output=True)
                self.assertEqual(got.returncode, 3, got.stderr)
        media = MediaDecoder()
        self.assertIsNone(media.open(self.dir / 'av.ts', 32, 32, 25.0))
        self.assertIsNone(media.open('testsrc2', 32, 32, 25.0, lavfi=True))
        self.assertIsNone(media.open(self.dir / 'missing.mp4', 32, 32, 25.0))
        bad = subprocess.run([HARNESS, self.dir / 'av.mp4', 'soon', 'null', 'gbrp', '0', '1'], capture_output=True)
        self.assertEqual(bad.returncode, 2)

    def test_sanitized_decoder(self):
        if not SANITIZED.exists():
            self.skipTest('make test-media builds the sanitized harness')
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:abort_on_error=1', UBSAN_OPTIONS='print_stacktrace=1')
        for name, start, size in [('av.mp4', 1.37, (161, 91)), ('sizes.mkv', 0.9, (161, 91)),
                                  ('rotated.mp4', 0.5, (55, 97)), ('vfr.mkv', 1.1, (100, 60))]:
            with self.subTest(name=name):
                path, cmd = self.command(name, start, size, 'gbrp')
                expected = subprocess.run(cmd, check=True, capture_output=True).stdout
                got = subprocess.run([SANITIZED, path, cmd[cmd.index('-ss') + 1], cmd[cmd.index('-vf') + 1], 'gbrp',
                                      '0', '1'], capture_output=True, env=env)
                self.assertEqual(got.returncode, 0, got.stderr.decode(errors='replace')[-3000:])
                self.assertTrue(got.stdout == expected)
                # Stopping early: the decoder thread is waiting on a full queue
                got = subprocess.run([SANITIZED, path, '0.000', cmd[cmd.index('-vf') + 1], 'gbrp', '0', '1', '1'],
                                     capture_output=True, env=env)
                self.assertEqual(got.returncode, 0, got.stderr.decode(errors='replace')[-3000:])

    def test_api_under_sanitizers(self):
        test = ROOT / 'build/sanitize/test_media'
        if not test.exists():
            self.skipTest('make test-media builds the API test')
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:abort_on_error=1', UBSAN_OPTIONS='print_stacktrace=1')
        got = subprocess.run([test, self.dir / 'video.mp4', self.dir / 'av.ts'], capture_output=True, env=env,
                             timeout=600)
        self.assertEqual(got.returncode, 0, got.stderr.decode(errors='replace')[-3000:])
        self.assertIn(b'passed', got.stdout)
        test = ROOT / 'build/tsan/test_media'
        if test.exists():
            env = dict(os.environ, TEST_MEDIA_THREADS='1', TSAN_OPTIONS='halt_on_error=1')
            got = subprocess.run([test, self.dir / 'video.mp4', self.dir / 'av.ts'], capture_output=True, env=env,
                                 timeout=600)
            self.assertEqual(got.returncode, 0, got.stderr.decode(errors='replace')[-3000:])
            self.assertNotIn(b'ThreadSanitizer', got.stderr)

    def test_python_frames_planes_and_composition(self):
        media = MediaDecoder()
        fitter = MultiInk()
        size = (161, 91)
        path, cmd = self.command('av.mp4', 1.37, size, 'gbrp')
        stream = media.open(path, *size, rate(path), start=1.37, pix_fmt='gbrp')
        reader = RGBFrameReader(*size, planar=True)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        copy = np.empty((3, size[1], size[0]), np.uint8)
        native = np.empty((size[1], size[0], 3), np.uint8)
        frames = 0
        try:
            while True:
                frame, expected = stream.read(), reader.read(process.stdout)
                if frame is None or expected is None:
                    self.assertIsNone(frame)
                    self.assertIsNone(expected)
                    break
                self.assertEqual(frame.number, frames)
                np.testing.assert_array_equal(stream.copy(frame, copy), expected)
                fitter.render_planes(*stream.planes(frame), *size, native)
                np.testing.assert_array_equal(native, fitter.render_gbrp(expected))
                frames += 1
        finally:
            process.kill()
            process.wait()
            process.stdout.close()
        self.assertEqual(stream.failure, '')
        self.assertGreater(frames, 50)
        stream.close()
        stream.close()
        with self.assertRaises(ValueError):
            stream.read()
        # Packed frames copy into the reader's layout
        stream = media.open(path, *size, rate(path), start=3.9, pix_fmt='rgb24')
        expected = subprocess.run(self.command('av.mp4', 3.9, size, 'rgb24')[1], check=True,
                                  capture_output=True).stdout
        packed = np.empty((size[1], size[0], 3), np.uint8)
        got = b''
        while (frame := stream.read()) is not None:
            got += stream.copy(frame, packed).tobytes()
        self.assertTrue(got == expected)
        self.assertIsNone(stream.planes(frame) if frame else None)

    def test_closing_while_the_decoder_runs_ahead(self):
        media = MediaDecoder()
        path = self.dir / 'av.mp4'
        begin = time.monotonic()
        for start in (0, 1.37, 3.9) * 5:
            stream = media.open(path, 161, 91, 25.0, start=start, pix_fmt='gbrp')
            stream.read()
            time.sleep(.01)
            stream.close()
        self.assertLess(time.monotonic() - begin, 20)

    def player(self, temp, decoder, *args, keys=(), source='long.mp4', code=0):
        """Run the player off a terminal, as check_video does; keys are
        (seconds to wait, bytes) written to its key pipe."""
        stats = Path(temp) / 'stats.json'
        stats.unlink(missing_ok=True)
        cmd = [sys.executable, str(ROOT / 'tools/neuronte-play.py'), str(self.dir / source), '--no-status',
               '--no-audio', '--stats', str(stats), '--decoder', decoder, *args]
        env = dict(os.environ, COLUMNS='200', LINES='60')
        env.pop('KITTY_WINDOW_ID', None)
        read, write = os.pipe()
        with tempfile.TemporaryFile() as picture:
            child = subprocess.Popen(cmd + ['--input-fd', str(read)], stdout=picture, stderr=subprocess.PIPE,
                                     env=env, pass_fds=[read])
            os.close(read)
            try:
                for wait, key in keys:
                    time.sleep(wait)
                    if child.poll() is None:
                        os.write(write, key)
                _, err = child.communicate(timeout=120)
            finally:
                os.close(write)
                if child.poll() is None:
                    child.kill()
            picture.seek(0)
            out = picture.read()
        self.assertEqual(child.returncode, code, err)
        return pixel_frames(out), (json.loads(stats.read_text()) if stats.exists() else None), err

    def test_player_presents_the_same_pictures_with_either_decoder(self):
        with tempfile.TemporaryDirectory() as temp:
            results = {}
            for decoder in ('libav', 'ffmpeg'):
                frames, summary, _ = self.player(temp, decoder, '--pixel-size', '161x91', '--untimed',
                                                 '--frames', '40', '--start', '1.37')
                self.assertEqual(summary['decoder'], decoder)
                self.assertEqual(summary['shown'], 40)
                results[decoder] = [pixels for _, pixels in frames]
            self.assertEqual(len(results['libav']), 40)
            self.assertTrue(results['libav'] == results['ffmpeg'])
            # The default takes the library for a local file
            frames, summary, _ = self.player(temp, 'auto', '--pixel-size', '161x91', '--untimed', '--frames', '3')
            self.assertEqual(summary['decoder'], 'libav')
            # A paused seek restarts the decoder and presents one more picture
            frames, summary, _ = self.player(temp, 'libav', '--pixel-size', '161x91',
                                             keys=[(1.0, b' '), (.3, b'\x1b[C'), (.5, b'q')])
            self.assertEqual(summary['seeks'], 1)
            self.assertEqual(summary['decoder'], 'libav')
            self.assertEqual(len(frames), summary['shown'] + 1)
            # A grid of cells takes packed frames from the library
            frames, summary, _ = self.player(temp, 'libav', '--cols', '20', '--rows', '6', '--untimed', '--frames', '5')
            self.assertEqual((summary['decoder'], summary['shown']), ('libav', 5))

    def test_player_falls_back_to_the_command(self):
        with tempfile.TemporaryDirectory() as temp:
            frames, summary, _ = self.player(temp, 'auto', '--pixel-size', '33x17', '--untimed', '--frames', '3',
                                             source='av.ts')
            self.assertEqual((summary['decoder'], summary['shown']), ('ffmpeg', 3))
            self.assertIn('decoder: ffmpeg command (the in-process decoder declined this file)', summary['notes'])
            frames, summary, err = self.player(temp, 'libav', '--pixel-size', '33x17', '--untimed', '--frames', '3',
                                               source='av.ts', code=1)
            self.assertIn(b'the in-process decoder declined this file', err)
            self.assertNotIn(b'Traceback', err)
            frames, summary, err = self.player(temp, 'libav', '--lavfi', source='av.mp4', code=2)
            self.assertIn(b'--decoder libav requires a local file', err)


def pixel_frames(out):
    """The pictures in kitty graphics packets, as check_video reads them."""
    frames, parts, header = [], [], None
    for packet in re.findall(rb'\x1b_G(.*?)\x1b\\', out, re.S):
        control, data = packet.split(b';', 1)
        fields = dict(item.split(b'=', 1) for item in control.split(b','))
        if fields.get(b'a') == b'T':
            header, parts = fields, []
        elif b'a' in fields:
            continue
        if header is None:
            continue
        parts.append(data)
        if fields.get(b'm', b'0') == b'0':
            frames.append((header, zlib.decompress(base64.standard_b64decode(b''.join(parts)))))
            header = None
    return frames


if __name__ == '__main__':
    unittest.main()
