"""Interrupt and resume both real trainers; weights must be byte-identical."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
with tempfile.TemporaryDirectory(prefix='neuronte-checkpoint-') as directory:
    work=Path(directory)
    for trainer,extra in [('train.py',['--set','ascii','--unlabelled','0','--score-sizes','4']),
                          ('colour.py',['--drawing','font/emoji.txt','--palette','font/emoji-palette.txt','--wide','--shard','0/300','--form','A','--head-width','8'])]:
        common=['--device','cpu','--grid','8','--width','8','--steps','6','--seed','7','--log-every','0',*extra]
        def run(name,args,expected=0):
            result=subprocess.run([sys.executable,str(ROOT/'train'/trainer),str(work/(name+'.json')),*common,*args],cwd=ROOT,env=env,capture_output=True,text=True)
            assert result.returncode==expected,(trainer,result.returncode,result.stderr)
        run('baseline',[])
        ck=work/'state.pt'
        run('stopped',['--checkpoint',str(ck),'--stop-after','3'],75)
        assert ck.exists() and not (work/'stopped.json').exists()
        run('resumed',['--resume',str(ck),'--checkpoint',str(ck)])
        assert (work/'baseline.json').read_bytes()==(work/'resumed.json').read_bytes(),trainer+' differs after resume'
        run('finished',['--resume',str(ck)])
        assert (work/'baseline.json').read_bytes()==(work/'finished.json').read_bytes(),trainer+' differs after final checkpoint resume'
        bad=subprocess.run([sys.executable,str(ROOT/'train'/trainer),str(work/'bad.json'),*common,'--seed','8','--resume',str(ck)],cwd=ROOT,env=env,capture_output=True,text=True)
        assert bad.returncode!=0 and 'checkpoint source/arguments differ' in bad.stderr
        print(trainer+': interrupted/final resume byte-exact; incompatible resume rejected')
