"""Five animated enemy families and shared, bounded projectile lifetimes."""
import math
import pygame as pg
class Projectile:
    def __init__(self,x,y,vx,vy,kind='orb',life=5):
        self.x=float(x); self.y=float(y); self.vx=vx; self.vy=vy; self.kind=kind; self.life=life; self.radius=6 if kind=='orb' else 9
    @property
    def rect(self): return pg.Rect(int(self.x)-self.radius,int(self.y)-self.radius,self.radius*2,self.radius*2)
    def update(self,dt,level):
        self.x+=self.vx*dt; self.y+=self.vy*dt; self.life-=dt
        if self.kind!='wave' and any(not s.one_way for s in level.query(self.rect)): self.life=0
    def draw(self,s,camera,t):
        x,y=int(self.x-camera),int(self.y)
        if self.kind=='wave':
            pg.draw.arc(s,'#ffaf88',(x-12,y-14,24,29),0,math.pi,3); pg.draw.arc(s,'#ffe7bc',(x-8,y-10,16,21),0,math.pi,2)
        else:
            pg.draw.circle(s,'#48344e',(x,y),8); pg.draw.circle(s,'#f9a28e',(x,y),6); pg.draw.circle(s,'#fff1c8',(x-1,y-1),3)
class Enemy:
    def __init__(self,d):
        self.hp=d.get('hp',2 if d['kind'] in ('ram','sentry') else 1); self.kind=d['kind']; self.x=float(d['x']); self.y=float(d['y']); self.origin_y=self.y; self.left=d['left']; self.right=d['right']; self.direction=1; self.vy=0.; self.time=0.; self.cooldown=1.5; self.dead=False; self.death_time=0.; self.grounded=False
    @property
    def rect(self): return pg.Rect(round(self.x),round(self.y),24,22)
    def defeat(self,game,damage=99):
        self.hp-=damage
        if self.hp>0: return
        if self.dead: return
        self.dead=True; self.death_time=.4; game.add_score(150); game.audio.play('stomp'); game.particles.burst(self.x+12,self.y+12,'#ffd29a',12); game.enemies_defeated+=1
    def update(self,dt,level,game):
        self.time+=dt
        if self.dead: self.death_time=max(0,self.death_time-dt); return
        if abs(self.x-game.player.x)>800: return
        self.cooldown-=dt
        if self.kind=='wing':
            self.x+=self.direction*44*dt; self.y=self.origin_y+math.sin(self.time*2.6)*26
            if self.x>self.right: self.direction=-1
            if self.x<self.left: self.direction=1
            return
        if self.kind=='sentry':
            if self.cooldown<0 and abs(game.player.x-self.x)<390:
                dx=game.player.x-self.x; dy=game.player.y+12-(self.y+12); length=max(1,math.hypot(dx,dy))
                level.projectiles.append(Projectile(self.x+12,self.y+10,dx/length*100,dy/length*100)); self.cooldown=2.8
            return
        speed=31 if self.kind=='beetle' else 52
        if self.kind=='ram' and abs(game.player.x-self.x)<145 and abs(game.player.y-self.y)<36:
            speed=94; self.direction=1 if game.player.x>self.x else -1
        if self.kind=='spark' and self.grounded and self.cooldown<=0: self.vy=-230; self.cooldown=1.5; self.grounded=False
        ahead=self.rect.right+3 if self.direction>0 else self.rect.left-3
        if self.grounded and not level.floor_at(ahead,self.rect.bottom): self.direction*=-1
        if self.x>=self.right: self.direction=-1
        if self.x<=self.left: self.direction=1
        self.x+=self.direction*speed*dt
        for s in level.query(self.rect):
            if not s.one_way:
                self.x=s.rect.left-24 if self.direction>0 else s.rect.right; self.direction*=-1
        old_bottom=self.y+22; self.vy=min(420,self.vy+900*dt); self.y+=self.vy*dt; self.grounded=False
        for s in level.query(self.rect):
            if self.vy>=0 and old_bottom<=s.rect.top+3: self.y=s.rect.top-22; self.vy=0; self.grounded=True
        if self.y>440: self.dead=True
    def draw(self,screen,art,camera):
        if self.dead and self.death_time<=0: return
        image=art.image(f'{self.kind}_{int(self.time*7)%4}',self.direction<0)
        if self.dead:
            image=pg.transform.scale(image,(32,max(2,int(32*self.death_time/.4))))
        screen.blit(image,(int(self.x-camera)-4,int(self.y)-7+(32-image.get_height())))
        if self.kind=='sentry' and self.cooldown<.5 and not self.dead: pg.draw.circle(screen,'#ffe9a6',(int(self.x-camera)+12,int(self.y)+10),int(2+math.sin(self.time*25)*1))
