# QQQ月末四相位稳健性｜结果前合同

冻结时间：2026-08-29 13:22 MYT。冻结时尚未运行或查看任何月度模型结果。本测试由用户在季度old8＋new4结果后提出，明确标记`POST_HOC_TIMING_ROBUSTNESS`。

## 问题

季度末结果是否只是取样时点碰巧？改用每个月末观察后，12条代表组合能否在四条真正不重叠的错位路线中，稳定胜过past63、预先固定的VIX单条和old8，同时不恶化未来63日下跌路径？

## Origin与目标

- Origin：每个自然月最后一个QQQ交易日收盘。
- `R63 = close[i+63] / close[i] - 1`。
- `W63 = min(close[j] / close[i] - 1), j=i..i+63`，保持旧季度合同定义。
- `past63 = close[i] / close[i-63] - 1`。
- `i+63`不存在的未成熟origin不评分。
- 12条特征、来源、available-date与陈旧上限严格使用同目录`SOURCE_MAP.md`；所有模型使用相同完整行。

## 为什么是四相位

结果前日期预检证明，三相位每隔3个月仍分别出现18、31、21次`previous_end > next_origin`。改用四相位后四组均为0：

- A：1／5／9月末。
- B：2／6／10月末。
- C：3／7／11月末。
- D：4／8／12月末。

每组只用本组历史独立训练、预测和评分。组与组之间仍会覆盖相同市场事件，因此四组是四个错位复现，不是四个完全独立实验；合并月度指标只能作描述。

## 固定模型

每个cohort独立从2016年第一个可用origin开始expanding replay：

- 训练行必须同时满足`train_end < test_origin`与`train_origin <= test_origin - 92 calendar days`。
- 首次预测前至少20条本cohort合格训练行。
- StandardScaler只拟合当时训练折。
- Ridge固定`alpha=10`，不搜索参数。
- `base`：past63。
- 12个`single`：base分别加一条信号。
- `old8`：base加eps13w、fpe_level、real91、vix_level、baa_level、breadth63、easing5、g20_cli3m。
- `all12`：old8再加A、B、C、D。
- R63与W63分别拟合同样规格。
- 禁止变量筛选、交互、PCA、树、boosting、神经网络、阈值或交易策略。

## 样本与数据门

每个cohort必须：

- 至少28个2016年后OOS评分origin；
- 覆盖至少9个自然年；
- 组内`previous_end < next_origin`零违规；
- 全部宏观`available < origin`、市场close型`date <= origin`；
- 双purge零违规；base、single、old8、all12使用完全相同origin。

任一信号没有可审计available-date：`BLOCK_PIT`。任一cohort未达到样本门：`BLOCK_SAMPLE`。不得删除坏月份、移动起点或降低门槛补救。

## 单组通过线

一个`COHORT_PASS`必须四项同时满足：

1. all12的R63 RMSE相对base改善至少2%。
2. all12的R63 RMSE相对结果前已固定的`single_vix_level`再改善至少1%。
3. all12的R63 RMSE相对old8再改善至少1%。
4. all12的W63 RMSE不高于base。

12个single全部报告；测试后找到的best single只作描述，不能替换预先固定的VIX门。

## 正式总判定

`PASS_TIMING_ROBUSTNESS`必须全部满足：

1. 至少3／4个cohort为`COHORT_PASS`。
2. 由四个cohort各自模型产生的全部预测合并描述时，R63仍同时满足对base +2%、对VIX +1%、对old8 +1%，W63不差于base。
3. 任一失败cohort的R63或W63相对base不得恶化超过5%。
4. 2016–2020与2021+两个合并描述分段，all12相对base的R63 RMSE均改善。
5. 排除origin年份2020与2022后，all12相对base的R63 RMSE仍改善。

数据与样本合格但任何性能门失败：`REJECT_TIMING_ROBUSTNESS`。即使全部通过，结论上限也是`POST_HOC_CURRENT_VINTAGE_ROBUSTNESS_CANDIDATE`，只能说明季度末选点并非唯一来源，不能升级为真正PIT/OOS、生产模型或交易信号。

## 证据与停止规则

- 冻结全部输入路径、字节数、SHA-256与aggregate hash。
- 保存月末完整特征、每条source reference／available-date／age、逐cohort逐fold预测、系数、指标、相关矩阵和排除原因。
- 保存合同hash、代码hash、参数、环境、起止时间、退出状态与全部输出hash。
- 独立闭式重算、重算所有门、核对四组零重叠和双purge；确定性复跑。
- 核心脚本软上限300行，只允许这一种模型与这一次运行。
- 通过或失败后立即关闭，不改cohort、窗口、alpha、对手、样本门或目标。

