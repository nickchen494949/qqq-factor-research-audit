"""Monthly rank with a net-profit-only sell constraint; adjusted total-return basis."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
exec(compile((BASE/'backtest.py').read_text().split('results={};ledger=[]')[0],str(BASE/'backtest.py'),'exec'))
OUT=BASE/'profit_only_results';OUT.mkdir(exist_ok=True)
def constrained(name,k,cost=.001):
 q=np.zeros(len(SYMS));basis=q.copy();entered={};cash=1.;nav=[];logs=[];sales=[];blocked=[]
 for i,dt in enumerate(IX):
  p=OV[i];active=q>1e-12
  assert np.isfinite(p[active]).all()
  if i==len(IX)-1:
   nav.append(cash+np.sum(q[active]*p[active])*(1-cost));break
  if i in REBAL:
   old=q*np.nan_to_num(p);before=cash+old.sum()
   # Profit permission uses the last available close; an opening limit-price
   # guard also prevents a gap-down fill below net break-even.
   prior=q*np.nan_to_num(CV[i-1]) if i else old
   locked=active & ((prior*(1-cost)<=basis+1e-12) | (old*(1-cost)<=basis+1e-12))
   ranking=selection(dt,POOL,len(POOL),60)
   desired=[s for s in ranking if not locked[SIDX[s]]][:k-int(locked.sum())]
   target=np.zeros(len(SYMS));target[[SIDX[s] for s in desired]]=1/len(desired) if desired else 0
   free=cash+old[~locked].sum();new=free
   for _ in range(20):new=free-cost*np.abs(new*target[~locked]-old[~locked]).sum()
   nq=q.copy();nq[~locked]=np.divide(new*target[~locked],p[~locked],out=np.zeros((~locked).sum()),where=target[~locked]>0)
   delta=nq-q;fee=0.
   for j in np.flatnonzero(np.abs(delta)>1e-12):
    fee+=abs(delta[j])*p[j]*cost
    if delta[j]<0:
     fraction=-delta[j]/q[j];removed=basis[j]*fraction;proceeds=-delta[j]*p[j]*(1-cost)
     assert proceeds>removed-1e-10,(dt,SYMS[j],proceeds,removed)
     sales.append(dict(strategy=name,date=str(dt.date()),ticker=SYMS[j],net_return=proceeds/removed-1,days=(dt-entered[j]).days,proceeds=proceeds,basis=removed))
     basis[j]-=removed
     if nq[j]<1e-12:entered.pop(j,None)
    else:
     if q[j]<1e-12:entered[j]=dt
     basis[j]+=delta[j]*p[j]*(1+cost)
   cash=before-old[locked].sum()-np.sum(nq[~locked]*np.nan_to_num(p[~locked]))-fee
   assert cash>-1e-9,(dt,cash)
   cash=max(cash,0.);q=nq
   assert (q>1e-12).sum()<=k
   for j in np.flatnonzero(locked):
    blocked.append(dict(strategy=name,date=str(dt.date()),ticker=SYMS[j],days_held=(dt-entered[j]).days,net_unrealized=old[j]*(1-cost)/basis[j]-1,outside_target=SYMS[j] not in ranking[:k]))
   logs.append(dict(strategy=name,date=str(dt.date()),holdings=' '.join(SYMS[j] for j in np.flatnonzero(q>1e-12)),locked=' '.join(SYMS[j] for j in np.flatnonzero(locked)),nav_open_before=before,cost=fee))
  nav.append(cash+np.sum(q[q>1e-12]*CV[i,q>1e-12]))
 terminal=[]
 for j in np.flatnonzero(q>1e-12):terminal.append(dict(strategy=name,ticker=SYMS[j],days_held=(IX[-1]-entered[j]).days,net_unrealized=q[j]*OV[-1,j]*(1-cost)/basis[j]-1))
 return pd.Series(nav,index=IX,name=name),logs,sales,blocked,terminal
rows=[];series={};hold=[];sale=[];block=[];terminal=[]
for start in ['2005-01-03','2017-02-01']:
 IX=C.loc[start:END].index;CV=C.loc[IX].to_numpy();OV=O.loc[IX].to_numpy()
 REBAL={i:dt for i,dt in enumerate(IX) if i==0 or dt.month!=IX[i-1].month}
 for k in [1,3]:
  for restricted in [False,True]:
   name=f'{"ProfitOnly" if restricted else "Original"}_Top{k}_{start}'
   if restricted:
    v,l,s,b,t=constrained(name,k);sale+=s;block+=b;terminal+=t
   else:v,l=run(name,POOL,k,60,.001)
   hold+=l;series[name]=v
   z=pd.concat([pd.Series([1.],index=[IX[0]-pd.Timedelta(days=1)]),v])
   opens=np.array([a['nav_open_before'] for a in l]+[v.iloc[-1]])
   r=opens[1:]/opens[:-1]-1;w=r[r>0];loss=r[r<0]
   rows.append(dict(strategy=name,**metrics(z),monthly_win_rate=len(w)/len(r),avg_win=w.mean(),avg_loss=loss.mean(),payoff=w.mean()/abs(loss.mean()),worst_month=r.min(),months=len(r)))
pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False)
pd.DataFrame(series).to_csv(OUT/'daily_nav.csv');pd.DataFrame(hold).to_csv(OUT/'monthly_holdings.csv',index=False)
pd.DataFrame(sale).to_csv(OUT/'realized_sales.csv',index=False);pd.DataFrame(block).to_csv(OUT/'blocked_positions.csv',index=False)
pd.DataFrame(terminal).to_csv(OUT/'terminal_positions.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
print('Longest blocked:');print(pd.DataFrame(block).sort_values('days_held',ascending=False).groupby('strategy',sort=False).head(1).to_string(index=False))
print('Terminal:');print(pd.DataFrame(terminal).to_string(index=False))
print('PASS: every normal sale profitable after costs; no leverage; max holdings respected')
