# North Star Navigation

## NORTH STAR

- 最终结果：判断“QQQ 盈利变化 × 宏观状态”是否对未来 Nasdaq-100 / QQQ 收益有稳定的样本外预测价值。
- 非目标：继续扩张旧 SEC 身份验证架构；制造好看的历史曲线；把市场代理称为 QQQ EPS。
- 不得触碰：Phase 0 生产数据库、现有 `qqq-dashboard` 生产策略、无关脏文件、旧冻结证据包原件。

## MILESTONES

1. `[IN PROGRESS]` 找到或否定可用的时点正确 EPS 数据源
2. `[PENDING]` 冻结最小研究数据集与定义
3. `[PENDING]` 单变量和最简单回归诊断
4. `[PENDING]` 有界交互/非线性探索
5. `[PENDING]` 完全独立的 walk-forward OOS
6. `[PENDING]` 比较复杂度、成本和决策价值

## CURRENT GATE

- 阶段：数据来源可行性
- 通过条件：至少一个来源拥有明确 QQQ/NDX 口径、足够历史、时点/vintage 信息、可导出数据和可审计方法。
- 当前状态：`IN PROGRESS`
- 当前任务为何关闭此闸门：先决定数据是否存在，避免再次用代码修补不存在的资料。

## ACTIVE TASK

- 最小动作：比较官方、数据商和指数供应商的直接 EPS / revision 数据。
- 拥有路径：本目录内的新报告；旧 `artifacts/` 只读。
- 预算：最多一轮来源搜索与一轮独立核对；实现代码软上限 300 行，仅在找到可用来源后才允许写。
- 停止规则：若没有满足条件的数据，明确 BLOCK，并给出购买/代理/停止三种选择；不回到 2,745 行重建。

## BLOCKER ROUTE

- 当前阻碍：现有本地资料缺少完整公司级 EPS vintage，公开 Nasdaq 答案仅 6/8。
- 类型：data
- 安全替代：可靠付费数据；明确标注的市场盈利代理；或停止该分支。
- 不得弱化：代理不能改名为 QQQ EPS，现值数据不能冒充 point-in-time。

## PARKING LOT

- SEC realized EPS 自建
- 2,745 行完整身份桥
- 非线性模型、随机森林、XGBoost、神经网络
- Dashboard 美化与自动更新
- TSMC 订单、台湾出口、期货等早期指标

## NEXT

- PASS：冻结来源和最小字段，再做便宜的单变量诊断。
- FAIL：报告缺失原因、可靠购买选择和诚实代理；等待用户决策。
