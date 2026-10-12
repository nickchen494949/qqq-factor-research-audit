from pathlib import Path
import pandas as pd,numpy as np,json,exchange_calendars as xc
R=Path(__file__).resolve().parent;B=R.parent;M=R/'metadata';O=R/'results'
s=pd.read_csv(O/'monthly_selection_audit.csv');assert len(s)==428 and s.n_blocked.sum()==0
aliases={81138:'APOL',90805:'DISCA',77281:'WFM',91277:'LINTA',87299:'AKAM',79588:'GMCR',78875:'CREE',75577:'ALTR',85961:'ARM_OLD'}
s['asset']=[aliases.get(int(r.permno),r.ticker) if pd.notna(r.permno) and r.trade_month<'2020' else r.ticker for r in s.itertuples()]
assert s.asset.notna().all();s.to_csv(O/'monthly_signals.csv',index=False)
data={t:g.set_index('date').sort_index() for t,g in pd.read_parquet(B/'full_2009/trading_prices.parquet').groupby('asset')}
for t,g in pd.read_parquet(M/'yahoo_daily.parquet').groupby('asset'):data[t]=g.set_index('date').sort_index()
W=pd.read_parquet(M/'wiki_extra.parquet')
wi=pd.read_parquet(M/'wiki_identity_prices.parquet');a=wi[wi.ticker.eq('SIRI')].copy();a['date']=pd.to_datetime(a.date);data['SIRI']=a.rename(columns={'adj_open':'adjopen','adj_close':'adjclose'}).set_index('date')
for t in set(s.asset)-set(data):
 wt='SNDK' if t=='SNDK_OLD' else t;g=W[W.ticker.eq(wt)].copy()
 if len(g):g['date']=pd.to_datetime(g.date);data[t]=g.rename(columns={'adj_open':'adjopen','adj_close':'adjclose'}).set_index('date')
for t in ['CERN','XLNX']:
 f=R/'raw_prices'/f'{t}_jacksoncrow.csv'
 if f.exists():
  g=pd.read_csv(f,parse_dates=['Date']).rename(columns={'Date':'date','Open':'open','Close':'close','Adj Close':'adjclose'}).set_index('date');g['adjopen']=g.open*g.adjclose/g.close;data[t]=g
f=R/'raw_prices/CERN_wiki.csv'
if f.exists():data['CERN']=pd.read_csv(f,parse_dates=['date']).rename(columns={'adj_open':'adjopen','adj_close':'adjclose'}).set_index('date')
# ARM's old ADR has daily total returns but no verified opens. Never invent them.
for n,label in [(85961,'ARM_OLD'),(48267,'LSI')]:
 p=pd.read_parquet(B/'full_2009/crsp_allcodes_daily_2007_2019.parquet',filters=[('permno','=',n)]);p['date']=pd.to_datetime(p.date);p=p.set_index('date').sort_index();p['ret']=pd.to_numeric(p.ret,errors='coerce');p=p[p.prc.notna()];p['adjclose']=(1+p.ret).cumprod();p['close']=p.prc.abs();p['open']=np.nan;p['adjopen']=np.nan;data[label]=p
cal=xc.get_calendar('XNYS',start='2006-01-01',end='2026-12-31');ix=cal.sessions_in_range('2009-01-02','2026-10-09');start=ix[0];end=ix[-1]
rates=pd.read_csv(B/'economic_pool/raw/DFF.csv',index_col=0,parse_dates=True).iloc[:,0].astype(float)/100;rates=rates.reindex(pd.date_range(rates.index.min(),end)).ffill().shift(2)
signals={fund:g.assign(dt=pd.to_datetime(g.trade_date)).set_index('dt').asset.to_dict() for fund,g in s.groupby('fund')}
coverage=[]
for fund,sig in signals.items():
 old='CASH'
 for i,dt in enumerate(ix):
  new=sig.get(dt,old)
  for t in set([old,new])-{'CASH'}:
   if t not in data or dt not in data[t].index:coverage.append(dict(fund=fund,date=str(dt.date()),asset=t,missing='DAILY_QUOTE'))
   elif dt in sig and t!=old or dt in sig and new!=old:
    if pd.isna(data[t].loc[dt,'adjopen']):coverage.append(dict(fund=fund,date=str(dt.date()),asset=t,missing='EXECUTION_OPEN'))
  old=new
pd.DataFrame(coverage).to_csv(O/'execution_coverage.csv',index=False)
assert not [x for x in coverage if x['missing']=='DAILY_QUOTE'],coverage
def replay(fund,execution='close',cost=.001):
 sig=signals.get(fund,{ix[0]:fund});wealth=1.;old='CASH';prev=None;nav=[];ledger=[]
 for dt in ix:
  new=sig.get(dt,old);rebalance=new!=old
  if execution=='open':
   if old!='CASH':wealth*=data[old].loc[dt,'adjopen']/data[old].loc[prev,'adjclose']
   if rebalance:
    before=wealth
    if old!='CASH':wealth*=1-cost
    wealth/=1+cost;ledger.append(dict(date=str(dt.date()),old=old,new=new,cost=before-wealth));old=new
   wealth*=data[old].loc[dt,'adjclose']/data[old].loc[dt,'adjopen']
  else:
   if old!='CASH':wealth*=data[old].loc[dt,'adjclose']/data[old].loc[prev,'adjclose']
   if rebalance:
    before=wealth
    if old!='CASH':wealth*=1-cost
    wealth/=1+cost;ledger.append(dict(date=str(dt.date()),old=old,new=new,cost=before-wealth));old=new
  if dt==end:wealth*=1-cost
  assert np.isfinite(wealth) and wealth>0,(fund,execution,dt,old,wealth)
  nav.append(wealth);prev=dt
 return pd.Series(nav,index=ix),ledger
def metric(v):
 ret=v.pct_change();ret.iloc[0]=v.iloc[0]-1;gaps=v.index.to_series().diff().dt.days.fillna(0);ex=ret-rates.reindex(v.index)*gaps/360;assert ex.notna().all();a=np.r_[1,v.to_numpy()];dd=a/np.maximum.accumulate(a)-1
 return dict(start=str(start.date()),end=str(end.date()),CAGR=v.iloc[-1]**(365.25/((end-start).days+1))-1,MDD=dd.min(),Sharpe=ex.mean()/ex.std(ddof=1)*252**.5,Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*252**.5,multiple=v.iloc[-1])
navs={};metrics=[];led=[]
for execution,funds in [('close',['QQQ','SMH','QQQ_BH','SPY_BH']),('open',['QQQ','QQQ_BH','SPY_BH'])]:
 for f in funds:
  if f.endswith('_BH'):signals[f]={ix[0]:f[:-3]}
  v,l=replay(f,execution);label=f+'_'+execution;navs[label]=v;metrics.append(dict(strategy=label,**metric(v)));led.extend(dict(strategy=label,**r) for r in l)
pd.DataFrame(navs).to_csv(O/'daily_nav.csv');pd.DataFrame(metrics).to_csv(O/'performance.csv',index=False);pd.DataFrame(led).to_csv(O/'trade_ledger.csv',index=False)
out=[]
for t,d in data.items():
 if t in set(s.asset)|{'QQQ','SPY'}:
  a=d[['open','close','adjopen','adjclose']].copy();a['asset']=t;out.append(a.reset_index())
pd.concat(out,ignore_index=True).to_parquet(M/'trading_prices.parquet',index=False)
print(pd.DataFrame(metrics).to_string(index=False));print('OPEN GAPS',coverage)
