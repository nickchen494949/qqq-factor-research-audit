from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
v=pd.read_csv(R/'input_daily_nav.csv',index_col=0,parse_dates=True)
m=v.resample('ME').last().pct_change();m.iloc[0]=v.resample('ME').last().iloc[0]-1
m['partial']=m.index>v.index[-1];full=m[~m.partial].copy()
rows=[];annual=[]
for f in ['SMH','QQQ']:
 a=full[f+'_close'];b=full[f+'_BH_close'];ex=a-b;win=ex>1e-12
 runs=[];start=None
 for dt,lose in (~win).items():
  if lose and start is None:start=dt
  if not lose and start is not None:runs.append((len(ex.loc[start:dt])-1,str(start.date())[:7],str(ex.loc[:dt].index[-2].date())[:7]));start=None
 if start is not None:runs.append((len(ex.loc[start:]),str(start.date())[:7],str(ex.index[-1].date())[:7]))
 row=dict(fund=f,months=len(a),wins=int(win.sum()),win_rate=win.mean(),positive_rate=(a>0).mean(),benchmark_positive_rate=(b>0).mean(),mean_excess=ex.mean(),median_excess=ex.median(),longest_losing_streak=max(runs),worst_month=str(ex.idxmin().date())[:7],worst_excess=ex.min(),best_month=str(ex.idxmax().date())[:7],best_excess=ex.max())
 for n in [12,36,60]:
  diff=(1+a).rolling(n).apply(np.prod,raw=True)-(1+b).rolling(n).apply(np.prod,raw=True);diff=diff.dropna();row[f'rolling_{n}m_wins']=int((diff>0).sum());row[f'rolling_{n}m_n']=len(diff);row[f'rolling_{n}m_rate']=(diff>0).mean()
 for year,g in full.groupby(full.index.year):
  ar=(1+g[f+'_close']).prod()-1;br=(1+g[f+'_BH_close']).prod()-1
  annual.append(dict(fund=f,year=year,months=len(g),top1=ar,benchmark=br,outperformance=ar-br,months_won=int((g[f+'_close']>g[f+'_BH_close']).sum())))
 rows.append(row)
print(json.dumps(rows,indent=2));print(pd.DataFrame(annual).to_string(index=False))
m['SMH_excess']=m.SMH_close-m.SMH_BH_close;m['QQQ_excess']=m.QQQ_close-m.QQQ_BH_close
m.to_csv(R/'monthly_returns.csv');pd.DataFrame(annual).to_csv(R/'annual_comparison.csv',index=False);(R/'summary.json').write_text(json.dumps(rows,indent=2))
# Each month's return uses calendar-month boundaries; first month starts January 2 close.
cols=['SMH_close','SMH_BH_close','SMH_excess','QQQ_close','QQQ_BH_close','QQQ_excess']
t=m[cols].map(lambda x:f'{x*100:.2f}%');t.index=t.index.strftime('%Y-%m');t.loc['2026-10',:]=t.loc['2026-10',:].astype(str)+' *'
a=pd.DataFrame(annual);af=a.copy()
for c in ['top1','benchmark','outperformance']:af[c]=af[c].map(lambda x:f'{100*x:.2f}%')
html='''<!doctype html><meta charset="utf-8"><title>Top 1 每月一致性检验</title><style>body{font:16px system-ui;max-width:1150px;margin:40px auto;line-height:1.6}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}td,th{border:1px solid #ccc;padding:7px;text-align:right}th{background:#eaf0f7}h1,h2{color:#17385a}</style><h1>SMH / QQQ Top 1：每月是否稳定跑赢？</h1><p>2009-01-02 至 2026-10-09，12–1M 动量，次月首个交易日收盘成交，单边成本0.1%，分红再投资。主要统计使用截至2026年9月的213个完整日历月；2009年1月从首个交易日收盘起算。2026年10月仅截至9日，不纳入月度及滚动胜率。跑赢 = Top 1 当月收益高于对应ETF，并不等于当月赚钱。</p><p>限制：2009–2011 SMH含旧HOLDRS衔接；早期选股池为有披露滞后的已公布名单。此为原有研究结果的统计检查，不修复其历史成分数据限制。滚动窗口互相重叠，不能当作独立样本。所有结果均为回顾性，不能证明未来胜率。</p>'''
html+='<h2>一致性统计</h2><pre>'+json.dumps(rows,ensure_ascii=False,indent=2)+'</pre><h2>逐年对比（2026仅1–9月）</h2>'+af.to_html(index=False)+'<h2>逐月收益（* 为不完整月份）</h2>'+t.to_html()+'<p>来源：先前冻结回测 daily_nav.csv；SMH Yahoo Chart 已缓存复权收盘价。原始输入、复算代码及明细随附。</p>'
(R/'Top1_Monthly_Consistency.html').write_text(html)
# Freeze exact input subset for audit.
v.to_csv(R/'input_daily_nav.csv')
