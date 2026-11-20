"""Application, menus, progression, and fixed-step orchestration."""
import math, random
import pygame as pg
from .settings import WIDTH, HEIGHT, STEP, FPS, TITLE, EXTRA_LIFE_SCORE, PALETTES
import json
from .settings import ROOT
from .save_system import SaveStore
from .audio import Audio
from .art import Art
from .level import Level
from .player import Player
from .particles import Particles
from .weapons import WEAPON_SPECS

class Game:
    def __init__(self,save_path=None):
        pg.display.init(); pg.font.init()
        self.save=SaveStore(save_path); self.settings=self.save.data['settings']
        self.window=pg.display.set_mode((1280,720),pg.RESIZABLE)
        pg.display.set_caption(TITLE)
        self.canvas=pg.Surface((WIDTH,HEIGHT)); self.art=Art(); pg.display.set_icon(self.art.image('player_idle_0'))
        self.audio=Audio(self.settings); self.audio.music(1); self.particles=Particles()
        self.clock=pg.time.Clock(); self.running=True; self.state='menu'; self.previous_state='menu'; self.selection=0; self.buttons=[]
        self.time=0.; self.accumulator=0.; self.camera=0.; self.shake=0.; self.message=''; self.message_timer=0.; self.transition=0.
        self.level=None; self.player=None; self.score=0; self.coins=0; self.lives=5; self.next_life=EXTRA_LIFE_SCORE
        self.elapsed=0.; self.deaths=0; self.enemies_defeated=0; self.confirm_action=None; self.mouse_pos=(-100,-100); self.mouse_active=False
        self.clear_timer=0.; self.level_start_score=0; self.level_start_coins=0
        self.shots=[]; self.pending_weapon=None; self.pickup_requested=False; self.names=[json.loads((ROOT/'levels'/f'level_{n}.json').read_text())['name'] for n in range(1,16)]
        if self.settings['fullscreen']: self.toggle_fullscreen(initial=True)
    def notify(self,text,duration=2.5): self.message=text; self.message_timer=duration
    def set_state(self,state): self.state=state; self.selection=0; self.mouse_active=False
    def toggle_fullscreen(self,initial=False):
        if not initial: self.settings['fullscreen']=not self.settings['fullscreen']
        try:
            self.window=pg.display.set_mode((0,0),pg.FULLSCREEN) if self.settings['fullscreen'] else pg.display.set_mode((1280,720),pg.RESIZABLE)
        except pg.error:
            self.settings['fullscreen']=False; self.window=pg.display.set_mode((1280,720),pg.RESIZABLE)
        self.save.flush()
    def start(self,number,new=True,resume=False):
        if new:
            self.score=0; self.coins=0; self.lives=5; self.next_life=EXTRA_LIFE_SCORE; self.elapsed=0.; self.deaths=0; self.enemies_defeated=0
        self.level=Level(number,self.art); self.player=Player(*self.level.checkpoint); self.shots=[]; self.pending_weapon=None; self.pickup_requested=False
        cp=self.save.data.get('checkpoint',{})
        if resume and cp.get('level')==number:
            self.level.checkpoint_index=min(cp.get('index',-1),len(self.level.data['checkpoints'])-1); self.level.checkpoint=tuple(self.level.data['checkpoints'][self.level.checkpoint_index]) if self.level.checkpoint_index>=0 else tuple(self.level.data['spawn'])
            self.player.x=self.level.checkpoint[0]; self.player.y=self.level.checkpoint[1]-26
            self.player.inventory=list(cp.get('inventory',[None,None,None])); self.player.weapon_slot=cp.get('slot',0)
            self.player.max_health=max(3,min(4,int(cp.get('max_health',3)))); self.player.health=self.player.max_health
            for i in cp.get('taken',[]):
                if 0<=i<len(self.level.weapon_pickups): self.level.weapon_pickups[i]['active']=False
        self.camera=0.; self.particles.items.clear()
        self.level_start_score=self.score; self.level_start_coins=self.coins
        self.set_state('playing'); self.transition=1.; self.clear_timer=0.; self.audio.music(self.level.index+1); self.snapshot()
        self.save.data['resume_level']=min(number,self.save.data['unlocked']); self.save.flush()
        self.notify(f'{number:02}  /  {self.level.data["name"].upper()}',3.5)
    def snapshot(self):
        self.save.data['checkpoint']=dict(level=self.level.number,index=self.level.checkpoint_index,inventory=list(self.player.inventory),slot=self.player.weapon_slot,max_health=self.player.max_health,taken=[i for i,w in enumerate(self.level.weapon_pickups) if not w['active']])
    def respawn(self):
        old=self.level; number=old.number; checkpoint=old.checkpoint; index=old.checkpoint_index
        collected=[i for i,c in enumerate(old.coins) if not c['active']]
        powers=[i for i,c in enumerate(old.powerups) if not c['active']]
        used=[(i,s.used,s.active) for i,s in enumerate(old.solids) if s.kind in ('block','break')]
        self.level=Level(number,self.art); self.level.checkpoint=checkpoint; self.level.checkpoint_index=index
        for i in collected: self.level.coins[i]['active']=False
        for i in powers:
            if i<len(self.level.powerups): self.level.powerups[i]['active']=False
        for i,use,active in used: self.level.solids[i].used=use; self.level.solids[i].active=active
        inventory=list(self.player.inventory); slot=self.player.weapon_slot; max_health=self.player.max_health
        self.pickup_requested=False; self.pending_weapon=None
        self.player=Player(*checkpoint); self.player.inventory=inventory; self.player.weapon_slot=slot
        self.player.max_health=max(3,min(4,max_health)); self.player.health=self.player.max_health; self.player.invulnerable=2.; self.shots.clear()
        self.level.weapon_pickups=old.weapon_pickups; self.player.y-=26 if index>=0 else 0
        self.snapshot(); self.save.flush(); self.camera=max(0,min(self.level.width-WIDTH,self.player.x-200)); self.transition=.65
        self.notify('Lantern rekindled • checkpoint restored',2.)
    def add_score(self,value):
        self.score+=value
        while self.score>=self.next_life:
            self.next_life+=EXTRA_LIFE_SCORE; self.lives+=1; self.notify('EXTRA LIFE • The lantern burns brighter'); self.audio.play('power')
    def collect_coin(self,c):
        c['active']=False; self.coins+=1; self.save.data['total_coins']+=1; self.add_score(50)
        self.audio.play('coin'); self.particles.burst(c['x'],c['y'],'#ffe59f',6,45)
    def hit_block(self,s):
        if s.kind=='break':
            s.active=False; self.add_score(30); self.audio.play('break'); self.particles.burst(s.rect.centerx,s.rect.centery,'#caa68e',15)
        elif not s.used:
            s.used=True; self.add_score(100); self.audio.play('power')
            self.level.powerups.append({'x':s.rect.centerx,'y':s.rect.top-18,'kind':'health','active':True,'rect':pg.Rect(s.rect.centerx-10,s.rect.top-31,20,26)})
            self.notify('Bloomheart revealed • +1 health',1.5)
    def pickup(self,p):
        p['active']=False; kind=p['kind']; self.add_score(100); self.audio.play('power'); self.player.transform=.6
        if kind=='health':
            self.player.max_health=min(4,self.player.max_health+1); self.player.health=min(self.player.max_health,self.player.health+1)
            text='BLOOMHEART • health restored / capacity increased'
        else:
            self.player.powers[kind]={'speed':18.,'star':12.,'wings':24.}[kind]
            text={'speed':'MINT RUSH • faster feet for 18 seconds','star':'SUNSEED • invincible for 12 seconds','wings':'MOONWINGS • press jump again in midair'}[kind]
        self.notify(text); self.particles.burst(p['x'],p['y'],'#ecceff',20)
    def finish_level(self):
        if self.state!='playing': return
        self.add_score(1000); self.save.complete(self.level.number,self.score); self.audio.play('victory'); self.clear_timer=0.
        self.set_state('victory' if self.level.number==15 else 'clear')
    def return_menu(self):
        self.save.data['best_score']=max(self.save.data['best_score'],self.score); self.save.flush(); self.set_state('menu'); self.audio.music(1)
    def restart(self):
        self.score=self.level_start_score; self.coins=self.level_start_coins
        self.next_life=(self.score//EXTRA_LIFE_SCORE+1)*EXTRA_LIFE_SCORE
        self.start(self.level.number,new=False)
    def update(self,dt,controls):
        self.time+=dt
        if self.player and self.player.attack_timer>0: self.player.attack_timer=max(0,self.player.attack_timer-dt)
        if self.player and self.player.swing>0: self.player.swing=max(0,self.player.swing-dt)
        self.message_timer=max(0,self.message_timer-dt); self.transition=max(0,self.transition-dt); self.shake=max(0,self.shake-dt*18)
        self.particles.enabled=self.settings['particles']; self.particles.update(dt)
        if self.state in ('clear','victory'):
            self.clear_timer+=dt
            if int(self.time*12)!=int((self.time-dt)*12): self.particles.burst(self.camera+random.randrange(40,600),random.randrange(40,180),'#ffe3a2',4,70)
            return
        if self.state!='playing': return
        self.elapsed+=dt; level=self.level; p=self.player
        pickup_pressed=bool(self.pickup_requested or controls.get('pickup'))
        self.pickup_requested=False
        level.update_terrain(dt); p.update(dt,controls,level,self)
        if p.dead:
            if p.death_time>1.3:
                self.lives-=1
                if self.lives<=0:
                    self.set_state('gameover'); self.audio.play('over'); self.save.data['best_score']=max(self.save.data['best_score'],self.score); self.save.flush()
                else: self.respawn()
            return
        for enemy in level.enemies:
            enemy.update(dt,level,self)
            if not enemy.dead and p.rect.colliderect(enemy.rect):
                if p.powers['star']>0: enemy.defeat(self)
                elif p.vy>0 and p.previous_bottom<=enemy.rect.top+9:
                    enemy.defeat(self); p.bounce()
                else: p.damage(self,-1 if p.x<enemy.x else 1)
        if controls.get('attack'): self.attack()
        active_shots=[]
        for shot in self.shots:
            shot['x']+=shot['vx']*dt; shot['y']+=shot['vy']*dt; shot['life']-=dt
            width=10 if shot['weapon']=='machinegun' else 8
            height=4 if shot['weapon']!='shotgun' else 5
            rect=pg.Rect(round(shot['x']),round(shot['y']),width,height)
            if shot['life']<=0 or abs(shot['x']-p.x)>850:
                continue
            # Bullets stop at solid terrain instead of travelling through walls.
            if level.query(rect):
                continue
            hit_target=False
            for enemy in level.enemies:
                if not enemy.dead and rect.colliderect(enemy.rect):
                    enemy.defeat(self,shot['damage']); hit_target=True; break
            if not hit_target and level.boss and not level.boss.dead and rect.colliderect(level.boss.rect):
                level.boss.hit(self); hit_target=True
            if not hit_target:
                active_shots.append(shot)
        self.shots=active_shots
        if p.swing>0:
            reach=34
            hit=pg.Rect(round(p.x+p.w if p.facing>0 else p.x-reach),round(p.y+2),reach,24)
            for enemy in level.enemies:
                if not enemy.dead and enemy not in p.struck and hit.colliderect(enemy.rect):
                    enemy.defeat(self,2); p.struck.add(enemy)
            if level.boss and level.boss.vulnerable and hit.colliderect(level.boss.rect): level.boss.hit(self)
        if pickup_pressed:
            for item in level.weapon_pickups:
                if item['active'] and abs(item['x']-p.rect.centerx)<32 and abs(item['y']-p.rect.centery)<40:
                    weapon=item['weapon']; stored_slot=p.collect_weapon(weapon)
                    if stored_slot is not None:
                        item['active']=False; self.notify(f'{weapon.upper()}  •  SLOT {stored_slot+1}'); self.snapshot(); self.save.flush()
                    else:
                        self.pending_weapon=item; self.set_state('replace')
                    break
        for c in level.coins:
            if c['active'] and p.rect.colliderect(c['rect']): self.collect_coin(c)
        for item in level.powerups:
            if item['active'] and p.rect.colliderect(item['rect']): self.pickup(item)
        for i,(x,y) in enumerate(level.data['checkpoints']):
            if i>level.checkpoint_index and abs(p.x-x)<26 and abs(p.rect.bottom-y)<45:
                level.checkpoint_index=i; level.checkpoint=(x,y); p.health=p.max_health; self.snapshot(); self.add_score(200); self.audio.play('checkpoint'); self.save.flush()
                self.notify('CHECKPOINT • Health restored'); self.particles.burst(x,y-50,'#ffe9ac',24)
        for h in level.hazards:
            if abs(h['x']-p.x)>200: continue
            r,active,_=level.hazard_rect(h)
            if active and p.rect.colliderect(r):
                if h['kind'] in ('water','lava'): p.kill(self)
                else: p.damage(self,-1 if p.rect.centerx<r.centerx else 1)
        boss=level.boss
        if boss:
            boss.update(dt,level,self)
            if boss.state not in ('sleep','dead'):
                p.x=max(boss.arena[0]-8,min(boss.arena[1]-p.w,p.x))
                if p.rect.colliderect(boss.rect):
                    if p.vy>0 and p.previous_bottom<=boss.rect.top+12 and boss.vulnerable:
                        boss.hit(self); p.bounce()
                    elif p.vy>0 and p.previous_bottom<=boss.rect.top+12 and boss.state=='weak': p.bounce()
                    else: p.damage(self,-1 if p.x<boss.x else 1)
        for projectile in level.projectiles:
            projectile.update(dt,level)
            if projectile.life>0 and p.rect.colliderect(projectile.rect):
                p.damage(self,-1 if projectile.x>p.x else 1); projectile.life=0
        level.projectiles[:]=[b for b in level.projectiles if b.life>0 and abs(b.x-p.x)<1000 and b.y<450]
        if not p.dead and abs(p.x-level.data['exit'])<26 and (not boss or boss.dead and boss.death_time>2.1): self.finish_level()
        target=max(0,min(level.width-WIDTH,p.x-WIDTH*.38))
        if boss and boss.state not in ('sleep',): target=min(level.width-WIDTH,boss.arena[0]-40)
        self.camera+=(target-self.camera)*(1-math.exp(-dt*6))
    def settings_menu(self): self.previous_state=self.state; self.set_state('settings')
    def ask_restart(self): self.confirm_action='restart'; self.previous_state=self.state; self.set_state('confirm')
    def options(self):
        if self.state=='menu':
            return [('Continue adventure' if self.save.data['unlocked']>1 else 'Begin adventure',lambda:self.start(self.save.data['resume_level'],resume=True)),('Choose a lantern / level',lambda:self.set_state('levels')),('Settings',self.settings_menu),('How to play',lambda:self.set_state('help')),('Quit',self.quit)]
        if self.state=='levels':
            result=[]
            for n in range(1,16):
                label=f'{n:02}   '+self.names[n-1]
                if n>self.save.data['unlocked']: label+='  [LOCKED]'; action=lambda:self.audio.play('hurt')
                else: action=lambda n=n:self.start(n)
                result.append((label,action))
            return result+[('Back',lambda:self.set_state('menu'))]
        if self.state=='paused': return [('Resume',lambda:self.set_state('playing')),('Restart level',self.ask_restart),('Settings',self.settings_menu),('Return to main menu',self.return_menu)]
        if self.state=='settings':
            return [(f'Music volume   {round(self.settings["music"]*100)}%',lambda:self.volume('music')),(f'Sound effects   {round(self.settings["sfx"]*100)}%',lambda:self.volume('sfx')),(f'Fullscreen   {"ON" if self.settings["fullscreen"] else "OFF"}',self.toggle_fullscreen),(f'Particles   {"ON" if self.settings["particles"] else "OFF"}',self.toggle_particles),('Back',lambda:self.set_state(self.previous_state))]
        if self.state=='help': return [('Ready • back to menu',lambda:self.set_state('menu'))]
        if self.state=='confirm': return [('Yes • restart from the beginning',self.restart),('No • keep my progress',lambda:self.set_state(self.previous_state))]
        if self.state=='gameover': return [('Retry this level',lambda:self.start(self.level.number)),('Return to main menu',self.return_menu)]
        if self.state=='clear': return [('Carry the flame onward',lambda:self.start(self.level.number+1,new=False)),('Return to main menu',self.return_menu)]
        if self.state=='victory': return [('Replay • choose a level',lambda:self.set_state('levels')),('Return to main menu',self.return_menu)]
        return []
    def volume(self,key,direction=1):
        self.settings[key]=round((round(self.settings[key]*10)+direction*2)%12/10,1); self.settings[key]=min(1,self.settings[key]); self.audio.apply(); self.save.flush()
    def toggle_particles(self): self.settings['particles']=not self.settings['particles']; self.save.flush()
    def quit(self): self.save.data['best_score']=max(self.save.data['best_score'],self.score); self.save.flush(); self.running=False
    def viewport(self):
        w,h=self.window.get_size(); scale=min(w/WIDTH,h/HEIGHT)
        if scale>=1: scale=max(1,int(scale))
        size=(max(1,int(WIDTH*scale)),max(1,int(HEIGHT*scale)))
        return size,((w-size[0])//2,(h-size[1])//2)
    def event(self,event):
        if event.type==pg.QUIT: self.quit(); return
        if event.type==pg.WINDOWFOCUSLOST and self.state=='playing': self.set_state('paused')
        if event.type==pg.VIDEORESIZE and not self.settings['fullscreen']:
            self.window=pg.display.set_mode((max(320,event.w),max(180,event.h)),pg.RESIZABLE)
        if event.type==pg.MOUSEMOTION:
            size,offset=self.viewport(); self.mouse_pos=((event.pos[0]-offset[0])*WIDTH/size[0],(event.pos[1]-offset[1])*HEIGHT/size[1]); self.mouse_active=True
        if event.type==pg.MOUSEBUTTONDOWN and event.button==1 and self.state!='playing':
            size,offset=self.viewport(); pos=((event.pos[0]-offset[0])*WIDTH/size[0],(event.pos[1]-offset[1])*HEIGHT/size[1])
            for i,r in enumerate(self.buttons):
                if r.collidepoint(pos):
                    options=self.options()
                    if i<len(options): self.audio.play('click'); options[i][1]()
                    break
        if event.type!=pg.KEYDOWN: return
        key=event.key
        if key==pg.K_F11: self.toggle_fullscreen(); return
        if self.state=='replace':
            if key in (pg.K_1,pg.K_2,pg.K_3) and self.pending_weapon:
                slot=key-pg.K_1
                replaced=self.player.replace_weapon(slot,self.pending_weapon['weapon'])
                self.pending_weapon['active']=False
                self.snapshot(); self.save.flush(); self.pending_weapon=None; self.set_state('playing')
                self.notify(f'{self.player.inventory[slot].upper()} REPLACED {replaced.upper() if replaced else "EMPTY"}')
            elif key==pg.K_ESCAPE:
                self.pending_weapon=None; self.set_state('playing')
            return
        if self.state=='playing':
            if key in (pg.K_1,pg.K_2,pg.K_3):
                slot=key-pg.K_1
                if self.player.select_weapon(slot):
                    self.snapshot(); self.save.flush()
                    self.notify(f'SLOT {slot+1}  •  {self.player.inventory[slot].upper()}',1.0)
                else: self.notify(f'SLOT {slot+1} IS EMPTY',1.0)
            elif key==pg.K_e: self.pickup_requested=True
            elif key==pg.K_j: self.attack()
            elif key in (pg.K_SPACE,pg.K_w,pg.K_UP): self.player.queue_jump()
            elif key==pg.K_ESCAPE: self.set_state('paused')
            elif key==pg.K_r: self.ask_restart()
            return
        if key==pg.K_ESCAPE:
            if self.state=='paused': self.set_state('playing')
            elif self.state in ('settings','confirm'): self.set_state(self.previous_state)
            elif self.state in ('help','levels'): self.set_state('menu')
            return
        options=self.options()
        if not options: return
        if key in (pg.K_UP,pg.K_w): self.selection=(self.selection-1)%len(options); self.mouse_active=False; self.audio.play('click')
        elif key in (pg.K_DOWN,pg.K_s): self.selection=(self.selection+1)%len(options); self.mouse_active=False; self.audio.play('click')
        elif key in (pg.K_RETURN,pg.K_SPACE): options[self.selection%len(options)][1](); self.audio.play('click')
        elif key in (pg.K_LEFT,pg.K_RIGHT) and self.state=='settings' and self.selection<2: self.volume(('music','sfx')[self.selection],1 if key==pg.K_RIGHT else -1)
    def attack(self):
        p=self.player; weapon=p.loadout.current
        if not weapon or p.dead or p.attack_timer>0: return False
        spec=WEAPON_SPECS[weapon]
        p.attack_timer=spec.cooldown
        if weapon=='sword':
            p.swing=.23; p.struck.clear(); self.audio.play('stomp'); return True
        self.audio.play('break' if weapon=='shotgun' else 'click')
        self.particles.burst(p.rect.centerx+p.facing*15,p.rect.centery-2,spec.projectile_color,3,24)
        for spread in spec.pellets:
            self.shots.append(dict(
                x=p.rect.centerx+p.facing*10, y=p.rect.centery-2,
                vx=p.facing*spec.speed, vy=spread, damage=spec.damage,
                life=spec.lifetime, weapon=weapon,
            ))
        return True
    def panel(self,rect,color=(27,30,48,235)):
        surf=pg.Surface((rect[2],rect[3]),pg.SRCALPHA); surf.fill(color); self.canvas.blit(surf,rect[:2]); pg.draw.rect(self.canvas,'#756c87',rect,1,border_radius=5)
    def draw_hud(self):
        a=self.art; s=self.canvas; p=self.player
        self.panel((10,8,620,42),(25,29,43,225))
        a.text(s,f'{self.level.number:02}  {self.level.data["name"]}',(21,14),12,'#ffe5b6',True)
        a.text(s,f'SCORE {self.score:07}    COINS {self.coins:03}    LIVES {self.lives}',(267,15),11)
        for i in range(p.max_health):
            x=23+i*15; col='#f59496' if i<p.health else '#574b66'
            pg.draw.polygon(s,col,[(x,33),(x+3,30),(x+6,33),(x+9,30),(x+12,33),(x+6,41)])
        active='  '.join(f'{k.upper()} {math.ceil(v)}s' for k,v in p.powers.items() if v>0)
        slots='   '.join(f'{">" if i==p.weapon_slot else " "}{i+1}: {(w or "EMPTY").upper()}' for i,w in enumerate(p.inventory))
        ammo='  •  ∞ AMMO' if p.loadout.current in ('pistol','machinegun','shotgun') else ''
        a.text(s,slots+ammo+'   '+active,(102,32),9,'#b7c2cc')
        boss=self.level.boss
        if boss and boss.state not in ('sleep','dead'):
            self.panel((180,55,280,18),(31,29,47,235)); pg.draw.rect(s,'#ad6885',(184,59,int(272*boss.hp/boss.max_hp),10)); a.text(s,f'{boss.name.upper()}  /  PHASE {boss.phase}',(320,64),9,'#fff0d7',True,True)
        # Thin stage-progress indicator below the HUD.
        pg.draw.rect(s,'#5d6175',(15,50,610,2)); pg.draw.rect(s,'#e8bd83',(15,50,max(1,int(610*p.x/self.level.width)),2))
    def draw_world(self):
        s=self.canvas; level=self.level; cam=self.camera
        if self.shake: cam+=math.sin(self.time*91)*self.shake
        self.art.draw_background(s,level.index,cam,self.time)
        level.draw_terrain(s,self.art,cam); level.draw_items(s,self.art,cam)
        for enemy in level.enemies:
            if -40<enemy.x-cam<680: enemy.draw(s,self.art,cam)
        if level.boss: level.boss.draw(s,self.art,cam)
        for projectile in level.projectiles: projectile.draw(s,cam,self.time)
        for shot in self.shots:
            sx=int(shot['x']-cam); sy=int(shot['y']); color=WEAPON_SPECS[shot['weapon']].projectile_color
            if shot['weapon']=='machinegun':
                pg.draw.line(s,color,(sx-5,sy+2),(sx+10,sy+2),3)
            elif shot['weapon']=='shotgun':
                pg.draw.circle(s,color,(sx+3,sy+2),3)
            else:
                pg.draw.ellipse(s,color,(sx,sy,8,4))
        for item in level.weapon_pickups:
            if not item['active'] or not cam-24<item['x']<cam+664: continue
            wx=int(item['x']-cam); wy=int(item['y'])
            color=WEAPON_SPECS[item['weapon']].projectile_color
            pg.draw.ellipse(s,'#252b3b',(wx-12,wy-7,24,14))
            pg.draw.rect(s,color,(wx-8,wy-3,15,5),border_radius=2)
            if item['weapon']=='sword':
                pg.draw.line(s,'#fff0c8',(wx-5,wy+3),(wx+8,wy-7),3)
                pg.draw.line(s,'#b68c5a',(wx-7,wy+5),(wx-3,wy+1),3)
            elif item['weapon']=='pistol':
                pg.draw.rect(s,'#d0d3d8',(wx+1,wy-5,7,3),border_radius=1)
                pg.draw.rect(s,'#8f95a4',(wx-4,wy+1,4,5),border_radius=1)
            elif item['weapon']=='machinegun':
                pg.draw.rect(s,'#c1c5cc',(wx+2,wy-5,12,2),border_radius=1)
                pg.draw.rect(s,'#8f95a4',(wx-7,wy+1,5,5),border_radius=1)
                pg.draw.rect(s,'#6c7588',(wx-2,wy+3,8,3),border_radius=1)
            else:
                pg.draw.rect(s,'#c1c5cc',(wx+1,wy-6,10,2),border_radius=1)
                pg.draw.rect(s,'#c1c5cc',(wx+1,wy-3,10,2),border_radius=1)
                pg.draw.rect(s,'#8f95a4',(wx-6,wy+1,5,5),border_radius=1)
            if abs(item['x']-self.player.rect.centerx)<32 and abs(item['y']-self.player.rect.centery)<40:
                self.art.text(s,'E: PICK UP '+item['weapon'].upper(),(wx,wy-22),9,'#ffe8ac',center=True)
        if self.player.swing>0:
            p=self.player; x=p.rect.centerx-cam; y=p.rect.centery; angle=1.2-p.swing*12
            pg.draw.line(s,'#fff2b0',(x,y),(x+p.facing*33*math.cos(angle),y+27*math.sin(angle)),4)
        self.player.draw(s,self.art,cam); self.particles.draw(s,cam); self.draw_hud()
        if self.state=='playing':
            for sign in level.data['signs']:
                if abs(sign['x']-self.player.x)<70:
                    text=sign['text']; width=min(618,self.art.font(10).size(text)[0]+22)
                    self.panel(((640-width)//2,300,width,24)); self.art.text(s,text,(320,312),10,'#fff0c8',center=True)
                    break
            if self.message_timer>0:
                width=min(620,self.art.font(11).size(self.message)[0]+24)
                self.panel(((640-width)//2,328,width,24)); self.art.text(s,self.message,(320,340),11,'#ffe3a8',center=True)
    def draw_menu(self):
        s=self.canvas; a=self.art
        if self.level and self.state in ('replace','paused','settings','confirm','gameover','clear','victory') and self.previous_state!='menu': self.draw_world()
        elif self.level and self.state in ('replace','paused','confirm','gameover','clear','victory'): self.draw_world()
        else:
            a.draw_background(s,0,self.time*12,self.time)
            for x in range(0,640,24): s.blit(a.image('tile_0_ground'),(x,336))
            for x in (25,550,605): s.blit(a.image('decor_0'),(x,273))
            s.blit(pg.transform.scale(a.image(f'player_idle_{int(self.time*4)%4}'),(64,80)),(62,252))
        overlay=pg.Surface((640,360),pg.SRCALPHA); overlay.fill((17,21,37,150)); s.blit(overlay,(0,0))
        titles={'replace':'REPLACE WITH '+self.pending_weapon['weapon'].upper() if self.pending_weapon else '', 'menu':'EMBERCAP','levels':'CHOOSE YOUR LANTERN','settings':'SETTINGS','paused':'TAKE A BREATH','confirm':'RESTART THIS LEVEL?','help':'A COURIER’S FIELD GUIDE','gameover':'THE FLAME WILL RETURN','clear':'LANTERN RESTORED','victory':'YOU BROUGHT BACK THE DAWN'}
        y=42 if self.state!='help' else 25
        a.text(s,titles.get(self.state,''),(320,y),30 if self.state=='menu' else 21,'#ffe4b2',True,True,True)
        if self.state=='menu':
            a.text(s,'T H E   F I F T E E N   L A N T E R N S',(320,76),12,'#a8d9ce',True,True)
            a.text(s,'An original woodland adventure',(320,99),10,'#d5d0da',center=True)
            a.text(s,f'BEST {self.save.data["best_score"]:07}  •  LIFETIME COINS {self.save.data["total_coins"]}',(320,315),10,'#c9c4d1',center=True)
            if self.save.data['completed']: a.text(s,'DAWNKEEPER • All fifteen lanterns restored',(320,333),10,'#ffe6a4',center=True)
        elif self.state=='replace':
            a.text(s,'   '.join(f'{i+1}: {w.upper()}' for i,w in enumerate(self.player.inventory)),(320,145),12,center=True)
            a.text(s,'Choose 1 / 2 / 3 to replace, or Esc to cancel',(320,184),12,center=True)
        elif self.state=='help':
            lines=[('MOVE','A / D or Left / Right     •     Shift to run'),('JUMP','Space / W / Up  •  Hold for height, tap for a short hop'),('COMBAT','E: pick up. 1/2/3: switch slots. Hold J: attack. Ammo is infinite.'),('EXPLORE','Bump gold blocks, break bricks, follow upper coin trails.'),('BLOOMHEART','Pink bloom: restores health and expands capacity to 4.'),('MINT / SUN','Green: speed boost. Gold: temporary invincibility.'),('MOONWINGS','Purple: press jump again in the air for a double jump.'),('CHECKPOINTS','Lantern flags refill health and save weapons for your next return.'),('DANGER','Pits, water and lava cost a life, even with a Sunseed.'),('BOSSES','Dodge the warning attacks; strike or stomp the exposed weak point.'),('OTHER','Esc: pause   R: confirm restart   F11: fullscreen')]
            self.panel((32,48,576,248))
            for i,(label,text) in enumerate(lines):
                a.text(s,label,(43,58+i*21),9,'#ffdba2',True); a.text(s,text,(143,58+i*21),9,'#e1dce4')
        elif self.state=='settings':
            a.text(s,'Select a setting to change it • volumes wrap from 100% to mute',(320,81),10,'#d9d1e1',center=True)
            a.text(s,'Audio ready' if self.audio.available else 'No audio device • silent mode is active',(320,298),10,'#c5d7d4',center=True)
        elif self.state=='levels': a.text(s,'Restore a lantern to unlock the next road',(320,79),11,'#b8d5cf',center=True)
        elif self.state=='paused': a.text(s,'Your lantern is safe here.',(320,85),12,'#c1d9d4',center=True)
        elif self.state=='confirm':
            a.text(s,'Checkpoint, level score and items will reset. Lives are kept.',(320,95),11,'#ded4df',center=True)
        elif self.state in ('gameover','clear','victory'):
            subtitle={'gameover':'Every journey begins with another spark.','clear':self.level.data['name']+' is bright again.','victory':'Fifteen lights. One brave courier. A world awake.'}[self.state]
            a.text(s,subtitle,(320,81),12,'#bcdad2',center=True)
            self.panel((160,105,320,77))
            a.text(s,f'SCORE  {self.score:07}     COINS  {self.coins}',(320,123),13,'#ffe7b8',True,True)
            a.text(s,f'Time {int(self.elapsed)//60}:{int(self.elapsed)%60:02}   •   Foes {self.enemies_defeated}   •   Falls {self.deaths}',(320,149),11,'#d5cfdf',center=True)
            if self.state=='victory':
                for k in range(5):
                    x=235+k*42; pg.draw.circle(s,'#e8b775',(x,205),10); pg.draw.circle(s,'#fff0b7',(x,205),5)
            self.particles.draw(s,self.camera)
        options=self.options(); self.buttons=[]
        start=122 if self.state=='menu' else 104 if self.state=='levels' else 113 if self.state in ('settings','paused') else 310 if self.state=='help' else 244 if self.state=='victory' else 207 if self.state in ('gameover','clear') else 147
        step=31 if self.state!='levels' else 32
        for i,(label,_) in enumerate(options):
            r=pg.Rect(12+(i//8)*310,93+(i%8)*30,305,26) if self.state=='levels' else pg.Rect(165,start+i*step,310,26); self.buttons.append(r)
            if self.mouse_active and r.collidepoint(self.mouse_pos): self.selection=i
            selected=self.selection==i
            pg.draw.rect(s,'#526d70' if selected else '#2c3049',r,border_radius=4); pg.draw.rect(s,'#f4d4a0' if selected else '#5a566e',r,1,border_radius=4)
            if selected: a.text(s,'›',(r.x+10,r.y+2),15,'#ffdf96',True)
            a.text(s,label,r.center,11,'#fff0cd' if selected else '#d2cbd9',True,True)
        if self.state!='help': a.text(s,'↑ ↓  select     ENTER  confirm     Mouse supported',(320,350),9,'#b5adbf',center=True)
        if self.save.warning: a.text(s,self.save.warning,(320,335),9,'#ffb695',center=True)
    def draw(self):
        if self.state=='playing': self.draw_world()
        else: self.draw_menu()
        if self.transition>0 and self.state=='playing':
            shade=pg.Surface((WIDTH,HEIGHT)); shade.fill('#1b2032'); shade.set_alpha(int(255*min(1,self.transition))); self.canvas.blit(shade,(0,0))
        size,offset=self.viewport(); self.window.fill('#10131d'); self.window.blit(pg.transform.scale(self.canvas,size),offset); pg.display.flip()
    def run(self,max_frames=None):
        count=0
        while self.running:
            dt=min(.1,self.clock.tick(FPS)/1000)
            for event in pg.event.get(): self.event(event)
            keys=pg.key.get_pressed(); controls={'attack':bool(keys[pg.K_j]),'pickup':False,'move':int(keys[pg.K_d] or keys[pg.K_RIGHT])-int(keys[pg.K_a] or keys[pg.K_LEFT]),'jump':bool(keys[pg.K_SPACE] or keys[pg.K_w] or keys[pg.K_UP]),'run':bool(keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT])}
            self.accumulator+=dt
            while self.accumulator>=STEP: self.update(STEP,controls); self.accumulator-=STEP
            self.draw(); count+=1
            if max_frames and count>=max_frames: break
        pg.quit()
