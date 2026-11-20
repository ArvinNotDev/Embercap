"""Telegraphed three-phase Bellwarden encounter, vulnerable to crown stomps."""
import math
import pygame as pg
from .enemy import Projectile
class Boss:
    def __init__(self,d):
        self.x=float(d['x']); self.floor=d['y']; self.arena=d['arena']; self.hp=self.max_hp=d['hp']; self.name=d['type']; self.variant=d['silhouette']; self.rain_targets=[self.x-90,self.x,self.x+90]
        self.state='sleep'; self.timer=0.; self.cycle=0; self.hit_timer=0.; self.dead=False; self.death_time=0.; self.time=0.; self.fired=False
    @property
    def phase(self): return 1 if self.hp>self.max_hp*2/3 else 2 if self.hp>self.max_hp/3 else 3
    @property
    def rect(self):
        height=38 if self.state=='weak' else 76
        return pg.Rect(round(self.x)-36,self.floor-height,72,height)
    @property
    def vulnerable(self): return self.state=='weak' and self.hit_timer<=0 and not self.dead
    def hit(self,game):
        if not self.vulnerable: return False
        self.hp-=1; self.hit_timer=.85; game.shake=7; game.audio.play('boss'); game.particles.burst(self.x,self.rect.top,'#ffe4a6',30,110); game.add_score(250)
        if self.hp<=0:
            self.dead=True; self.state='dead'; self.death_time=0.; game.level.projectiles.clear(); game.add_score(3000); game.audio.play('victory')
        return True
    def update(self,dt,level,game):
        self.time+=dt; self.hit_timer=max(0,self.hit_timer-dt)
        if self.dead:
            self.death_time+=dt
            if int(self.time*20)!=int((self.time-dt)*20) and self.death_time<2: game.particles.burst(self.x+math.sin(self.time*47)*40,self.floor-40+math.sin(self.time*33)*30,'#e4b4fa',4,80)
            return
        if self.state=='sleep':
            if game.player.x>self.arena[0]: self.state='tell'; self.timer=1.15; game.notify(self.name.upper()+'  •  WAIT FOR THE GLOWING CROWN',3.5)
            return
        self.timer-=dt
        if self.state=='tell' and self.timer<=0:
            self.state='attack'; self.timer=1.15; self.fired=False; game.audio.play('boss'); game.shake=3
            pattern=(self.variant+self.cycle%self.phase)%3
            if pattern==0:
                for direction in (-1,1): level.projectiles.append(Projectile(self.x+direction*42,self.floor-9,direction*(115+15*self.phase+3*self.variant),0,'wave',5))
            elif pattern==1:
                dx=game.player.x+8-self.x; dy=game.player.y+10-(self.floor-56); length=max(1,math.hypot(dx,dy))
                for offset in (-.23-self.variant*.014,0,.23+self.variant*.014):
                    a=math.atan2(dy,dx)+offset
                    level.projectiles.append(Projectile(self.x,self.floor-56,math.cos(a)*130,math.sin(a)*130,'orb',4))
            else:
                for x in self.rain_targets: level.projectiles.append(Projectile(x,0,0,145+self.variant*7,'orb',3))
                for direction in (-1,1): level.projectiles.append(Projectile(self.x+direction*42,self.floor-9,direction*115,0,'wave',5))
        elif self.state=='attack' and self.timer<=0:
            self.state='weak'; self.timer=3.3; game.notify('CROWN EXPOSED!  JUMP ON TOP',1.6)
        elif self.state=='weak' and self.timer<=0:
            self.cycle+=1; self.state='tell'; self.timer=1.25 if self.phase<3 else 1.0
            self.rain_targets=[max(self.arena[0]+20,min(self.arena[1]-20,game.player.x+8+off)) for off in (-95,0,95)]
    def draw(self,screen,art,camera):
        if self.dead and self.death_time>2.1: return
        image=art.image(f'boss_{int(self.time*5)%4}')
        image=image.copy(); tint=pg.Color(0); tint.hsva=(self.variant*24,36,100,100); image.fill(tint,special_flags=pg.BLEND_RGB_MULT)
        if self.state=='weak': image=pg.transform.scale(image,(96,52))
        if self.dead:
            image=pg.transform.rotate(image,math.sin(self.time*30)*8); image.set_alpha(max(0,int(255*(1-self.death_time/2.1))))
        if self.hit_timer>0 and int(self.time*25)%2==0: return
        screen.blit(image,(int(self.x-camera)-48,self.floor-image.get_height()+5))
        if self.state=='weak':
            x=int(self.x-camera); y=self.rect.top-12
            pg.draw.polygon(screen,'#fff0a9',[(x-6,y-4),(x,y+3),(x+6,y-4)])
            pg.draw.ellipse(screen,'#ffe8a4',(x-19,self.rect.top-3,38,6),1)
        if self.state=='tell':
            label=['GROUND WAVE • JUMP','EMBER FAN • KEEP MOVING','SKYFALL • LEAVE THE MARKS'][(self.variant+self.cycle%self.phase)%3]
            art.text(screen,label,(320,83),11,'#ffe4b1',bold=True,center=True,shadow=True)
            pg.draw.circle(screen,'#ffb288',(int(self.x-camera),self.floor-53),int(9+math.sin(self.time*18)*3),2)
            if (self.variant+self.cycle%self.phase)%3==2:
                for x in getattr(self,'rain_targets',[]): pg.draw.line(screen,'#b1738a',(x-camera,105),(x-camera,285),1)
