from pathlib import Path
import pandas as pd,zipfile,json,hashlib
R=Path(__file__).resolve().parent
p=pd.read_csv(R/'performance.csv').set_index('strategy');s=pd.read_csv(R/'monthly_selections.csv');labels={'original':'原版','five_year_history':'个股五年历史','green3of5':'个股五年中至少三年上涨','relative_green':'个股上涨次数不低于ETF'};rows=[]
for f in ['QQQ','SMH']:
 for rule,label in labels.items():
  a=p.loc[f+'_'+rule];b=p.loc[f+'_'+rule+'_absolute'];g=s[(s.fund==f)&(s.variant==rule)]
  rows.append({'股票池':f,'个股规则':label,'年化：前→后':f'{100*a.CAGR:.2f}% → {100*b.CAGR:.2f}%','最大回撤：前→后':f'{100*a.MDD:.2f}% → {100*b.MDD:.2f}%','Sharpe：前→后':f'{a.Sharpe:.3f} → {b.Sharpe:.3f}','Sortino：前→后':f'{a.Sortino:.3f} → {b.Sortino:.3f}','新增现金月份':int((g.selected.eq('CASH')&g.asset.ne('CASH')).sum())})
t=pd.DataFrame(rows);t.to_csv(R/'paired_comparison.csv',index=False)
notes='''测试期间2009-01-02至2026-10-09，月末信号，次月首交易日收盘成交。各池内先执行对应个股资格过滤，再用12–1M总回报动量选第一名，动量严格>0才持有，否则现金。不使用ETF自身动量做择时。月度正常卖出盈利和亏损持仓。
八条原版均独立重跑，与先前冻结净值误差<1e-10；每条新增过滤策略也分别使用收益累计和股数现金两套账本核对。全部实际持仓日价格完整，年末收益统计只使用当时已结束年度。与此前持仓名单、排名和价格同口径，没有追加择时条件。
每次实际买卖单边成本0.1%，结束时清仓0.1%。现金利息代理采用滞后2日DFF/360；不是某只真实现金基金。含股息、拆股，不含税。月度跑赢率只取213个完整统计月份至2026年9月，2026年10月收益截至9日。最大回撤为日末净值，年度表按每年年初重设回撤起点。
关键结果：QQQ四组均从未因动量<=0而转现金，收益回撤完全不变。SMH四组收益和Sharpe改善，但最大回撤全部不变；固定3/5组原先已有12个月现金，绝对动量额外增加2个月。其他SMH组各额外增加5个月。新增交易次数很少，不能视为稳健样本外证据。
边界：严格>0意味着恰好0也转现金。原版SMH在2022年12月的ON信号恰好0（2021-11月底和2022-10月底复权价相同），因此被排除。上轮已保存零利息、允许零动量的敏感度，主规则不依据敏感度结果改变。
研究限制：沿用早期披露滞后的持仓名单，不是完全精确逐月指数成分；SMH含HOLDRS前身及2012初始两月发行前指数代理；部分早期行情来自CRSP公开镜像，原有少量跨源差异仍在。两套记账吻合不证明原始数据与身份完全可靠。没有真正未来样本外验证。
复现：run.py读取本包signals.csv、prices.parquet、baseline.csv、DFF.csv，独立复算16条策略和2条ETF对照。依赖pandas、numpy、pyarrow。输入源来自前期QQQ_SMH_Research_Checkpoint.zip、Green3of5_Backtest.zip、Relative_Green_Backtest.zip。
'''
(R/'README.txt').write_text(notes)
cash=s[(s.selected=='CASH')&(s.asset!='CASH')]
html='<!doctype html><meta charset="utf-8"><title>绝对动量：四组个股规则完整比较</title><style>body{font:16px system-ui;max-width:1300px;margin:35px auto;line-height:1.6}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ccc;text-align:right}th{background:#e8eef5}h1,h2{color:#234569}</style><h1>绝对动量过滤：两只ETF股票池 × 四组个股规则</h1><p><b>QQQ四组不变；SMH四组收益提高，但最大回撤没有改善。</b></p>'+t.to_html(index=False)+'<h2>规则和限制</h2>'+''.join('<p>'+line+'</p>' for line in notes.splitlines())+'<h2>所有新增转现金信号</h2>'+cash[['fund','variant','trade_month','asset','momentum']].to_html(index=False)+'<h2>完整绩效</h2>'+p.to_html()
(R/'Absolute_All_Report.html').write_text(html)
(R/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2))
with zipfile.ZipFile(R.parent/'Absolute_Momentum_All_Variants.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in R.iterdir():
  if f.is_file():z.write(f,f.name)
print('ZIP bytes',(R.parent/'Absolute_Momentum_All_Variants.zip').stat().st_size)
