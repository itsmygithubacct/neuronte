"""Exercise the real fixed-feature calibration trainer on two source glyphs."""
from pathlib import Path
import os,sys,json,subprocess,tempfile
import argparse
p=argparse.ArgumentParser(description='Verify fixed-feature colour calibration and exact phase resume')
p.add_argument('source',type=Path);p.add_argument('--target-cache',type=Path);a=p.parse_args()
sys.path[:0]=['train'];import pack
from colour_sources import drawing_hashes
raw=json.loads(a.source.read_text());labels=pack.labelled_scalars(raw,'fixture')[:2];raw['training']['labelled']=' '.join(f'U+{s:X}' for s in labels);raw['training']['drawings_sha256']['glyphs']=drawing_hashes(pack.colour_drawings(raw),labels)
env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
with tempfile.TemporaryDirectory(prefix='nrt-colour-phase-') as temp:
 t=Path(temp);source=t/'source.json';source.write_text(json.dumps(raw));target=t/'targets.npz';ck=t/'state.pt'
 def run(out,extra,expected=0):
  cmd=['python3','train/colour_calibrate.py',str(source),str(t/out),*extra];r=subprocess.run(cmd,env=env,capture_output=True,text=True);assert r.returncode==expected,(r.returncode,r.stdout,r.stderr)
 run('targets.npz',['--prepare-targets',*(['--target-cache',str(a.target_cache)] if a.target_cache else [])])
 args=['--device','cpu','--steps','3','--batch-pixels','4','--targets',str(target),'--log-every','0']
 run('direct.json',args)
 run('stopped.json',[*args,'--checkpoint',str(ck),'--stop-after','1'],75)
 run('resumed.json',[*args,'--resume',str(ck)])
 assert (t/'direct.json').read_bytes()==(t/'resumed.json').read_bytes()
 d=json.loads((t/'direct.json').read_text())
 assert d['head']==raw['head'] and all(d['layers'][k]==raw['layers'][k] for k in ('l1','l2','l3'))
 assert d['layers']['out']!=raw['layers']['out'] and d['training']['drawings_sha256']==raw['training']['drawings_sha256']
 print('PASS: source coverage identity, fixed body/head, trained output only, exact optimizer/RNG checkpoint resume')
