from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;B=R.parent
c=pd.read_csv(B/'qqq_smh_top1/results/candidate_rankings.csv');s=pd.read_csv(B/'qqq_smh_top1/results/monthly_signals.csv');oldmap={int(r.permno):r.asset for r in s[s.trade_month<'2020'].itertuples() if pd.notna(r.permno)}
y=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');yg={a:g.set_index('date').sort_index().adjclose for a,g in y.groupby('asset')}
rows=[];blocks=[]
for (fund,m),g in c.groupby(['fund','trade_month']):
 rank=g[g.status.eq('RANKED')].sort_values(['momentum','name'],ascending=[False,True]);cut=rank.iloc[4].momentum
 bad=g[g.status.ne('RANKED')&g.status.str.contains('BLOCK|BOUNDED')]
 for r in bad.itertuples():
  if pd.isna(r.bound_upper) or r.bound_upper>=cut:blocks.append(r._asdict())
 for i,r in enumerate(rank.head(5).itertuples(),1):
  pn=int(r.permno) if pd.notna(r.permno) else None
  asset=str(r.ticker) if m>='2020' and r.ticker in yg else oldmap.get(pn,str(r.ticker) if pd.notna(r.ticker) else 'P_'+str(pn))
  rows.append(dict(fund=fund,month=m,date=r.trade_date,rank=i,asset=asset,permno=pn,ticker=r.ticker,name=r.name,momentum=r.momentum))
a=pd.DataFrame(rows);a.to_csv(R/'selection.csv',index=False);pd.DataFrame(blocks).to_csv(R/'blocks.csv',index=False);print('BLOCKS',blocks)
orig=pd.read_parquet(B/'qqq_smh_top1/metadata/trading_prices.parquet');data={t:g.set_index('date').sort_index().adjclose for t,g in orig.groupby('asset')};sources=[]
crsp=pd.read_parquet(B/'green5_test/crsp_history_daily.parquet');crsp.date=pd.to_datetime(crsp.date);pg={int(n):g.set_index('date').sort_index() for n,g in crsp.groupby('permno')}
for r in a.itertuples():
 if r.asset in data:continue
 if r.asset in yg:data[r.asset]=yg[r.asset];source='YAHOO'
 elif pd.notna(r.permno) and int(r.permno) in pg:data[r.asset]=(1+pg[int(r.permno)].ret).cumprod();source='CRSP'
 else:print('NO DATA',r);continue
 sources.append(dict(asset=r.asset,permno=r.permno,source=source))
for asset,pn in [('EA',75828),('MXIM',11896),('AKAM',87299)]:
 if pn in pg:
  q=(1+pg[pn].ret).cumprod();old=data.get(asset);both=old.dropna().index.intersection(q.dropna().index) if old is not None else []
  if len(both):q=q*(old.loc[both[-1]]/q.loc[both[-1]]);data[asset]=old.combine_first(q)
  else:data[asset]=q
ref=pd.read_csv(B/'green5_test/daily_nav.csv',index_col=0,parse_dates=True);ix=ref.index
p=pd.DataFrame({t:data[t] for t in set(a.asset) if t in data}).reindex(ix);p.to_parquet(R/'prices.parquet');pd.DataFrame(sources).to_csv(R/'new_sources.csv',index=False)
gaps=[]
for fund,g in a.groupby('fund'):
 sig={pd.Timestamp(dt):set(h.asset) for dt,h in g.groupby('date')};old=set()
 for dt in ix:
  new=sig.get(dt,old)
  for t in old|new:
   if t not in p or pd.isna(p.loc[dt,t]):gaps.append(dict(fund=fund,date=str(dt.date()),asset=t))
  old=new
pd.DataFrame(gaps).to_csv(R/'price_gaps.csv',index=False);print('GAPS',len(gaps));print(pd.DataFrame(gaps).groupby('asset').agg(first=('date','min'),last=('date','max'),n=('date','size')).to_string() if gaps else '')
