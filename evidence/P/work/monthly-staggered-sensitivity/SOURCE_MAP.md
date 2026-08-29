# 月末四相位稳健性｜结果前数据源地图

冻结目的：不用季度成品表复制月度行；每条信号从自身日／周／月／季事件流，按真实月末origin做保守as-of。

## 价格与目标

- QQQ旧段：`work/evidence/qqq-proxy-backtest/raw/qqq-macrotrends-github.csv`。
- QQQ延长段：`work/evidence/qqq-proxy-backtest/raw/chartexchange-qqq.html`。
- 两段重叠close必须一致；origin是每个自然月最后一个QQQ交易日。

## old8

1. `eps13w`：`outputs/NDX_IMPLIED_FORWARD_EPS_PROXY_SINCE_2009.csv::change_13w_pct`。周频；最新`date<=origin`，最长陈旧10日。源为History of Market `.forward`与官方NDX close；current-vintage PROXY。
2. `fpe_level`：同文件`forward_pe`。同一周频与陈旧规则；current-vintage PROXY。
3. `real91`：`work/evidence/fred-dfii10/2026-08-28/raw/DFII10.csv::DFII10`。最新观察减91个日历日前最新观察；日频，最长陈旧7日；无ALFRED vintage。
4. `vix_level`：`work/evidence/fred-vix/2026-08-29/raw/VIXCLS.csv::VIXCLS`。日频market close，最长陈旧7日。
5. `baa_level`：`work/evidence/fred-baa10y/2026-08-29/raw/BAA10Y.csv::BAA10Y`。每条观察保守加1个美国营业日后才可用；最长陈旧10日；current-vintage。
6. `breadth63`：官方NDX与NDXE xlsx的`History!A:B`。共同交易日`ratio=NDXE/NDX`，再算63个共同交易日前变化；最新共同close不晚于origin且最长陈旧7日。NDXE部分历史可能是indicative/back-tested。
7. `easing5`：五个FRED三个月银行间利率月序列。参考月值从次月1日可用；各国最新as-of值减origin前91日的as-of值，下降者计1。每国最新available距origin不得超过62日；current-vintage且不是OIS。
8. `g20_cli3m`：`work/evidence/oecd-cli-current/2026-08-29/raw/oecd_cli_korea_g20_current.csv`中G20 harmonised CLI。参考月值从次月10日可用，减三个月前参考值；最新available距origin不得超过62日。2009–2022没有逐月edition，PROXY。

## new4

9. `A`：`work/network-reaudit-batch2/m3-sloos/normalized/m3_monthly.csv::signal`。月频；参考月末+45日可用，最新available距origin不得超过62日。订单与库存宇宙不完全一致，PROXY。
10. `B`：`work/network-reaudit-batch2/m3-sloos/normalized/sloos_quarterly.csv::signal`。季度；季末+45日可用，公布后hold-last，最长陈旧130日；current-vintage。
11. `C`：`work/network-reaudit-batch2/z1/derived/z1_current_vintage_series.csv::signal`。季度；`available_date`后hold-last，最长陈旧130日；current-vintage且2016Q3有结构断点。
12. `D`：`work/network-reaudit-batch2/qfr/derived/qfr_current_vintage.csv::feature_pp`。季度；`available`后hold-last，最长陈旧130日；current-vintage。

## 共同边界

- 市场close型记录允许`date<=origin`，代表origin收盘后预测。
- 只有日期、没有时间的宏观发布日期必须`available<origin`；同日记录从下一交易日才可用。
- 禁止插值、倒填、同季度直接连接、使用下一条记录或放宽陈旧上限。
- 任一信号缺失或过期，整个origin删除；所有模型共享同一批origin。
- 预计共同覆盖为2009-04至2026-03；末端由G7欧元区／英国共同最新参考月限制。

