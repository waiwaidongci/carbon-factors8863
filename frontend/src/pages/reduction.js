import {heading} from '../components/common/header.js';import {table} from '../components/common/table.js';import {status} from '../components/common/status.js';import {esc,fmt} from '../utils/format.js';
const OUTCOME={optimal:'已证实最优',infeasible:'无解',timeout:'超时未证实'};
export const baseActivities=d=>[...new Set(d.sources.map(s=>s.data.activity))].sort();
const outcomeTag=p=>p.outcome?`<span class="status ${p.outcome==='optimal'?'':'failed'}">${OUTCOME[p.outcome]}</span>`:'';
function planDetail(p,d){
 if(!p)return '<p class="empty">暂无求解方案。先登记情景与措施，再以已复核报告为底发起求解。</p>';
 const stale=p.catalog_version!==d.catalog.version;
 let h=`<section class="report"><div class="report-top"><h2>${esc(p.name)}</h2><span>${status(p.status)} ${outcomeTag(p)} ${p.effective?'<span class="status">已生效</span>':''}</span></div><p>基线报告 #${p.run_id} ${esc(p.input.run_name)} · SHA256 ${esc(p.input.checksum).slice(0,16)}… · 目录版本 v${p.catalog_version}${stale?`（当前 v${d.catalog.version}，方案已过期）`:''} · 请求键 ${esc(p.request_key)}</p>`;
 if(p.error)h+=`<p class="error">${esc(p.error)}</p>`;
 if(['queued','running'].includes(p.status)){const pr=p.progress||{nodes:0,elapsed:0};h+=`<p>求解中：已探索 ${fmt(pr.nodes)} 个节点，已用 ${fmt(pr.elapsed)} 秒 / 预算 ${fmt(p.budget_seconds)} 秒${pr.best_cost!=null?`，当前最优费用 ${fmt(pr.best_cost)} 元`:''}。求解中断可从进度恢复。</p>`}
 if(p.outcome==='infeasible')h+='<p class="error">无解：现有措施的任何组合都无法使全部情景达标，请调整目标或补充措施。</p>';
 if(p.outcome==='timeout')h+='<p class="warning">超时：时限内未证实最优，方案不生效。可加大时限重新求解；已保存的断点进度不会丢失。</p>';
 if(p.result){
  const r=p.result;
  h+=`<div class="metrics"><div><small>总费用（元）</small><strong>${fmt(r.cost)}</strong></div><div><small>入选措施</small><strong>${r.selected.length}</strong></div><div><small>最优性</small><strong>${r.proven?'已证实':'未证实'}</strong></div></div><h3>入选措施</h3>`+table(r.measures.map(m=>({编号:m.id,名称:m.name,'费用（元）':m.cost,前置措施:(m.prereq||[]).join('、')||'—'})))+`<h3>各情景达标依据</h3>`;
  for(const s of r.scenarios)h+=`<h4>${esc(s.name)}：${s.met?'达标':'未达标'}</h4><div class="metrics"><div><small>基线排放kg</small><strong>${fmt(s.baseline_kg)}</strong></div><div><small>减排目标kg</small><strong>${fmt(s.target_kg)}</strong></div><div><small>实际减排kg</small><strong>${fmt(s.reduction_kg)}</strong></div><div><small>剩余排放kg</small><strong>${fmt(s.remaining_kg)}</strong></div></div>`+table(s.activities.map(a=>({活动:a.activity,'基线kg':a.baseline_kg,'剩余系数（连乘）':a.remaining_factor,'剩余kg':a.remaining_kg,'减排kg':a.reduction_kg})));
 }
 if(p.outcome==='optimal'&&!p.effective)h+=stale?'<p class="warning">措施或情景已更新，此方案已过期，不能发布；请重新求解。</p>':`<button id="publish" data-id="${p.id}">发布为生效方案</button>`;
 if(p.effective)h+='<p><b>当前生效的减排预算方案。</b>重复发布同一方案不会新增生效记录。</p>';
 return h+'</section>';
}
export function reduction(c,d,selected){
 const activities=baseActivities(d),approved=d.runs.filter(r=>r.approved&&r.status==='completed');
 const plan=d.plans.find(p=>p.id===selected)||d.plans[0];
 const key=(typeof crypto!=='undefined'&&crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random()).replaceAll('-','');
 return heading('REDUCTION BUDGET / 05','减排预算与组合求解','以已复核报告的冻结活动为基线；多项措施对同一活动按剩余排放连乘，求解全部情景都达标的最低费用组合。')
 +`<h2>减排情景</h2><form id="scenario-form" class="inline-form"><label>编号（留空新增）<input name="id" type="number" min="1"></label><label>情景名称<input name="name" required></label><label>减排目标（kgCO₂e）<input name="target_kg" type="number" step="any" min="0" required></label><button>保存情景</button></form>`
 +table(d.scenarios.map(s=>({编号:s.id,情景:s.name,'减排目标kg':s.target_kg})))
 +`<div>${d.scenarios.map(s=>`<button class="toggle edit-scenario" data-id="${s.id}">编辑</button><button class="toggle del-scenario" data-id="${s.id}">删除 ${esc(s.name)}</button>`).join('')}</div>`
 +`<h2>减排措施</h2><details open><summary>新增或编辑减排措施</summary><form id="measure-form"><div class="form-grid"><label>编号（留空新增）<input name="id" type="number" min="1"></label><label>措施名称<input name="name" required></label><label>费用（元）<input name="cost" type="number" step="0.01" min="0.01" required></label></div><fieldset><legend>前置措施（先实施才可选用）</legend>${d.measures.length?d.measures.map(m=>`<label class="weekday"><input type="checkbox" name="prereq" value="${m.id}">#${m.id} ${esc(m.name)}</label>`).join(''):'暂无已登记措施'}</fieldset>${d.scenarios.length?d.scenarios.map(s=>`<fieldset><legend>情景「${esc(s.name)}」分活动减排比例（0–1，留空为0）</legend><div class="form-grid">${activities.map(a=>`<label>${esc(a)}<input name="r_${s.id}_${esc(a)}" data-ratio data-sid="${s.id}" data-act="${esc(a)}" type="number" min="0" max="1" step="0.01" placeholder="0"></label>`).join('')}</div></fieldset>`).join(''):'<p class="empty">请先登记减排情景。</p>'}<button>保存措施</button></form></details>`
 +table(d.measures.map(m=>({编号:m.id,名称:m.name,'费用（元）':m.cost,前置措施:(m.prereq||[]).join('、')||'—','分情景减排比例':m.ratios})))
 +`<div>${d.measures.map(m=>`<button class="toggle edit-measure" data-id="${m.id}">编辑</button><button class="toggle del-measure" data-id="${m.id}">删除 #${m.id} ${esc(m.name)}</button>`).join('')}</div>`
 +`<h2>发起求解</h2><form id="plan-form" class="inline-form"><label>方案名称<input name="name" value="明年减排预算方案" required minlength="2"></label><label>基线报告（已复核）<select name="run_id">${approved.map(r=>`<option value="${r.id}">${esc(r.name)}</option>`).join('')}</select></label><label>求解时限（秒，1–300）<input name="budget_seconds" type="number" min="1" max="300" value="30"></label><input type="hidden" name="request_key" value="${key}"><button ${approved.length?'':'disabled'}>发起求解</button></form><p>同一请求键重复提交不会新增方案；未证实最优的方案不能生效。</p>`
 +`<div class="run-layout"><aside class="run-list">${d.plans.map(p=>`<button class="select-plan" data-id="${p.id}">${esc(p.name)} ${status(p.status)}${outcomeTag(p)}${p.effective?'<span class="status">已生效</span>':''}</button>`).join('')}</aside><div>${planDetail(plan,d)}</div></div>`;
}
