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
        run('deadline',['--checkpoint',str(ck),'--deadline','0'],75)
        run('deadline-resume',['--resume',str(ck)])
        assert (work/'baseline.json').read_bytes()==(work/'deadline-resume.json').read_bytes(),trainer+' differs after deadline resume'
        bad=subprocess.run([sys.executable,str(ROOT/'train'/trainer),str(work/'bad.json'),*common,'--seed','8','--resume',str(ck)],cwd=ROOT,env=env,capture_output=True,text=True)
        assert bad.returncode!=0 and 'checkpoint source/arguments differ' in bad.stderr
        print(trainer+': interrupted/final resume byte-exact; incompatible resume rejected')

    # A restarted cosine phase is distinct from fresh training with a longer
    # horizon. Verify that phase's own interruption/resume and lineage.
    import hashlib
    import torch
    mono=[sys.executable,str(ROOT/'train/train.py')]
    common=['--device','cpu','--grid','8','--width','8','--seed','7','--log-every','0',
            '--set','ascii','--unlabelled','0','--score-sizes','4']
    def phase(name,args,expected=0,message=None):
        result=subprocess.run([*mono,str(work/(name+'.json')),*common,*args],cwd=ROOT,env=env,capture_output=True,text=True)
        assert result.returncode==expected,(result.returncode,result.stderr)
        if message:assert message in result.stderr,result.stderr
    parent=work/'parent.pt';ck=work/'phase.pt'
    phase('parent',['--steps','4','--checkpoint',str(parent)])
    continuation=['--steps','8','--continue-from',str(parent),'--continue-source',str(ROOT),'--continue-lr','.0002']
    phase('phase-direct',continuation+['--checkpoint',str(ck)])
    complete=torch.load(ck,map_location='cpu',weights_only=True)
    assert complete['step']==8 and complete['schedule']['T_max']==4 and complete['schedule']['last_epoch']==4
    assert all(float(s['step'])==8 for s in complete['optimizer']['state'].values())
    lineage=complete['identity']['continuation']
    assert lineage['parent_steps']==4 and lineage['phase_steps']==4 and lineage['phase_initial_lr']==.0002
    assert lineage['parent_checkpoint_sha256']==hashlib.sha256(parent.read_bytes()).hexdigest()
    original=torch.load(parent,map_location='cpu',weights_only=True)
    assert any(not torch.equal(v,original['models']['net'][k]) for k,v in complete['models']['net'].items())
    phase('phase-stopped',continuation+['--checkpoint',str(ck),'--stop-after','6'],75)
    phase('phase-resumed',['--steps','8','--resume',str(ck),'--checkpoint',str(ck)])
    assert (work/'phase-direct.json').read_bytes()==(work/'phase-resumed.json').read_bytes()
    phase('wrong-phase-seed',continuation+['--seed','8'],1,'continuation arguments differ')
    phase('wrong-phase-source',[*continuation,'--continue-source',str(work)],1,'historical source mismatch')
    phase('incomplete-parent',['--steps','4','--checkpoint',str(parent),'--stop-after','2'],75)
    phase('wrong-phase-parent',continuation,1,'requires a completed parent')
    print('mono continuation: Adam/RNG lineage retained; new cosine horizon recorded; phase resume byte-exact; invalid parents refused')
