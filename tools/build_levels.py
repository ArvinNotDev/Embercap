"""Authoring recipes bake full, non-random layouts into editable JSON files.
Every mandatory gap is <= 84 px (walking jump reaches ~94 px; running ~140).
Optional upper routes use <=48 px rises; moving/collapsing routes have fallbacks.
"""
import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.settings import ROOT
NAMES=['Green Meadows','Crystal Caverns','Sky Ruins','Molten Foundry','Shadow Citadel']
SUB=['A courier, a spark, a long road home.','Follow the light beneath the roots.','The wind remembers the old kingdom.','Keep a cool head above the furnace.','Ring the dawn through the endless night.']
# Deliberately ordered challenges, not random generation.
PLANS=[
 ['intro','steps','garden','gap','blocks','garden','gap','steps','bridge','garden','blocks','gap','steps','bridge','garden','gap','blocks','rest'],
 ['rest','crystal','steps','water','rocks','narrow','crystal','water','blocks','rocks','narrow','water','steps','rocks','crystal','water','narrow','blocks','rest'],
 ['rest','islands','wind','bridge','ruins','islands','lift','wind','ruins','bridge','islands','lift','ruins','wind','bridge','islands','ruins','lift','bridge','rest'],
 ['rest','furnace','cogs','collapse','lava','furnace','steps','cogs','lava','collapse','furnace','cogs','bridge','collapse','lava','steps','furnace','cogs','collapse','lava','rest'],
 ['rest','traps','steps','guards','bridge','traps','ruins','guards','gap','traps','bridge','guards','ruins','gap','traps','guards','steps','bridge','traps','sanctum']]
EXTRA=[
 'rest crystal rocks narrow steps water bridge guards crystal narrow rocks lift crystal bridge narrow water guards steps rest',
 'rest water bridge guards lift islands water bridge ruins water guards lift wind water narrow bridge guards rest',
 'rest steps rocks gap guards narrow rocks blocks lift gap ruins rocks steps guards narrow gap rocks garden rest',
 'rest garden traps steps guards gap garden bridge traps blocks guards garden gap traps ruins guards bridge rest',
 'rest cogs lift collapse steps cogs bridge guards furnace lift cogs ruins collapse traps cogs narrow bridge rest',
 'rest guards furnace steps ruins lava guards blocks bridge furnace traps guards lava ruins bridge guards collapse rest',
 'rest narrow guards water ruins traps bridge narrow rocks guards water lift ruins guards rocks bridge narrow rest',
 'rest wind cogs bridge lift guards islands cogs wind collapse bridge guards lift cogs islands wind ruins rest',
 'rest crystal lava rocks collapse furnace lava crystal lift guards cogs lava narrow rocks furnace collapse crystal rest',
 'rest guards steps traps ruins lava cogs bridge guards rocks collapse furnace narrow wind guards traps lift lava sanctum']
PLANS.extend(p.split() for p in EXTRA)
NAMES.extend(['Frostline Depot','Sunken Armada','Red Dune Pass','Thornwood Camp','Clockwork Works','Ashen Capital','Moonlit Trenches','Stormrail Crossing','Deep Core','Dawn Bastion'])
BOSSES=['Briar Knight','Crystal Wyrm','Sky Carrier','Siege Tank','Shadow Colossus','Ice Walker','Dreadnought','Burrower','Thorn Queen','Gear Titan','War Train','Wraith Gunship','Rail Cannon','Core Sentinel','Emperor Mech']
for idx,plan in enumerate(PLANS):
    data={'id':idx+1,'name':NAMES[idx],'subtitle':SUB[idx%5],'width':len(plan)*480+720,'height':432,'spawn':[48,250], 'solids':[], 'coins':[], 'powerups':[], 'enemies':[], 'hazards':[], 'checkpoints':[], 'signs':[], 'decor':[], 'sections':[]}
    def solid(x,y,w,h=24,kind='ground',**kw): data['solids'].append(dict(x=x,y=y,w=w,h=h,kind=kind,**kw))
    def enemy(x,kind,y=260,span=100): data['enemies'].append(dict(x=x,y=y,kind=kind,left=x-span/2,right=x+span/2))
    def hazard(x,y,w,kind,**kw): data['hazards'].append(dict(x=x,y=y,w=w,h=16,kind=kind,**kw))
    for n,kind in enumerate(plan):
        x=n*480; data['sections'].append({'x':x,'design':kind})
        gaps=[]
        if kind in ('gap','water','lava'): gaps=[(192,72),(360,60)]
        elif kind in ('islands','wind'): gaps=[(144,72),(324,84)]
        elif kind in ('bridge','lift'): gaps=[(192,84)]
        elif kind=='narrow': gaps=[(144,60),(276,60),(396,48)]
        elif kind=='collapse': gaps=[(168,72),(336,72)]
        cursor=0
        for start,width in gaps:
            solid(x+cursor,288,start-cursor,144)
            cursor=start+width
            if kind in ('water','lava'): hazard(x+start,342,width,'water' if kind=='water' else 'lava')
            if kind in ('bridge','lift'):
                solid(x+start+12,260,48,12,'moving',axis='y' if kind=='lift' else 'x',distance=28 if kind=='lift' else 24,period=3.4)
            if kind=='collapse': solid(x+start+12,288,48,16,'collapse')
        solid(x+cursor,288,480-cursor,144)
        # Nonessential upper coin routes branch from a clearly reachable stair.
        if kind in ('steps','blocks','ruins','crystal','garden','guards'):
            solid(x+100,244,72,16,'platform'); solid(x+196,204,96,16,'platform'); solid(x+324,240,72,16,'platform')
            for a in range(5): data['coins'].append([x+204+a*16,177])
            if kind=='blocks':
                for a in range(4): solid(x+196+a*24,136,24,24,'block' if a==1 else 'break')
            if kind in ('crystal','ruins'): data['powerups'].append({'x':x+234,'y':173,'kind':'wings'})
        if kind=='intro':
            data['signs'] += [{'x':70,'text':'A / D   MOVE     SHIFT   RUN'},{'x':235,'text':'SPACE   JUMP • HOLD TO LEAP HIGHER'}]
        if idx==0 and n==1: data['signs'].append({'x':x+40,'text':'STOMP SHELLBACKS • SEEK THE HIGH ROAD'})
        if idx==0 and n==4: data['signs'].append({'x':x+45,'text':'BUMP GOLD BLOCKS FROM BELOW'})
        if kind in ('furnace','traps'):
            for a in (190,350): hazard(x+a,272,24,'vent' if kind=='furnace' else 'trap',period=3.2,phase=n*.37+a*.01)
        if kind=='rocks':
            for a in (210,355): hazard(x+a,0,20,'rock',period=3.8,phase=a*.01)
        if kind=='cogs':
            hazard(x+245,267,24,'saw',axis='x',distance=54,period=3.0)
            solid(x+170,240,144,16,'moving',axis='y',distance=14,period=3.6)
        if kind=='wind': data['signs'].append({'x':x+35,'text':'TRUST THE COIN TRAIL • RUN FOR DISTANCE'})
        if kind in ('lava','water'):
            for start,width in gaps:
                for a in range(4): data['coins'].append([x+start-4+a*24,227-int(10*(a in (1,2)))])
        else:
            for a in (68,92,116,380,404,428): data['coins'].append([x+a,252])
        if n>0 and n%3==0: data['powerups'].append({'x':x+62,'y':256,'kind':['health','speed','star','wings'][(n//3+idx)%4]})
        if n not in (0,len(plan)-1) and n%2==0:
            typ=['beetle','ram','spark','sentry','ram'][(idx+n//2)%5] if idx>=5 else ['beetle','beetle','ram','sentry','spark'][idx]
            # Put ground enemies in a solid, hazard-free stretch at the start of a section.
            enemy(x+64,typ,260,84)
        if n>2 and n%3==1: enemy(x+305,'wing',191 if idx==2 else 218,100)
        if idx>=2 and kind in ('guards','ruins','furnace'): enemy(x+360,'sentry',260,40)
        if n in (len(plan)//3,2*len(plan)//3):
            data['checkpoints'].append([x+26,288]); data['powerups'].append({'x':x+47,'y':252,'kind':'health'})
        for a in (34,305,450): data['decor'].append([x+a,288])
    arena=len(plan)*480
    solid(arena,288,720,144)
    data['checkpoints'].append([arena+50,288]); data['powerups'].append({'x':arena+78,'y':256,'kind':'health'})
    data['boss']={'type':BOSSES[idx],'silhouette':idx,'hp':7+idx//2,'x':arena+430,'y':288,'arena':[arena+120,arena+675]}
    data['signs'].append({'x':arena+60,'text':BOSSES[idx].upper()+' • DODGE, THEN STRIKE THE GLOWING CROWN'})
    data['exit']=arena+670
    data['weapon_pickups']=[dict(x=x,y=269,weapon=w) for x,w in zip((160+idx%5*16,510+idx%4*480,1940+idx%3*480,3860+idx%5*480),('sword','pistol','machinegun','shotgun'))]
    (ROOT/'levels'/f'level_{idx+1}.json').write_text(json.dumps(data,indent=2)+'\n')
print('Fifteen authored level layouts exported.')
