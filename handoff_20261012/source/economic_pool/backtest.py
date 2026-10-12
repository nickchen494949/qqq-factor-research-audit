"""Frozen universe exploratory backtest; USD gross tax basis. See README.txt."""
import json,pathlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).parent
POOL='SPY IWM XLK SMH XLC XLY XLI XLRE XLF HYG XLE XLB PDBC XLP XLV XLU IEF TLT TIP GLD UUP SGOV'.split()
SECTOR='XLK XLC XLY XLI XLRE XLF XLE XLB XLP XLV XLU'.split()
EXTRA='QQQ BIL EFA EEM VEA VWO VNQ LQD SHY AGG DBC SLV GDX SOXX XBI ITA XRT DIA MTUM SPMO QUAL USMV IWD IWF IWN IWO EMB BWX'.split()
SYMS=sorted(set(POOL+EXTRA))
def load(s):
 j=json.loads((ROOT/'raw'/f'{s}.json').read_text())['chart']['result'][0]
 ix=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
 d=pd.DataFrame(j['indicators']['quote'][0],index=ix)
 d['adjclose']=j['indicators']['adjclose'][0]['adjclose']
 d=d[~d.index.duplicated(keep='last')].dropna(subset=['open','close','adjclose'])
 if s=='SMH':d=d.loc['2011-12-20':]
 d['adjopen']=d.open*d.adjclose/d.close
 return d
DATA={s:load(s) for s in SYMS}
C=pd.DataFrame({s:d.adjclose for s,d in DATA.items()}).reindex(DATA['SPY'].index)
O=pd.DataFrame({s:d.adjopen for s,d in DATA.items()}).reindex(C.index)
MC=C.resample('ME').last(); MOM=MC.shift(1)/MC.shift(12)-1
FIRST={s:d.index[0].to_period('M') for s,d in DATA.items()}
audit=[]
for s,d in DATA.items():
 audit.append(dict(ticker=s,first=str(d.index[0].date()),last=str(d.index[-1].date()),rows=len(d),main_first_trade=str((FIRST[s]+61).start_time.date()),max_abs_daily_return=d.adjclose.pct_change().abs().max(),missing_after_start=int(C.loc[d.index[0]:,s].isna().sum())))
pd.DataFrame(audit).to_csv(ROOT/'data_audit.csv',index=False)
START=pd.Timestamp('2005-01-03'); END=pd.Timestamp('2026-10-01')
assert END in O.index
IX=C.loc[START:END].index
CV=C.loc[IX].to_numpy(); OV=O.loc[IX].to_numpy(); SIDX={s:i for i,s in enumerate(SYMS)}
REBAL={i:dt for i,dt in enumerate(IX) if i==0 or dt.month!=IX[i-1].month}
def selection(dt,pool,k,age):
 prev=dt.to_period('M')-1; sig=MOM.loc[prev.to_timestamp('M')]
 ok=[s for s in pool if prev.ordinal-FIRST[s].ordinal>=age and pd.notna(sig[s])]
 return sorted(ok,key=lambda s:(-sig[s],s))[:k]
def run(name,pool,k=1,age=60,cost=.001,buyhold=False,bil=False):
 shares=np.zeros(len(SYMS)); nav=[]; trades=[]; opened=False
 for i,dt in enumerate(IX):
  active=shares!=0
  if active.any():assert np.isfinite(CV[i,active]).all() and np.isfinite(OV[i,active]).all(),(name,dt)
  if i in REBAL and (not buyhold or not opened):
   candidates=pool.copy()
   if bil and dt.to_period('M').ordinal-FIRST['SGOV'].ordinal<=age:
    candidates=[s for s in pool if s!='SGOV']+['BIL']
   picks=pool if buyhold else selection(dt,candidates,k,age)
   if not picks: raise ValueError((name,dt,'no eligible'))
   target=np.zeros(len(SYMS));target[[SIDX[s] for s in picks]]=1/len(picks)
   old=np.where(active,shares*np.nan_to_num(OV[i]),0)
   capital=old.sum() if opened else 1.
   if i==len(IX)-1:
    nav.append(capital*(1-cost));break
   new=capital
   for _ in range(15):new=capital-cost*np.abs(new*target-old).sum()
   turnover=np.abs(new*target-old).sum()/capital
   shares=np.divide(new*target,OV[i],out=np.zeros(len(SYMS)),where=target>0)
   opened=True
   trades.append(dict(strategy=name,date=str(dt.date()),holdings=' '.join(picks),eligible=len([s for s in candidates if (dt.to_period('M')-1).ordinal-FIRST[s].ordinal>=age]),turnover=turnover,cost_fraction=1-new/capital,nav_open_before=capital))
  if i==len(IX)-1:
   nav.append(np.sum(shares[shares!=0]*OV[i,shares!=0])*(1-cost));break
  nav.append(np.sum(shares[shares!=0]*CV[i,shares!=0]))
 return pd.Series(nav,index=IX,name=name),trades
def metrics(v):
 r=v.pct_change().dropna();years=(v.index[-1]-v.index[0]).days/365.25
 return dict(CAGR=(v.iloc[-1]/v.iloc[0])**(1/years)-1,MDD=(v/v.cummax()-1).min(),vol=r.std()*np.sqrt(252),Sharpe_rf0=r.mean()/r.std()*np.sqrt(252),multiple=v.iloc[-1]/v.iloc[0])
results={};ledger=[]
configs=[]
for age in [60,12]:
 for p,pool in [('Economic22',POOL),('Sector11',SECTOR),('Sector13_reconstructed',SECTOR+['SMH','SOXX']),('Broad50',SYMS)]:
  for k in [1,3]:configs.append((f'{p}_Top{k}_{age}m',pool,k,age,.001,False,False))
for k in [1,3]:
 configs.append((f'Economic22_BILbridge_Top{k}_60m',POOL,k,60,.001,False,True))
 for c in [0,.0025]:configs.append((f'Economic22_Top{k}_cost{c}',POOL,k,60,c,False,False))
for s in ['SPY','QQQ','SMH']:
 if s!='SMH':configs.append((s,[s],1,0,.001,True,False))
for cfg in configs:
 v,l=run(*cfg);results[cfg[0]]=v;ledger+=l
NAV=pd.DataFrame(results);NAV.to_csv(ROOT/'daily_nav.csv');pd.DataFrame(ledger).to_csv(ROOT/'holdings.csv',index=False)
summary=[]
for name,v in results.items():
 for start in ['2005-01-03','2017-02-01','2022-01-03','2025-06-02']:
  x=v.loc[start:].copy()
  # Use previous close as base for subperiod returns; initial capital is exactly 1.
  pos=v.index.get_loc(x.index[0]);base=v.iloc[pos-1] if pos else 1.
  x=pd.concat([pd.Series([base],index=[x.index[0]-pd.Timedelta(days=1)]),x])
  summary.append(dict(strategy=name,start=start,end=str(END.date()),**metrics(x)))
SUMMARY=pd.DataFrame(summary);SUMMARY.to_csv(ROOT/'summary.csv',index=False)
annual=NAV.resample('YE').last().pct_change();annual.iloc[0]=NAV.resample('YE').last().iloc[0]-1
annual.to_csv(ROOT/'annual_returns.csv')
events=[]
for label,a,b in [('GFC2008','2008-01-01','2008-12-31'),('Covid2020','2020-01-01','2020-12-31'),('Inflation2022','2022-01-01','2022-12-31'),('Tech2023_24','2023-01-01','2024-12-31')]:
 for name in ['Economic22_Top1_60m','Economic22_Top3_60m','Sector13_reconstructed_Top1_60m','Sector13_reconstructed_Top3_60m','SPY','QQQ']:
  v=NAV[name];sub=v.loc[a:b];base=v.loc[v.index<sub.index[0]].iloc[-1]
  z=pd.concat([pd.Series([base]),sub.reset_index(drop=True)])
  events.append(dict(event=label,strategy=name,total_return=sub.iloc[-1]/base-1,within_period_MDD=(z/z.cummax()-1).min()))
pd.DataFrame(events).to_csv(ROOT/'event_windows.csv',index=False)
# Random pools: same 22 names drawn uniformly from the frozen 50-fund research universe.
# Monthly open-to-open simulation for distribution comparisons only (not daily MDD).
DATES=list(REBAL.values()); opens=O.loc[DATES]
def month_sim(pool,k,age=60):
 wealth=1.;values=[wealth];w=np.zeros(len(SYMS))
 for t in range(len(DATES)-1):
  picks=selection(DATES[t],pool,k,age);target=np.zeros(len(SYMS));target[[SIDX[s] for s in picks]]=1/len(picks)
  new=wealth
  for _ in range(8):new=wealth-.001*np.abs(new*target-wealth*w).sum()
  ratio=opens.iloc[t+1].to_numpy()/opens.iloc[t].to_numpy();positions=np.where(target>0,new*target*np.nan_to_num(ratio),0)
  wealth=positions.sum();w=positions/wealth;values.append(wealth)
 values[-1]*=.999
 return np.array(values)
rng=np.random.default_rng(20261011);random=[]
for trial in range(300):
 pool=sorted(rng.choice(SYMS,22,replace=False).tolist())
 for k in [1,3]:
  v=month_sim(pool,k);years=(DATES[-1]-DATES[0]).days/365.25
  random.append(dict(trial=trial,k=k,CAGR=v[-1]**(1/years)-1,monthly_MDD=np.min(v/np.maximum.accumulate(v)-1),pool=' '.join(pool)))
pd.DataFrame(random).to_csv(ROOT/'random_pools.csv',index=False)
for k in [1,3]:
 v=month_sim(POOL,k)
 assert abs(v[-1]-NAV[f'Economic22_Top{k}_60m'].iloc[-1])<1e-7
print('PASS: independent monthly versus daily terminal wealth checks',flush=True)
names=['Economic22_Top1_60m','Economic22_Top3_60m','SPY','QQQ']
fig,axs=plt.subplots(2,1,figsize=(12,8),sharex=True,gridspec_kw={'height_ratios':[2,1]})
for n in names:
 axs[0].plot(NAV.index,NAV[n],label=n);axs[1].plot(NAV.index,100*(NAV[n]/NAV[n].cummax()-1),label=n)
axs[0].set_yscale('log');axs[0].set_ylabel('Growth of $1 (log scale)');axs[0].legend();axs[0].set_title('Frozen economic ETF pool | 12-1 momentum | 60 full months eligibility')
axs[1].set_ylabel('Drawdown (%)')
for ax in axs:ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(ROOT/'equity_drawdown.png',dpi=160)
print(SUMMARY[(SUMMARY.start=='2005-01-03') & SUMMARY.strategy.isin(names+['Sector11_Top1_60m','Sector11_Top3_60m','Sector13_reconstructed_Top1_60m','Sector13_reconstructed_Top3_60m','Broad50_Top1_60m','Broad50_Top3_60m'])].to_string(index=False))
print('RANDOM',pd.DataFrame(random).groupby('k').CAGR.describe().to_string())
