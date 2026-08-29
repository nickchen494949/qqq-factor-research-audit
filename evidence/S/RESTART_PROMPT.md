# 新任务提示词

读取并服从以下文件：

1. `[LOCAL_SOURCE_ROOT]/PROJECT_STATE.md`
2. `[LOCAL_SOURCE_ROOT]/NORTH_STAR.md`
3. `[LOCAL_SOURCE_ROOT]/ARCHIVE_SCOPE.md`

当前只做“数据来源可行性”这一关：判断能否直接取得可信、历史足够长、时点正确的 Nasdaq-100 / QQQ aggregate EPS、forward EPS 或 revision 数据。

先读取旧负面证据：

- `artifacts/eps-feasibility-old/FEASIBILITY_REPORT.md`
- `artifacts/nasdaq-anchor-evidence/verdict.json`
- `artifacts/nasdaq-anchor-evidence/audit_report.md`

不要重复已经完成的公开 Nasdaq 有界搜索。优先检查官方指数数据产品和可靠数据商，输出一份简短决策表：定义、历史、频率、vintage、方法、导出、价格/许可、PASS/PROXY/REJECT。

硬规则：

- 不继续修 2,745 条身份资料。
- 不触碰 Phase 0 或 `qqq-dashboard` 生产策略。
- 数据没找到就报告 BLOCK，不用更多代码掩盖。
- 在数据来源通过前，不做模型、机器学习或回测。
- 核心实现软上限 300 行；没有数据时应为 0 行。
- 最终用人话报告：做完、找到什么、缺什么、下一步需要用户决定什么。
