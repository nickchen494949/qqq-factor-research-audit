from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;O=R/'results';M=R/'metadata'
s=pd.read_csv(O/'monthly_signals.csv');d=pd.read_parquet(M/'trading_prices.parquet');data={t:g.set_index('date').sort_index() for t,g in d.groupby('asset')};reference=pd.read_csv(O/'daily_nav.csv',index_col=0,parse_dates=True);ix=reference.index
rates=pd.read_csv(M/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2)
out=[]
for label in reference:
 f,execution=label.rsplit('_',1);a=s[s.fund.eq(f)];sig=a.set_index(pd.to_datetime(a.trade_date)).asset.to_dict() if not f.endswith('_BH') else {ix[0]:f[:-3]};qty=0.;cash=1.;old='CASH';nav=[]
 for dt in ix:
  new=sig.get(dt,old)
  if new!=old:
   key='adjopen' if execution=='open' else 'adjclose'
   if old!='CASH':cash=qty*data[old].loc[dt,key]*.999
   qty=cash/1.001/data[new].loc[dt,key];old=new
  val=qty*data[old].loc[dt,'adjclose'];nav.append(val*.999 if dt==ix[-1] else val)
 v=pd.Series(nav,index=ix);error=float(np.max(np.abs(v/reference[label]-1)));assert error<1e-10
 ret=v.pct_change();ret.iloc[0]=v.iloc[0]-1;ex=ret-rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360;a=np.r_[1,v.to_numpy()]
 out.append(dict(strategy=label,CAGR=v.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,MDD=(a/np.maximum.accumulate(a)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*252**.5,Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*252**.5,max_nav_error=error))
print(pd.DataFrame(out).to_string(index=False))
