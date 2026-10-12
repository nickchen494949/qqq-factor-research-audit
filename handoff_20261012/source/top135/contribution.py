from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;B=R.parent
s=pd.read_csv(B/'qqq_smh_top1/results/monthly_signals.csv');p=pd.read_parquet(B/'qqq_smh_top1/metadata/trading_prices.parquet');d={t:g.set_index('date').sort_index().adjclose for t,g in p.groupby('asset')};ref=pd.read_csv(B/'qqq_smh_top1/results/daily_nav.csv',index_col=0,parse_dates=True);out=[];summary=[]
for f,g in s.groupby('fund'):
 a=g[g.asset.ne(g.asset.shift())].reset_index(drop=True)
 for i,r in a.iterrows():
  start=pd.Timestamp(r.trade_date);end=pd.Timestamp(a.iloc[i+1].trade_date) if i+1<len(a) else ref.index[-1];gross=d[r.asset].loc[end]/d[r.asset].loc[start]*.999/1.001
  out.append(dict(fund=f,asset=r.asset,permno=r.permno,start=str(start.date()),end=str(end.date()),net_return=gross-1,log_contribution=np.log(gross)))
 q=pd.DataFrame(out).query('fund==@f').sort_values('log_contribution',ascending=False);assert abs(np.exp(q.log_contribution.sum())/ref[f+'_close'].iloc[-1]-1)<1e-10
 T=((ref.index[-1]-ref.index[0]).days+1)/365.25
 for n in [0,1,3,5,10]:
  log=q.log_contribution.sum()-q.head(n).log_contribution.sum();summary.append(dict(fund=f,removed_best_episodes=n,CAGR=np.exp(log/T)-1,meaning='Ex post set selected episode net returns to zero; not tradable'))
a=pd.DataFrame(out);a.to_csv(R/'top1_episodes.csv',index=False);pd.DataFrame(summary).to_csv(R/'winner_dependence.csv',index=False);print(a.sort_values('log_contribution',ascending=False).groupby('fund').head(5).to_string(index=False));print(pd.DataFrame(summary).to_string(index=False))
