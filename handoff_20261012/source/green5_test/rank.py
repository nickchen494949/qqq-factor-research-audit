from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
c=pd.read_csv(B/'qqq_smh_top1/results/candidate_rankings.csv');base=pd.read_csv(B/'qqq_smh_top1/results/monthly_signals.csv')
p=pd.read_parquet(R/'crsp_history_monthly.parquet');pg={int(n):g.set_index('month').sort_index() for n,g in p.groupby('permno')}
y=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');yg={}
for t,g in y.groupby('asset'):
 d=g.set_index('date').sort_index();v=d.adjclose.resample('ME').last();a=pd.DataFrame({'gross':v.pct_change(fill_method=None)+1,'prc':d.close.resample('ME').last()});a.index=a.index.to_period('M').astype(str);yg[t]=a
cache={};annual=[]
def history(pn,t,year):
 key=(pn,t,year)
 if key in cache:return cache[key]
 # Use exactly the historical security for old records and current ticker only in the modern panel.
 a=yg.get(t) if year>=2020 and t in yg else pg.get(pn)
 source='YAHOO' if year>=2020 and t in yg else 'CRSP'
 if a is None:return ('UNKNOWN_SERIES',0,[],source)
 start=f'{year-6}-12';months=[str(x) for x in pd.period_range(f'{year-5}-01',f'{year-1}-12',freq='M')]
 if a.index.min()>start:state='SHORT_HISTORY';vals=[]
 elif start not in a.index or not all(m in a.index for m in months):state='UNKNOWN_GAP';vals=[]
 elif a.loc[months,'gross'].isna().any():state='UNKNOWN_RETURN';vals=[]
 else:
  vals=[float(a.loc[[f'{yr}-{m:02d}' for m in range(1,13)],'gross'].prod()-1) for yr in range(year-5,year)];state='COMPLETE'
  if source=='CRSP' and (a.loc[months,'n']!=a.loc[months,'rows']).any():state='REVIEW_RETURN_GAP'
 if state=='REVIEW_RETURN_GAP' and t in yg and start in yg[t].index and all(m in yg[t].index for m in months):
  check=[float(yg[t].loc[[f'{yr}-{m:02d}' for m in range(1,13)],'gross'].prod()-1) for yr in range(year-5,year)]
  if np.max(np.abs(np.array(vals)-np.array(check)))<.003 and all((x>0)==(y>0) for x,y in zip(vals,check)):state='COMPLETE';source='CRSP_ANNUAL_YAHOO_CROSSCHECK'
 result=(state,sum(v>0 for v in vals),vals,source);cache[key]=result
 annual.append(dict(permno=pn,ticker=t,trade_year=year,status=state,green_years=result[1],annual_returns=json.dumps(vals),source=source))
 return result
old_map={int(r.permno):r.asset for r in base[base.trade_month<'2020'].itertuples() if pd.notna(r.permno)}
out=[];audit=[];blocked=[]
for (f,m),g in c.groupby(['fund','trade_month'],sort=False):
 year=int(m[:4]);rank=g[g.status.eq('RANKED')].sort_values(['momentum','name'],ascending=[False,True]).copy()
 hs=[history(int(r.permno) if pd.notna(r.permno) else None,r.ticker,year) for r in rank.itertuples()]
 rank['history_status']=[h[0] for h in hs];rank['green_years']=[h[1] for h in hs];rank['annual_returns']=[json.dumps(h[2]) for h in hs];rank['history_source']=[h[3] for h in hs];audit+=rank.to_dict('records')
 for variant in ['five_year_history','green3of5']:
  eligible=rank[rank.history_status.eq('COMPLETE')]
  if variant=='green3of5':eligible=eligible[eligible.green_years>=3]
  top=eligible.iloc[0] if len(eligible) else None;best=top.momentum if top is not None else -np.inf
  unknown=rank[rank.history_status.str.startswith(('UNKNOWN','REVIEW')) & (rank.momentum>=best)]
  if len(unknown):blocked+=unknown.assign(variant=variant).to_dict('records')
  # Ambiguous early filing name is tested under both identity possibilities.
  for r in g[g.status.eq('BOUNDED_NONWINNER_IDENTITY_UNRESOLVED')].itertuples():
   for pn in [12067,86580]:
    h=history(pn,'NVLS' if pn==12067 else 'NVDA',year);months=[str(pd.Period(r.signal_month)-j) for j in range(11,0,-1)];score=pg[pn].loc[months,'gross'].prod()-1
    if h[0]!='SHORT_HISTORY' and (h[0]!='COMPLETE' or variant=='five_year_history' or h[1]>=3) and score>=best:blocked.append(dict(fund=f,trade_month=m,variant=variant,name='AMBIGUOUS_NVLS_NVDA',permno=pn,momentum=score,history_status=h[0]))
  orig=base[(base.fund==f)&(base.trade_month==m)].iloc[0]
  d=dict(fund=f,trade_month=m,trade_date=orig.trade_date,variant=variant,ticker=top.ticker if top is not None else 'CASH',permno=top.permno if top is not None else np.nan,name=top['name'] if top is not None else 'CASH',momentum=best,green_years=top.green_years if top is not None else np.nan,n_eligible=len(eligible),original_asset=orig.asset)
  d['asset']='CASH' if top is None else (str(top.ticker) if year>=2020 and top.ticker in yg else old_map.get(int(top.permno),str(top.ticker) if pd.notna(top.ticker) else 'P_'+str(int(top.permno))))
  out.append(d)
pd.DataFrame(out).to_csv(R/'signals.csv',index=False);pd.DataFrame(audit).to_csv(R/'candidate_audit.csv',index=False);pd.DataFrame(annual).to_csv(R/'annual_history_audit.csv',index=False);pd.DataFrame(blocked).to_csv(R/'blocked.csv',index=False)
print('BLOCKED',len(blocked));print(pd.DataFrame(blocked).to_string(index=False)[:7000]);print(pd.DataFrame(out).groupby(['fund','variant']).agg(months=('asset','size'),cash=('asset',lambda a:(a=='CASH').sum()),changed=('asset',lambda a:0)).to_string());print(pd.DataFrame(annual).groupby(['status','source']).size().to_string())
