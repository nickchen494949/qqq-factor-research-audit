"""Daily-reset hypothetical leverage of a frozen ETF pool, not real fund history."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
exec(compile((BASE/'backtest.py').read_text().split('results={};ledger=[]')[0],str(BASE/'backtest.py'),'exec'))
OUT=BASE/'leverage_results';OUT.mkdir(exist_ok=True)
ORIG_C=C.copy();ORIG_O=O.copy();ORIG_MOM=MOM.copy()
RATE=pd.read_csv(BASE/'raw/DFF.csv',index_col=0,parse_dates=True).iloc[:,0].astype(float)/100
def synthetic(L,spread=.005,extra_fee=.009):
 c=ORIG_C.loc['2000-01-01':];o=ORIG_O.reindex(c.index)
 if L==1:return c.copy(),o.copy()
 rate=RATE.reindex(pd.date_range(RATE.index[0],c.index[-1],freq='D')).ffill().shift(2).reindex(c.index).ffill()
 assert rate.iloc[1:].notna().all()
 days=c.index.to_series().diff().dt.days.fillna(1).to_numpy()
 charge=(L-1)*(rate.to_numpy()+spread)*days/360+extra_fee*days/365.25
 close_factor=1+L*(c/c.shift()-1)-charge[:,None]
 open_factor=1+L*(o/c.shift()-1)-charge[:,None]
 cv=close_factor.to_numpy();ov=open_factor.to_numpy();cc=c.to_numpy();oo=o.to_numpy()
 sc=np.full_like(cc,np.nan);so=np.full_like(cc,np.nan)
 for j in range(len(SYMS)):
  first=np.flatnonzero(np.isfinite(cc[:,j]))[0]
  sc[first,j]=100.;so[first,j]=100.*oo[first,j]/cc[first,j]
  assert np.nanmin(cv[first+1:,j])>0 and np.nanmin(ov[first+1:,j])>0,(SYMS[j],L,'bankruptcy requires explicit handling')
  for i in range(first+1,len(c)):
   sc[i,j]=sc[i-1,j]*cv[i,j];so[i,j]=sc[i-1,j]*ov[i,j]
 return pd.DataFrame(sc,index=c.index,columns=SYMS),pd.DataFrame(so,index=c.index,columns=SYMS)
def setup(start,cc,oo,mm):
 global C,O,MOM,IX,CV,OV,REBAL
 C=cc;O=oo;MOM=mm;IX=C.loc[start:END].index;CV=C.loc[IX].to_numpy();OV=O.loc[IX].to_numpy()
 REBAL={i:dt for i,dt in enumerate(IX) if i==0 or dt.month!=IX[i-1].month}
def stats(v,logs):
 z=pd.concat([pd.Series([1.],index=[v.index[0]-pd.Timedelta(days=1)]),v])
 opens=np.array([a['nav_open_before'] for a in logs]+[v.iloc[-1]])
 rr=opens[1:]/opens[:-1]-1;w=rr[rr>0];loss=rr[rr<0]
 d=metrics(z);d.update(monthly_win_rate=len(w)/len(rr),avg_win=w.mean(),avg_loss=loss.mean(),payoff=w.mean()/abs(loss.mean()),worst_month=rr.min())
 return d
summary=[];navs={};ledger=[];syn={}
for L in [1,2,3]:
 cc,oo=synthetic(L);syn[L]=(cc,oo)
 for signal in (['base'] if L==1 else ['base','leveraged']):
  mc=cc.resample('ME').last();mm=ORIG_MOM if signal=='base' else mc.shift(1)/mc.shift(12)-1
  for start in ['2005-01-03','2017-02-01']:
   setup(start,cc,oo,mm)
   for k in [1,3]:
    name=f'L{L}_{signal}_Top{k}_{start}'
    v,l=run(name,POOL,k,60,.001)
    summary.append(dict(strategy=name,L=L,signal=signal,k=k,start=start,**stats(v,l)));navs[name]=v;ledger+=l
# Sensitivity to a wider financing spread and annual overlay cost; unchanged signal rule.
for L in [2,3]:
 cc,oo=synthetic(L,spread=.02,extra_fee=.014)
 for signal in ['base','leveraged']:
  mc=cc.resample('ME').last();mm=ORIG_MOM if signal=='base' else mc.shift(1)/mc.shift(12)-1
  setup('2005-01-03',cc,oo,mm)
  for k in [1,3]:
   name=f'L{L}_{signal}_Top{k}_higher_cost'
   v,l=run(name,POOL,k,60,.001)
   summary.append(dict(strategy=name,L=L,signal=signal,k=k,start='2005-01-03',**stats(v,l)))
summary=pd.DataFrame(summary);summary.to_csv(OUT/'summary.csv',index=False)
pd.DataFrame(navs).to_csv(OUT/'daily_nav.csv');pd.DataFrame(ledger).to_csv(OUT/'holdings.csv',index=False)
# Event windows use end-of-year marked-to-market values, not just realized sales.
events=[]
for name,v in navs.items():
 if not name.endswith('2005-01-03'):continue
 for year in [2008,2020,2022,2023,2024]:
  z=v.loc[str(year)];prior=v.loc[v.index<z.index[0]].iloc[-1]
  zz=np.r_[prior,z.to_numpy()]
  events.append(dict(strategy=name,year=year,total_return=z.iloc[-1]/prior-1,within_year_MDD=np.min(zz/np.maximum.accumulate(zz)-1)))
pd.DataFrame(events).to_csv(OUT/'events.csv',index=False)
# Independent monthly open-to-open engine must match final daily engine wealth.
for L in [1,2,3]:
 cc,oo=syn[L];setup('2005-01-03',cc,oo,ORIG_MOM)
 dates=list(REBAL.values());op=oo.loc[dates].to_numpy()
 for k in [1,3]:
  wealth=1.;weights=np.zeros(len(SYMS))
  for t in range(len(dates)-1):
   picks=selection(dates[t],POOL,k,60);target=np.zeros(len(SYMS));target[[SIDX[s] for s in picks]]=1/k
   after=wealth
   for _ in range(15):after=wealth-.001*np.abs(after*target-wealth*weights).sum()
   active=target>0;values=np.zeros(len(SYMS));values[active]=after*target[active]*op[t+1,active]/op[t,active]
   wealth=values.sum();weights=values/wealth
  assert np.isclose(wealth*.999,navs[f'L{L}_base_Top{k}_2005-01-03'].iloc[-1],rtol=1e-10)
print('PASS: independent open-to-open terminal wealth; positive leverage factors; same base-signal holdings',flush=True)
# Real-fund calibration, same-index pairs. Not used to tune the model.
checks=[]
for asset,fund,L in [('SPY','SSO',2),('SPY','UPRO',3),('QQQ','QLD',2),('QQQ','TQQQ',3),('TLT','UBT',2),('IEF','UST',2)]:
 d=load(fund);cc,oo=syn[L]
 ix=cc.loc['2017-02-01':END].index
 if not ix.isin(d.index).all():raise ValueError(f'calibration missing {fund}')
 for kind,close,open_ in [('synthetic',cc[asset],oo[asset]),('actual',d.adjclose,d.adjopen)]:
  v=close.loc[ix]/open_.loc[ix[0]];v.iloc[-1]=open_.loc[END]/open_.loc[ix[0]]
  z=pd.concat([pd.Series([1.],index=[ix[0]-pd.Timedelta(days=1)]),v])
  checks.append(dict(asset=asset,fund=fund,L=L,kind=kind,**metrics(z)))
pd.DataFrame(checks).to_csv(OUT/'real_fund_calibration.csv',index=False)
# Actual TQQQ benchmark uses real fund prices, no synthetic backfill.
for fund in ['TQQQ','UPRO']:
 d=load(fund);ix=d.loc['2017-02-01':END].index;v=d.adjclose.loc[ix]/d.adjopen.loc[ix[0]]*.999
 v.iloc[-1]=d.adjopen.loc[END]/d.adjopen.loc[ix[0]]*.999*.999
 z=pd.concat([pd.Series([1.],index=[ix[0]-pd.Timedelta(days=1)]),v]);print('REAL_HOLD',fund,metrics(z))
print(summary[['strategy','CAGR','MDD','monthly_win_rate','payoff','worst_month']].to_string(index=False))
print('CALIBRATION');print(pd.DataFrame(checks)[['fund','kind','CAGR','MDD']].to_string(index=False))
