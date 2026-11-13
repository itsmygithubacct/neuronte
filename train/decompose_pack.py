"""Pack completed ASCII experiments and write a SHA256-bound benchmark manifest."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import decompose as d
import pack


def build(directory, seeds=(0,1), completed_only=False, *, recipe=None, parts=None, unlabelled=1., hidden_width=None, steps=20000):
    if recipe is None:
        if parts is not None or unlabelled != 1 or hidden_width is not None or steps != 20000:
            raise ValueError('changed parts/loss/width/schedule require an explicit development recipe')
        modes, counts, cohort = ('spatial','repertoire'), d.COUNTS, 'fixed-matrix'
    else:
        if recipe not in ('spatial','repertoire') or parts not in d.DEVELOPMENT_COUNTS or unlabelled not in (0,1):
            raise ValueError('invalid development recipe')
        modes, counts, cohort = (recipe,), (parts,), 'development'
    if steps < 1:
        raise ValueError('training steps must be positive')
    metadata=json.loads((directory/'teacher.json').read_text())
    if d.digest(directory/'teacher.npy') != metadata['sha256']:
        raise ValueError('teacher changed')
    for target in metadata['targets'].values():
        if d.digest(directory/target['file']) != target['sha256']:
            raise ValueError('teacher target changed')
    models={};cases=[];missing=[]
    def asset(name,path,**extra):
        models[name]={'file':path.name,'sha256':d.digest(path),'bytes':path.stat().st_size,**extra}
    for name,filename in (('ascii128','neuronte-ascii-v0.nrt'),('split-v5','neuronte-split-v5.nrt')):
        dest=directory/filename;shutil.copyfile(d.ROOT/'weights'/filename,dest)
        asset(name,dest)
        cases.append({'name':name,'kind':'bundle','members':[name],'routes':[0]*95,'design':'baseline'})
    for mode in modes:
        for count in counts:
            specs=d.specs(mode,count,hidden_width)
            for seed in seeds:
                name=f'{mode}-k{count}-s{seed}'
                sources=[directory/(s['name']+f'-s{seed}.json') for s in specs]
                if not all(path.is_file() for path in sources):
                    missing.append(name)
                    if completed_only:continue
                    raise ValueError('unfinished case: '+name)
                docs=[json.loads(p.read_text()) for p in sources]
                for doc,spec in zip(docs,specs):
                    training=doc['training'];experiment=training['experiment'];identity=experiment['identity']
                    if (training['steps']!=steps or training['seed']!=seed or
                            doc['shape']['hidden_width']!=spec['width'] or
                            doc['shape']['tau']!=.15/(spec['region'][1]-spec['region'][0]) or
                            any(experiment[k]!=v for k,v in spec.items()) or
                            identity['teacher']!=metadata or identity['steps']!=steps or
                            identity['unlabelled_weight']!=unlabelled or identity['tf32'] is not False):
                        raise ValueError('candidate training identity differs: '+name)
                    if pack.scalars(str(sources[spec['index']]))[1]!=set(spec['scalars']):
                        raise ValueError('candidate repertoire differs: '+name)
                    packed=directory/(spec['name']+f'-s{seed}.nrt')
                    packed.write_bytes(pack.pack(str(sources[spec['index']])))
                path=directory/(name+'.nrt')
                if mode=='repertoire':
                    image,_=pack.bundle([str(p) for p in sources])
                    routes=[next(i for i,s in enumerate(specs) if c in s['scalars']) for c in d.SCALARS]
                else:
                    if not hasattr(pack,'pack_tiled'):
                        raise ValueError('spatial experiments require the version 6 tiled runtime/packer')
                    cols,rows=d.GRIDS[count]
                    tiled={'format':'neuronte-tiled-weights','version':1,
                           'first':'U+0000','last':'U+1FFFFF',
                           'columns':[i/cols for i in range(cols+1)],
                           'rows':[2*i/rows for i in range(rows+1)],
                           'nets':docs,
                           'tiles':[{'net':i,'mask':'0x1FFFFF','base':'U+0000','code':'place'} for i in range(count)],
                           'training':{'set':'ascii-'+name,'labelled':'U+0020..U+007E',
                                       'sources_sha256':{p.name:d.digest(p) for p in sources},
                                       'teacher':metadata,'steps':steps,'seed':seed}}
                    tiled_path=directory/(name+'.json');tiled_path.write_text(json.dumps(tiled)+'\n')
                    image=pack.pack(str(tiled_path));routes=[0]*95
                path.write_bytes(image)
                parameters=sum(len(layer['weight'])+len(layer['bias']) for doc in docs for layer in doc['layers'].values())
                asset(name,path,parameters=parameters,source_sha256={p.name:d.digest(p) for p in sources})
                cases.append({'name':name,'kind':'bundle','members':[name],'routes':routes,
                              'design':mode,'parts':count,'width':specs[0]['width'],'seed':seed,
                              'total_hidden_width':count*specs[0]['width'],'training_steps':steps,
                              'cohort':cohort,'unlabelled_weight':unlabelled,
                              'parameters':parameters,'canonical_patterns_per_handle':[95],
                              'regions':[s['region'] for s in specs],
                              'repertoires':[s['scalars'] for s in specs]})
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=d.ROOT,text=True).strip()
    manifest={'schema':'kilix-bench.ascii-experiment/v1','corpus':d.SCALARS,'teacher':metadata,
              'targets':metadata['targets'],'models':models,'cases':cases,'runtime_revision':revision,
              'cohort':cohort,'recipe':{'modes':modes,'parts':counts,'unlabelled_weight':unlabelled,
                                       'hidden_width':hidden_width,'steps':steps},
              'campaign_complete':not missing,'missing_cases':missing,
              'packer_sources_sha256':{p.name:d.digest(p) for p in (Path(__file__),Path(pack.__file__))}}
    path=directory/('partial-manifest.json' if completed_only else 'manifest.json')
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(path),'cases':len(cases),'missing':missing,'sha256':d.digest(path)}))
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--seeds',default='0,1')
    parser.add_argument('--completed-only',action='store_true',help='explicitly marked partial manifest for progress quality checks')
    parser.add_argument('--recipe',choices=('spatial','repertoire'),help='explicit separate development recipe')
    parser.add_argument('--parts',type=int,choices=d.DEVELOPMENT_COUNTS)
    parser.add_argument('--unlabelled',type=float,default=1.,choices=(0.,1.))
    parser.add_argument('--hidden-width',type=int)
    parser.add_argument('--steps',type=int,default=20000)
    args=parser.parse_args()
    build(args.directory,tuple(int(s) for s in args.seeds.split(',')),args.completed_only,
          recipe=args.recipe,parts=args.parts,unlabelled=args.unlabelled,
          hidden_width=args.hidden_width,steps=args.steps)
