from pathlib import Path
import pandas as pd,numpy as np,json,shutil,zipfile,hashlib
R=Path(__file__).resolve().parent;B=R.parent
names={'QQQ_original':'QQQ股票池：原版','QQQ_five_year_history':'QQQ股票池：仅五年历史','QQQ_green3of5':'QQQ股票池：固定3/5上涨','QQQ_relative_green':'QQQ股票池：上涨次数≥QQQ','QQQ_BH':'持有QQQ','SMH_original':'SMH股票池：原版','SMH_five_year_history':'SMH股票池：仅五年历史','SMH_green3of5':'SMH股票池：固定3/5上涨','SMH_relative_green':'SMH股票池：上涨次数≥SMH','SMH_BH':'持有SMH'}
p=pd.read_csv(R/'performance.csv').set_index('strategy').loc[list(names)];p['total_return']=p.terminal_multiple-1;p.to_csv(R/'comparison.csv');t=p[['CAGR','total_return','MDD','Sharpe','Sortino','monthly_outperform']].copy();t.index=t.index.map(names)
for c in ['CAGR','total_return','MDD','monthly_outperform']:t[c]=t[c].map(lambda x:f'{100*x:,.2f}%')
for c in ['Sharpe','Sortino']:t[c]=t[c].map(lambda x:f'{x:.3f}')
t.loc[['持有QQQ','持有SMH'],'monthly_outperform']='—';t.columns=['年化收益','累计总收益','最大回撤','Sharpe','Sortino','月度跑赢ETF比例']
v=pd.read_csv(R/'daily_nav.csv',index_col=0,parse_dates=True);annual=[]
for yr,g in v.groupby(v.index.year):
 prev=v.loc[v.index<g.index[0]].iloc[-1] if (v.index<g.index[0]).any() else pd.Series(1.,index=v.columns)
 for name in names:
  q=np.r_[prev[name],g[name].values];annual.append(dict(year=yr,strategy=name,return_=q[-1]/q[0]-1,MDD=(q/np.maximum.accumulate(q)-1).min()))
a=pd.DataFrame(annual);a.to_csv(R/'annual_return_drawdown.csv',index=False);a['收益 / 年内回撤']=a.apply(lambda r:f'{100*r.return_:+.2f}% / {100*r.MDD:.2f}%',axis=1);at=a.pivot(index='year',columns='strategy',values='收益 / 年内回撤')[list(names)].rename(columns=names)
s=pd.read_csv(R/'signals.csv');th=pd.read_csv(R/'etf_thresholds.csv');
text='''结果：相对ETF年度上涨频率过滤未提高全期收益或风险调整表现。QQQ原版年化30.54%→27.67%，最大回撤-84.14%→-77.61%；SMH原版44.71%→37.29%，最大回撤-60.30%→-58.49%。QQQ/SMH月度跑赢率由53.1%/51.2%降至47.4%/49.3%。这是收益与回撤的权衡，不应说所有指标都恶化。
精确规则：在当时已公开的QQQ或SMH成分名单中，个股必须有过去5个完整年度记录；计算这5个年度总回报>0的次数，要求不低于对应ETF同5年的次数。保留合格股票，再按12–1M总回报动量降序选1只，月末信号、下月首个交易日收盘交易，正常卖出盈利及亏损股票。没有合格股票持现金；本次两组各214个月均有合格股票。
时点：交易年份Y只检查Y-5到Y-1，绝不使用未结束的当年。5年完整历史门槛与上一轮一致。门槛每年更新，月度重新筛选及排名。2009年QQQ门槛4/5，SMH前身门槛1/5；QQQ在2014–2018年门槛5/5，明显更严格。SMH早期ETF收益含HOLDRS前身，不应称作当前VanEck基金当时已经存在。
统一比较期间：2009-01-02至2026-10-09；保留上一轮终点保证同期间，没有加入本轮运行日之后的行情。单边交易成本0.1%、终点卖出0.1%，含股息和拆股。所有收益非税后。初日从收盘买入起算。
风险指标：日末净值最大回撤。Sharpe采用日收益减滞后2日DFF、sqrt(252)年化；Sortino使用同样超额收益、全部交易日下行平方均值。现金按滞后DFF/360计息是假设。本次没有现金持仓。累计收益=终值/初值-1。每月跑赢率使用213个月至2026-09，2026-10仅至9日不算完整月。年度表2026不完整；年内回撤每年从上年末净值重新起算，不等于跨年回撤。
核验：428个新选择全部通过年度门槛；全部实际持仓日价格齐全；未解决身份/年度缺口均无可能影响入选第一名，没有静默丢弃可能赢家。第二套股数记账与第一套净值记账最大相对误差<5e-15。新引入Yahoo股票在实际持仓日期与CRSP日收益交叉检查，无大于0.5个百分点差异。该核验不代表底层历史成分身份和所有原始数据已由独立机构认证。
研究局限：沿用早期有披露滞后的公开持仓名单，不是完整精确逐月指数名单。SMH含前身衔接与2012初始两月发行前指数名单代理。早期CRSP来自公开镜像，不是持牌直接交付。此前VRTX少量日收益源差异仍保留。本次是已探索多种规则后的回顾性研究，无真正未来样本外证据。
来源与可复算性：本包保存QQQ/SMH的Yahoo Chart原始响应、ETF五年阈值、所有入选股票及五个年度回报、选股候选审计、冻结持仓价格、逐月逐年收益与复算脚本。reproduce.py可脱离原工作区独立核对两条新策略NAV；rank.py/replay.py/validate.py为实际研究脚本，部分路径依赖此前研究包，不声称这些全部能独立运行。股票候选及年回报来自已保存Green3of5_Backtest.zip与QQQ_SMH_Research_Checkpoint.zip；ETF年度收益使用本轮取得的复权历史，价格截止2026-10-09。
'''
(R/'README.txt').write_text(text)
html='<!doctype html><meta charset="utf-8"><title>个股上涨频率不低于ETF：回测</title><style>body{font:16px system-ui;max-width:1400px;margin:35px auto;line-height:1.65}table{border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{border:1px solid #ccc;padding:7px;text-align:right}th{background:#e9eff7}h1,h2{color:#193e61}.scroll{overflow:auto}</style><h1>个股过去五年上涨次数 ≥ 所属ETF</h1><p><b>全期结果：两组收益与Sharpe下降，回撤有所改善；月度跑赢ETF比例下降。</b></p>'+t.to_html()+'<h2>规则与审计说明</h2>'+''.join('<p>'+x+'</p>' for x in text.splitlines())+'<h2>逐年门槛</h2>'+th[['fund','trade_year','years','required_green','annual_returns']].to_html(index=False)+'<h2>逐年收益 / 年内最大回撤</h2><div class="scroll">'+at.to_html()+'</div><h2>逐月选择</h2>'+s[['fund','trade_month','name','asset','green_years','etf_green_years','n_eligible']].to_html(index=False)
(R/'Relative_Green_Report.html').write_text(html)
shutil.copy(B/'green5_test/DFF.csv',R/'DFF.csv');shutil.copy(B/'green5_test/candidate_audit.csv',R/'input_candidate_audit.csv');shutil.copy(B/'green5_test/annual_history_audit.csv',R/'input_annual_history.csv')
src=(R/'validate.py').read_text();src=src[:src.index('# Actual held-day')].replace("B/'qqq_smh_top1/metadata/DFF.csv'","R/'DFF.csv'");src+='\nprint(pd.DataFrame(checks).to_string(index=False))\n';(R/'reproduce.py').write_text(src)
(R/'file_hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='file_hashes.json'},indent=2))
with zipfile.ZipFile(B/'Relative_Green_Backtest.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in R.iterdir():
  if f.is_file():z.write(f,f.name)
print('saved', (B/'Relative_Green_Backtest.zip').stat().st_size)
