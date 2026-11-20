import time,json,traceback
from pathlib import Path
import redis
from src.config.database import Base,engine,Session
from src.config.settings import REDIS_URL
from src.models import identity,source,run,reduction
from src.models.run import Run
from src.models.reduction import Plan
from src.services.calculation import calculate
from src.services.delivery import tick
from src.services.reduction import work_slice
Base.metadata.create_all(engine)
r=redis.Redis.from_url(REDIS_URL)
while True:
 Path('/tmp/worker-heartbeat').write_text(str(time.time()))
 try:
  item=r.lpop('report-jobs')
  if item:
   with Session() as db:
    job=db.get(Run,int(item))
    if job and job.status=='queued':
     job.status='running';db.commit()
     try: job.result=calculate(job.snapshot['sources'],job.snapshot['policy']);job.status='completed'
     except Exception as exc: job.status='failed';job.error=str(exc);traceback.print_exc()
     db.commit()
  with Session() as db: tick(db)
  with Session() as db:
   plan=db.query(Plan).filter(Plan.status.in_(['queued','running'])).order_by(Plan.id).first()
   if plan:
    try: work_slice(db,plan)
    except Exception as exc:
     db.rollback()
     with Session() as retry:
      stuck=retry.get(Plan,plan.id)
      if stuck: stuck.status='failed';stuck.error=str(exc);retry.commit()
     traceback.print_exc()
 except Exception: traceback.print_exc()
 time.sleep(1)
