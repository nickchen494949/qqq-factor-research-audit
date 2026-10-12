"""Reuse frozen engine and cached data; no selection changes after results."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
# Load only the shared engine definitions, not the original experiment runner.
source=(BASE/'backtest.py').read_text().split('results={};ledger=[]')[0]
exec(compile(source,str(BASE/'backtest.py'),'exec'))
POOL32='SPY QQQ SMH SOXX IWM DIA MTUM SPMO QUAL USMV XBI ITA XRT XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC EEM EFA GLD TLT IEF LQD HYG SGOV'.split()
assert len(POOL32)==32 and set(POOL32)<=set(SYMS)
out=BASE/'comparison_22_32';out.mkdir(exist_ok=True)
rows=[];allnav={};trades=[]
for start in ['2017-02-01','2005-01-03']:
 START=pd.Timestamp(start);IX=C.loc[START:END].index
 CV=C.loc[IX].to_numpy();OV=O.loc[IX].to_numpy()
 REBAL={i:dt for i,dt in enumerate(IX) if i==0 or dt.month!=IX[i-1].month}
 for age in [60,12]:
  for label,pool in [('Economic22',POOL),('Previous32',POOL32)]:
   for k in [1,3]:
    name=f'{label}_Top{k}_{age}m_{start}'
    v,l=run(name,pool,k,age,.001)
    z=pd.concat([pd.Series([1.],index=[IX[0]-pd.Timedelta(days=1)]),v])
    rows.append(dict(pool=label,k=k,age_months=age,start=start,end=str(END.date()),**metrics(z)))
    allnav[name]=v;trades+=l
 for s in ['SPY','QQQ']:
  v,l=run(s,[s],1,0,.001,True)
  z=pd.concat([pd.Series([1.],index=[IX[0]-pd.Timedelta(days=1)]),v])
  rows.append(dict(pool=s,k=0,age_months=0,start=start,end=str(END.date()),**metrics(z)))
  allnav[s+'_'+start]=v
pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False)
pd.DataFrame(allnav).to_csv(out/'daily_nav.csv')
pd.DataFrame(trades).to_csv(out/'holdings.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
