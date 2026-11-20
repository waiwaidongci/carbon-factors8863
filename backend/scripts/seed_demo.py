import json,random,time
from src.config.database import Base,engine,Session
from src.config.settings import CONFIG
from src.models.identity import User
from src.models.source import Source,Policy,Period
from src.models import run
from src.models.reduction import Scenario,Measure,Catalog
from src.utils.security import password_hash
from src.services.validation import validate_source

def demo_rows():
 rng=random.Random(42);rows=[]
 for i in range(240):
  activity=['电力','柴油','通勤'][i%3];unit={'电力':'kWh','柴油':'L','通勤':'km'}[activity];rows.append({'period':'2026-'+('10' if i<120 else '11'),'department':['材料试验室','工艺试验室','光学试验室'][i%3],'activity':activity,'quantity':round(rng.uniform(2,300),3),'unit':unit})
 return rows

def demo_reduction():
 return [('基准情景',10000.0),('严峻情景',14000.0)],[('照明LED改造',8000.0,[],{'电力':(0.2,0.15)}),('光伏自发自用',30000.0,[],{'电力':(0.4,0.35)}),('充电桩建设',5000.0,[],{'通勤':(0.05,0.05)}),('班车电动化',12000.0,['充电桩建设'],{'通勤':(0.6,0.5)}),('柴油设备电替代',18000.0,[],{'柴油':(0.5,0.45)})]

def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ('admin','analyst','viewer'):
   if not db.query(User).filter_by(email=role+'@demo.local').first():db.add(User(email=role+'@demo.local',role=role,password=password_hash('Demo2026!')))
  rows=demo_rows()
  for name in sorted(set(r['period'] for r in rows)):
   if not db.query(Period).filter_by(name=name).first():db.add(Period(name=name,description='合成演示业务期间，seed=42'))
  for i,data in enumerate(rows):
   validate_source(data);key='demo-'+str(i+1)
   if not db.query(Source).filter_by(natural_key=key).first():db.add(Source(natural_key=key,data=data))
  if not db.query(Policy).filter_by(version=CONFIG['policy']['version']).first():db.add(Policy(version=CONFIG['policy']['version'],data=CONFIG['policy']))
  db.flush()
  scenarios,measures=demo_reduction();changed=False
  sid={}
  for name,target in scenarios:
   obj=db.query(Scenario).filter_by(name=name).first()
   if not obj: obj=Scenario(name=name,target_kg=target,created=time.time());db.add(obj);db.flush();changed=True
   sid[name]=obj.id
  by_name={m.name:m for m in db.query(Measure).all()}
  for name,cost,prereq,effect in measures:
   if name in by_name: continue
   ratios={}
   for act,(base,severe) in effect.items():
    ratios[str(sid['基准情景'])]={**ratios.get(str(sid['基准情景']),{}),act:base}
    ratios[str(sid['严峻情景'])]={**ratios.get(str(sid['严峻情景']),{}),act:severe}
   obj=Measure(name=name,cost=cost,prereq=[by_name[p].id for p in prereq],ratios=ratios,created=time.time());db.add(obj);db.flush();by_name[name]=obj;changed=True
  if changed:
   cat=db.get(Catalog,1)
   if not cat: cat=Catalog(id=1,version=1);db.add(cat);db.flush()
   cat.version+=1
  db.commit();print(json.dumps({'users':db.query(User).count(),'sources':db.query(Source).count(),'policies':db.query(Policy).count(),'periods':db.query(Period).count(),'scenarios':db.query(Scenario).count(),'measures':db.query(Measure).count()},ensure_ascii=False))
if __name__=='__main__':seed()
