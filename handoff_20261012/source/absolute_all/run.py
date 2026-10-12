from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent
s=pd.read_csv(R/'signals.csv');prices=pd.read_parquet(R/'prices.parquet');ref=pd.read_csv(R/'baseline.csv',index_col=0,parse_dates=True);ix=ref.index
rates=pd.read_csv(R/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
navs={};checks=[];chosen=[];trades=[]
for (fund,variant),g in s.groupby(['fund','variant']):
 for filt in [False,True]:
  name=fund+'_'+variant+('_absolute' if filt else '');g=g.copy();g['selected']=g.asset.where((g.momentum>0)|(not filt),'CASH');sig=g.set_index(pd.to_datetime(g.trade_date)).selected.to_dict()
  w=1.;cash=1.;qty=0.;old='CASH';prev=None;nav=[];other=[]
  if filt:chosen.extend(g.to_dict('records'))
  for dt in ix:
   if prev is not None:
    if old=='CASH':w*=1+rf.loc[dt];cash*=1+rf.loc[dt]
    else:
     q=prices[old].reindex([prev,dt]);assert q.notna().all(),(name,old,dt);w*=q.iloc[1]/q.iloc[0]
   new=sig.get(dt,old)
   if new!=old:
    if old!='CASH':w*=.999;cash=qty*prices.loc[dt,old]*.999
    if new!='CASH':w/=1.001;qty=cash/1.001/prices.loc[dt,new];cash=0.
    trades.append(dict(strategy=name,date=dt,sold=old,bought=new));old=new
   val=cash if old=='CASH' else qty*prices.loc[dt,old]
   if dt==ix[-1] and old!='CASH':w*=.999;val*=.999
   nav.append(w);other.append(val);prev=dt
  v=pd.Series(nav,index=ix);error=max(abs(v/np.array(other)-1));assert error<1e-10
  base_error=max(abs(v/ref[name]-1)) if not filt else np.nan
  if not filt:assert base_error<1e-10,(name,base_error)
  checks.append(dict(strategy=name,ledger_error=error,baseline_error=base_error));navs[name]=v
for f in ['QQQ','SMH']:navs[f+'_BH']=ref[f+'_BH']
v=pd.DataFrame(navs);v.to_csv(R/'daily_nav.csv');m=v.resample('ME').last().pct_change();m.iloc[0]=v.resample('ME').last().iloc[0]-1;m.to_csv(R/'monthly_returns.csv');full=m[m.index<=ix[-1]]
metrics=[]
for name,q in v.items():
 ret=q.pct_change();ret.iloc[0]=q.iloc[0]-1;ex=ret-rf;a=np.r_[1,q];f=name.split('_')[0]
 metrics.append(dict(strategy=name,CAGR=q.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,total_return=q.iloc[-1]-1,MDD=(a/np.maximum.accumulate(a)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*np.sqrt(252),Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*np.sqrt(252),monthly_win=(full[name]>full[f+'_BH']).mean()))
pd.DataFrame(metrics).to_csv(R/'performance.csv',index=False);pd.DataFrame(checks).to_csv(R/'validation.csv',index=False);pd.DataFrame(chosen).to_csv(R/'monthly_selections.csv',index=False);pd.DataFrame(trades).to_csv(R/'trades.csv',index=False)
a=[]
for yr,g in v.groupby(v.index.year):
 prev=v.loc[v.index<g.index[0]].iloc[-1] if (v.index<g.index[0]).any() else pd.Series(1.,index=v.columns)
 for name in v:
  q=np.r_[prev[name],g[name]];a.append(dict(year=yr,strategy=name,return_=q[-1]/q[0]-1,MDD=(q/np.maximum.accumulate(q)-1).min()))
pd.DataFrame(a).to_csv(R/'annual_returns_drawdown.csv',index=False)
print(pd.DataFrame(metrics).round(5).to_string(index=False));print('CASH');print(pd.DataFrame(chosen).groupby(['fund','variant']).apply(lambda g:pd.Series({'cash_months':int(g.selected.eq('CASH').sum()),'additional_cash':int((g.selected.eq('CASH')&g.asset.ne('CASH')).sum())}),include_groups=False).to_string())
