"""Headless integration + route tests. Run: python -m unittest discover -s tests -v"""
import os
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'; os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import json, tempfile, unittest
from pathlib import Path
import pygame as pg
from src.game import Game
from src.settings import STEP, ROOT, JUMP_SPEED, GRAVITY, RUN_SPEED
from src.save_system import SaveStore
from src.level import Level, Solid
from src.player import Player
from src.enemy import Enemy

class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(); cls.game=Game(Path(cls.temp.name)/'save.json')
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup(); pg.quit()
    def setUp(self):
        self.g=self.game; self.g.start(1); self.g.transition=0
    def ticks(self,n=60,**controls):
        for _ in range(n): self.g.update(STEP,controls)
    def settle(self): self.ticks(50)
    def test_start_menu_and_navigation(self):
        g=self.g; g.set_state('menu'); g.draw(); self.assertEqual(len(g.buttons),5)
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_DOWN)); self.assertEqual(g.selection,1)
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN)); self.assertEqual(g.state,'levels'); g.draw()
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_RETURN)); self.assertEqual(g.state,'playing')
    def test_mouse_menu(self):
        g=self.g; g.set_state('menu'); g.draw(); size,offset=g.viewport(); r=g.buttons[2]
        pos=(int(r.centerx*size[0]/640+offset[0]),int(r.centery*size[1]/360+offset[1]))
        g.event(pg.event.Event(pg.MOUSEBUTTONDOWN,button=1,pos=pos)); self.assertEqual(g.state,'settings')
    def test_all_fifteen_levels_load_and_render(self):
        for n in range(1,16):
            self.g.start(n); self.ticks(120); self.g.draw()
            self.assertGreater(len(self.g.level.coins),70); self.assertGreaterEqual(len(self.g.level.data['checkpoints']),2)
            self.assertFalse(self.g.player.dead)
    def test_movement_and_floor(self):
        self.settle(); p=self.g.player; self.assertTrue(p.grounded); self.assertEqual(p.rect.bottom,288)
        self.ticks(60,move=1,run=True); self.assertGreater(p.x,110); self.assertLessEqual(p.vx,RUN_SPEED)
        self.ticks(60); self.assertEqual(p.vx,0); self.assertEqual(p.rect.bottom,288)
    def test_jump_height_and_release(self):
        self.settle(); p=self.g.player; start=p.y; p.queue_jump(); highest=p.y
        for _ in range(95): self.g.update(STEP,{'jump':True}); highest=min(highest,p.y)
        full=start-highest; self.assertGreater(full,60); self.assertLess(full,66); self.assertTrue(p.grounded)
        p.queue_jump(); self.ticks(7,jump=True); short_y=p.y
        for _ in range(90): self.g.update(STEP,{'jump':False}); short_y=min(short_y,p.y)
        self.assertLess(start-short_y,full-15)
    def test_jump_buffer(self):
        self.settle(); p=self.g.player; p.y=250; p.vy=130; p.grounded=False; p.support=None; p.coyote=0; p.queue_jump()
        self.ticks(14,jump=True); self.assertLess(p.vy,0)
    def test_coyote(self):
        self.settle(); p=self.g.player; p.grounded=False; p.support=None; p.y-=2; p.coyote=.08; p.queue_jump()
        self.ticks(1,jump=True); self.assertLess(p.vy,-300)
    def test_solid_wall(self):
        self.settle(); wall=Solid({'x':90,'y':200,'w':24,'h':88,'kind':'ground'},0)
        self.g.level.buckets.setdefault(0,[]).append(wall)
        self.ticks(100,move=1,run=True); self.assertLessEqual(self.g.player.rect.right,90)
    def test_collectibles_and_abilities(self):
        g=self.g; c=g.level.coins[0]; g.player.x=c['x']-8; g.player.y=c['y']-8; self.ticks(1)
        self.assertFalse(c['active']); self.assertGreater(g.score,0); self.assertEqual(g.coins,1)
        for kind in ('health','speed','star','wings'):
            g.pickup({'active':True,'kind':kind,'x':g.player.x,'y':g.player.y})
        self.assertEqual(g.player.max_health,4); self.assertTrue(all(v>0 for v in g.player.powers.values()))
        g.player.grounded=False; g.player.support=None; g.player.coyote=0; g.player.y=180; g.player.queue_jump(); self.ticks(1,jump=True)
        self.assertTrue(g.player.air_jump); self.assertLess(g.player.vy,0)
    def test_damage_invulnerability(self):
        p=self.g.player; self.assertTrue(p.damage(self.g)); self.assertEqual(p.health,2)
        self.assertFalse(p.damage(self.g)); self.assertEqual(p.health,2)
    def test_enemy_stomp(self):
        g=self.g; self.settle(); e=Enemy({'kind':'beetle','x':200,'y':266,'left':180,'right':230}); g.level.enemies=[e]
        p=g.player; p.x=200; p.y=239; p.vy=160; p.grounded=False; p.support=None
        self.ticks(3); self.assertTrue(e.dead); self.assertLess(p.vy,0); self.assertEqual(p.health,3)
    def test_enemy_families(self):
        g=self.g; g.player.x=140; g.player.invulnerable=100
        for kind in ('beetle','ram','wing','sentry','spark'):
            e=Enemy({'kind':kind,'x':200,'y':266 if kind!='wing' else 180,'left':180,'right':260}); old=(e.x,e.y)
            for _ in range(400): e.update(STEP,g.level,g)
            if kind=='sentry': self.assertGreater(len(g.level.projectiles),0)
            else: self.assertNotEqual((e.x,e.y),old)
    def test_blocks(self):
        g=self.g; s=next(s for s in g.level.solids if s.kind=='block'); n=len(g.level.powerups); g.hit_block(s)
        self.assertTrue(s.used); self.assertEqual(len(g.level.powerups),n+1); g.hit_block(s); self.assertEqual(len(g.level.powerups),n+1)
        s=next(s for s in g.level.solids if s.kind=='break'); g.hit_block(s); self.assertFalse(s.active)
    def test_checkpoint_and_death_respawn(self):
        g=self.g; x,y=g.level.data['checkpoints'][0]; g.player.x=x; g.player.y=y-26; self.ticks(2)
        self.assertEqual(g.level.checkpoint_index,0); g.player.kill(g); self.ticks(165)
        self.assertEqual(g.lives,4); self.assertAlmostEqual(g.player.x,x,delta=2); self.assertFalse(g.player.dead)
    def test_platforms(self):
        moving=Solid({'x':100,'y':200,'w':48,'h':16,'kind':'moving','axis':'x','distance':24,'period':3},0)
        moving.update(.75,STEP); self.assertEqual(moving.rect.x,124)
        collapsing=Solid({'x':100,'y':200,'w':48,'h':16,'kind':'collapse'},0); collapsing.timer=0
        for i in range(100): collapsing.update(i*STEP,STEP)
        self.assertFalse(collapsing.active)
        for i in range(450): collapsing.update(i*STEP,STEP)
        self.assertTrue(collapsing.active)
    def test_progression_pause_restart_and_return(self):
        g=self.g; g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE)); self.assertEqual(g.state,'paused')
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE)); self.assertEqual(g.state,'playing')
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_r)); self.assertEqual(g.state,'confirm'); g.options()[0][1](); self.assertEqual(g.state,'playing')
        g.level.boss.dead=True; g.level.boss.death_time=3
        g.player.x=g.level.data['exit']; g.player.y=262; self.ticks(1); self.assertEqual(g.state,'clear'); self.assertGreaterEqual(g.save.data['unlocked'],2)
        g.options()[0][1](); self.assertEqual(g.level.number,2); g.return_menu(); self.assertEqual(g.state,'menu')
    def test_weapons_and_resume(self):
        g=self.g
        for item in g.level.weapon_pickups:
            g.player.x=item['x']; g.player.y=item['y']; self.ticks(1,pickup=True)
            if g.state=='replace': g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_2))
            self.assertFalse(item['active']); g.player.attack_timer=0; g.attack()
            self.assertTrue(g.player.swing if item['weapon']=='sword' else g.shots)
        inv=list(g.player.inventory); x,y=g.level.data['checkpoints'][-1]; g.player.x=x; g.player.y=y-26; self.ticks(1)
        g.respawn(); self.assertEqual(g.player.inventory,inv)
        g.save=SaveStore(g.save.path); g.start(1,resume=True); self.assertEqual(g.player.inventory,inv); self.assertEqual(g.player.x,x); self.assertFalse(any(w['active'] for w in g.level.weapon_pickups))
    def test_weapon_slot_selection_and_explicit_replacement(self):
        g=self.g; p=g.player
        p.inventory=['sword','pistol','machinegun']; p.weapon_slot=0
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_2)); self.assertEqual(p.weapon_slot,1)
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_3)); self.assertEqual(p.weapon_slot,2)
        p.inventory=['sword',None,'machinegun']; p.weapon_slot=0
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_2)); self.assertEqual(p.weapon_slot,0)
        item={'x':p.rect.centerx,'y':p.rect.centery,'weapon':'shotgun','active':True}
        g.level.weapon_pickups=[item]
        self.ticks(1,pickup=True)
        self.assertEqual(g.state,'playing'); self.assertEqual(p.inventory,['sword','shotgun','machinegun'])
        self.assertEqual(p.weapon_slot,1); self.assertFalse(item['active'])

    def test_full_weapon_slots_require_explicit_choice(self):
        g=self.g; p=g.player
        p.inventory=['sword','pistol','machinegun']; p.weapon_slot=0
        item={'x':p.rect.centerx,'y':p.rect.centery,'weapon':'shotgun','active':True}
        g.level.weapon_pickups=[item]
        self.ticks(1,pickup=True)
        self.assertEqual(g.state,'replace'); self.assertTrue(item['active'])
        self.assertEqual(p.inventory,['sword','pistol','machinegun'])
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_2))
        self.assertEqual(g.state,'playing'); self.assertEqual(p.inventory,['sword','shotgun','machinegun'])
        self.assertEqual(p.weapon_slot,1); self.assertFalse(item['active'])

    def test_weapon_pickup_is_edge_triggered(self):
        g=self.g; p=g.player
        first={'x':p.rect.centerx,'y':p.rect.centery,'weapon':'sword','active':True}
        second={'x':p.rect.centerx,'y':p.rect.centery,'weapon':'pistol','active':True}
        g.level.weapon_pickups=[first,second]
        g.event(pg.event.Event(pg.KEYDOWN,key=pg.K_e))
        g.update(STEP,{})
        self.assertFalse(first['active']); self.assertTrue(second['active'])

    def test_checkpoint_respawn_resets_boss_and_keeps_loadout_capacity(self):
        g=self.g; p=g.player
        x,y=g.level.data['checkpoints'][-1]
        p.x=x; p.y=y-26; p.inventory=['sword','shotgun','machinegun']; p.weapon_slot=1; p.max_health=4; p.health=2
        g.level.checkpoint_index=len(g.level.data['checkpoints'])-1; g.level.checkpoint=(x,y)
        g.snapshot(); g.save.flush()
        boss=g.level.boss; boss.hp=1; boss.state='weak'
        g.player.kill(g); self.ticks(165)
        self.assertEqual(g.player.inventory,['sword','shotgun','machinegun'])
        self.assertEqual(g.player.weapon_slot,1); self.assertEqual(g.player.max_health,4); self.assertEqual(g.player.health,4)
        self.assertEqual(g.level.boss.hp,g.level.boss.max_hp); self.assertEqual(g.level.boss.state,'sleep')

    def test_gameover_retry(self):
        g=self.g; g.lives=1; g.player.kill(g); self.ticks(170); self.assertEqual(g.state,'gameover'); g.draw()
        g.options()[0][1](); self.assertEqual(g.state,'playing'); self.assertEqual(g.lives,5)
    def test_boss_actual_stomp_collisions_and_phases(self):
        g=self.g; g.start(15); b=g.level.boss; p=g.player; phases=set(); p.invulnerable=999
        p.x=b.arena[0]+20; p.y=262
        # Advance real attack/weak state machine; place descending player over crown
        # only during openings. Hits still go through the game's collision code.
        for _ in range(18000):
            phases.add(b.phase)
            if b.vulnerable:
                p.x=b.x-8; p.y=b.rect.top-p.h-1; p.vy=180; p.grounded=False; p.support=None
            elif not b.dead:
                p.x=b.arena[0]+30; p.y=262; p.vy=0
            g.update(STEP,{})
            if b.dead and b.death_time>2.2: break
        self.assertTrue(b.dead); self.assertEqual(b.hp,0); self.assertEqual(phases,{1,2,3})
        p.x=g.level.data['exit']; p.y=262; self.ticks(1); self.assertEqual(g.state,'victory'); g.draw()
    def test_all_required_routes_with_physics(self):
        # Geometry-only traversal: disable combat/hazards, retain real terrain,
        # moving platforms, collapsing platforms, acceleration and collision.
        for number in range(1,16):
            g=self.g; g.start(number)
            self.assertIsNotNone(g.level.boss, f'Level {number} is missing its boss')
            self.assertEqual(len(g.level.weapon_pickups),4, f'Level {number} weapon placements changed')
            self.assertGreater(g.level.boss.max_hp,0)
            g.level.enemies=[]; g.level.hazards=[]; g.level.boss=None
            g.level.powerups=[]; g.level.coins=[]; p=g.player
            for tick in range(15000):
                if p.grounded:
                    look_x=p.rect.right+26
                    support=g.level.query(pg.Rect(int(look_x),p.rect.bottom-3,3,14))
                    if not support: p.queue_jump()
                g.update(STEP,{'move':1,'run':True,'jump':True})
                self.assertFalse(p.dead,f'Level {number}, x={p.x:.0f}: route fall')
                if g.state in ('clear','victory'): break
            self.assertIn(g.state,('clear','victory'),f'Level {number} route stuck at {p.x:.0f}')

class SaveTests(unittest.TestCase):
    def test_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'save.json'; s=SaveStore(path); self.assertEqual(s.data['unlocked'],1)
            s.data['total_coins']=37; s.data['settings']['music']=.2; s.complete(3,5700)
            loaded=SaveStore(path); self.assertEqual(loaded.data['unlocked'],4); self.assertEqual(loaded.data['best_score'],5700); self.assertEqual(loaded.data['total_coins'],37)
            self.assertEqual(loaded.data['settings']['music'],.2)
            path.write_text('{invalid'); self.assertEqual(SaveStore(path).data['unlocked'],1)
            path.write_text(json.dumps({'unlocked':999,'settings':{'music':5}})); loaded=SaveStore(path); self.assertEqual(loaded.data['unlocked'],15); self.assertEqual(loaded.data['settings']['music'],1)
    def test_layout_contract(self):
        files=list((ROOT/'levels').glob('level_*.json')); self.assertEqual(len(files),15)
        for path in files:
            d=json.loads(path.read_text()); self.assertGreater(d['width'],8000); self.assertLess(d['exit'],d['width'])
            self.assertGreaterEqual(len(d['checkpoints']),2)
        self.assertGreater(RUN_SPEED*2*JUMP_SPEED/GRAVITY,130)

if __name__=='__main__': unittest.main()
