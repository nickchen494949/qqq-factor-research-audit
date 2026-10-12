from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parent;B=R.parent
p=pd.read_csv(R/'performance.csv').set_index('strategy');names={'QQQ_top1':'QQQ内Top 1','QQQ_top3':'QQQ内Top 3等权','QQQ_top5':'QQQ内Top 5等权','QQQ_BH':'持有QQQ','SMH_top1':'SMH内Top 1','SMH_top3':'SMH内Top 3等权','SMH_top5':'SMH内Top 5等权','SMH_BH':'持有SMH'}
t=p.loc[list(names)].copy();t.index=t.index.map(names)
for c in ['CAGR','total_return','MDD','monthly_win','rolling_36m_win','rolling_60m_win']:t[c]=t[c].map(lambda x:f'{100*x:,.2f}%')
for c in ['Sharpe','Sortino']:t[c]=t[c].map(lambda x:f'{x:.3f}')
t.columns=['年化收益','累计收益','最大回撤','Sharpe','Sortino','月度跑赢率','滚动3年跑赢率','滚动5年跑赢率'];t.loc[['持有QQQ','持有SMH'],['月度跑赢率','滚动3年跑赢率','滚动5年跑赢率']]='—'
v=pd.read_csv(R/'daily_nav.csv',index_col=0,parse_dates=True);annual=[]
for yr,g in v.groupby(v.index.year):
 prev=v.loc[v.index<g.index[0]].iloc[-1] if (v.index<g.index[0]).any() else pd.Series(1.,index=v.columns)
 for name in v:
  x=np.r_[prev[name],g[name]];annual.append(dict(year=yr,strategy=name,return_=x[-1]/x[0]-1,MDD=(x/np.maximum.accumulate(x)-1).min()))
a=pd.DataFrame(annual);a.to_csv(R/'annual_comparison.csv',index=False);a['收益 / 年内回撤']=a.apply(lambda r:f'{100*r.return_:+.2f}% / {100*r.MDD:.2f}%',axis=1);at=a.pivot(index='year',columns='strategy',values='收益 / 年内回撤')[list(names)].rename(columns=names)
notes='''结论：分散确实降低这段历史最大回撤。QQQ Top 3相较Top 1年化略升、回撤明显下降，但回撤仍约63%；QQQ Top 5回撤约56%。SMH Top 3/5以收益降低换取回撤下降。风险调整指标并未全面胜过直接持有ETF，不能宣称稳定碾压。
规则：2009-01-02至2026-10-09。沿用原版当时已知名单，12–1M总回报排名，取前1/3/5只证券，月末信号，下月首交易日收盘调成等权，月内权重自由漂移。没有五年历史、上涨频率或绝对动量额外过滤。每次实际交易额单边0.1%，期末清仓0.1%。费用以扣费后目标净值求解，只对净买卖金额收费。含分红拆股、未计税。
证券单位：不同股权类别作为不同上市证券，本轮不另做发行人去重。QQQ Top 5有1个月同时选入GOOG和GOOGL，因此5只证券不一定代表5家独立公司。新买入日已停止交易的目标份额留现金，不事后回填其他股票；Broadcom旧股2016-02-01发生此情况。现金按滞后DFF/360代理利息。
公司事件：现金收购按官方金额形成现金应收款；混合对价按现金及承接股票市值延续到下次月度调仓，不以旧股票价格无条件前填。已核验Altera每股54美元、National Semiconductor25美元、Seagen229美元。Virgin Media转17.50美元及Liberty Global两类股；Express Scripts转48.75美元及0.2434股Cigna；旧Broadcom默认现金选择按最终比例51.4829美元及0.0242股新Broadcom。Fox按2019-03-19分拆比例持有FOX与剩余母股，后者默认换成Disney股份。现金应收款不生息，换股部分随市场估值，出售成本只计算股权部分。这仍是理想化可交易/结算假设，并未逐笔模拟券商到账日和零碎股。
ARM特殊处理必须披露：未取得2016收购最终ADR美元净到账额，采用2016-09-02收盘卖出并扣0.1%费用，之后现金至月度调仓。依据MIAX当日15:14（收盘前）公开退市通知，可在当时执行；这是一次预告退市退出规则，Top 3/5的2016年9月受影响，不是声称已完整复现实际ADR结算。Top 1未受这些新增事件影响。
核验：原版Top 1完整复算与冻结结果误差<1e-9；六条策略收益账与股数现金账吻合；持仓日行情无缺口。所有可能影响Top 5的未决身份上界均已检查，无阻塞候选。新引入Yahoo资产实际持有日期与CRSP比较无大于0.5个百分点日收益差异；这不等于证明全部身份或原始数据绝对正确。
大赢家审计：按连续持有同一证券到实际换股作为一段，含买卖费用。两组各取收益贡献前5段，早期NVDA/TSLA/MU以CRSP总回报交叉检查；近期MU/WDC/AVGO/NVDA/PLTR价格以Alpaca SIP交叉检查，显式校正2024年拆股。早期最大整段回报差异约0.066个百分点；近期对照最大相对价格差异不足0.004%。分红复权仍依赖原主源，独立价格吻合不能替代全套公司行动核验。
集中度压力测试：把事后最强三段持仓净收益设为零，QQQ Top 1年化30.54%→4.59%，SMH44.71%→15.19%。这不是可交易策略、不预测未来，也未对ETF做对称剔除，不能据此单独判定动量失效。它只说明收益依赖少数大赢家。
风险统计：日收盘最大回撤；Sharpe与Sortino使用滞后DFF超额日收益及sqrt(252)，Sortino以下行平方均值按全部交易日计算。月度及滚动胜率为2009-01至2026-09的213个月，滚动窗口互相重叠，不是独立样本。2026年度收益只到10月9日；年度回撤每年重设起点。
继承限制：早期公开持仓名单有披露滞后，不是精确逐月指数成分；SMH有HOLDRS前身和2012初始两月发行前指数代理。CRSP来自公开第三方镜像。早期已披露的少量行情源差异仍存在。所有结果是多次探索后的回顾性研究，无真正未来样本外验证。
复算：replay.py读取同包selection.csv、prices_events.parquet、cost_fraction.parquet、events.csv、baseline_input.csv、DFF.csv，独立复算六条策略及两个ETF对照。prepare.py/events.py/contribution.py为实际研究过程脚本，部分依赖前期研究包；不能宣称全部数据采集在本ZIP中独立重建。依赖pandas、numpy、pyarrow。交叉核对原始Alpaca响应、关键事件来源及逐月持仓均保留。
'''
(R/'README.txt').write_text(notes)
urls=['https://www.sec.gov/Archives/edgar/data/768251/000119312515414631/d102231d8k.htm','https://www.sec.gov/Archives/edgar/data/70530/000009747611000043/d8k09232011national.htm','https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2023-721','https://www.sec.gov/Archives/edgar/data/1270400/000119312513256243/d552872d8k.htm','https://www.sec.gov/Archives/edgar/data/1532063/000114036118045477/form8k.htm','https://investors.broadcom.com/news-releases/news-release-details/broadcom-limited-announces-final-broadcom-corporation-merger','https://www.sec.gov/Archives/edgar/data/1308161/000119312519079034/d721340d8k.htm','https://www.sec.gov/Archives/edgar/data/1744489/000095015719000301/form8k-12b.htm','https://www.miaxglobal.com/alert/2016/09/02/miax-delisting-alert-arm-holdings-plc-armh'];(R/'sources.txt').write_text('\n'.join(urls))
e=pd.read_csv(R/'top1_episodes.csv').sort_values('log_contribution',ascending=False).groupby('fund').head(5);e.net_return=e.net_return.map(lambda x:f'{100*x:.2f}%')
html='<!doctype html><meta charset="utf-8"><title>Top 1 / 3 / 5 分散与大赢家审计</title><style>body{font:16px system-ui;max-width:1400px;margin:35px auto;line-height:1.7}table{border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{border:1px solid #ccc;padding:7px;text-align:right}th{background:#e9eff7}h1,h2{color:#193e61}.wide{overflow:auto}</style><h1>Top 1 / 3 / 5：分散是否降低回撤？</h1><p><b>QQQ Top 3改善收益与回撤；SMH分散则牺牲收益降低回撤。两者都没有消除大跌风险。</b></p><div class="wide">'+t.to_html()+'</div><h2>最强持仓段</h2>'+e.to_html(index=False)+'<h2>逐年收益 / 年内最大回撤</h2><div class="wide">'+at.to_html()+'</div><h2>规则、验证与限制</h2>'+''.join('<p>'+x+'</p>' for x in notes.splitlines())+'<h2>事件来源</h2>'+''.join('<p><a href="'+u+'">'+u+'</a></p>' for u in urls)
(R/'Top135_Report.html').write_text(html)
shutil.copy(B/'green5_test/daily_nav.csv',R/'baseline_input.csv');shutil.copy(B/'green5_test/DFF.csv',R/'DFF.csv')
f=R/'replay.py';src=f.read_text().replace("B/'green5_test/daily_nav.csv'","R/'baseline_input.csv'").replace("B/'green5_test/DFF.csv'","R/'DFF.csv'");f.write_text(src)
(R/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2))
with zipfile.ZipFile(B/'Top135_Comparison_Audit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in R.iterdir():
  if f.is_file():z.write(f,f.name)
print('ZIP bytes',(B/'Top135_Comparison_Audit.zip').stat().st_size)
