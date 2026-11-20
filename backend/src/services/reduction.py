import time
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.models.reduction import Scenario,Measure,Catalog,Plan
from src.models.run import Run
from src.services.audit import log
from src.services.validation import validate_scenario,validate_measure
from src.services.solver import prepare,initial_state,run_slice,build_result
SLICE_SECONDS=0.8
def catalog(db):
 obj=db.get(Catalog,1)
 if not obj: obj=Catalog(id=1,version=1);db.add(obj);db.flush()
 return obj
def save_scenario(db,user,data,id=None):
 validate_scenario(data);data=dict(data);data['name']=data['name'].strip()
 obj=db.get(Scenario,id) if id else None
 if id and not obj: raise HTTPException(404,'情景不存在')
 clash=db.query(Scenario).filter(Scenario.name==data['name']).first()
 if clash and clash.id!=(id or 0): raise HTTPException(409,'情景名称已存在')
 if obj: obj.name=data['name'];obj.target_kg=data['target_kg'];action='scenario.update'
 else: obj=Scenario(name=data['name'],target_kg=data['target_kg'],created=time.time());db.add(obj);action='scenario.create'
 catalog(db).version+=1;log(db,user.email,action,data['name']);db.commit();return obj
def delete_scenario(db,user,id):
 obj=db.get(Scenario,id)
 if not obj: raise HTTPException(404,'情景不存在')
 db.delete(obj)
 for m in db.query(Measure).all():
  if m.ratios and str(id) in m.ratios:
   r=dict(m.ratios);r.pop(str(id),None);m.ratios=r
 catalog(db).version+=1;log(db,user.email,'scenario.delete',id);db.commit();return {'deleted':id}
def save_measure(db,user,data,id=None):
 measure_ids={m.id for m in db.query(Measure).all()}
 scenario_ids={s.id for s in db.query(Scenario).all()}
 validate_measure(data,measure_ids,scenario_ids,self_id=id)
 data=dict(data);data['name']=data['name'].strip();data['cost']=round(float(data['cost']),2)
 obj=db.get(Measure,id) if id else None
 if id and not obj: raise HTTPException(404,'措施不存在')
 if obj: obj.name=data['name'];obj.cost=data['cost'];obj.prereq=data['prereq'];obj.ratios=data['ratios'];action='measure.update'
 else: obj=Measure(name=data['name'],cost=data['cost'],prereq=data['prereq'],ratios=data['ratios'],created=time.time());db.add(obj);action='measure.create'
 catalog(db).version+=1;log(db,user.email,action,data['name']);db.commit();return obj
def delete_measure(db,user,id):
 obj=db.get(Measure,id)
 if not obj: raise HTTPException(404,'措施不存在')
 db.delete(obj)
 for m in db.query(Measure).all():
  if m.prereq and id in m.prereq: m.prereq=[p for p in m.prereq if p!=id]
 catalog(db).version+=1;log(db,user.email,'measure.delete',id);db.commit();return {'deleted':id}
def submit_plan(db,user,body):
 existing=db.query(Plan).filter_by(request_key=body.request_key).first()
 if existing: return existing
 run=db.get(Run,body.run_id)
 if not run or run.status!='completed' or not run.approved: raise HTTPException(409,'减排预算需以已复核的完成报告为底')
 scenarios=db.query(Scenario).order_by(Scenario.id).all()
 measures=db.query(Measure).order_by(Measure.id).all()
 if not scenarios: raise HTTPException(422,'请先登记减排情景')
 if not measures: raise HTTPException(422,'请先登记减排措施')
 if len(measures)>64: raise HTTPException(422,'措施数量超出求解上限64项')
 baseline={}
 for r in (run.result or {}).get('rows',[]): baseline[r['活动']]=baseline.get(r['活动'],0)+r['排放kgCO2e']
 if not baseline: raise HTTPException(409,'报告结果没有活动排放行')
 frozen={'run_id':run.id,'run_name':run.name,'checksum':run.checksum,'baseline':baseline,'scenarios':[{'id':s.id,'name':s.name,'target_kg':s.target_kg} for s in scenarios],'measures':[{'id':m.id,'name':m.name,'cost':m.cost,'prereq':m.prereq or [],'ratios':m.ratios or {}} for m in measures]}
 obj=Plan(request_key=body.request_key,name=body.name,run_id=run.id,catalog_version=catalog(db).version,budget_seconds=body.budget_seconds,status='queued',outcome=None,input=frozen,progress=None,result=None,effective=False,created=time.time(),published=None)
 db.add(obj)
 try: log(db,user.email,'plan.queue',body.name);db.commit()
 except IntegrityError:
  db.rollback();return db.query(Plan).filter_by(request_key=body.request_key).first()
 return obj
def publish(db,user,id):
 obj=db.get(Plan,id)
 if not obj: raise HTTPException(404,'方案不存在')
 if obj.outcome!='optimal': raise HTTPException(409,'未证实最优的方案不能生效')
 if obj.effective: return obj
 if obj.catalog_version!=catalog(db).version: raise HTTPException(409,'措施或情景已更新，方案已过期，请重新求解')
 for p in db.query(Plan).filter(Plan.effective==True).all(): p.effective=False
 obj.effective=True;obj.published=time.time();log(db,user.email,'plan.publish',id);db.commit();return obj
def work_slice(db,plan):
 model=prepare(plan.input)
 state=plan.progress or initial_state()
 state={**state,'stack':[list(n) for n in state['stack']]}
 if plan.status=='queued': plan.status='running'
 state,done,outcome=run_slice(model,state,SLICE_SECONDS,plan.budget_seconds)
 plan.progress=state
 if done:
  plan.status='completed';plan.outcome=outcome
  if outcome=='optimal': plan.result=build_result(model,state['best_sel'],True)
  elif outcome=='timeout' and state['best_sel'] is not None: plan.result=build_result(model,state['best_sel'],False)
  log(db,'worker','plan.'+outcome,plan.id)
 db.commit()
