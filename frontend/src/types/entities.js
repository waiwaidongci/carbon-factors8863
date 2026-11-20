// API实体字段约定：来源{id,natural_key,data}、口径{id,version,data}、报告{id,status,snapshot,checksum,result,approved}、计划{next_at,enabled}、情景{id,name,target_kg}、措施{id,name,cost,prereq,ratios}、方案{id,request_key,status,outcome,input,progress,result,effective,catalog_version}。
export const ENTITY_KEYS=['sources','policies','runs','schedules','deliveries','scenarios','measures','plans'];
