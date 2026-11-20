import math, random
import pygame as pg
from .settings import ROOT, WIDTH, HEIGHT, PALETTES
class Art:
    def __init__(self):
        self.images={p.stem:pg.image.load(str(p)).convert_alpha() for p in (ROOT/'assets'/'sprites').glob('*.png')}
        self.flipped={k:pg.transform.flip(v,True,False) for k,v in self.images.items()}
        self.fonts={}; self.backgrounds={}
    def image(self,key,flip=False): return (self.flipped if flip else self.images)[key]
    def font(self,size,bold=False):
        key=(size,bold)
        if key not in self.fonts: self.fonts[key]=pg.font.Font(str(ROOT/'assets'/'fonts'/('Title.ttf' if bold else 'UI.ttf')),size)
        return self.fonts[key]
    def text(self,screen,text,pos,size=12,color='#f6e7cf',bold=False,center=False,shadow=False):
        font=self.font(size,bold); im=font.render(str(text),False,color); r=im.get_rect()
        if center: r.center=pos
        else: r.topleft=pos
        if shadow: screen.blit(font.render(str(text),False,'#27283c'),r.move(1,2))
        screen.blit(im,r); return r
    def background(self,index):
        if index in self.backgrounds: return self.backgrounds[index]
        p=PALETTES[index]; rng=random.Random(index+55); layers=[]
        base=pg.Surface((WIDTH,HEIGHT)); a=pg.Color(p['sky']); b=pg.Color(p['far'])
        for y in range(HEIGHT):
            c=a.lerp(b,(y/HEIGHT)*.4); pg.draw.line(base,c,(0,y),(WIDTH,y))
        for layer in range(2):
            s=pg.Surface((WIDTH,HEIGHT),pg.SRCALPHA); color=p['far'] if layer==0 else p['near']
            if index in (0,2):
                for _ in range(9):
                    x,y=rng.randrange(WIDTH),rng.randrange(25,160)
                    for off in (0,15,30): pg.draw.ellipse(s,'#e0eee1' if index==0 else '#e8dff1',(x+off,y+rng.randrange(-5,5),40,12))
                if index==0:
                    for x in range(-80,WIDTH+100,120): pg.draw.ellipse(s,color,(x,175+layer*35,210,210))
                    for x in range(0,WIDTH,90):
                        pg.draw.rect(s,color,(x+10,200,5,120)); pg.draw.polygon(s,color,[(x-20,240),(x+12,160),(x+44,240)])
                else:
                    for x in range(0,WIDTH,145):
                        y=190+rng.randrange(40); pg.draw.polygon(s,color,[(x,y),(x+100,y),(x+60,y+42),(x+20,y+25)])
                        for xx in (x+20,x+55): pg.draw.rect(s,color,(xx,y-55,10,56)); pg.draw.rect(s,color,(xx-4,y-58,18,5))
            elif index==1:
                for x in range(-20,WIDTH,45):
                    h=rng.randrange(30,130); pg.draw.polygon(s,color,[(x,0),(x+48,0),(x+28,h)])
                    h=rng.randrange(70,160); pg.draw.polygon(s,color,[(x,360),(x+60,360),(x+23,360-h)])
                for _ in range(30):
                    x,y=rng.randrange(WIDTH),rng.randrange(HEIGHT); pg.draw.line(s,'#557991',(x,y),(x+3,y-9),2)
            else:
                for x in range(0,WIDTH,85):
                    h=rng.randrange(110,240); pg.draw.rect(s,color,(x,360-h,55,h))
                    if index==4:
                        pg.draw.polygon(s,color,[(x-5,360-h),(x+27,320-h),(x+60,360-h)])
                        for y in range(380-h,330,35): pg.draw.rect(s,'#776180',(x+20,y,9,17),border_radius=4)
                    else:
                        pg.draw.rect(s,'#a75b4b',(x+18,360-h+10,10,h-30)); pg.draw.rect(s,color,(x-5,350-h,65,10))
                if index==4 and layer==0:
                    pg.draw.circle(s,'#b4aac8',(490,65),32); pg.draw.circle(s,p['sky'],(503,58),29)
            layers.append(s)
        self.backgrounds[index]=(base,layers); return base,layers
    def draw_background(self,screen,index,camera,t):
        base,layers=self.background(index); screen.blit(base,(0,0))
        for i,s in enumerate(layers):
            off=int(camera*(.12+i*.16))%WIDTH
            screen.blit(s,(-off,0)); screen.blit(s,(WIDTH-off,0))
        # Slow, environment-specific motes, deterministic and allocation-free.
        for k in range(25):
            x=int((k*137-camera*.45+t*(8 if index!=2 else 19))%(WIDTH+10))-5
            y=int((k*71-t*(9 if index==3 else 3))%HEIGHT)
            col=PALETTES[index]['accent']
            if index==2: pg.draw.line(screen,col,(x,y),(x+9,y))
            else: pg.draw.rect(screen,col,(x,y,2,1 if index==0 else 2))
