# 数据定位与复算

恢复后目录结构与原工作区相同，避免破坏脚本的兄弟目录依赖。建议复制恢复工作区后再运行会覆盖输出的旧脚本。

| 入口 | 作用 |
|---|---|
| `qqq_smh_top1/results/candidate_rankings.csv` | 原历史候选表，含基金、交易月、证券身份、名单来源和价格动量状态 |
| `qqq_smh_top1/results/monthly_signals.csv` | 原12–1M Top1；不能替代EPS全候选排名 |
| `qqq_smh_top1/metadata/` | 持仓、身份、源行情、DFF与审计材料 |
| `qqq_smh_top1/raw_sec/` | 原持仓披露缓存 |
| `green5_test/crsp_history_daily.parquet` | 早期候选日总回报扩展输入 |
| `absolute_momentum/` | 冻结信号、长表prices.parquet、reference_nav、DFF、自包含run.py |
| `top135/` | Top1/3/5选择、公司行动、宽表价格、回放和核验 |
| `quality_trial/raw/` | SEC companyfacts JSON，仅实际财报，不是分析师预期 |
| `earnings_trial/events.csv` | 旧动量Top1相关股票的EPS/营收预期事件表 |
| `eps_growth/candidates.csv` | 当前EPS任务冻结的完整候选表 |
| `eps_growth/events.csv` | 扩大的公开EPS实际值/预期值/季度/公告日期表 |
| `eps_growth/candidate_audit.csv` | 每只候选每个月的通过、失败、未知原因及增长区间 |
| `eps_growth/monthly_coverage.csv` | 每月覆盖、未知数、有数据子集候选；非实际持仓 |
| `eps_growth/annual_coverage.csv` | 分年覆盖率 |
| `eps_growth/STRATEGY.txt` | 当前默认规则与数据约束 |

## 可从冻结输入执行的入口

```bash
python eps_growth/audit.py                 # 只审计，不是收益回测
python absolute_momentum/run.py           # 绝对动量旧实验
python top135/replay.py                    # Top1/3/5旧实验
python top135_absolute/replay.py           # Top1/3/5 + 绝对动量
python green5_test/reproduce.py            # 5年/3年上涨旧实验净值复算
python relative_green/reproduce.py         # 相对ETF上涨次数旧实验净值复算
python earnings_trial/replay.py            # 旧动量Top1加双超预期，不是当前策略
python quality_trial/replay.py             # 现金流实验
python combined_quality/replay.py          # 错方向的组合实验，勿错贴标签
```

以上是根据实际脚本读取方式整理的入口；本次交接没有从互联网重新采集并重跑所有实验。历史报告可复现与整个原始采集流程已独立验证是两回事。

`eps_growth/audit.py`：存在raw目录时重新解析网页；没有raw目录时从冻结events.csv复算。保留Expected/Actual字符串精度用于四舍五入区间，勿自行转换为浮点后再格式化。已有冻结数据模式逐月覆盖结果一致的检查。

## 输出文件的一般含义

- `performance.csv`：该目录实验的总指标，通常收益是小数，展示时乘100。
- `daily_nav.csv`：日末净值；不是盘中净值。
- `monthly_selections.csv` / `holdings.csv`：已回测策略的选择；EPS审计例外，不能混用。
- `annual_comparison.csv`：年度收益和年度内回撤，区别于跨年度最大回撤。
- `validation.csv` / `accounting_controls.csv`：账本/冻结结果一致性，非所有原始数据的真实性证书。
- `README.txt`、`sources.txt`、`*_audit.csv`：各实验自身限制和数据来源。

## 文件保存范围

保留13个当前研究目录、根目录研究报告、18个旧ZIP的清单与内容（其中4个坏ZIP保留原字节，其余14个解包去重）。技术传输助手、临时复算副本、Python缓存未纳入，它们不是研究数据；不携带会话认证材料。FILE_MANIFEST.json记录具体数量与完整路径，INTEGRITY.json记录不可读取的旧包。

授权和来源不因放入私有仓库而改变。CRSP第三方镜像和网站数据的后续使用/再分发由其来源条款约束；本交接不额外授予数据许可，也不把这个仓库公开。
