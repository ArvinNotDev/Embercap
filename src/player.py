"""Fixed-step, swept-axis player collision with forgiving jump inputs."""
import math
import pygame as pg
from .settings import GRAVITY, JUMP_SPEED, WALK_SPEED, RUN_SPEED
from .weapons import WeaponInventory
class Player:
    def __init__(self,x,y):
        self.x=float(x); self.y=float(y); self.w=16; self.h=26; self.vx=self.vy=0.; self.facing=1
        self.grounded=False; self.support=None; self.coyote=0.; self.buffer=0.; self.jump_held=False; self.air_jump=False
        self.health=3; self.max_health=3; self.invulnerable=0.; self.hurt=0.; self.land=0.; self.transform=0.; self.dead=False; self.death_time=0.; self.anim=0.
        self.loadout=WeaponInventory(); self.attack_timer=0.; self.swing=0.; self.struck=set()
        self.powers={'speed':0.,'star':0.,'wings':0.}
        self.previous_bottom=y+self.h; self.jumps=0
    @property
    def rect(self): return pg.Rect(round(self.x),round(self.y),self.w,self.h)
    @property
    def inventory(self): return self.loadout.slots
    @inventory.setter
    def inventory(self, value):
        self.loadout=WeaponInventory(value,self.weapon_slot if hasattr(self,'loadout') else 0)
    @property
    def weapon_slot(self): return self.loadout.selected
    @weapon_slot.setter
    def weapon_slot(self, value):
        try: value=int(value)
        except (TypeError,ValueError,OverflowError): return
        if hasattr(self,'loadout') and 0<=value<3:
            if self.loadout.slots[value] is not None or not any(self.loadout.slots): self.loadout.selected=value
    def select_weapon(self, slot): return self.loadout.select(slot)
    def collect_weapon(self, weapon): return self.loadout.collect(weapon)
    def replace_weapon(self, slot, weapon): return self.loadout.replace(slot,weapon)
    def queue_jump(self): self.buffer=.13
    def damage(self,game,direction=1):
        if self.dead or self.invulnerable>0 or self.powers['star']>0: return False
        self.health-=1; self.invulnerable=1.65; self.hurt=.32; self.vx=direction*165; self.vy=-180; self.grounded=False; self.support=None
        game.audio.play('hurt'); game.shake=5; game.particles.burst(self.x+8,self.y+12,'#ffab92',18)
        if self.health<=0: self.kill(game)
        return True
    def kill(self,game):
        if self.dead: return
        self.dead=True; self.vy=-230; self.vx=0.; self.death_time=0.; game.audio.play('hurt'); game.shake=7; game.deaths+=1
    def bounce(self): self.vy=-260; self.grounded=False; self.support=None; self.coyote=0.; self.air_jump=False
    def update(self,dt,controls,level,game):
        self.anim+=dt
        if self.dead:
            self.death_time+=dt; self.vy+=GRAVITY*dt; self.y+=self.vy*dt; return
        self.previous_bottom=self.y+self.h
        for key in self.powers: self.powers[key]=max(0,self.powers[key]-dt)
        for name in ('invulnerable','hurt','land','transform','buffer','coyote'): setattr(self,name,max(0,getattr(self,name)-dt))
        if self.support and self.support.active and self.grounded:
            self.x+=self.support.dx; self.y+=self.support.dy
        elif self.support and not self.support.active: self.grounded=False; self.support=None
        self.grounded=bool(self.grounded and self.support and self.support.active and self.rect.bottom==self.support.rect.top and self.rect.right>self.support.rect.left and self.rect.left<self.support.rect.right)
        if self.grounded: self.coyote=.1; self.air_jump=False
        move=controls.get('move',0); held=controls.get('jump',False)
        if move: self.facing=1 if move>0 else -1
        speed=(RUN_SPEED if controls.get('run') else WALK_SPEED)*(1.22 if self.powers['speed'] else 1)
        target=move*speed; accel=1300 if self.grounded else 850
        if self.hurt<=0:
            change=accel*dt if move else (1600 if self.grounded else 500)*dt
            self.vx+=max(-change,min(change,target-self.vx))
        if self.buffer>0 and (self.coyote>0 or (self.powers['wings']>0 and not self.air_jump)):
            double=self.coyote<=0
            self.vy=-JUMP_SPEED; self.buffer=0.; self.coyote=0.; self.grounded=False; self.support=None
            if double: self.air_jump=True
            self.jumps+=1; game.audio.play('jump'); game.particles.burst(self.x+8,self.y+26,'#c9b8ff' if double else '#e8d6ad',8,40)
        if self.jump_held and not held and self.vy<-125: self.vy=-125
        self.jump_held=held
        self.vy=min(500,self.vy+GRAVITY*dt)
        self.x+=self.vx*dt
        for s in level.query(self.rect):
            if s.one_way: continue
            if self.vx>0: self.x=s.rect.left-self.w
            elif self.vx<0: self.x=s.rect.right
            self.vx=0
        self.x=max(0,min(level.width-self.w,self.x))
        old_bottom=self.y+self.h; self.y+=self.vy*dt; self.grounded=False; self.support=None
        candidates=level.query(self.rect)
        # Nearest surface first, important where a broad floor meets a small block.
        candidates.sort(key=lambda s:s.rect.top if self.vy>=0 else -s.rect.bottom)
        for s in candidates:
            if not self.rect.colliderect(s.rect): continue
            if self.vy>=0 and old_bottom<=s.rect.top+max(2,abs(s.dy)):
                if self.vy>150: self.land=.12; game.particles.burst(self.x+8,s.rect.top,'#d8c5aa',6,35)
                self.y=s.rect.top-self.h; self.vy=0.; self.grounded=True; self.support=s; self.air_jump=False
                if s.kind=='collapse' and s.timer<0: s.timer=0.
            elif self.vy<0 and not s.one_way:
                self.y=s.rect.bottom; self.vy=30
                if s.kind in ('break','block'): game.hit_block(s)
        # Integer rectangles can miss a subpixel downward step at rest. Keep
        # contact stable instead of alternating grounded/falling every few ticks.
        if self.vy>=0 and not self.grounded:
            feet=pg.Rect(self.rect.left,self.rect.bottom,self.w,1)
            for s in level.query(feet):
                if old_bottom<=s.rect.top+1 and self.y+self.h>=s.rect.top-.5:
                    self.y=s.rect.top-self.h; self.vy=0.; self.grounded=True; self.support=s; self.air_jump=False
                    if s.kind=='collapse' and s.timer<0: s.timer=0.
                    break
        if self.y>460: self.kill(game)
    def draw(self,screen,art,camera):
        if self.dead: state='death'; frame=min(3,int(self.death_time*7))
        else:
            if self.invulnerable>0 and int(self.anim*20)%2==0 and self.hurt<=0: return
            if self.transform>0: state='transform'
            elif self.hurt>0: state='hurt'
            elif not self.grounded: state='jump' if self.vy<0 else 'fall'
            elif self.land>0: state='land'
            elif abs(self.vx)>140: state='run'
            elif abs(self.vx)>12: state='walk'
            else: state='idle'
            frame=int(self.anim*(15 if state=='run' else 10 if state=='walk' else 5))%4
        x=int(self.x-camera)-8; y=int(self.y)-10
        if self.powers['star']>0:
            for k in range(6):
                a=self.anim*4+k*math.tau/6
                pg.draw.circle(screen,'#fff0b3',(int(x+16+math.cos(a)*20),int(y+20+math.sin(a)*22)),2)
        if self.powers['wings']>0:
            pg.draw.polygon(screen,'#b7ade6',[(x+8,y+21),(x-3,y+11),(x+1,y+26)])
        screen.blit(art.image(f'player_{state}_{frame}',self.facing<0),(x,y))
        # Keep the currently equipped weapon visible without requiring separate
        # character sprite sheets for every weapon/animation combination.
        weapon=self.loadout.current
        if weapon=='sword':
            hand=(x+24,y+22) if self.facing>0 else (x+8,y+22)
            tip=(hand[0]+self.facing*13,hand[1]-13)
            pg.draw.line(screen,'#aebcc9',hand,tip,3)
            pg.draw.line(screen,'#fff0c8',(hand[0]+self.facing*2,hand[1]-2),tip,1)
            pg.draw.line(screen,'#a77f59',(hand[0]-self.facing*3,hand[1]+3),(hand[0]+self.facing*3,hand[1]-3),3)
        elif weapon:
            length={'pistol':10,'machinegun':17,'shotgun':15}[weapon]
            hand_x=x+24 if self.facing>0 else x+8
            body_x=hand_x if self.facing>0 else hand_x-length
            body_y=y+19
            pg.draw.rect(screen,'#596273',(body_x,body_y,length,5),border_radius=1)
            pg.draw.rect(screen,'#c7ccd3',(body_x,body_y,length-2,2),border_radius=1)
            barrel_x=body_x+length if self.facing>0 else body_x-5
            pg.draw.rect(screen,'#aeb7c5',(barrel_x,body_y+1,5,2))
            if weapon=='machinegun':
                grip_x=body_x+4 if self.facing>0 else body_x+length-7
                pg.draw.rect(screen,'#737e91',(grip_x,body_y+4,4,5))
            else:
                grip_x=body_x+2 if self.facing>0 else body_x+length-6
                pg.draw.rect(screen,'#737e91',(grip_x,body_y+4,4,4))
