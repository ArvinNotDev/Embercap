import random, math
import pygame as pg
class Particles:
    def __init__(self): self.items=[]; self.enabled=True; self.rng=random.Random(17)
    def burst(self,x,y,color,n=12,force=65):
        if not self.enabled: return
        for _ in range(min(n,400-len(self.items))):
            a=self.rng.random()*math.tau; speed=self.rng.uniform(force*.3,force)
            self.items.append([x,y,math.cos(a)*speed,math.sin(a)*speed-20,self.rng.uniform(.25,.65),color,self.rng.choice([1,2,3])])
    def update(self,dt):
        for p in self.items: p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[3]+=180*dt; p[4]-=dt
        self.items[:]=[p for p in self.items if p[4]>0]
    def draw(self,s,camera):
        for x,y,_,__,life,color,size in self.items: pg.draw.rect(s,color,(int(x-camera),int(y),size,size))
