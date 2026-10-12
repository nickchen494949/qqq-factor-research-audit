from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
s=pd.read_csv(R/'signals.csv');ref=pd.read_csv(B/'qqq_smh_top1/results/daily_nav.csv',index_col=0,parse_dates=True);ix=ref.index
old=pd.read_parquet(B/'qqq_smh_top1/metadata/trading_prices.parquet');data={t:g.set_index('date').sort_index().adjclose for t,g in old.groupby('asset')}
y=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');yg={t:g.set_index('date').sort_index().adjclose for t,g in y.groupby('asset')}
c=pd.read_parquet(R/'crsp_history_daily.parquet');c['date']=pd.to_datetime(c.date);pg={int(n):g.set_index('date').sort_index() for n,g in c.groupby('permno')}
sources=[]
for r in s.itertuples():
 if r.asset=='CASH' or r.asset in data:continue
 if r.asset in yg:data[r.asset]=yg[r.asset];source='YAHOO'
 elif pd.notna(r.permno) and int(r.permno) in pg:
  d=pg[int(r.permno)];data[r.asset]=(1+d.ret).cumprod();source='CRSP'
 else:raise ValueError(('No prices',r.asset,r.permno))
 sources.append(dict(asset=r.asset,permno=r.permno,source=source))
rates=pd.read_csv(B/'qqq_smh_top1/metadata/DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2);rf=rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360
navs={};ledger=[];gaps=[]
for (fund,variant),g in s.groupby(['fund','variant']):
 sig=g.set_index(pd.to_datetime(g.trade_date)).asset.to_dict();wealth=1.;old='CASH';prev=None;nav=[]
 for dt in ix:
  if prev is not None:
   if old=='CASH':wealth*=1+rf.loc[dt]
   else:
    q=data[old].reindex([prev,dt]);
    if q.isna().any():gaps.append(dict(fund=fund,variant=variant,asset=old,date=str(dt.date())))
    wealth*=q.iloc[1]/q.iloc[0]
  new=sig.get(dt,old)
  if new!=old:
   if old!='CASH':wealth*=.999
   if new!='CASH':wealth/=1.001
   ledger.append(dict(fund=fund,variant=variant,date=str(dt.date()),sell=old,buy=new));old=new
  if dt==ix[-1] and old!='CASH':wealth*=.999
  nav.append(wealth);prev=dt
 navs[fund+'_'+variant]=pd.Series(nav,index=ix)
pd.DataFrame(gaps).to_csv(R/'price_gaps.csv',index=False)
if gaps:print(pd.DataFrame(gaps).to_string(index=False));raise ValueError('Cannot publish missing holding prices')
for f in ['SMH','QQQ']:
 navs[f+'_original']=ref[f+'_close']
navs['QQQ_BH']=ref.QQQ_BH_close
j=json.load(open(B/'economic_pool/raw/SMH.json'))['chart']['result'][0];p=pd.Series(j['indicators']['adjclose'][0]['adjclose'],index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()).reindex(ix);assert p.notna().all();v=p/p.iloc[0]/1.001;v.iloc[-1]*=.999;navs['SMH_BH']=v
v=pd.DataFrame(navs);assert v.notna().all().all();v.to_csv(R/'daily_nav.csv');m=v.resample('ME').last().pct_change();m.iloc[0]=v.resample('ME').last().iloc[0]-1;m.to_csv(R/'monthly_returns.csv');full=m.iloc[:-1]
metrics=[]
for label,q in v.items():
 ret=q.pct_change();ret.iloc[0]=q.iloc[0]-1;ex=ret-rf;a=np.r_[1,q.values];f=label.split('_')[0];bm=full[f+'_BH'];r=full[label];win=r>bm
 metrics.append(dict(strategy=label,CAGR=q.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,MDD=(a/np.maximum.accumulate(a)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*np.sqrt(252),Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*np.sqrt(252),monthly_outperform=win.mean(),monthly_positive=(r>0).mean(),terminal_multiple=q.iloc[-1]))
pd.DataFrame(metrics).to_csv(R/'performance.csv',index=False);pd.DataFrame(ledger).to_csv(R/'trades.csv',index=False);pd.DataFrame(sources).to_csv(R/'new_price_sources.csv',index=False)
# Freeze only the actually selected total-return series, including baseline assets.
used=set(s.asset)-{'CASH'};pd.DataFrame({t:data[t].reindex(ix) for t in used}).to_parquet(R/'selected_daily_prices.parquet')
print(pd.DataFrame(metrics).to_string(index=False));print('NEW SOURCES',sources)
