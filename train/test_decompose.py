"""Check batching against independent nets, and interrupted training against a full run."""
import argparse
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

import decompose as d


class DecompositionTests(unittest.TestCase):
    def test_geometry_and_repertoire(self):
        n = 16
        yy, xx = np.mgrid[0:2*n+1, 0:n+1]/n
        full = np.stack((xx+3*yy, 2*xx-yy))
        for count in d.DEVELOPMENT_COUNTS:
            groups = d.specs('repertoire', count)
            self.assertEqual([c for group in groups for c in group['scalars']], d.SCALARS)
            self.assertLessEqual(max(len(g['scalars']) for g in groups)-min(len(g['scalars']) for g in groups), 1)
            tiles = d.specs('spatial', count)
            self.assertEqual(sum(g['width'] for g in tiles), 128)
            self.assertAlmostEqual(sum((s['region'][1]-s['region'][0])*(s['region'][3]-s['region'][2]) for s in tiles), 2.)
            for spec in tiles:
                x0,x1,y0,y1=spec['region']
                x,y=x0+xx*(x1-x0),y0+yy*(y1-y0)/2
                np.testing.assert_allclose(d.crop(full,spec['region']),np.stack((x+3*y,2*x-y)),rtol=0,atol=1e-12)

    def test_independent_gradients_and_adam(self):
        # A padded three-character model and a full five-character model.
        # The reference uses individual Linear layers and the original broadcast
        # distance loss, so neither batching nor cdist defines its answer.
        torch.manual_seed(8)
        torch.set_num_threads(1)
        torch.set_default_device(os.environ.get('DECOMPOSE_TEST_DEVICE', 'cpu'))
        nets=[torch.nn.Sequential(torch.nn.Linear(90,8),torch.nn.ReLU(),torch.nn.Linear(8,8),
              torch.nn.ReLU(),torch.nn.Linear(8,8),torch.nn.ReLU(),torch.nn.Linear(8,1)) for _ in range(2)]
        layers=[[m for m in net if isinstance(m,torch.nn.Linear)] for net in nets]
        ws=[torch.nn.Parameter(torch.stack([net[i].weight.detach() for net in layers])) for i in range(4)]
        bs=[torch.nn.Parameter(torch.stack([net[i].bias.detach() for net in layers])) for i in range(4)]
        optim=torch.optim.Adam(ws+bs,lr=.002)
        refs=[torch.optim.Adam(net.parameters(),lr=.002) for net in nets]
        valid=torch.tensor([[1,1,1,0,0],[1,1,1,1,1.]])
        for _ in range(3):
            xy=torch.rand(2,5,17,2)*torch.tensor([1.,2.]);cf=torch.randn(2,5,64)
            pu=torch.rand(2,7,13,2)*torch.tensor([1.,2.]);cu=torch.randn(2,7,64)
            wanted=torch.rand(2,5,17)*2-1;truth=(torch.rand(2,5,13)>.7).float()
            got=d.objective(torch,ws,bs,cf,xy,wanted,valid,cu,pu,truth,1.)
            expected=[]
            for k,g in enumerate((3,5)):
                def field(c,p):
                    features=[p[...,:1]*2-1,p[...,1:]-1]
                    for octave in range(6):
                        phase=2*np.pi*2**octave*p
                        features.extend((phase.sin(),phase.cos()))
                    features.append(c[:,None].expand(-1,p.shape[1],-1))
                    return nets[k](torch.cat(features,-1)).squeeze(-1)
                labelled=(field(cf[k,:g],xy[k,:g])-wanted[k,:g]).abs().mean()
                su=(8*field(cu[k],pu[k])).sigmoid();area=su.mean(1)
                dd=(su[:,None]-su[None]).abs().mean(-1)
                dt=(su[:,None]-truth[k,None,:g]).abs().mean(-1)
                loss=labelled+(torch.relu(.08-area)+torch.relu(area-.25)).mean()
                loss=loss+torch.relu(.12-dd)[~torch.eye(7,dtype=torch.bool)].mean()+torch.relu(.12-dt).mean()
                expected.append(loss)
            torch.testing.assert_close(got,torch.stack(expected),rtol=2e-6,atol=2e-7)
            optim.zero_grad();got.sum().backward()
            for k,ref in enumerate(refs):
                ref.zero_grad();expected[k].backward()
                for i,layer in enumerate(layers[k]):
                    torch.testing.assert_close(ws[i].grad[k],layer.weight.grad,rtol=2e-5,atol=2e-7)
                    torch.testing.assert_close(bs[i].grad[k],layer.bias.grad,rtol=2e-5,atol=2e-7)
                ref.step()
            optim.step()
            for k in range(2):
                for i,layer in enumerate(layers[k]):
                    # Independent CUDA GEMMs and batched GEMMs reduce in a
                    # different order. Adam can amplify sub-ULP near-zero
                    # gradient differences; require <1e-6 absolute drift.
                    torch.testing.assert_close(ws[i][k],layer.weight,rtol=1e-5,atol=1e-6)
                    torch.testing.assert_close(bs[i][k],layer.bias,rtol=1e-5,atol=1e-6)

    def test_checkpoint_resume_and_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            dirs=[Path(temp)/name for name in ('full','interrupted')]
            for directory in dirs:
                directory.mkdir()
                # A small analytic teacher keeps this test independent of fonts.
                yy,xx=np.mgrid[0:17,0:9]/8
                fields=np.repeat((.4-((xx-.5)**2+(yy-1)**2))[None],95,axis=0).astype(np.float16)
                np.save(directory/'teacher.npy',fields)
                (directory/'teacher.json').write_text(json.dumps({'sha256':d.digest(directory/'teacher.npy'),
                    'identity':{'grid':8,'sources':{},'pen':.075}}))
            a=argparse.Namespace(directory=dirs[0],mode='repertoire',parts=64,seeds='0,1',start=63,batch_models=2,
                steps=4,device='cpu',unlabelled=1.,compile=False,resume=False,log_every=1,checkpoint_every=2,stop_after=None)
            with contextlib.redirect_stdout(io.StringIO()):
                d.train(a)
                b=copy.copy(a);b.directory=dirs[1];b.stop_after=2;d.train(b)
                self.assertFalse(list(dirs[1].glob('ascii-*.json')))
                b.stop_after=None;b.resume=True;d.train(b)
                first=sorted(dirs[0].glob('ascii-*.json'));self.assertEqual(len(first),2)
                for path in first:self.assertEqual(path.read_bytes(),(dirs[1]/path.name).read_bytes())
                before=[p.read_bytes() for p in first];a.resume=True;d.train(a)
                self.assertEqual(before,[p.read_bytes() for p in first])
                b.unlabelled=.5
                with self.assertRaisesRegex(ValueError,'identity differs'):d.train(b)


if __name__=='__main__':
    unittest.main()
