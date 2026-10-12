from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent
s=pd.read_csv(R/'monthly_audit.csv');p=pd.read_parquet(R/'prices.parquet');d={a:g.set_index('date').sort_index().adjclose for a,g in p.groupby('asset')};ref=pd.read_csv(R/'reference_nav.csv',index_col=0,parse_dates=True);ix=ref.index
rates=pd.read_csv(R/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
navs={};chosen=[];trades=[];controls=[]
for fund,g in s.groupby('fund'):
 for rule in ['original','unknown_keep','unknown_cash']:
  a=g.copy();a['selected']=a.asset.where((rule=='original')|a.filter_status.eq('pass')|((rule=='unknown_keep')&a.filter_status.eq('unknown')),'CASH');sig=a.set_index(pd.to_datetime(a.trade_date)).selected.to_dict();wealth=1.;old='CASH';prev=None;nav=[];qty=0.;cash=1.;nav2=[]
  if rule!='original':a['rule']=rule;chosen.extend(a.to_dict('records'))
  for dt in ix:
   interest=rf.loc[dt] if rule!='positive_zero_cash' else 0.
   if prev is not None:
    if old=='CASH':wealth*=1+interest;cash*=1+interest
    else:
     prices=d[old].reindex([prev,dt]);assert prices.notna().all(),(fund,rule,old,dt);wealth*=prices.iloc[1]/prices.iloc[0]
   new=sig.get(dt,old)
   if new!=old:
    if old!='CASH':wealth*=.999;cash=qty*d[old].loc[dt]*.999
    if new!='CASH':wealth/=1.001;qty=cash/1.001/d[new].loc[dt];cash=0.
    if rule!='original':trades.append(dict(fund=fund,rule=rule,date=dt,sold=old,bought=new))
    old=new
   second=cash if old=='CASH' else qty*d[old].loc[dt]
   if dt==ix[-1] and old!='CASH':wealth*=.999;second*=.999
   assert np.isfinite(wealth);nav.append(wealth);nav2.append(second);prev=dt
  v=pd.Series(nav,index=ix);err=max(abs(v/np.array(nav2)-1));assert err<1e-10
  if rule=='original':baseline_err=max(abs(v/ref[fund+'_original']-1));assert baseline_err<1e-10
  else:baseline_err=np.nan
  controls.append(dict(strategy=fund+'_'+rule,two_ledger_error=err,baseline_error=baseline_err));navs[fund+'_'+rule]=v
for fund in ['QQQ','SMH']:navs[fund+'_BH']=ref[fund+'_BH']
v=pd.DataFrame(navs);v.to_csv(R/'daily_nav.csv');m=v.resample('ME').last().pct_change();m.iloc[0]=v.resample('ME').last().iloc[0]-1;m.to_csv(R/'monthly_returns.csv');full=m[m.index<=ix[-1]]
metrics=[]
for k,q in v.items():
 ret=q.pct_change();ret.iloc[0]=q.iloc[0]-1;ex=ret-rf;arr=np.r_[1,q];fund=k.split('_')[0];row=dict(strategy=k,CAGR=q.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,total_return=q.iloc[-1]-1,MDD=(arr/np.maximum.accumulate(arr)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*np.sqrt(252),Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*np.sqrt(252),monthly_win_rate=(full[k]>full[fund+'_BH']).mean())
 for n in [36,60]:
  a=(1+full[k]).rolling(n).apply(np.prod,raw=True);b=(1+full[fund+'_BH']).rolling(n).apply(np.prod,raw=True);valid=a.notna()&b.notna();row[f'rolling_{n}m_win_rate']=(a[valid]>b[valid]).mean()
 metrics.append(row)
pd.DataFrame(metrics).to_csv(R/'performance.csv',index=False);pd.DataFrame(chosen).to_csv(R/'monthly_selections.csv',index=False);pd.DataFrame(trades).to_csv(R/'trades.csv',index=False);pd.DataFrame(controls).to_csv(R/'validation.csv',index=False)
annual=[]
for yr,g in v.groupby(v.index.year):
 prev=v.loc[v.index<g.index[0]].iloc[-1] if (v.index<g.index[0]).any() else pd.Series(1.,index=v.columns)
 for k in v:
  a=np.r_[prev[k],g[k]];annual.append(dict(year=yr,strategy=k,return_=a[-1]/a[0]-1,MDD=(a/np.maximum.accumulate(a)-1).min()))
pd.DataFrame(annual).to_csv(R/'annual_comparison.csv',index=False)
print(pd.DataFrame(metrics).round(4).to_string(index=False))
