组合实验：12–1M Top1 + 绝对动量 + 现金流质量
区间2009-01-02至2026-10-09。每月首个交易日收盘成交；这不是开盘成交回测。
先按原12–1M信号选Top1，再过滤。绝对动量要求>0；质量要求当时已披露最近年报净利润>0且经营现金流>=净利润，年报期末最多550天。失败持现金，不递补下一名，不保留亏损股。
original原版；absolute只加绝对动量；quality只加现金流；combined同时要求两者；combined_strict另外将未知财报也排除。主试验未知保留原资格。
各方向交易费用0.1%，含股息拆股，最终卖出费，现金DFF滞后两日代理。年化按日历时间，Sharpe/Sortino按日超额收益，回撤按日收盘。2026为部分年度。年度回撤计入上年末净值。
original、absolute、quality逐日净值复现前轮冻结结果；所有策略双账本核对。validation.csv保留误差。
结果：SMH组合年化52.76%，最大回撤60.30%，Sharpe1.119，Sortino1.749。QQQ组合20.84%，回撤50.45%，Sharpe0.649，Sortino0.963。
但缺失全部持现金时SMH组合降至36.83%，回撤仍60.30%。QQQ25.02%，回撤38.19%。这些不是收益区间上下界，而是两种不同规则。财报未知QQQ46/214个月、SMH58/214个月。
结论：组合在SMH全区间提高回报，没有降低最大回撤，QQQ未提高风险调整收益。不可据此证明筛选能稳定抓到飙涨股。多次事后探索，非未触碰样本外测试。
局限：早期ETF成分披露滞后、QQQ个别名单陈旧；SMH旧HOLDRS及指数代理；第三方CRSP行情镜像；SEC标准标签不含全部自定义标签、IPO和重述；未知不是随机缺失。详见quality_source/README.txt。原始采集与证券映射未独立重建。
复算：安装pandas,numpy,pyarrow后运行replay.py。monthly_audit.csv为冻结时点信号；quality_source保留SEC JSON及其解析代码。所有结果CSV，monthly_selections含逐月持仓。
