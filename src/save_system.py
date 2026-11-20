"""Validated, atomic JSON persistence; never write into an installed package."""
import json, os
from pathlib import Path
from .weapons import VALID_WEAPONS
DEFAULTS = {'unlocked':1,'best_score':0,'total_coins':0,'completed':False,'resume_level':1,'checkpoint':{},'settings':{'music':0.45,'sfx':0.7,'fullscreen':False,'particles':True}}
class SaveStore:
    def __init__(self, path=None):
        self.path=Path(path) if path else Path(os.environ.get('EMBERCAP_SAVE_DIR',Path.home()/'.embercap'))/'save.json'
        self.warning=''; self.data=self.load()
    def load(self):
        d=dict(DEFAULTS); d['settings']=dict(DEFAULTS['settings'])
        try:
            raw=json.loads(self.path.read_text())
            if not isinstance(raw,dict): return d
            for k in ('unlocked','resume_level'): d[k]=max(1,min(15,int(raw.get(k,1))))
            for k in ('best_score','total_coins'): d[k]=max(0,min(10**12,int(raw.get(k,0))))
            d['completed']=raw.get('completed') is True
            s=raw.get('settings',{})
            if isinstance(s,dict):
                for k in ('music','sfx'): d['settings'][k]=max(0,min(1,float(s.get(k,d['settings'][k]))))
                for k in ('fullscreen','particles'): d['settings'][k]=s.get(k,d['settings'][k]) is True
            d['unlocked']=max(1,min(15,d['unlocked']))
            d['resume_level']=min(d['resume_level'],d['unlocked'])
            cp=raw.get('checkpoint',{})
            if isinstance(cp,dict) and 1<=int(cp.get('level',0))<=15:
                weapons=cp.get('inventory',[None,None,None])
                weapons=list(weapons) if isinstance(weapons,(list,tuple)) else []
                taken=cp.get('taken',[])
                taken=taken if isinstance(taken,list) else []
                d['checkpoint']={
                    'level':int(cp['level']),
                    'index':max(-1,int(cp.get('index',-1))),
                    'slot':max(0,min(2,int(cp.get('slot',0)))),
                    'taken':[i for i in taken if type(i)==int and 0<=i<64],
                    'inventory':[(w if isinstance(w,str) and w in VALID_WEAPONS else None) for w in (weapons+[None]*3)[:3]],
                    'max_health':max(3,min(4,int(cp.get('max_health',3)))),
                }
        except (OSError,ValueError,TypeError,OverflowError): pass
        return d
    def flush(self):
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.path.with_suffix('.tmp'); tmp.write_text(json.dumps(self.data,indent=2)); tmp.replace(self.path)
            self.warning=''
        except OSError: self.warning='Could not write save. Progress is kept for this session.'
    def complete(self,level,score):
        self.data['unlocked']=max(self.data['unlocked'],min(15,level+1))
        self.data['resume_level']=min(15,level+1)
        self.data['completed'] |= level==15
        self.data['best_score']=max(self.data['best_score'],score); self.flush()
