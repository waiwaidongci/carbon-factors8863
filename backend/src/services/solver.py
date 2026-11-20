import time
EPS=1e-9
def money(v): return round(float(v),6)
def prepare(frozen):
 baseline=frozen['baseline'];activities=sorted(baseline)
 scenarios=[{'id':s['id'],'name':s['name'],'target_kg':float(s['target_kg'])} for s in frozen['scenarios']]
 measures=sorted(frozen['measures'],key=lambda m:m['id'])
 n=len(measures);S=len(scenarios);A=len(activities)
 red=[]
 for m in measures:
  per=[]
  for s in scenarios:
   ratios=(m.get('ratios') or {}).get(str(s['id'])) or {}
   per.append([min(1.0,max(0.0,1.0-float(ratios.get(a) or 0.0))) for a in activities])
  red.append(per)
 suffix=[[[1.0]*A for _ in range(S)] for _ in range(n+1)]
 for i in range(n-1,-1,-1):
  for s in range(S):
   for a in range(A): suffix[i][s][a]=suffix[i+1][s][a]*red[i][s][a]
 idx_of={m['id']:i for i,m in enumerate(measures)}
 prereq=[sorted({idx_of[p] for p in (m.get('prereq') or []) if p in idx_of and p!=m['id']}) for m in measures]
 required_by=[[] for _ in range(n)]
 for i,ps in enumerate(prereq):
  for p in ps: required_by[p].append(i)
 E=[float(baseline[a]) for a in activities]
 return {'activities':activities,'scenarios':scenarios,'measures':measures,'n':n,'S':S,'A':A,'red':red,'suffix':suffix,'prereq':prereq,'required_by':required_by,'E':E,'total':sum(E),'targets':[s['target_kg'] for s in scenarios],'costs':[float(m['cost']) for m in measures],'ones':[[1.0]*A for _ in range(S)]}
def initial_state(): return {'stack':[[0,[],0.0,None]],'best_cost':None,'best_sel':None,'nodes':0,'elapsed':0.0}
def run_slice(model,state,slice_seconds,budget_seconds):
 # 分支定界：按措施编号顺序决策选/不选（栈内sel为下标序列，命中时转编号）；
 # 费用超当前最优即剪枝；剩余措施全选也达不到任一情景目标即剪枝；同价取编号序列最小者。
 n=model['n'];S=model['S'];A=model['A'];E=model['E'];total=model['total']
 suffix=model['suffix'];red=model['red'];targets=model['targets'];costs=model['costs']
 prereq=model['prereq'];required_by=model['required_by'];measures=model['measures']
 stack=state['stack'];best_cost=state['best_cost'];best_sel=state['best_sel']
 best_key=None if best_cost is None else money(best_cost)
 start=time.monotonic();budget_left=max(0.0,budget_seconds-state['elapsed']);deadline=start+slice_seconds
 timed_out=False
 while stack:
  idx,sel,cost,prods=stack.pop()
  if prods is None: prods=model['ones']
  if best_key is not None and money(cost)>best_key: continue
  ok=True
  for s in range(S):
   ps,ss=prods[s],suffix[idx][s];acc=0.0
   for a in range(A): acc+=E[a]*ps[a]*ss[a]
   if total-acc<targets[s]-EPS: ok=False;break
  if not ok: continue
  if idx==n:
   ck=money(cost);ids=tuple(measures[i]['id'] for i in sel)
   if best_key is None or ck<best_key or (ck==best_key and ids<tuple(best_sel)):
    best_key=ck;best_cost=cost;best_sel=list(ids)
   continue
  sset=set(sel)
  if not any(i in sset for i in required_by[idx]): stack.append([idx+1,sel,cost,prods])
  if all((p in sset) or (p>idx) for p in prereq[idx]):
   ri=red[idx]
   stack.append([idx+1,sel+[idx],cost+costs[idx],[[prods[s][a]*ri[s][a] for a in range(A)] for s in range(S)]])
  state['nodes']+=1
  if state['nodes']&1023==0:
   now=time.monotonic()
   if now-start>=budget_left: timed_out=True;break
   if now>=deadline: break
 state['elapsed']+=time.monotonic()-start
 state['best_cost']=best_cost;state['best_sel']=best_sel
 if not stack: return state,True,('optimal' if best_sel is not None else 'infeasible')
 if timed_out: return state,True,'timeout'
 return state,False,None
def build_result(model,sel,proven):
 sel=sel or [];idset=set(sel);S=model['S'];A=model['A'];total=model['total']
 prods=[[1.0]*A for _ in range(S)]
 for i,m in enumerate(model['measures']):
  if m['id'] in idset:
   for s in range(S):
    for a in range(A): prods[s][a]*=model['red'][i][s][a]
 scenarios=[]
 for si,s in enumerate(model['scenarios']):
  acts=[]
  for a,act in enumerate(model['activities']):
   base=model['E'][a];factor=prods[si][a];rem=base*factor
   acts.append({'activity':act,'baseline_kg':base,'remaining_factor':factor,'remaining_kg':rem,'reduction_kg':base-rem})
  reduction=total-sum(x['remaining_kg'] for x in acts)
  scenarios.append({'id':s['id'],'name':s['name'],'target_kg':s['target_kg'],'baseline_kg':total,'reduction_kg':reduction,'remaining_kg':total-reduction,'met':reduction>=s['target_kg']-EPS,'activities':acts})
 chosen=[m for m in model['measures'] if m['id'] in idset]
 return {'selected':[m['id'] for m in chosen],'cost':sum(float(m['cost']) for m in chosen),'proven':proven,'measures':[{'id':m['id'],'name':m['name'],'cost':m['cost'],'prereq':m.get('prereq') or []} for m in chosen],'scenarios':scenarios}
