# 002 减排预算求解

SQLAlchemy启动创建以下业务表：

- `reduction_scenarios`：减排情景（名称唯一、减排目标kgCO₂e）。
- `reduction_measures`：减排措施（费用、前置措施编号列表、分情景分活动减排比例JSON）。
- `reduction_catalog`：目录版本单行表；情景或措施任何增删改都会使版本+1，用于发布时拒绝过期方案。
- `reduction_plans`：求解方案。`request_key`唯一保证同一请求重试不新增记录；`input`冻结基线报告活动排放、情景与措施快照；`progress`保存分支定界断点（搜索栈、当前最优、节点数、已用秒），worker中断后从进度恢复；`outcome`区分optimal/infeasible/timeout；仅`outcome=optimal`且目录版本未过期的方案可发布生效，`effective`全表至多一条。

已有数据库升级需先备份，后续字段演进应以独立迁移执行。
