from fastapi import APIRouter,Depends,HTTPException
from src.config.database import database
from src.controllers.auth import current,editor,admin
from src.models.reduction import Scenario,Measure,Plan
from src.schemas.requests import DataInput,PlanInput
from src.services import reduction as svc
from src.utils.serialize import row
router=APIRouter()
@router.get('/catalog')
def catalog(db=Depends(database),u=Depends(current)): return {'version':svc.catalog(db).version}
@router.get('/scenarios')
def scenarios(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(Scenario).order_by(Scenario.id).all()]
@router.post('/scenarios')
def scenario_create(b:DataInput,db=Depends(database),u=Depends(editor)): return row(svc.save_scenario(db,u,b.data))
@router.put('/scenarios/{id}')
def scenario_update(id:int,b:DataInput,db=Depends(database),u=Depends(editor)): return row(svc.save_scenario(db,u,b.data,id))
@router.delete('/scenarios/{id}')
def scenario_delete(id:int,db=Depends(database),u=Depends(editor)): return svc.delete_scenario(db,u,id)
@router.get('/measures')
def measures(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(Measure).order_by(Measure.id).all()]
@router.post('/measures')
def measure_create(b:DataInput,db=Depends(database),u=Depends(editor)): return row(svc.save_measure(db,u,b.data))
@router.put('/measures/{id}')
def measure_update(id:int,b:DataInput,db=Depends(database),u=Depends(editor)): return row(svc.save_measure(db,u,b.data,id))
@router.delete('/measures/{id}')
def measure_delete(id:int,db=Depends(database),u=Depends(editor)): return svc.delete_measure(db,u,id)
@router.get('/plans')
def plans(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(Plan).order_by(Plan.id.desc()).all()]
@router.get('/plans/{id}')
def plan_detail(id:int,db=Depends(database),u=Depends(current)):
 obj=db.get(Plan,id)
 if not obj: raise HTTPException(404,'方案不存在')
 return row(obj)
@router.post('/plans')
def plan_create(b:PlanInput,db=Depends(database),u=Depends(editor)): return row(svc.submit_plan(db,u,b))
@router.post('/plans/{id}/publish')
def plan_publish(id:int,db=Depends(database),u=Depends(admin)): return row(svc.publish(db,u,id))
