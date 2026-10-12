from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;B=R.parent
s=pd.read_csv(R/'signals.csv');v=pd.read_csv(R/'daily_nav.csv',index_col=0,parse_dates=True);p=pd.read_parquet(R/'selected_daily_prices.parquet');ix=v.index
rates=pd.read_csv(R/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
checks=[]
for (fund,variant),g in s.groupby(['fund','variant']):
 sig=g.set_index(pd.to_datetime(g.trade_date)).asset.to_dict();old='CASH';cash=1.;qty=0.;nav=[]
 for dt in ix:
  if old=='CASH':cash*=1+rf.loc[dt]
  new=sig.get(dt,old)
  if new!=old:
   if old!='CASH':cash=qty*p.loc[dt,old]*.999
   if new!='CASH':qty=cash/1.001/p.loc[dt,new];cash=0
   old=new
  wealth=cash if old=='CASH' else qty*p.loc[dt,old]
  if dt==ix[-1] and old!='CASH':wealth*=.999
  nav.append(wealth)
 err=np.max(np.abs(np.array(nav)/v[fund+'_'+variant]-1));assert err<1e-10;checks.append(dict(strategy=fund+'_'+variant,max_nav_error=err))
 assert (g.trade_month.str[:4].astype(int)>pd.to_datetime(g.trade_date).dt.year-1).all()
 assert (g.loc[g.variant.eq('green3of5')&g.asset.ne('CASH'),'green_years']>=3).all()
pd.DataFrame(checks).to_csv(R/'accounting_validation.csv',index=False)

print(pd.DataFrame(checks).to_string(index=False))
