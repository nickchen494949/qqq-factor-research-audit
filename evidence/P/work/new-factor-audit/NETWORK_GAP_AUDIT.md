# QQQ 因子旧路线网络补漏审计

审计口径：只把“机制不同、免费、历史够长、可按发布日期回放”的东西算真实遗漏；换名字、换分母或当前快照不能算。官方机构与原始论文优先。

## 收口结论

- 用户新提的 **总体利润率变化**和**企业偿债压力**已经按固定口径测完，分别 `REJECT`；FINRA margin debt / 市值只是旧保证金债务换分母，不算新因子。
- 真正发现 4 条机制缺口，其中 SCOOS 已立即测完并 `REJECT`。仍值得最小测试的最多 3 条是：**① Census 科技订单/库存，② SLOOS 企业贷款标准，③ Z.1 券商杠杆**。
- ACM 利率分解在概念上不同，但官方历史 vintage 不足；CBOE 没有免费长历史的 NDX implied correlation/skew。两条都不能在严格 PIT 门下冒充可用数据。

## 真正遗漏（4 条）

| 优先级 | 固定候选 | 与旧失败因子的实质差别 | 免费历史与 PIT | 最小证伪测试 | 本轮决定 |
|---|---|---|---|---|---|
| 已完成 | **Fed SCOOS 股票融资条件** | FINRA 是客户已经借了多少；SCOOS 是 dealer 对股票融资额度、期限、haircut、利差正在收紧还是放松，属于上游信用供给。[Fed 说明调查覆盖证券融资/OTC市场且机构几乎涵盖全部美元 dealer 活动](https://www.federalreserve.gov/data/scoos.htm)。 | 季频；官方 DDP 提供 2010Q2 至今全量 CSV，发布页逐季存档。Q60 连续数据从 2011Q4；当前 DDP 是当前快照，live OOS 仍须每期冻结。[DDP](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=SCOOS) | 已冻结 average-clients 四项净收紧平均，真实季末、未来63日；方向预设为负。独立复算：58期，rho 全期 +.081、2011–18 +.245、2019+ −.010、排除20/22 +.164。 | **REJECT，停止换分项追结果** |
| **P1** | **Census M3：电脑/电子产品新订单相对库存** | 旧 TSMC 营收/出口是单一供应商或出口额同比；这里直接测美国科技制造需求相对库存的失衡，机制是“订单先转、库存后消化”。 | 月频 NAICS 历史与 new orders、total inventories、inventory/shipments 均免费；官方旧新闻稿从 1992 起可按发布日期回放。[时间序列及2010口径提示](https://www.census.gov/manufacturing/m3/historical/timeseries.html)、[逐月历史发布档](https://www.census.gov/manufacturing/m3/historical_data/index.html) | 下载数据前固定 `Δ12 log(SA new orders / SA total inventories)`；发布日期向后取值，季度 origin，R63/W63；预期正。必须单列 2009–18、2019+，并预先处理 2010-04 半导体并入口径断点。若两时期转号或去20/22后消失即拒绝。 | **值得马上测** |
| **P2** | **Fed SLOOS：大中型企业 C&I 贷款标准净收紧** | EBP 是公司债市场已经反映的价格压力；SLOOS 是银行主动收紧企业授信的调查供给信号。也不同于 SCOOS：它测企业银行贷款，不是股票/stock-loan 融资。 | 官方调查季频，发布页至少从 1997 连续存档，DDP 免费 CSV/XML；问题覆盖贷款标准、条款和需求，报告按 FOMC 节奏公开。[官方发布档与调查说明](https://www.federalreserve.gov/data/sloos.htm)、[DDP](https://www.federalreserve.gov/datadownload/Choose.aspx?rel=SLOOS) | 固定“国内银行对大中型企业 C&I 标准净收紧百分比”，不混需求；按发布日期 origin，未来 R63/W63；预期负。与 past63、VIX、EBP、实际利率做增量基线。若稳定题目不能从旧发布表重建、少于48期或分期转号即拒绝。 | **值得测，但排在 M3 后** |
| **P3** | **Fed Z.1 券商资产负债表杠杆** | FINRA 是客户融资余额；Z.1 是证券 broker-dealer 自己的风险承载能力。原始论文把券商杠杆冲击作为中介资产定价核，并指出融资恶化伴随去杠杆。[NY Fed 原始论文](https://www.newyorkfed.org/research/staff_reports/sr464) | 季频、免费。固定 `assets/(assets-liabilities)`，资产/负债代码 `FL664090005` / `FL664190005`；Z.1 官方发布档可回到 1996，2016后有 CSV，更早需 HTML/PDF 重建。[Z.1 发布档](https://www.federalreserve.gov/releases/z1/release-dates.htm)、[当前 L.130 指南](https://www.federalreserve.gov/apps/fof/guide/l130.pdf)。2016Q3 IHC 规则造成结构变化，且表号曾调整。 | 下载前固定 `Δ4q log(leverage)`，预期正向 R63、负向去杠杆对应更差 W63；只按发布日期使用旧版值。2016Q3 不平滑，强制报告断点前后；任一时期反向或历史发布重建不完整即拒绝。 | **值得测，但重建成本最高** |

## 两条看起来聪明、但不满足数据门的路线

| 路线 | 审计结果 | 决定 |
|---|---|---|
| **NY Fed ACM 10Y expected short-rate path / term premium** | 它确实把 10Y yield 分成预期短率路径与期限溢价，和已测 DGS2/DFII10 不同；官方当前下载从 1961 至今，含 term premium、fitted yield、expected average short rates。[NY Fed 官方数据页](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs) 但未找到官方逐次历史模型估计档；整段序列会随重估改变。 | **严格 PIT 下 BLOCK**；只能 current-vintage PROXY 或今后 live 冻结，不能马上回测后宣称历史可交易。 |
| **CBOE NDX implied correlation / skew** | 官方 implied correlation 是 SPX 前50成分，不是 NDX；CBOE 页面明确其 COR3M 用 SPX 与成分期权。CBOE 对 NDX 提供的是 implied-volatility 系列，并非 NDX correlation/skew。[CBOE correlation 定义](https://www.cboe.com/us/indices/implied/)、[NDX implied-volatility 方法](https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Nasdaq_100_Implied_Volatility_Index_Series_Methodology.pdf) 自建 NDX correlation/skew 需要历史 NDX 与成分期权面，免费长历史不可得。 | **BLOCK/REJECT 数据路线**；不能拿 SPX 指标冒充 NDX，也不买 OPRA 数据。 |

## 最终推荐顺序

1. **先测 M3 科技新订单/库存**：机制最贴近 QQQ 上游，历史长，官方旧发布档最完整。
2. **再测 SLOOS C&I 标准**：是真正的信用供给，不是 EBP 的换名；提取成本低于 Z.1 vintage 重建。
3. **最后测 Z.1 券商杠杆**：机制强，但要认真处理旧表、2016Q3 断点和发布日期，不能用当前序列直接回填。

除这三条外，本轮没有找到第 4 条同时满足“本质不同 + 免费 + 够长 + PIT 可回放”的遗漏。盈利、估值、实际利率、通胀、Fed 路径、信用波动、流动性、G7 carry、宽度、拥挤与复杂交互的既有 `REJECT/BLOCK` 维持，不因换窗口、换分母或加非线性而升级。
