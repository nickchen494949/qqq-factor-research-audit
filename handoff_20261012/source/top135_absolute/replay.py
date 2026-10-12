from pathlib import Path
import pandas as pd,numpy as np
from itertools import product
R=Path(__file__).resolve().parent;B=R.parent
s=pd.read_csv(R/'selection.csv');p=pd.read_parquet(R/'prices_events.parquet');cf=pd.read_parquet(R/'cost_fraction.parquet');ev=pd.read_csv(R/'events.csv');ref=pd.read_csv(R/'baseline_input.csv',index_col=0,parse_dates=True);ix=ref.index;p=p.reindex(ix);cols=list(p);prices=p.to_numpy();ratios=p.pct_change(fill_method=None).to_numpy()+1
rates=pd.read_csv(R/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
enddates={r.asset:pd.Timestamp(r.date) for r in ev.itertuples()};out={};valid=[];led=[];held=[]
for f,n,positive in product(['QQQ','SMH'],[1,3,5],[False,True]):
 if True:
  label=f+'_top'+str(n)+('_absolute' if positive else '');sig={pd.Timestamp(dt):g.head(n) for dt,g in s[s.fund.eq(f)].sort_values(['date','rank']).groupby('date')};values=np.zeros(len(cols));cash=1.;qty=np.zeros(len(cols));cash2=1.;nav=[];nav2=[]
  for i,dt in enumerate(ix):
   active=values!=0
   if i:
    assert np.isfinite(ratios[i,active]).all(),(label,dt,np.array(cols)[active]);values[active]*=ratios[i,active];cash*=1+rf.iloc[i];cash2*=1+rf.iloc[i]
   if dt in sig:
    weight=np.zeros(len(cols));cw=0.
    for r in sig[dt].itertuples():
     if r.asset in enddates and dt>=enddates[r.asset]:cw+=1/n;selected='CASH_UNTRADEABLE'
     elif positive and r.momentum<=0:cw+=1/n;selected='CASH_NONPOSITIVE'
     else:weight[cols.index(r.asset)]+=1/n;selected=r.asset
     held.append(dict(strategy=label,date=dt,rank=r.rank,momentum=r.momentum,name=r.name,ranked_asset=r.asset,selected=selected,weight=1/n))
    total=values.sum()+cash;costrate=.001*cf.loc[dt].to_numpy();lo=total*.997;hi=total
    for _ in range(50):
     mid=(lo+hi)/2;fee=np.sum(costrate*np.abs(weight*mid-values))
     if mid+fee>total:hi=mid
     else:lo=mid
    net=(lo+hi)/2;target=net*weight;delta=target-values;fee=np.sum(costrate*np.abs(delta));assert abs(total-net-fee)<max(1,total)*1e-12
    cash2-=delta.sum()+fee
    mask=weight>0;assert np.isfinite(prices[i,mask]).all();qty[:]=0;qty[mask]=target[mask]/prices[i,mask];values=target;cash=cw*net
    assert abs(cash2-cash)<max(1,total)*1e-10
    for j in np.where(abs(delta)>total*1e-12)[0]:led.append(dict(strategy=label,date=dt,asset=cols[j],dollars=delta[j],fee=costrate[j]*abs(delta[j])))
   v=values.sum()+cash;v2=np.nansum(qty*prices[i])+cash2
   if dt==ix[-1]:fee=np.sum(.001*cf.loc[dt].to_numpy()*values);v-=fee;v2-=fee
   nav.append(v);nav2.append(v2)
  v=pd.Series(nav,index=ix);err=max(abs(v/np.array(nav2)-1));assert err<1e-9
  baserr=max(abs(v/ref[f+'_original']-1)) if n==1 and not positive else np.nan
  if n==1 and not positive:assert baserr<1e-9,(label,baserr)
  valid.append(dict(strategy=label,independent_ledger_error=err,baseline_error=baserr));out[label]=v
for f in ['QQQ','SMH']:out[f+'_BH']=ref[f+'_BH']
v=pd.DataFrame(out);v.to_csv(R/'daily_nav.csv');m=v.resample('ME').last().pct_change();m.iloc[0]=v.resample('ME').last().iloc[0]-1;m.to_csv(R/'monthly_returns.csv');fm=m[m.index<=ix[-1]];metrics=[]
for name,q in v.items():
 ret=q.pct_change();ret.iloc[0]=q.iloc[0]-1;ex=ret-rf;a=np.r_[1,q];f=name.split('_')[0];r=dict(strategy=name,CAGR=q.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,total_return=q.iloc[-1]-1,MDD=(a/np.maximum.accumulate(a)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*np.sqrt(252),Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*np.sqrt(252),monthly_win=(fm[name]>fm[f+'_BH']).mean())
 for n in [36,60]:
  diff=(1+fm[name]).rolling(n).apply(np.prod,raw=True)-(1+fm[f+'_BH']).rolling(n).apply(np.prod,raw=True);r[f'rolling_{n}m_win']=(diff.dropna()>0).mean()
 metrics.append(r)
pd.DataFrame(metrics).to_csv(R/'performance.csv',index=False);pd.DataFrame(valid).to_csv(R/'validation.csv',index=False);pd.DataFrame(held).to_csv(R/'holdings.csv',index=False);pd.DataFrame(led).to_csv(R/'trades.csv',index=False);print(pd.DataFrame(metrics).round(5).to_string(index=False))
