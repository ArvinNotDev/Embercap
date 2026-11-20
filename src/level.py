"""Spatially indexed terrain and authored stage objects."""
import json, math
import pygame as pg
from .settings import ROOT, TILE, PALETTES
class Solid:
    def __init__(self,d,index,art=None):
        self.rect=pg.Rect(d['x'],d['y'],d['w'],d['h']); self.base=self.rect.copy(); self.kind=d['kind']; self.data=d
        self.active=True; self.one_way=self.kind in ('platform','moving','collapse'); self.dx=self.dy=0.; self.timer=-1.; self.reset=0.; self.used=False
        self.image=None
        if art:
            self.image=pg.Surface(self.rect.size,pg.SRCALPHA)
            tile=art.image(f'tile_{index}_{self.kind}')
            for y in range(0,self.rect.h,TILE):
                for x in range(0,self.rect.w,TILE): self.image.blit(tile,(x,y))
            if self.kind=='ground' and self.rect.h>24:
                # The top lip occurs only at the terrain surface, not on every row.
                for y in range(24,self.rect.h,24):
                    pg.draw.rect(self.image,PALETTES[index]['soil'],(0,y,self.rect.w,6))
    def update(self,t,dt):
        old=self.rect.topleft
        if self.kind=='moving':
            offset=math.sin(t*math.tau/self.data['period'])*self.data['distance']
            if self.data['axis']=='x': self.rect.x=self.base.x+round(offset)
            else: self.rect.y=self.base.y+round(offset)
        if self.kind=='collapse':
            if self.timer>=0:
                self.timer+=dt
                if self.timer>.65: self.active=False; self.reset+=dt
                if self.reset>3: self.timer=-1; self.reset=0; self.active=True
        self.dx=self.rect.x-old[0]; self.dy=self.rect.y-old[1]
    def draw(self,s,camera,t):
        if not self.active: return
        x=self.rect.x-camera
        if self.image:
            shake=round(math.sin(t*70)*2) if self.kind=='collapse' and self.timer>=0 else 0
            s.blit(self.image,(round(x)+shake,self.rect.y))
            if self.used: pg.draw.rect(s,'#645b6b',(round(x)+4,self.rect.y+5,self.rect.w-8,self.rect.h-9))
class Level:
    def __init__(self,number,art=None):
        self.data=json.loads((ROOT/'levels'/f'level_{number}.json').read_text()); self.number=number; self.index=(number-1)%5
        self.weapon_pickups=[dict(d,active=True) for d in self.data['weapon_pickups']]
        self.width=self.data['width']; self.time=0.; self.solids=[Solid(d,self.index,art) for d in self.data['solids']]
        self.buckets={}; self.dynamic=[]
        for s in self.solids:
            if s.kind in ('moving','collapse'): self.dynamic.append(s)
            else:
                for bucket in range(s.rect.left//128,s.rect.right//128+1): self.buckets.setdefault(bucket,[]).append(s)
        self.coins=[{'rect':pg.Rect(x-7,y-8,14,17),'active':True,'x':x,'y':y} for x,y in self.data['coins']]
        self.powerups=[dict(d,rect=pg.Rect(d['x']-10,d['y']-13,20,26),active=True) for d in self.data['powerups']]
        self.checkpoint=tuple(self.data['spawn']); self.checkpoint_index=-1; self.hazards=self.data['hazards']; self.projectiles=[]
        from .enemy import Enemy
        from .boss import Boss
        self.enemies=[Enemy(d) for d in self.data['enemies']]
        self.boss=Boss(self.data['boss']) if 'boss' in self.data else None
    def query(self,rect):
        result=[]; seen=set()
        for bucket in range(max(0,rect.left//128),rect.right//128+1):
            for s in self.buckets.get(bucket,()):
                if id(s) not in seen and s.active and s.rect.colliderect(rect): result.append(s); seen.add(id(s))
        for s in self.dynamic:
            if s.active and s.rect.colliderect(rect): result.append(s)
        return result
    def floor_at(self,x,y): return any(s.rect.top>=y-4 and s.rect.top<=y+8 for s in self.query(pg.Rect(x,y-4,2,14)))
    def update_terrain(self,dt):
        self.time+=dt
        for s in self.dynamic: s.update(self.time,dt)
    def hazard_rect(self,h):
        t=self.time+h.get('phase',0); r=pg.Rect(h['x'],h['y'],h['w'],h['h']); kind=h['kind']; active=True; warning=False
        if kind in ('vent','trap'):
            cycle=t%h['period']; active=cycle>1.5; warning=1.0<cycle<=1.5
            if kind=='vent': r.y=240; r.h=48
        elif kind=='rock':
            cycle=t%h['period']; warning=.6<cycle<1.35; active=1.35<=cycle<=2.3
            r.y=int(-24+max(0,cycle-1.35)**2*550); r.h=22
        elif kind=='saw': r.x+=round(math.sin(t*math.tau/h['period'])*h['distance']); r.h=24
        return r,active,warning
    def draw_terrain(self,screen,art,camera):
        p=PALETTES[self.index]
        for x,y in self.data['decor']:
            if -50<x-camera<680:
                screen.blit(art.image(f'decor_{self.index}'),(int(x-camera)-24,y-64))
                if self.index==0:
                    for a in (0,10,19):
                        pg.draw.line(screen,'#80a563',(int(x-camera)+a,y),(int(x-camera)+a,y-6))
                        pg.draw.rect(screen,'#f8d998',(int(x-camera)+a-1,y-7,3,2))
        for s in self.solids:
            if s.rect.right>camera-24 and s.rect.left<camera+665: s.draw(screen,camera,self.time)
        for h in self.hazards:
            if not camera-120<h['x']<camera+760: continue
            r,active,warning=self.hazard_rect(h); r.x-=round(camera); kind=h['kind']
            if kind in ('lava','water'):
                pg.draw.rect(screen,'#eb714b' if kind=='lava' else '#427aab',r)
                for x in range(r.left,r.right,6): pg.draw.line(screen,'#ffdb85' if kind=='lava' else '#8ed7dc',(x,r.y+int(math.sin(x*.4+self.time*4)*2)),(x+4,r.y+1))
            elif kind=='saw':
                center=r.center
                for k in range(10):
                    a=k*math.tau/10+self.time*3
                    pg.draw.polygon(screen,'#bbc0c6',[(center[0]+math.cos(a)*14,center[1]+math.sin(a)*14),(center[0]+math.cos(a+.3)*9,center[1]+math.sin(a+.3)*9),(center[0]+math.cos(a-.3)*9,center[1]+math.sin(a-.3)*9)])
                pg.draw.circle(screen,'#60586b',center,9); pg.draw.circle(screen,'#eaa875',center,3)
            elif kind=='rock':
                if warning:
                    art.text(screen,'!',(h['x']-camera,228),20,'#ffe0a0',bold=True)
                    pg.draw.line(screen,'#c3a6b5',(h['x']-camera+10,25),(h['x']-camera+10,210),1)
                if active:
                    pg.draw.polygon(screen,'#333448',[(r.x,r.y+7),(r.x+8,r.y),(r.right,r.y+3),(r.right+2,r.bottom-7),(r.x+9,r.bottom),(r.x-2,r.y+16)])
                    pg.draw.line(screen,'#a3abb3',(r.x+3,r.y+7),(r.x+14,r.y+4),3)
            else:
                pg.draw.rect(screen,'#292c40',(h['x']-camera,282,h['w'],6))
                if active:
                    for x in range(r.x,r.right,8):
                        height=r.h if kind=='trap' else int(24+math.sin(x+self.time*19)*10)
                        pg.draw.polygon(screen,'#e4d7cf' if kind=='trap' else '#ffab61',[(x,r.bottom),(x+4,r.bottom-height),(x+8,r.bottom)])
                        if kind=='vent': pg.draw.polygon(screen,'#ffe9a6',[(x+2,r.bottom),(x+4,r.bottom-height*.6),(x+6,r.bottom)])
                if warning: art.text(screen,'!',(r.x+7,252),16,'#ffc87d',bold=True)
        for i,(x,y) in enumerate(self.data['checkpoints']):
            sx=int(x-camera); lit=i<=self.checkpoint_index
            pg.draw.rect(screen,'#292b40',(sx,y-57,4,57)); pg.draw.rect(screen,'#b99b87',(sx+1,y-56,1,55))
            pg.draw.polygon(screen,'#ffe29a' if lit else '#8da6b3',[(sx+4,y-55),(sx+26,y-51),(sx+20,y-40),(sx+4,y-42)])
            if lit: pg.draw.circle(screen,'#fff4c9',(sx+2,y-59),3)
        x=int(self.data['exit']-camera)
        if not self.boss or self.boss.dead:
            pg.draw.rect(screen,'#38334c',(x-20,214,40,74),border_radius=16); pg.draw.rect(screen,'#bca1b6',(x-17,218,34,70),3,border_radius=15)
            pg.draw.rect(screen,'#ffdda0',(x-10,230,20,58),border_radius=9)
            for k in range(4): pg.draw.rect(screen,'#fff5d6',(x-5+int(math.sin(self.time*2+k)*8),238+k*10,2,3))
        for sign in self.data['signs']:
            sx=sign['x']-camera
            if -280<sx<650:
                pg.draw.rect(screen,'#9b7864',(sx,269,3,19)); pg.draw.rect(screen,'#5b514e',(sx-8,256,21,15)); art.text(screen,'?',(sx-3,255),11,'#ffe9ac',bold=True)
    def draw_items(self,screen,art,camera):
        for c in self.coins:
            if c['active'] and -24<c['x']-camera<665:
                frame=int(self.time*10+c['x']*.02)%6; screen.blit(art.image(f'coin_{frame}'),(int(c['x']-camera)-10,c['y']-12+int(math.sin(self.time*3+c['x'])*2)))
        for p in self.powerups:
            if p['active'] and -24<p['x']-camera<665: screen.blit(art.image(p['kind']),(int(p['x']-camera)-12,p['y']-14+int(math.sin(self.time*3)*3)))
