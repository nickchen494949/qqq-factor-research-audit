# 全历史弱信号代表组合｜结果前合同

冻结时间：2026-08-29 13:24 MYT。本挑战在所有单因素历史结果已经看过后提出，明确标记 `POST_HOC_BROAD_ENSEMBLE`；它不改写任何旧 PASS/REJECT，也不是真正未来 OOS。

## 问题与选取原则

测试“以前所有长历史弱信号中，每个因果渠道取一个代表后，组合是否能胜过动量和最好单条”。禁止把同一机制的多个窗口、水平/变化、国家或商品重复塞入，让同一信息重复投票。

## 固定 old8 代表

1. 盈利预期：`outputs/QQQ_EPS_DIRECTION_DIAGNOSTIC.csv` 的 `eps_change_13w_pct`。
2. 估值：`outputs/QQQ_PE_REAL_YIELD_UNIFORM_DIAGNOSTIC.csv` 的 `forward_pe`。
3. 美国折现率：同文件 `real_yield_change_91d`。
4. 市场恐慌：`outputs/QQQ_MISSING_FACTOR_JOINED.csv` 的 `vix`。
5. 信用风险：同文件 `baa`。
6. 市场宽度：`outputs/QQQ_NFCI_BREADTH_DIAGNOSTIC.csv` 的 `ndxe_vs_ndx_63d`。
7. 全球资金成本：`outputs/QQQ_G7_FUNDING_JOINED.csv` 的 `easing_breadth`。
8. 全球商业周期：`outputs/QQQ_OECD_CLI_JOINED.csv` 的 `g20_cli_change_3m`。

明确排除：2年利率与实际利率重复；NFCI/EBP与Baa/VIX高度重叠；Fed净流动性与全球资金同渠道；铜油气/PMI/TSMC/亚洲出口由G20与M3代表上游；同一系列的水平/变化不双收。

## 固定 new4

9. M3科技订单相对库存 A。
10. SLOOS大中型企业C&I净收紧 B。
11. Z.1券商账面杠杆四季增长 C。
12. QFR科技经营利润率同比百分点变化 D。

只读取 `work/network-reaudit-batch2/{m3-sloos,z1,qfr}` 已审计的 finalized CSV，不重算或换定义。

## 日期与目标修正

- 目标、past63、R63、W63、end_date 全部以纠正后的 69 个真实 QQQ 季末输入为准。
- 旧8文件曾用季度内最后一个周五。固定映射：按同一 `year-quarter` 连接到真实季末，且旧 `signal_date <= true_origin`；这是0–6日的保守滞后，不允许向后取下一季度或季末后的值。
- 只有12条特征与目标全部存在的季度进入模型；若2016Q1起成熟测试少于40，决定 `BLOCK_SAMPLE`。
- 报告旧信号日期滞后的最小/中位/最大天数和任何重复/缺季。

## 固定模型

- 外层从2016Q1起逐季 expanding replay。
- 双 purge：训练结果结束日必须早于预测 origin；训练 origin 至少早92个日历日。
- 标准化只用当时训练折；所有模型统一 Ridge `alpha=10`，不搜索参数。
- `base`：past63。
- 12个 `single`：base + 每一条代表。
- `old8`：base + 旧8。
- `all12`：base + old8 + new4。
- 不运行变量筛选、交互、PCA、树、boosting、神经网络、阈值或策略。

## 主通过线

`all12` 只有同时满足才可保留：

1. R63 RMSE 相对 base 改善至少2%。
2. R63 RMSE 至少比12个 single中最好的再低1%。
3. R63 RMSE 至少比 old8 再低1%，证明new4没有稀释旧组合。
4. 相对base至少60%完整样本年份改善。
5. 2016–2020、2021+、排除2020/2022三段相对base均改善。
6. 测试origin至少40。

同时报告MAE、预测/实际rho、W63 RMSE、逐年结果、old8/all12训练系数符号频率和特征相关矩阵；辅助指标不能救活主门。

## 短历史篮子与结论上限

- Carry、CFTC、FINRA、BIS×MOF、EBP、VIX期限等短历史拥挤/融资篮子不重复纳入；它们此前已在固定正则Logit与深度2浅树中组合测试并REJECT。
- 多数输入是current-vintage或免费代理；即使过线，最高为 `POST_HOC_PROXY_CANDIDATE`，不得接生产或生成交易指令。
- 核心脚本软上限300行；输入、派生、输出与失败运行全部哈希冻结。
