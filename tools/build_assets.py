"""Reproducible original pixel art and synthesized music. No network assets."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import sys, math, random, wave, struct, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame as pg
from src.settings import ROOT, PALETTES
pg.init()
OUT = ROOT / 'assets'
INK = '#25283e'
def surface(w, h): return pg.Surface((w, h), pg.SRCALPHA)
def rect(s, c, r): pg.draw.rect(s, c, r)
def line(s, c, a, b, w=1): pg.draw.line(s, c, a, b, w)
def poly(s, c, pts): pg.draw.polygon(s, c, pts)
def ellipse(s, c, r): pg.draw.ellipse(s, c, r)
def save(s, name): pg.image.save(s, OUT / 'sprites' / (name + '.png'))
def player(state, f):
    s = surface(32, 40)
    bob = [0, -1, 0, 1][f] if state in ('idle','walk','run') else 0
    if state == 'land': bob = 2
    if state == 'jump': bob = -1
    # Scarf streaming in the wind, boot silhouette, warm hood and tiny lantern.
    poly(s, INK, [(9,19+bob),(2,20+bob),(0,27+bob),(10,24+bob)])
    poly(s, '#58b5ad', [(9,20+bob),(3,21+bob),(2,25+bob),(10,23+bob)])
    stride = [0,3,0,-3][f] if state in ('walk','run') else 0
    if state == 'jump': stride = 3
    if state == 'fall': stride = -2
    rect(s, INK,(9-stride,29+bob,6,7)); rect(s, INK,(18+stride,29+bob,6,7))
    rect(s,'#7c5c57',(10-stride,30+bob,4,4)); rect(s,'#b17f66',(19+stride,30+bob,4,4))
    ellipse(s,INK,(7,18+bob,20,16)); ellipse(s,'#508f80',(9,19+bob,16,12))
    rect(s,'#90d3b0',(12,21+bob,8,6)); rect(s,'#d9b57e',(9,28+bob,15,2))
    ellipse(s, INK,(6,5+bob,22,19)); ellipse(s,'#f8d9a0',(9,9+bob,17,13))
    poly(s, INK,[(4,15+bob),(6,7+bob),(12,3+bob),(21,2+bob),(27,8+bob),(29,15+bob)])
    poly(s,'#d95b53',[(6,13+bob),(8,7+bob),(13,5+bob),(21,4+bob),(25,8+bob),(27,13+bob)])
    rect(s,'#f48c65',(10,7+bob,11,3)); rect(s,'#ffb47a',(12,6+bob,5,2))
    rect(s,'#943e50',(5,14+bob,23,3)); rect(s,'#ffc883',(8,13+bob,18,2))
    rect(s,INK,(20,18+bob,2,3)); rect(s,'#d98e79',(23,21+bob,3,2))
    if state == 'hurt': rect(s,'#fff1c4',(18,17+bob,5,2))
    line(s,INK,(26,24+bob),(28,28+bob)); rect(s,INK,(26,27+bob,6,7)); rect(s,'#ffdf88',(27,28+bob,4,5)); rect(s,'#fff4d4',(28,29+bob,2,3))
    if state == 'transform':
        for k in range(5):
            a = k*math.tau/5+f*.6
            x,y=int(16+15*math.cos(a)),int(19+17*math.sin(a))
            rect(s,'#fff4be',(x,y,2,2))
    if state == 'death': s=pg.transform.rotate(s, [15,40,75,90][f]); s=pg.transform.scale(s,(32,40))
    return s
for state in ('idle','walk','run','jump','fall','land','hurt','death','transform'):
    for f in range(4): save(player(state,f),f'player_{state}_{f}')
for kind in ('beetle','wing','ram','sentry','spark'):
    for f in range(4):
        s=surface(32,32); bob=f%2
        if kind in ('beetle','ram'):
            for x in (5,13,21): line(s,INK,(x,23),(x+(-2 if f%2 else 2),28),2)
            ellipse(s,INK,(3,10+bob,26,17)); ellipse(s,'#a97363' if kind=='ram' else '#7a8e60',(5,11+bob,22,13))
            ellipse(s,'#e8b879' if kind=='ram' else '#bdd178',(7,12+bob,16,6))
            line(s,INK,(16,11+bob),(17,24+bob)); rect(s,'#fff0bd',(24,17+bob,3,3)); rect(s,INK,(26,18+bob,2,2))
            if kind=='ram': poly(s,'#f6d9b1',[(23,11),(29,6),(27,16)]); poly(s,'#f6d9b1',[(6,11),(2,6),(4,16)])
        elif kind=='wing':
            poly(s,INK,[(14,15),(2,4+f*3),(0,18),(11,23)]); poly(s,'#a399dc',[(12,16),(3,8+f*3),(3,18),(11,21)])
            poly(s,INK,[(18,15),(30,4+f*3),(32,18),(21,23)]); poly(s,'#d1bef0',[(20,16),(29,8+f*3),(29,18),(21,21)])
            ellipse(s,INK,(10,10+bob,12,18)); ellipse(s,'#8071aa',(12,12+bob,8,13)); rect(s,'#fff0ad',(12,15+bob,3,3)); rect(s,'#fff0ad',(18,15+bob,3,3))
        elif kind=='sentry':
            poly(s,INK,[(5,28),(7,9),(16,3),(25,9),(27,28)]); poly(s,'#8c8199',[(8,25),(10,10),(16,7),(22,11),(24,25)])
            rect(s,'#c6b4b1',(10,10,12,3)); rect(s,INK,(10,15,13,7)); rect(s,'#f6977d',(12,17,9,3)); rect(s,'#ffe4ab',(13+f%3,17,3,2))
            rect(s,'#514760',(4,27,24,3))
        else:
            poly(s,INK,[(3,24),(6,14),(10,18),(15,2+f),(21,13),(25,10),(29,24),(22,30),(10,30)])
            poly(s,'#ee704d',[(6,24),(9,17),(12,20),(16,8+f),(20,18),(24,15),(26,24),(21,28),(11,28)])
            ellipse(s,'#ffe08b',(12,19,10,9)); rect(s,INK,(11,21,2,3)); rect(s,INK,(21,21,2,3))
        save(s,f'{kind}_{f}')
for f in range(6):
    s=surface(20,24); w=[12,9,5,3,5,9][f]
    ellipse(s,INK,(10-w//2-1,4,w+2,16)); ellipse(s,'#d98b45',(10-w//2,5,w,14)); ellipse(s,'#ffe18a',(10-w//2,5,max(2,w-2),11))
    if w>4: line(s,'#fff2c2',(8,8),(8,13),2)
    save(s,f'coin_{f}')
for kind,color in [('health','#f17b86'),('speed','#6ce3b7'),('star','#ffe788'),('wings','#c9b8ff')]:
    s=surface(24,28); ellipse(s,INK,(2,4,20,21)); ellipse(s,color,(4,6,16,16)); ellipse(s,'#fff0d2',(7,8,4,3)); rect(s,INK,(8,23,8,3))
    if kind=='health': rect(s,'#fff7df',(10,10,4,10)); rect(s,'#fff7df',(7,13,10,4))
    elif kind=='speed': poly(s,INK,[(13,8),(7,15),(12,15),(10,21),(18,12),(13,12)])
    elif kind=='star': poly(s,'#fff8db',[(12,8),(14,12),(19,13),(15,16),(16,21),(12,18),(7,21),(9,16),(5,13),(10,12)])
    else:
        poly(s,'#fff8db',[(11,18),(5,10),(6,18),(11,21)]); poly(s,'#fff8db',[(13,18),(19,10),(18,18),(13,21)])
    save(s,kind)
for idx,p in enumerate(PALETTES):
    rng=random.Random(idx)
    for type_ in ('ground','platform','block','break','collapse','moving'):
        s=surface(24,24)
        rect(s,p['edge'],(0,0,24,24)); rect(s,p['soil'],(1,3,22,20))
        if type_=='ground':
            rect(s,p['top'],(0,0,24,4)); rect(s,p['near'],(0,4,24,2))
            for k in range(10):
                x,y=rng.randrange(2,22),rng.randrange(8,23); rect(s,p['edge'],(x,y,3,2))
            if idx==0:
                for x in range(2,24,6): line(s,p['top'],(x,4),(x+1,7))
            else:
                line(s,p['edge'],(0,14),(24,14)); line(s,p['edge'],(12,6),(12,14)); line(s,p['edge'],(6,15),(6,23))
        else:
            rect(s,p['top'],(1,1,22,3)); rect(s,p['far'],(3,6,18,14)); rect(s,p['edge'],(4,20,16,2))
            for x,y in ((4,6),(18,6),(4,17),(18,17)): rect(s,p['top'],(x,y,2,2))
            if type_=='break':
                line(s,p['edge'],(0,12),(24,12),2); line(s,p['edge'],(12,3),(12,12),2); line(s,p['edge'],(6,12),(6,24),2)
            if type_=='block':
                rect(s,'#ffc979',(7,6,10,10)); rect(s,p['edge'],(10,8,4,4)); rect(s,'#fff0b5',(10,16,4,2))
            if type_=='collapse': line(s,p['edge'],(9,4),(14,12),2); line(s,p['edge'],(14,12),(8,20),2)
            if type_=='moving': poly(s,p['accent'],[(8,8),(14,12),(8,17)]); line(s,p['accent'],(16,7),(16,18))
        save(s,f'tile_{idx}_{type_}')
    s=surface(48,64)
    if idx==0:
        rect(s,'#624e47',(21,30,8,34)); rect(s,'#8b6751',(23,33,3,29))
        for r,c in [((2,13,42,33),'#356b60'),((7,3,34,34),'#57956a'),((10,6,26,18),'#91bd78')]: ellipse(s,c,r)
        for x,y in ((13,12),(28,18),(8,27),(34,29)): rect(s,'#bed98a',(x,y,3,2))
    elif idx==1:
        for x,y,h in ((6,32,30),(18,12,50),(32,27,35)):
            poly(s,'#335a80',[(x,63),(x-4,y+10),(x+3,y),(x+11,y+11),(x+10,63)])
            poly(s,'#6dc6c5',[(x,60),(x-2,y+11),(x+3,y+2),(x+5,y+12),(x+5,60)]); line(s,'#bcfff0',(x+3,y+5),(x+3,55))
    elif idx==2:
        rect(s,'#686c8c',(10,14,28,50)); rect(s,'#b6b1b3',(14,16,20,48)); rect(s,'#e7d8b3',(15,16,4,48))
        for y in (14,22,55): rect(s,'#e7d8b3',(7,y,34,4))
        line(s,'#686c8c',(29,28),(25,37)); line(s,'#686c8c',(25,37),(31,42))
    elif idx==3:
        rect(s,'#282b3c',(8,3,33,61)); rect(s,'#776071',(12,3,25,61)); rect(s,'#b88b86',(14,3,4,61))
        for y in (10,40): rect(s,'#332e41',(4,y,42,9)); rect(s,'#c89380',(7,y+2,36,2))
    else:
        rect(s,'#302c48',(8,0,32,64)); poly(s,'#8c6f9f',[(12,48),(12,14),(24,4),(36,14),(36,48)])
        poly(s,'#ceb1d0',[(15,44),(15,17),(24,9),(33,17),(33,44)]); line(s,'#594769',(24,10),(24,46),3); line(s,'#594769',(15,27),(33,27),3)
        rect(s,'#7d6c91',(5,49,38,5))
    save(s,f'decor_{idx}')
for f in range(4):
    s=surface(96,96); bob=f%2
    # Bellwarden: crowned owl-shaped bronze/obsidian automaton.
    poly(s,INK,[(8,77),(4,41),(20,29),(21,11),(34,18),(48,6),(62,18),(76,11),(77,29),(92,41),(88,77),(68,87),(28,87)])
    poly(s,'#5b5070',[(10,72),(9,44),(25,34),(29,24),(48,16),(67,24),(72,34),(87,44),(83,72),(66,82),(29,82)])
    poly(s,'#8e7593',[(15,44),(30,34),(34,26),(48,20),(63,27),(67,35),(81,44),(70,66),(26,66)])
    for x in (27,54):
        ellipse(s,INK,(x-4,33+bob,23,24)); ellipse(s,'#d9ae8d',(x-2,35+bob,19,20)); ellipse(s,'#ffc984',(x,38+bob,15,13)); rect(s,'#fff5c9',(x+5,38+bob,5,10))
    poly(s,'#f0bd85',[(42,53),(54,53),(48,64)]); rect(s,'#282b42',(32,68,32,12)); rect(s,'#e3a78b',(36,71,24,3))
    for x in (14,72):
        rect(s,'#3d3955',(x,51,10,24)); rect(s,'#a08ba8',(x+2,53,3,19))
    for x in (24,58): rect(s,INK,(x,82,15,9)); rect(s,'#b6a0b8',(x+2,83,11,5))
    poly(s,'#ffe3a1',[(39,16),(39,5),(45,11),(48,0),(52,11),(58,5),(57,16)])
    save(s,f'boss_{f}')
# Tiny standalone FX sprites are also included.
for name,color in [('sparkle','#fff0ac'),('ember','#ff9866'),('dust','#d5c1ac')]:
    s=surface(9,9); line(s,color,(4,0),(4,8)); line(s,color,(0,4),(8,4)); rect(s,'#fff4d6',(3,3,3,3)); save(s,name)
# Fonts bundled with their upstream license.
shutil.copy('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', OUT/'fonts'/'UI.ttf')
shutil.copy('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', OUT/'fonts'/'Title.ttf')
license_path=Path('/usr/share/doc/fonts-dejavu-core/copyright')
if license_path.exists(): shutil.copy(license_path,OUT/'fonts'/'LICENSE.txt')
RATE=22050
def wav(name, data):
    with wave.open(str(OUT/'audio'/f'{name}.wav'),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(struct.pack('<'+'h'*len(data),*[int(max(-1,min(1,x))*26000) for x in data]))
def tone(freq,t): return math.sin(math.tau*freq*t)*.7 + math.sin(math.tau*freq*2*t)*.2 + math.sin(math.tau*freq*3*t)*.1
for name,notes,dur in [('jump',[340,510,680],.19),('coin',[880,1320],.16),('stomp',[180,100],.16),('hurt',[220,175,110],.32),('power',[440,550,660,880],.55),('checkpoint',[520,650,780,1040],.6),('boss',[100,130,70],.6),('victory',[440,550,660,880,660,880,1100],1.6),('over',[440,330,260,165],1.0),('break',[200,120,80],.2),('click',[660,800],.08)]:
    data=[]
    for i in range(int(RATE*dur)):
        t=i/RATE; part=t/dur*len(notes); env=min(1,t*100)*(1-t/dur)**1.3
        data.append(tone(notes[min(len(notes)-1,int(part))],t)*env*.27)
    wav(name,data)
melodies=[[0,4,7,12,11,7,4,7,2,5,9,14,12,9,5,2],[0,7,10,14,12,7,3,7,2,5,10,12,10,5,2,-2],[0,7,12,16,14,12,7,4,5,9,12,17,16,12,9,7],[0,3,7,10,7,3,2,7,-2,2,5,8,7,5,2,-2],[0,7,3,10,7,12,10,7,-2,5,2,8,5,10,8,5]]
for k,mel in enumerate(melodies):
    beat=[.32,.43,.34,.29,.37][k]; length=beat*32; root=[220,164.81,261.63,146.83,174.61][k]
    data=[]
    for i in range(int(RATE*length)):
        t=i/RATE; n=int(t/beat); local=t%beat; freq=root*2**(mel[n%16]/12)
        lead=tone(freq,t)*math.exp(-local*9)*.13
        bass=tone(root*2**([0,-5,-2,-7][(n//8)%4]/12)/2,t)*math.exp(-(t%(beat*2))*4)*.09
        pad=math.sin(math.tau*root*t)*.02+math.sin(math.tau*root*1.5*t)*.02
        tick=math.sin(math.tau*(75 if n%2==0 else 1200)*t)*math.exp(-local*65)*.035
        # Half-wave tremolo keeps seamless, gently articulated loop boundaries.
        data.append((lead+bass+pad+tick)*min(1,t*30,(length-t)*30))
    wav(f'theme_{k+1}',data)
pg.quit()
print('Original artwork, eleven sound effects and five musical themes generated.')
