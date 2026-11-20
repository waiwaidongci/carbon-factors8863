import math
from src.config.settings import CONFIG
def number(value,name,minimum=0,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<minimum or (integer and int(value)!=value): raise ValueError(name+'数值不合法')
 return value
def validate_source(d):
 if not isinstance(d,dict) or set(d)!=set(CONFIG['fields']): raise ValueError('底稿字段必须与业务字段一致')
 for key in ('period','department'):
  if not isinstance(d[key],str) or not 1<=len(d[key])<=100: raise ValueError(key+'不能为空或过长')
 number(d['quantity'],'活动量')
 if not isinstance(d['activity'],str) or not isinstance(d['unit'],str):raise ValueError('活动类型与单位需为文本')
def validate_policy(d):
 if not isinstance(d,dict) or not isinstance(d.get('version'),str) or not 2<=len(d['version'])<=120: raise ValueError('口径版本名不合法')
 if not isinstance(d.get('scope'),str) or len(d['scope'])<5:raise ValueError('必须填写核算范围说明')
 if not isinstance(d.get('factors'),dict) or not d['factors'] or len(d['factors'])>100:raise ValueError('因子不能为空')
 for key,f in d['factors'].items():
  if not isinstance(f,dict) or f.get('unit') not in ('kWh','L','km'):raise ValueError('因子单位只接受kWh/L/km')
  number(f.get('kg_per_unit'),'排放因子')
def validate_scenario(d):
 if not isinstance(d,dict) or set(d)!={'name','target_kg'}: raise ValueError('情景字段必须为名称与减排目标')
 if not isinstance(d['name'],str) or not 1<=len(d['name'].strip())<=120: raise ValueError('情景名称需为1-120字文本')
 number(d['target_kg'],'减排目标')
def validate_measure(d,measure_ids,scenario_ids,self_id=None):
 if not isinstance(d,dict) or set(d)!={'name','cost','prereq','ratios'}: raise ValueError('措施字段必须为名称、费用、前置措施与分情景减排比例')
 if not isinstance(d['name'],str) or not 1<=len(d['name'].strip())<=120: raise ValueError('措施名称需为1-120字文本')
 number(d['cost'],'措施费用')
 if d['cost']<=0: raise ValueError('措施费用必须大于0')
 if not isinstance(d['prereq'],list) or len(d['prereq'])>50: raise ValueError('前置措施需为编号列表')
 seen=set()
 for p in d['prereq']:
  if isinstance(p,bool) or not isinstance(p,int): raise ValueError('前置措施编号需为整数')
  if p==self_id: raise ValueError('措施不能以自身为前置')
  if p in seen: raise ValueError('前置措施不可重复')
  if p not in measure_ids: raise ValueError('前置措施不存在：'+str(p))
  seen.add(p)
 if not isinstance(d['ratios'],dict) or len(d['ratios'])>50: raise ValueError('分情景减排比例需为情景编号对象')
 for sid,per in d['ratios'].items():
  try: key=int(sid)
  except (TypeError,ValueError): raise ValueError('情景编号不合法：'+str(sid))
  if key not in scenario_ids: raise ValueError('情景不存在：'+str(sid))
  if not isinstance(per,dict) or len(per)>100: raise ValueError('情景'+str(sid)+'的比例需为活动对象')
  for act,r in per.items():
   if not isinstance(act,str) or not 1<=len(act)<=100: raise ValueError('活动名称不合法')
   number(r,'减排比例')
   if r>1: raise ValueError('减排比例需在0到1之间')
