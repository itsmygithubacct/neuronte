"""Original flat-colour, two-cell emoji drawings; no external artwork.

Run `python3 train/emoji.py` to reproduce font/emoji.txt and its manifest.
The drawings use this project's geometric vocabulary and existing original
prompt icons for the corresponding objects. No font, image or raster is read.
The square is 2 x 2 cell widths. Training splits it at x=1 while preserving
geometry across the join. Variation sequences and skin-tone modifiers are
outside this first single-scalar set.
"""
import json
import math
from pathlib import Path
import unicodedata

import glyphs
import strokes

ROOT = Path(strokes.ROOT)
PAL = ROOT / 'font/emoji-palette.txt'


def poly(*pts):
    return [('poly', list(pts))]


def box(x, y, w, h):
    return poly((x, y), (x+w, y), (x+w, y+h), (x, y+h))


def oval(x, y, rx, ry=None):
    ry = rx if ry is None else ry
    return poly(*[(x+rx*math.cos(i*math.pi/24), y+ry*math.sin(i*math.pi/24)) for i in range(48)])


def line(*pts, r=.065):
    return [('seg', *a, *b, r) for a, b in zip(pts, pts[1:])]


def arc(x, y, rx, ry, a, b, r=.065):
    return line(*[(x+rx*math.cos(math.radians(a+(b-a)*i/24)),
                   y+ry*math.sin(math.radians(a+(b-a)*i/24))) for i in range(25)], r=r)


def star(x, y, radius, points=5):
    return poly(*[(x+radius*(1 if i%2==0 else .42)*math.cos(-math.pi/2+i*math.pi/points),
                   y+radius*(1 if i%2==0 else .42)*math.sin(-math.pi/2+i*math.pi/points)) for i in range(points*2)])


def heart(x, y, s):
    return oval(x-s*.36,y-s*.24,s*.44)+oval(x+s*.36,y-s*.24,s*.44)+poly((x-s*.77,y-s*.1),(x+s*.77,y-s*.1),(x,y+s*.86))


def move(shapes, dx=0, dy=0, scale=1, angle=0, centre=(1,1)):
    c,s = math.cos(angle),math.sin(angle)
    def xy(x,y):
        x,y=(x-centre[0])*scale,(y-centre[1])*scale
        return x*c-y*s+centre[0]+dx,x*s+y*c+centre[1]+dy
    out=glyphs.moved(shapes,xy)
    # A uniform geometric scale also scales explicit stroke radii.
    return [(q[0],*q[1:5],q[5]*scale if q[5] is not None else None) if q[0]=='seg' else q for q in out]


def layer(entry, shapes):
    return entry, shapes


# Eyes, mouth, and semantic additions for each face. Every row is deliberate.
FACE_RULES = '''
600 dots grin teeth
601 happy grin teeth
602 happy laugh tears
603 wide grin -
604 happy grin -
605 happy grin sweat
606 squeeze laugh -
607 happy smile halo
608 slant smile horns
609 wink smile -
60a happy smile blush
60b happy smile tongue-side
60c closed smile brows
60d hearts grin -
60e shades smile -
60f side smirk -
610 dots flat -
611 closed flat -
612 side frown brows
613 closed frown sweat
614 down frown brows
615 dots diagonal -
616 squeeze wave -
617 dots kiss -
618 wink kiss heart
619 happy kiss -
61a closed kiss blush
61b dots open tongue
61c wink open tongue
61d squeeze open tongue
61e down frown -
61f wide frown brows
620 slant frown brows
621 slant frown red
622 down frown tear
623 squeeze frown brows
624 closed frown steam
625 down frown sweat
626 dots open brows
627 wide open brows
628 wide open blue
629 closed open brows
62a closed open bubble
62b squeeze open brows
62c dots grin grid
62d squeeze open tears
62e dots round -
62f wide round brows
630 wide round sweat
631 wide open hands
632 wide round teeth
633 wide flat blush
634 closed flat sleep
635 cross round -
636 dots none -
637 down flat mask
638 happy grin cat
639 happy laugh cat-tears
63a dots grin cat
63b hearts grin cat
63c side smirk cat
63d closed kiss cat
63e slant frown cat
63f down frown cat-tear
640 wide open cat
641 dots frown slight
642 dots smile slight
643 dots smile upside
644 roll flat -
910 dots zip -
911 money grin tongue
912 down diagonal thermometer
913 glasses grin teeth
914 side diagonal thinking
915 down frown bandage
916 square grid robot
917 happy smile hug
920 dots grin hat
921 dots grin clown
922 down wave green
923 squeeze laugh tilted-tears
924 closed smile drool
925 side flat nose
927 squeeze none tissue
928 side diagonal brow
929 stars grin -
92a uneven open tongue
92b dots flat hush
92c slant grid censor
92d happy none hand
92e squeeze open vomit
92f wide round burst
970 happy smile hearts
971 closed open hand
972 happy smile tear
973 happy round party
974 uneven wave blush
975 down open red-tongue
976 wide grid blue-icicles
9d0 mono smirk brow
'''


def face(eyes, mouth, extra):
    base='red' if extra in ('red','red-tongue') else 'blue' if extra in ('blue','blue-icicles') else 'green' if extra=='green' else 'purple' if extra=='horns' else 'silver' if extra=='robot' else 'paper' if extra=='clown' else 'yellow'
    back=box(.23,.28,1.54,1.45) if extra=='robot' else oval(1,1,.82)
    if 'cat' in extra: back+=poly((.28,.68),(.23,.13),(.73,.43))+poly((1.27,.43),(1.77,.13),(1.72,.68))
    if extra=='horns': back+=poly((.32,.65),(.28,.06),(.72,.42))+poly((1.28,.42),(1.72,.06),(1.68,.65))
    dark=[]; white=[]; red=[]; blue=[]; additions=[]
    for side,x in enumerate((.68,1.32)):
        if eyes in ('happy','closed','down') or eyes=='wink' and side==0:
            dark+=arc(x,.86,.17,.10,190,350) if eyes=='happy' else line((x-.14,.85),(x+.14,.85),r=.055)
            if eyes=='down': dark+=line((x-.16,.68),(x+.13,.75),r=.045)
        elif eyes in ('squeeze','cross'):
            dark+=line((x-.12,.73),(x+.12,.97),r=.055)+line((x+.12,.73),(x-.12,.97),r=.055)
        elif eyes in ('hearts','stars'):
            red+=(heart(x,.82,.24) if eyes=='hearts' else star(x,.84,.27))
        elif eyes=='shades':
            dark+=box(x-.23,.65,.46,.32)+line((.85,.74),(1.15,.74),r=.055)
        elif eyes in ('wide','roll','uneven','glasses','mono'):
            rx=.21 if eyes!='uneven' or side else .13
            white+=oval(x,.80,rx,.24)
            dark+=oval(x,.80,rx+.055,.29) if eyes in ('glasses','mono') else []
            # Pupils are a later layer, over the white eye.
            additions.append(('ink',oval(x,.69 if eyes=='roll' else .82,.075)))
            if eyes=='mono' and side==0: white[-1:]=[]
        elif eyes=='square': dark+=box(x-.14,.68,.28,.25)
        elif eyes=='money':
            dark+=line((x+.13,.68),(x-.13,.68),(x-.13,.84),(x+.13,.84),(x+.13,1),(x-.13,1),r=.045)+line((x,.60),(x,1.08),r=.035)
        else:
            dark+=oval(x+(.05 if eyes=='side' else 0),.85,.085,.11)
            if eyes=='slant': dark+=line((x-.16,.62 if side else .71),(x+.16,.71 if side else .62),r=.06)
    if mouth in ('smile','smirk','frown'):
        ry=.16 if extra!='slight' else .08
        dark+=arc(1.08 if mouth=='smirk' else 1,1.20 if mouth!='frown' else 1.50,.34,ry,10,170) if mouth!='frown' else arc(1,1.5,.34,ry,190,350)
    elif mouth in ('grin','laugh'):
        dark+=poly((.57,1.13),(1.43,1.13),(1.36,1.47),(1,1.61),(.64,1.47))
    elif mouth in ('open','round'): dark+=oval(1,1.34,.23 if mouth=='open' else .16,.30 if mouth=='open' else .19)
    elif mouth in ('flat','diagonal'): dark+=line((.68,1.33),(1.32,1.33 if mouth=='flat' else 1.2),r=.055)
    elif mouth=='wave': dark+=line((.64,1.33),(.83,1.23),(1.02,1.36),(1.20,1.24),(1.39,1.33),r=.055)
    elif mouth=='kiss': dark+=line((.9,1.19),(1.08,1.29),(.91,1.38),(1.07,1.47),r=.055)
    elif mouth in ('grid','zip'):
        dark+=box(.56,1.17,.88,.34)
        white+=box(.62,1.23,.76,.22)
        additions.append(('ink',sum((line((x,1.21),(x,1.47),r=.025) for x in (.77,1,1.23)),[])))
    if extra in ('teeth','grid') or extra=='robot':
        white+=box(.66,1.17,.68,.12)
        if extra=='grid': additions.append(('ink',sum((line((x,1.13),(x,1.53),r=.025) for x in (.78,1,1.22)),[])))
    if 'tongue' in extra or mouth=='open' and extra=='tongue': red+=oval(1.23 if extra=='tongue-side' else 1,1.53,.16,.22)
    if 'tear' in extra or extra in ('sweat','drool','bubble'):
        for x in ((.39,1.61) if 'tears' in extra else (1.6,)):
            y=.66 if extra=='sweat' else 1.42 if extra in ('drool','bubble') else 1.15
            blue+=oval(x,y,.12,.20)+poly((x-.10,y-.08),(x,y-.37),(x+.10,y-.08))
    if extra in ('blush','clown'): red+=oval(.39,1.13,.15,.10)+oval(1.61,1.13,.15,.10)
    if extra=='clown': red+=oval(1,1,.19)
    if extra in ('brows','brow'): dark+=line((.49,.59),(.77,.50),r=.045)+line((1.2,.52),(1.49,.61 if extra=='brows' else .44),r=.045)
    if extra=='halo': additions.append(('blue',arc(1,.25,.63,.12,0,360,r=.07)))
    if extra in ('heart','hearts'): red+=heart(1.66,1.46,.25)+(heart(.35,.44,.19)+heart(.30,1.56,.18) if extra=='hearts' else [])
    if extra in ('mask','tissue','bandage'):
        white+=box(.49,1.08,.99,.49) if extra!='bandage' else poly((.35,.40),(1.48,.25),(1.62,.58),(.48,.73))
        if extra=='mask': additions.append(('silver',line((.62,1.23),(1.36,1.23),r=.025)+line((.62,1.4),(1.36,1.4),r=.025)))
    if extra=='thermometer': white+=move(box(1.10,1.24,.70,.13),angle=-.35); red+=oval(1.17,1.38,.10)
    if extra in ('hand','hush','thinking','hands','hug'):
        hand=oval(1.22,1.47,.28,.20)+line((1.03,1.4),(1.03,.99 if extra=='hush' else 1.20),r=.09)
        if extra in ('hands','hug'): hand+=oval(.28,1.4,.18,.38)+oval(1.72,1.4,.18,.38)
        additions.append(('skin',hand))
    if extra=='nose': additions.append(('skin',box(.95,1,.72,.13)))
    if extra in ('hat','party'):
        additions.append(('brown' if extra=='hat' else 'purple',box(.12,.43,1.76,.14)+box(.52,.05,.96,.44) if extra=='hat' else poly((.5,.47),(.8,.02),(1.2,.47))))
        if extra=='party': additions.append(('red',poly((1.12,1.36),(1.85,1.23),(1.85,1.54))))
    if extra in ('steam','sleep','burst','blue-icicles','vomit','censor'):
        if extra=='steam': additions.append(('paper',oval(.23,1.46,.19,.12)+oval(1.77,1.46,.19,.12)))
        elif extra=='sleep': additions.append(('blue',line((1.45,.2),(1.84,.2),(1.45,.52),(1.84,.52),r=.045)))
        elif extra=='burst': additions.append(('orange',star(1,.20,.43,7)))
        elif extra=='blue-icicles': additions.append(('paper',poly((.5,1.52),(.72,1.83),(.8,1.52))+poly((1.2,1.52),(1.31,1.87),(1.50,1.52))))
        elif extra=='vomit': additions.append(('green',poly((.8,1.4),(1.2,1.4),(1.47,1.85),(.57,1.85))))
        else: additions.append(('red',box(.43,1.09,1.14,.48))); additions.append(('paper',star(.73,1.33,.13)+line((1.18,1.2),(1.18,1.34),r=.04)+oval(1.18,1.44,.035)))
    if 'cat' in extra: dark+=poly((.9,1.02),(1.1,1.02),(1,1.12))+line((.45,1.12),(.10,1.06),r=.035)+line((1.55,1.12),(1.9,1.06),r=.035)
    layers=[('yellow' if 'cat' in extra else base,back)]+[(c,s) for c,s in [('ink',dark),('paper',white),('red',red),('blue',blue)] if s]
    # Merge adjacent colours, while preserving depth where it matters.
    for entry,shapes in additions:
        if layers and layers[-1][0]==entry: layers[-1][1].extend(shapes)
        else: layers.append((entry,shapes))
    if extra in ('upside','tilted-tears'):
        layers=[(c,move(s,angle=math.pi if extra=='upside' else -.45)) for c,s in layers]
    return layers


def hand(kind):
    palm=box(.61,.85,.78,.72)+oval(1,1.48,.39,.22)
    fingers=[]
    lengths=[.50,.65,.59,.44]
    active=[0,1,2,3]
    if kind in ('fist','left-fist','right-fist'): lengths=[.15]*4
    if kind in ('up','down','left','right'): active=[0]; lengths[0]=.75
    if kind in ('thumb-up','thumb-down'): active=[]
    if kind in ('victory','crossed'): active=[0,1]
    if kind in ('horns','love'): active=[0,3]
    if kind=='call': active=[3]
    for i in range(4):
        x=.68+i*.21
        if kind=='vulcan': x += -.08 if i<2 else .08
        if kind=='splayed': x += (i-1.5)*.06
        fingers+=line((x,1.02),(x+(.13 if kind=='crossed' and i==0 else -.12 if kind=='crossed' and i==1 else 0),.87-(lengths[i] if i in active else .08)),r=.095)
    thumb=line((.66,1.36),(.36,.99 if kind not in ('thumb-up','thumb-down') else .62),r=.12)
    if kind=='okay': thumb=arc(.68,.88,.25,.26,0,360,r=.09); fingers+=line((1,.95),(1.08,.35),r=.09)
    shape=palm+fingers+thumb
    if kind in ('thumb-up','thumb-down'):
        shape=poly((.67,1.57),(.45,1.33),(.45,.88),(.76,.64),(.80,.22),
                   (1.02,.22),(1.11,.75),(1.62,.75),(1.55,1.56))
    if kind=='love': shape+=line((.67,1.12),(.25,.66),r=.12)
    angle={'down':math.pi,'left':-math.pi/2,'right':math.pi/2,'thumb-down':math.pi,'left-fist':-math.pi/2,'right-fist':math.pi/2}.get(kind,0)
    shape=move(shape,angle=angle)
    details=line((.81,1.22),(1.19,1.22),r=.035)
    if kind in ('pair','pray','clap','shake','up-pair','celebrate'):
        shape=move(shape,dx=-.38,scale=.68,angle=-.18)+move(shape,dx=.38,scale=.68,angle=.18)
        details=[]
    if kind=='pray':
        shape=poly((.37,1.64),(.73,.97),(.91,.31),(1,.19),(1.09,.31),(1.27,.97),(1.63,1.64))
        details=line((1,.40),(1,1.57),r=.035)
    if kind=='shake':
        shape=poly((.14,.68),(.51,.68),(.78,.84),(1.20,.66),(1.57,.83),(1.87,.78),(1.87,1.25),(1.50,1.24),(1.15,1.56),(.78,1.43),(.48,1.18),(.14,1.16))
        details=line((.61,1.04),(.92,1.26),(1.30,.94),r=.045)
    if kind=='up-pair':
        shape=move(palm+fingers+thumb,scale=.65,dx=-.38,angle=-math.pi/2)+move(palm+fingers+thumb,scale=.65,dx=.38,angle=math.pi/2)
    if kind=='celebrate':
        shape=move(shape,scale=.78,dy=-.15)+box(.45,1.22,.26,.64)+box(1.30,1.22,.26,.64)
    if kind=='back': details=sum((box(.62+i*.21,.35+(.12 if i in (0,3) else 0),.13,.16) for i in range(4)),[])
    layers=[('skin',shape),('brown',move(details,angle=angle))]
    if kind in ('wave','clap'): layers.append(('blue',arc(.25,.6,.17,.3,180,290,r=.045)+arc(1.75,.6,.17,.3,250,360,r=.045)))
    if kind=='writing': layers.append(('blue',line((1.25,1.75),(1.65,.65),r=.075)))
    if kind=='pinch': layers[0]=('skin',palm+arc(.8,.68,.25,.23,30,330,r=.10))
    if kind=='pinched': layers[0]=('skin',poly((.63,1.55),(.58,1.02),(1,.36),(1.42,1.02),(1.35,1.55)))
    return layers


def serial(shapes):
    out=[]
    def point(x,y): return f'{x*10:.7g},{y*10:.7g}'
    for sh in shapes:
        if sh[0]=='poly': out.append('F '+' '.join(point(x,y) for x,y in sh[1]))
        elif sh[0]=='seg': out.append(f'P@{(sh[5] or .075)*10:.7g} '+point(sh[1],sh[2])+' '+point(sh[3],sh[4]))
        else: raise ValueError(sh[0])
    return ' | '.join(out)


def drawings():
    out={}; categories={}
    def add(cp,category,layers):
        if cp in out: raise ValueError(f'duplicate U+{cp:04X}')
        if not unicodedata.name(chr(cp),None): raise ValueError(f'unassigned {cp:X}')
        out[cp]=[(c,s) for c,s in layers if s]; categories[cp]=category
    for row in FACE_RULES.strip().splitlines():
        code,eyes,mouth,extra=row.split()
        add(0x1f000+int(code,16),'faces',face(eyes,mouth,extra))
    hands={0x1f446:'up',0x1f447:'down',0x1f448:'left',0x1f449:'right',0x1f44a:'fist',0x1f44b:'wave',0x1f44c:'okay',0x1f44d:'thumb-up',0x1f44e:'thumb-down',0x1f44f:'clap',0x1f450:'pair',0x270a:'fist',0x270b:'open',0x270c:'victory',0x270d:'writing',0x1f590:'splayed',0x1f596:'vulcan',0x1f918:'horns',0x1f919:'call',0x1f91a:'back',0x1f91b:'left-fist',0x1f91c:'right-fist',0x1f91d:'shake',0x1f91e:'crossed',0x1f91f:'love',0x1f932:'up-pair',0x1f64c:'celebrate',0x1f64f:'pray',0x1f90c:'pinched',0x1f90f:'pinch'}
    for cp,kind in hands.items(): add(cp,'hands',hand(kind))
    for i in range(24):
        hour=(i%12)+1; minute=30 if i>=12 else 0
        angle=math.pi*(hour+minute/60)/6-math.pi/2
        h=(1+.41*math.cos(angle),1+.41*math.sin(angle))
        add(0x1f550+i,'clocks',[('blue',oval(1,1,.83)),('paper',oval(1,1,.70)),('ink',line((1,1),h,r=.065)+line((1,1),(1,1.60 if minute else .4),r=.05))])
    for cp,col,shape in [(0x1f534,'red','circle'),(0x1f535,'blue','circle'),(0x26ab,'ink','circle'),(0x26aa,'paper','circle'),(0x1f7e0,'orange','circle'),(0x1f7e1,'yellow','circle'),(0x1f7e2,'green','circle'),(0x1f7e3,'purple','circle'),(0x1f7e4,'brown','circle'),(0x1f7e5,'red','square'),(0x1f7e6,'blue','square'),(0x1f7e7,'orange','square'),(0x1f7e8,'yellow','square'),(0x1f7e9,'green','square'),(0x1f7ea,'purple','square'),(0x1f7eb,'brown','square'),(0x2b1b,'ink','square'),(0x2b1c,'paper','square')]:
        add(cp,'shapes',[(col,oval(1,1,.77) if shape=='circle' else box(.24,.24,1.52,1.52))])
    hearts={0x2764:'red',0x1f499:'blue',0x1f49a:'green',0x1f49b:'yellow',0x1f49c:'purple',0x1f5a4:'ink',0x1f90d:'paper',0x1f90e:'brown',0x1f9e1:'orange',0x1f494:'red',0x1f496:'red',0x1f497:'red',0x1f498:'red',0x1f49d:'red',0x1f49e:'red',0x1f495:'red',0x1f493:'red',0x1f49f:'purple'}
    for cp,col in hearts.items():
        layers=[(col,heart(1,.94,.89))]
        if cp==0x1f494: layers.append(('clear',line((1,.32),(.84,.85),(1.17,1.09),(.96,1.69),r=.07)))
        if cp==0x1f496: layers.append(('yellow',star(.33,.44,.21)+star(1.65,1.28,.18)))
        if cp==0x1f497: layers.append(('pink',heart(1,.97,.61))); layers.append(('red',heart(1,.99,.35)))
        if cp==0x1f498: layers.append(('blue',line((.15,1.74),(1.85,.22),r=.055)+poly((1.55,.18),(1.87,.16),(1.84,.5))))
        if cp==0x1f49d: layers.append(('yellow',box(.88,.3,.24,1.38)+box(.26,.82,1.48,.22)))
        if cp in (0x1f495,0x1f49e):
            layers=[(col,heart(.66,1.12,.62)+heart(1.46,.62,.44))]
            if cp==0x1f49e: layers.append(('pink',arc(1,1,.88,.65,20,155,r=.05)+arc(1,1,.88,.65,200,335,r=.05)))
        if cp==0x1f493: layers.append(('pink',arc(1,1,.98,.85,210,330,r=.05)))
        if cp==0x1f49f: layers=[('purple',box(.18,.18,1.64,1.64)),('paper',heart(1,.94,.68))]
        add(cp,'hearts',layers)
    # Reuse only our own original prompt-object shapes, enlarged into the square.
    icons=glyphs.colour_icons()
    objects='''
1f4c1 f07b Folder
1f4c2 f07c Open-folder
1f4c4 f15b Page
1f4c3 f016 Curl-page
1f4dd f0f6 Memo
1f4d1 f02e Bookmark-tabs
1f516 f02e Bookmark
1f3f7 f02b Label
1f4d5 f02d Red-book
1f4d7 f02d Green-book
1f4d8 f02d Blue-book
1f4d9 f02d Orange-book
1f4da f02d Books
1f5bc f03e Picture
1f4f7 f030 Camera
1f514 f0f3 Bell
1f4e7 f0e0 Email
2709 f0e0 Envelope
1f4ac f075 Speech
1f4e5 f01c Inbox
1f4e4 f093 Outbox
1f5d1 f014 Bin
1f517 f0c1 Link
1f4ce f0c6 Paperclip
1f4be f0c7 Disk
1f5a8 f02f Printer
1f512 f023 Lock
1f513 f09c Unlock
2699 f013 Gear
1f50d f002 Search-left
1f50e f002 Search-right
1f4bb f120 Laptop
1f3e0 f015 House
1f4c5 f073 Calendar
1f4c6 f073 Tear-calendar
1f4f6 f1eb Signal
1f50a f028 Loudspeaker
1f50b f0079 Battery
26a1 f0e7 Lightning
26a0 f071 Warning
2139 f05a Information
2705 f00c Check
274c f00d Cross
1f7f0 f00c Confirm
23f8 f04c Pause
1f310 f0ac Globe
1f527 f0ad Wrench
1f4ca f080 Chart
1f4c8 f201 Rising-chart
1f4c9 f201 Falling-chart
1f6a9 f024 Flag
1f4a1 f0eb Bulb
1f50c f1e6 Plug
1f5a5 f108 Monitor
1f5b1 f8cc Mouse
1f5b2 f8cc Trackball
2328 f11c Keyboard
1f3a7 f025 Headphones
1f3a4 f130 Microphone
1f3b5 f001 Note
1f3b6 f001 Notes
1f3ac f008 Film
1f4fa f26c Television
1f4f1 f10b Phone
2601 f0c2 Cloud
1f4e6 f187 Package
1f511 f084 Key
1f4cc f08d Pin
1f4cd f041 Round-pin
1f4a7 f043 Droplet
1f525 f06d Fire
1f680 f135 Rocket
1f41b f188 Bug
1f6e1 f132 Shield
1f3c6 f091 Trophy
1f381 f06b Gift
1f4b0 f0d6 Money
1f4b3 f09d Card
1f4b5 f0d6 Banknote
1f4b2 f155 Dollar
1f4af f292 Hundred
1f3af f140 Target
1f321 f2c9 Thermometer
1f9ed f14e Compass
1f3c1 f11e Finish
1f6ab f05e Prohibited
267b f1b8 Recycling
1f50f f023 Privacy-lock
1f510 f023 Key-lock
1f4e8 f0e0 Incoming-mail
1f4e9 f0e0 Outgoing-mail
1f4f8 f030 Flash-camera
1f4d2 f02d Ledger
1f4d3 f02d Notebook
1f4d4 f02d Decorated-notebook
1f4d6 f02d Open-book
1f4dc f0f6 Scroll
1f4cb f0ea Clipboard
1f4c7 f2bb Card-index
1f4df f10b Pager
1f4e0 f1ac Fax
1f4bd f0a0 Minidisc
1f4bf f51f Disc
1f4c0 f51f DVD
1f5c2 f07c Dividers
1f5c3 f187 Card-box
1f5c4 f0a0 Cabinet
1f6e0 f0ad Tools
2692 f0ad Hammer-pick
1f9f0 f0b1 Toolbox
'''
    # Sources not present in the icon collection receive a purpose-built shape
    # below; no arbitrary substitute icon is silently used.
    custom={
      'Globe': [('blue',oval(1,1,.8)),('paper',arc(1,1,.4,.75,0,360,r=.045)+line((.22,1),(1.78,1),r=.045))],
      'Wrench': [('silver',poly((.45,1.7),(.27,1.52),(1.18,.61),(1.08,.26),(1.36,.10),(1.32,.45),(1.58,.61),(1.87,.4),(1.78,.75),(1.44,.84)))],
      'Chart': [('blue',box(.25,1.12,.35,.61)+box(.81,.72,.35,1.01)+box(1.37,.28,.35,1.45))],
      'Rising-chart': [('blue',box(.18,.18,1.64,1.64)),('paper',line((.34,1.5),(.72,1.15),(1.05,1.3),(1.65,.48),r=.09))],
      'Flag': [('red',poly((.43,.3),(1.67,.3),(1.39,.8),(1.67,1.23),(.43,1.23))),('silver',line((.4,.2),(.4,1.82),r=.065))],
      'Bulb': [('yellow',oval(1,.77,.55)),('silver',box(.75,1.25,.5,.41)),('ink',line((.75,1.73),(1.25,1.73),r=.05))],
      'Plug': [('ink',box(.62,.60,.76,.72)+line((1,1.2),(1,1.84),r=.09)),('silver',line((.78,.2),(.78,.70),r=.08)+line((1.22,.2),(1.22,.70),r=.08))],
      'Monitor': [('silver',box(.17,.25,1.66,1.12)+box(.85,1.27,.30,.4)+box(.55,1.63,.9,.13)),('blue',box(.29,.37,1.42,.84))],
      'Mouse': [('silver',oval(1,1.13,.48,.65)),('ink',line((1,.48),(1,.95),r=.055)+arc(1,.28,.28,.22,180,360,r=.04))],
      'Keyboard': [('silver',box(.1,.47,1.8,1.06)),('ink',sum((box(.22+x*.32,.59+y*.28,.19,.16) for x in range(5) for y in range(2)),[])+box(.53,1.19,.94,.14))],
      'Headphones': [('blue',arc(1,1,.68,.73,180,360,r=.13)+box(.24,.94,.30,.61)+box(1.46,.94,.30,.61))],
      'Microphone': [('blue',oval(1,.77,.23,.52)),('silver',arc(1,1,.44,.49,0,180,r=.07)+line((1,1.4),(1,1.76),r=.07)+box(.65,1.72,.70,.12))],
      'Note': [('purple',oval(.62,1.52,.27,.17)+line((.84,1.5),(.84,.30),(1.48,.17),(1.48,.58),r=.07))],
      'Film': [('ink',box(.20,.24,1.6,1.52)),('paper',sum((box(x,y,.16,.16) for x in (.3,1.54) for y in (.35,.7,1.05,1.4)),[])),('blue',poly((.77,.69),(1.29,1),(.77,1.31)))],
      'Phone': [('ink',box(.5,.13,1,1.74)),('blue',box(.60,.31,.8,1.18)),('paper',oval(1,1.69,.07))],
      'Package': [('brown',box(.23,.39,1.54,1.35)),('yellow',box(.87,.39,.26,1.35)+box(.23,.74,1.54,.20))],
      'Key': [('yellow',arc(.66,.66,.38,.38,0,360,r=.13)+line((.92,.93),(1.69,1.70),r=.13)+line((1.36,1.36),(1.57,1.17),r=.10))],
      'Pin': [('red',oval(1,.50,.4)+poly((.72,.61),(1.28,.61),(1.42,1.21),(.58,1.21))),('silver',line((1,1.18),(1,1.88),r=.05))],
      'Round-pin': [('red',oval(1,.70,.55)+poly((.53,.95),(1.47,.95),(1,1.85))),('paper',oval(1,.67,.20))],
      'Droplet': [('blue',oval(1,1.25,.57,.54)+poly((.49,1.01),(1,.15),(1.51,1.01)))],
      'Fire': [('orange',poly((.35,1.57),(.23,1.12),(.62,.47),(.78,.87),(1.05,.12),(1.62,1.06),(1.71,1.48),(1.3,1.83),(.74,1.85))),('yellow',poly((.69,1.54),(.87,1.05),(1.07,1.40),(1.27,.97),(1.42,1.57),(1.11,1.78),(.88,1.76)))],
      'Rocket': [('red',poly((.49,1.01),(.2,1.69),(.84,1.4))+poly((1.01,1.49),(1.69,1.8),(1.4,1.16))),('silver',poly((.50,1.18),(.85,.56),(1.75,.25),(1.44,1.15),(.82,1.50))),('blue',oval(1.23,.77,.2)),('orange',poly((.57,1.44),(.18,1.82),(.7,1.6)))],
      'Bug': [('green',oval(1,1.1,.48,.62)+oval(1,.47,.29)),('ink',line((1,.54),(1,1.65),r=.05)+sum((line((.58,y),(.21,y-.12),r=.07)+line((1.42,y),(1.79,y-.12),r=.07) for y in (.75,1.1,1.45)),[]))],
      'Shield': [('blue',poly((.28,.25),(1.72,.25),(1.58,1.30),(1,1.82),(.42,1.30))),('paper',line((.61,.98),(.89,1.25),(1.40,.65),r=.10))],
      'Trophy': [('yellow',poly((.54,.22),(1.46,.22),(1.31,1.08),(1,1.28),(.69,1.08))+arc(.55,.61,.32,.32,70,285,r=.09)+arc(1.45,.61,.32,.32,250,465,r=.09)+box(.9,1.2,.2,.42)+box(.55,1.60,.9,.16))],
      'Gift': [('red',box(.25,.53,1.5,1.24)),('yellow',box(.87,.40,.26,1.37)+box(.18,.57,1.64,.25)+arc(.77,.34,.25,.16,0,360,r=.065)+arc(1.23,.34,.25,.16,0,360,r=.065))],
      'Money': [('green',box(.15,.48,1.7,1.04)),('paper',oval(1,1,.34)),('green',line((1.11,.79),(.88,.79),(.88,.99),(1.11,.99),(1.11,1.22),(.88,1.22),r=.035))],
      'Card': [('blue',box(.15,.48,1.7,1.04)),('ink',box(.15,.7,1.7,.23)),('yellow',box(.33,1.11,.35,.20))],
      'Dollar': [('green',line((1.45,.50),(.6,.50),(.5,.9),(1.4,1.1),(1.4,1.5),(.55,1.5),r=.12)+line((1,.18),(1,1.82),r=.08))],
      'Hundred': [('red',line((.27,.55),(.42,.4),(.42,1.33),r=.065)+arc(.88,.88,.22,.47,0,360,r=.07)+arc(1.48,.88,.22,.47,0,360,r=.07)+line((.25,1.56),(1.8,1.56),r=.06))],
      'Target': [('red',oval(1,1,.82)),('paper',oval(1,1,.58)),('red',oval(1,1,.34)),('paper',oval(1,1,.12))],
      'Compass': [('silver',oval(1,1,.81)),('paper',oval(1,1,.68)),('red',poly((.7,1.3),(.87,.87),(1.46,.45),(1.13,1.13)))],
      'Finish': [('paper',box(.45,.24,1.25,.97)),('ink',sum((box(.45+x*.25,.24+y*.24,.25,.24) for y in range(4) for x in range(5) if (x+y)%2==0),[])+line((.40,.18),(.40,1.84),r=.06))],
      'Prohibited': [('red',arc(1,1,.73,.73,0,360,r=.12)+line((.48,.48),(1.52,1.52),r=.12))],
      'Recycling': [('green',line((.52,1.47),(.25,1),(.60,.45),(1.14,.45),(1.65,1.30),(1.43,1.62),(.89,1.62),r=.10)+poly((.36,.46),(.78,.3),(.69,.78))+poly((1.35,.95),(1.72,1.43),(1.18,1.39))+poly((1.08,1.4),(.66,1.62),(1.04,1.85)))],
      'Clipboard': [('brown',box(.38,.27,1.24,1.52)),('paper',box(.5,.43,1,1.23)),('silver',box(.7,.16,.6,.38))],
      'Card-index': [('silver',box(.23,.37,1.54,1.26)),('blue',oval(.66,.82,.19)+box(.39,1.05,.54,.35)),('ink',line((1.09,.76),(1.52,.76),r=.045)+line((1.09,1.06),(1.52,1.06),r=.045))],
      'Fax': [('silver',box(.2,.83,1.6,.85)),('paper',box(.64,.24,.9,.91)),('ink',sum((oval(.38+x*.22,1.12+y*.20,.05) for y in range(2) for x in range(3)),[]))],
      'Minidisc': [('silver',box(.25,.25,1.5,1.5)),('blue',oval(1,1,.60)),('paper',oval(1,1,.18))],
      'Disc': [('silver',oval(1,1,.82)),('clear',oval(1,1,.18)),('blue',arc(1,1,.64,.64,210,280,r=.08))],
      'Toolbox': [('blue',box(.23,.66,1.54,1.03)+arc(1,.66,.40,.35,180,360,r=.10)),('silver',box(.9,.96,.2,.4))],
    }
    aliases={'Falling-chart':'Rising-chart','Trackball':'Mouse','Notes':'Note','Television':'Monitor','Banknote':'Money','Privacy-lock':'Lock','Key-lock':'Lock','Incoming-mail':'Email','Outgoing-mail':'Email','Flash-camera':'Camera','Ledger':'Red-book','Notebook':'Red-book','Decorated-notebook':'Red-book','Open-book':'Red-book','Scroll':'Memo','Pager':'Phone','DVD':'Disc','Dividers':'Open-folder','Card-box':'Package','Cabinet':'Minidisc','Tools':'Wrench','Hammer-pick':'Wrench'}
    byname={}
    omitted={0x1f4d1,0x1f7f0,0x1f5b2,0x1f3ac,0x1f4b0,0x1f4b5,0x1f50f,0x1f510,
             0x1f4d2,0x1f4d3,0x1f4d4,0x1f4d6,0x1f4dc,0x1f4df,0x1f4bd,0x1f5c2,
             0x1f5c3,0x1f5c4,0x2692,0x1f6e0}
    for index,row in enumerate(objects.strip().splitlines()):
        cp,icon,name=row.split(); cp=int(cp,16); icon=int(icon,16)
        if name in custom: layers=custom[name]
        elif name in aliases and aliases[name] in byname: layers=byname[aliases[name]]
        elif chr(icon) in icons:
            colour={'Red-book':'red','Green-book':'green','Blue-book':'blue','Orange-book':'orange','House':'orange','Battery':'green','Lock':'yellow','Unlock':'yellow','Email':'paper','Envelope':'paper','Cloud':'silver'}.get(name,'blue')
            layers=[(colour if c=='fg' else c,move(s,dy=-.8,scale=1.8,centre=(0,0))) for c,s in icons[chr(icon)]]
            layers=[(c,glyphs.moved(s,lambda x,y:(x+.1,y))) for c,s in layers]
        else: raise ValueError(f'needs original drawing: {name} ({icon:X})')
        # Differing objects retain meaningful identifying marks.
        if name=='Falling-chart': layers=[(c,glyphs.moved(s,lambda x,y:(x,2-y))) for c,s in layers]
        if name=='Search-right': layers=[(c,glyphs.moved(s,lambda x,y:(2-x,y))) for c,s in layers]
        if name=='Flash-camera': layers=layers+[('yellow',star(1.66,.25,.23))]
        if name=='DVD': layers=[('yellow' if c=='silver' else c,s) for c,s in layers]
        if name=='Television': layers=layers+[('ink',line((.66,.02),(1,.24),(1.34,.02),r=.04))]
        if name=='Tear-calendar': layers=layers+[('paper',poly((1.3,1.3),(1.8,1.3),(1.3,1.8)))]
        if name=='Incoming-mail': layers=layers+[('red',line((.8,.2),(.8,.71),r=.07)+poly((.58,.55),(1.02,.55),(.8,.84)))]
        if name=='Outgoing-mail': layers=layers+[('green',line((1.3,.80),(1.3,.29),r=.07)+poly((1.08,.45),(1.52,.45),(1.3,.16)))]
        if name in ('Notes','Books'): layers=[(c,move(s,scale=.65,dx=-.28)) for c,s in layers]+[(c,move(s,scale=.65,dx=.38,dy=-.18)) for c,s in layers]
        byname[name]=layers
        if cp not in omitted:
            add(cp,'objects',layers)
    # Twenty control arrows/status symbols complete the first collection.
    for cp,angle in [(0x2b05,math.pi),(0x27a1,0),(0x2b06,-math.pi/2),(0x2b07,math.pi/2),(0x2196,-3*math.pi/4),(0x2197,-math.pi/4),(0x2198,math.pi/4),(0x2199,3*math.pi/4)]:
        add(cp,'controls',[('blue',move(poly((.25,.84),(1.1,.84),(1.1,.46),(1.78,1),(1.1,1.54),(1.1,1.16),(.25,1.16)),angle=angle))])
    for cp,sh in [(0x25b6,poly((.5,.30),(1.65,1),(.5,1.70))),(0x25c0,poly((1.5,.30),(.35,1),(1.5,1.70))),(0x23f9,box(.4,.4,1.2,1.2)),(0x23fa,oval(1,1,.62)),(0x23cf,poly((.36,1.1),(1,.36),(1.64,1.1))+box(.36,1.38,1.28,.23)),(0x2795,box(.3,.85,1.4,.3)+box(.85,.3,.3,1.4)),(0x2796,box(.3,.85,1.4,.3)),(0x2797,box(.3,.85,1.4,.3)+oval(1,.43,.13)+oval(1,1.57,.13)),(0x2716,line((.5,.5),(1.5,1.5),r=.13)+line((1.5,.5),(.5,1.5),r=.13)),(0x2753,arc(1,.7,.38,.4,180,420,r=.13)+line((1.19,1.05),(1,1.24),r=.12)+oval(1,1.65,.13)),(0x2757,box(.85,.2,.3,1.03)+oval(1,1.65,.16)),(0x2734,star(1,1,.82,8))]:
        add(cp,'controls',[('red' if cp in (0x23fa,0x2753,0x2757) else 'blue',sh)])
    # These motifs have a projecting upper shape at a lower contour. Underpaint
    # that shape in the lower colour so a touching antialiased edge cannot open
    # a background seam. This is vector geometry, preserved in the target file.
    underpaint={0x1f381:[0],0x1f3c1:[0],0x1f41b:[0],0x1f496:[0],0x1f49d:[0],0x1f49e:[0],
                0x1f4e0:[1],0x1f4c6:[0],0x1f605:[1],0x1f61f:[1],0x1f625:[1],0x1f627:[1],
                0x1f62f:[1],0x1f630:[2],0x1f680:[0],0x1f912:[1,2],0x1f914:[1],0x1f915:[1],
                0x1f60b:[1],0x1f613:[1],0x1f917:[1],0x1f921:[1],0x1f972:[1],
                **{cp:[0] for cp in range(0x1f638,0x1f641)}}
    for cp,indices in underpaint.items():
        # Propagate to earlier layers too; an underpaint must not create a
        # new adjacent edge against its own backing layer.
        for i in range(max(indices),-1,-1):
            out[cp][i]=(out[cp][i][0],out[cp][i][1]+out[cp][i+1][1])
    return out,categories


def main():
    out,cat=drawings()
    lines=['# Original Neuronte emoji. Generated reproducibly by train/emoji.py.',
           '# 2 x 2 cell widths; same syntax as icons.txt, x and y design units 0..20.',
           '# No external artwork, font or raster used. Palette entries never follow foreground.']
    manifest=[]
    for cp,layers in sorted(out.items()):
        name=unicodedata.name(chr(cp))
        lines.append(f'# U+{cp:04X} {name}')
        lines.append(f'U+{cp:04X} '+' || '.join('{'+c+'} '+serial(s) for c,s in layers))
        manifest.append({'scalar':f'U+{cp:04X}','name':name,'category':cat[cp],'layers':len(layers)})
    (ROOT/'font/emoji.txt').write_text('\n'.join(lines)+'\n')
    (ROOT/'font/emoji-manifest.json').write_text(json.dumps({'version':1,'cell_columns':2,'glyphs':manifest},indent=2)+'\n')
    print(f'{len(out)} original emoji, max {max(map(len,out.values()))} layers')
    from collections import Counter
    print(dict(Counter(cat.values())))


if __name__=='__main__': main()
