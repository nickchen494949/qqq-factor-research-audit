from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;B=R.parent
s=pd.read_csv(R/'signals.csv');v=pd.read_csv(R/'daily_nav.csv',index_col=0,parse_dates=True);p=pd.read_parquet(R/'selected_daily_prices.parquet');ix=v.index
rates=pd.read_csv(B/'qqq_smh_top1/metadata/DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
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
# Actual held-day return comparison for all newly introduced Yahoo assets vs independent CRSP.
a=pd.read_csv(R/'new_price_sources.csv');c=pd.read_parquet(R/'crsp_history_daily.parquet');c['date']=pd.to_datetime(c.date);disc=[]
for row in a[a.source.eq('YAHOO')].itertuples():
 d=c[c.permno.eq(int(row.permno))].set_index('date').ret;ret=p[row.asset].pct_change(fill_method=None)
 for (fund,variant),g in s.groupby(['fund','variant']):
  held=g.set_index(pd.to_datetime(g.trade_date)).asset.reindex(ix).ffill().shift(1).eq(row.asset)
  comp=pd.DataFrame({'primary':ret[held],'crsp':d}).dropna();bad=comp[(comp.primary-comp.crsp).abs()>.005]
  for dt,r in bad.iterrows():disc.append(dict(asset=row.asset,date=str(dt.date()),fund=fund,variant=variant,primary=r.primary,crsp=r.crsp))
pd.DataFrame(disc).to_csv(R/'new_source_discrepancies.csv',index=False)
print('Independent accounting',checks);print('New source discrepancies >0.5pp',disc)
# Paired annual returns and period sensitivity, same dates per row.
m=pd.read_csv(R/'monthly_returns.csv',index_col=0,parse_dates=True);annual=(1+m).groupby(m.index.year).prod()-1;annual.to_csv(R/'annual_returns.csv')
rows=[]
for end in ['2019-12-31','2025-12-31','2026-10-09']:
 q=v.loc[:end]
 for name in v:rows.append(dict(end=end,strategy=name,CAGR=q[name].iloc[-1]**(365.25/((q.index[-1]-q.index[0]).days+1))-1))
pd.DataFrame(rows).to_csv(R/'endpoint_sensitivity.csv',index=False)
