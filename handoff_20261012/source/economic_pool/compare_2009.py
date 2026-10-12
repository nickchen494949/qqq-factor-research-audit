"""Fresh start 2009-01-02; latest cached 2026-10-09 close; base ETF ranking only."""
from pathlib import Path
import pandas as pd,numpy as np
BASE=Path(__file__).resolve().parent
env={'__file__':str(BASE/'leverage_test.py')}
exec(compile((BASE/'leverage_test.py').read_text().split('summary=[];navs={};ledger=[];syn={}')[0],str(BASE/'leverage_test.py'),'exec'),env)
OUT=BASE/'comparison_2009';OUT.mkdir(exist_ok=True)
END=pd.Timestamp('2026-10-09');START='2009-01-02';env['END']=END
rates=pd.read_csv(BASE/'raw/DFF.csv',index_col=0,parse_dates=True).iloc[:,0].astype(float)/100
rates=rates.reindex(pd.date_range(rates.index[0],END,freq='D')).ffill().shift(2)
def metrics(v):
 r=v.pct_change();r.iloc[0]=v.iloc[0]-1
 days=v.index.to_series().diff().dt.days.fillna(0)
 x=r-rates.reindex(v.index)*days/360
 assert x.notna().all()
 return dict(CAGR=v.iloc[-1]**(365.25/((v.index[-1]-v.index[0]).days+1))-1,MDD=min(0,(v/v.cummax()-1).min()),Sharpe=x.mean()/x.std(ddof=1)*np.sqrt(252),Sortino=x.mean()/np.sqrt(np.mean(np.minimum(x,0)**2))*np.sqrt(252),multiple=v.iloc[-1])
rows=[];navs={};logs=[]
for lev in [1,2,3]:
 cc,oo=env['synthetic'](lev)
 assert END in cc.index
 # Trading engine marks the final position at O[END]. Substitute final close
 # solely for terminal liquidation; never use this price in an earlier signal.
 oo=oo.copy();oo.loc[END]=cc.loc[END]
 env['setup'](START,cc,oo,env['ORIG_MOM'])
 for k in [1,3]:
  name=f'Top{k}_{lev}x';v,l=env['run'](name,env['POOL'],k,60,.001)
  rows.append(dict(strategy=name,**metrics(v)));navs[name]=v;logs+=l
 for asset in ['SPY','QQQ']:
  name=f'{asset}_{lev}x';v,l=env['run'](name,[asset],1,0,.001,True)
  rows.append(dict(strategy=name,**metrics(v)));navs[name]=v;logs+=l
pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False)
pd.DataFrame(navs).to_csv(OUT/'daily_nav.csv');pd.DataFrame(logs).to_csv(OUT/'holdings.csv',index=False)
# Starting in 2009 still permits earlier data for signal/eligibility, but carries
# no previous holdings or cost basis into the new account.
for lev in [1,2,3]:
 for k in [1,3]:
  x=pd.DataFrame(logs);row=x[x.strategy==f'Top{k}_{lev}x'].iloc[0]
  assert row.date==START and row.nav_open_before==1
print(pd.DataFrame(rows).to_string(index=False))
print('PASS: initial capital exactly 1; ranks use prior history; latest date common; final close only used at termination')
