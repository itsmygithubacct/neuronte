"""Check the draw trainer's coverage term against the native runtime and the teacher.

Needs build/libneuronte.so. MIT licence; see LICENSE.
"""
import ctypes
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

import decompose
import draw_split as ds
import pack
import strokes

ROOT = Path(__file__).resolve().parents[1]
SIZES = ((8, 16), (3, 6), (23, 46), (24, 47), (25, 49), (30, 40), (16, 48))


def native():
    lib = ctypes.CDLL(str(ROOT/'build'/'libneuronte.so'))
    lib.neuronte_open.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_float)]
    return lib


class CoverageTermTests(unittest.TestCase):
    def test_rendered_pixels_equal_native_coverage(self):
        torch.manual_seed(3)
        h = 16
        layers = [torch.nn.Linear(90, h), torch.nn.Linear(h, h), torch.nn.Linear(h, h), torch.nn.Linear(h, 1)]
        with torch.no_grad():
            layers[-1].bias.fill_(.02)
        masks = strokes.masks()
        doc = {'format': 'neuronte-weights', 'version': 1,
               'shape': {'position_octaves': 6, 'code_bits': 64, 'hidden_width': h, 'hidden_layers': 3, 'tau': .15,
                         'parity_masks': [f'0x{x:06X}' for x in masks]},
               'training': {'set': 'test', 'labelled': 'U+2500'},
               'layers': {name: {'rows': l.weight.shape[0], 'cols': l.weight.shape[1],
                                 'weight': l.weight.detach().flatten().tolist(), 'bias': l.bias.detach().tolist()}
                          for name, l in zip(('l1', 'l2', 'l3', 'out'), layers)}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'net.json'
            path.write_text(json.dumps(doc))
            image = pack.pack(str(path))
        lib = native()
        buf = ctypes.create_string_buffer(image, len(image))
        handle = ctypes.c_void_p()
        self.assertEqual(lib.neuronte_open(buf, len(image), ctypes.byref(handle)), 0)
        weights = [l.weight.detach()[None] for l in layers]
        biases = [l.bias.detach()[None] for l in layers]
        mask_bits = torch.tensor([[(m >> b) & 1 for b in range(21)] for m in masks], dtype=torch.float32)
        cf = decompose.code(torch, torch.tensor([[0x2500]]), mask_bits)
        worst, fractional = 0., 0
        for w, hh in SIZES:
            out = np.zeros(w*hh, np.float32)
            self.assertEqual(lib.neuronte_coverage(handle, 0x2500, w, hh, 0,
                                                   out.ctypes.data_as(ctypes.POINTER(ctypes.c_float))), 0)
            py, px = torch.meshgrid(torch.arange(hh), torch.arange(w), indexing='ij')
            shape = (1, 1, w*hh)
            got = ds.render_coverage(torch, weights, biases, cf, torch.full(shape, w), torch.full(shape, hh),
                                     px.reshape(shape), py.reshape(shape))
            diff = np.abs(got.reshape(-1).numpy()-out).max()
            worst = max(worst, float(diff))
            fractional += int(((out > .01) & (out < .99)).sum())
        lib.neuronte_close(handle)
        print(f'max |torch - native| = {worst:.3g} over {len(SIZES)} sizes; {fractional} fractional pixels')
        self.assertGreater(fractional, 100)
        self.assertLessEqual(worst, 1e-5)

    def test_teacher_coverage_equals_teacher_masks(self):
        n = 32
        yy, xx = np.mgrid[0:2*n+1, 0:n+1]/n
        fields = np.stack((.3-np.hypot(xx-.5, yy-1.), np.minimum(.12-np.abs(xx-.5), .4-np.abs(yy-1.3)))).astype(np.float16)
        flat = torch.tensor(fields).flatten()
        offsets = torch.arange(2).reshape(1, 2, 1)*(n+1)*(2*n+1)
        target = lambda xy: ds.bilinear(flat, offsets, n, xy)  # noqa: E731
        for w, hh in ((7, 13), (24, 48), (25, 49)):
            want = decompose.teacher_masks(fields, w, hh)
            py, px = torch.meshgrid(torch.arange(hh), torch.arange(w), indexing='ij')
            shape = (1, 2, w*hh)
            got = ds.teacher_coverage(torch, target, torch.full(shape, w), torch.full(shape, hh),
                                      px.reshape(1, 1, -1).expand(shape), py.reshape(1, 1, -1).expand(shape))
            mismatched = np.abs(got.numpy().reshape(2, hh, w)-want).max()
            self.assertLessEqual(mismatched, 1/64+1e-6)
            self.assertLess(np.mean(np.abs(got.numpy().reshape(2, hh, w)-want)), 1e-3)

    def test_pixel_samples_follow_the_native_grid(self):
        points, s = ds.pixel_samples(torch, torch.tensor([10, 30]), torch.tensor([20, 61]),
                                     torch.tensor([3, 29]), torch.tensor([0, 60]))
        self.assertEqual(s.tolist(), [2, 1])
        np.testing.assert_allclose(points[0].numpy(), [[(6.5)/20, .5/40*2], [(7.5)/20, .5/40*2],
                                                       [(6.5)/20, 1.5/40*2], [(7.5)/20, 1.5/40*2]], rtol=1e-6)
        np.testing.assert_allclose(points[1].numpy(), [[29.5/30, 60.5/61*2]]*4, rtol=1e-6)


if __name__ == '__main__':
    unittest.main()
