"""Optional audio. A missing device is not a fatal error."""
import pygame as pg
from .settings import ROOT
class Audio:
    def __init__(self,settings):
        self.settings=settings; self.sounds={}; self.theme=None; self.available=False
        try:
            if not pg.mixer.get_init(): pg.mixer.init(22050,-16,1,512)
            for path in (ROOT/'assets'/'audio').glob('*.wav'):
                if not path.stem.startswith('theme'): self.sounds[path.stem]=pg.mixer.Sound(str(path))
            self.available=True; self.apply()
        except (pg.error,OSError): pass
    def apply(self):
        if self.available:
            pg.mixer.music.set_volume(self.settings['music'])
            for s in self.sounds.values(): s.set_volume(self.settings['sfx'])
    def play(self,name):
        if self.available and name in self.sounds: self.sounds[name].play()
    def music(self,index):
        if not self.available or self.theme==index: return
        try:
            pg.mixer.music.load(str(ROOT/'assets'/'audio'/f'theme_{index}.wav')); pg.mixer.music.play(-1,fade_ms=650); self.theme=index
        except (pg.error,OSError): pass
