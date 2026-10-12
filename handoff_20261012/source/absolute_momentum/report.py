from pathlib import Path
import pandas as pd,json,zipfile,hashlib
R=Path(__file__).resolve().parent
p=pd.read_csv(R/'performance.csv').set_index('strategy');labels={'QQQ_original':'QQQ股票池：原版Top 1','QQQ_positive':'QQQ股票池：Top 1且动量>0','QQQ_BH':'直接持有QQQ','SMH_original':'SMH股票池：原版Top 1','SMH_positive':'SMH股票池：Top 1且动量>0','SMH_BH':'直接持有SMH'}
t=p.loc[list(labels),['CAGR','total_return','MDD','Sharpe','Sortino','monthly_win_rate']].copy();t.index=t.index.map(labels)
for c in ['CAGR','total_return','MDD','monthly_win_rate']:t[c]=t[c].map(lambda x:f'{100*x:,.2f}%')
for c in ['Sharpe','Sortino']:t[c]=t[c].map(lambda x:f'{x:.3f}')
t.loc[['直接持有QQQ','直接持有SMH'],'monthly_win_rate']='—';t.columns=['年化收益','累计收益','最大回撤','Sharpe','Sortino','月度跑赢ETF']
s=pd.read_csv(R/'monthly_selections.csv');cash=s[s.selected.eq('CASH')];c=cash[['fund','trade_month','asset','momentum']].copy();c.momentum=c.momentum.map(lambda x:f'{100*x:.6f}%')
a=pd.read_csv(R/'annual_comparison.csv');a=a[a.strategy.isin(labels)];a['收益 / 年内回撤']=a.apply(lambda r:f'{100*r.return_:+.2f}% / {100*r.MDD:.2f}%',axis=1);at=a.pivot(index='year',columns='strategy',values='收益 / 年内回撤')[list(labels)].rename(columns=labels)
text='''结论：绝对动量过滤对QQQ无效，因为214个交易月原版第一名股票的12–1M动量均>0。SMH仅5个月转为现金，年化由44.71%升至47.62%，Sharpe由0.951升至0.998；最大回撤仍为-60.30%，没有解决最深回撤。不能把5次触发的历史改善解读成已证实普遍有效。
规则：每个QQQ/SMH股票池沿用原版当时已知成分候选与12–1M总回报排名。月末选第一名；其12–1M动量严格>0，下月首个交易日收盘买入；<=0则持现金。盈利亏损均正常卖出。没有叠加五年历史或上涨频率过滤，也没有对ETF自身做择时。现金按滞后2日DFF年率乘日历天数/360计息，是现金收益代理而非某只真实ETF。
区间与费用：2009-01-02至2026-10-09，同此前收盘成交版。单边交易成本0.1%，结束时卖出0.1%；含股息和拆股，不含税。收益累计复利、回撤为每日收盘净值峰谷。月度跑赢率213个月至2026年9月，10月未完不计入。年度2026截至10月9日；年度回撤重设年初基点，不是跨年度最大回撤。
重要执行细节：现金月份从首个交易日收盘起切换，月初这一天仍承接旧持仓收益；因此转现金月份的日历月收益不一定接近0。收益核算未提前一天卖出，不用月末收盘偷换下月首日收盘。
触发：SMH 2009-01、2009-02、2009-05、2009-06、2022-12。QQQ没有触发。2022-12的ON动量恰好为零：2021-11-30与2022-10-31复权收盘价同为61.43000030517578；按既定>0规则持现金。2022年11月作为最近一个月被跳过，未计入动量。
验证：两套独立股数/收益记账误差<1e-14；原版复算与冻结净值吻合；全部实际持仓日价格完整。公开数据价格、身份和成分名单仍有研究限制，账本吻合并不证明底层数据完美。
敏感度：另保存现金零利息及允许零动量继续持股两个对照。它们用于展示假设影响，没有事后用最好结果替换主规则。主规则始终严格>0，现金DFF代理。
限制：沿用早期披露滞后的持仓名单，非完全精确逐月指数名单。SMH早期含Semiconductor HOLDRS衔接与2012初始两月发行前指数代理。CRSP为第三方公开镜像。原有少量源差异仍在。本次结果是探索性回测，无独立未来样本外证据。最深回撤仍发生在过滤未触发的持仓阶段。
复现：运行python run.py，读取同目录signals_input.csv、prices.parquet、reference_nav.csv和DFF.csv，可独立重算所有主对照、敏感度、月度年度收益和核验。所需Python依赖pandas、numpy、pyarrow。输入来源为之前保存的QQQ_SMH_Research_Checkpoint.zip、Green3of5_Backtest.zip；没有重选名单或改写原版排名。
'''
(R/'README.txt').write_text(text)
sens=p.loc[['SMH_positive','SMH_positive_zero_cash','SMH_nonnegative'],['CAGR','MDD','Sharpe','Sortino']].copy();sens['CAGR']=sens.CAGR.map(lambda x:f'{100*x:.3f}%');sens['MDD']=sens.MDD.map(lambda x:f'{100*x:.3f}%')
html='<!doctype html><meta charset="utf-8"><title>绝对动量过滤回测</title><style>body{font:16px system-ui;max-width:1250px;margin:36px auto;line-height:1.7}table{border-collapse:collapse;font-variant-numeric:tabular-nums}td,th{padding:8px;border:1px solid #ccc;text-align:right}th{background:#e8eff7}h1,h2{color:#183c5b}.wide{overflow:auto}</style><h1>个股Top 1：12–1M动量必须大于零</h1><p><b>QQQ完全不变；SMH收益改善，但最大回撤不变。只触发5个月，证据有限。</b></p>'+t.to_html()+'<h2>转现金的全部月份</h2>'+c.to_html(index=False)+'<h2>年度收益与年内回撤</h2><div class="wide">'+at.to_html()+'</div><h2>敏感度检查</h2>'+sens.to_html()+'<h2>规则、验证与限制</h2>'+''.join('<p>'+x+'</p>' for x in text.splitlines())+'<h2>逐月选择</h2>'+s[['fund','trade_month','name','asset','momentum','selected']].to_html(index=False)
(R/'Absolute_Momentum_Report.html').write_text(html)
(R/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2))
with zipfile.ZipFile(R.parent/'Absolute_Momentum_Backtest.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in R.iterdir():
  if f.is_file():z.write(f,f.name)
print(sens.to_string());print('ZIP bytes',(R.parent/'Absolute_Momentum_Backtest.zip').stat().st_size)
