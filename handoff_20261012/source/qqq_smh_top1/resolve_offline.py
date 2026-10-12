from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent;M=R/'metadata'
# Candidate symbols; identity must also agree with independent historical price series.
symbols='ADP BIDU BEAS CDWC CDW CKFR CMCSA CMCSK CTRP DTV DISCA DISCK FAST FMCN FOX FOXA KFT MDLZ LAMR LEAP LBTYA LBTYK QVCA QRTEA LINTA ERIC MSFT MICC NVLS NVDA PTEN PPDI SGEN SEPR SIRI SPLK XMSR'.split()
out=M/'wiki_identity_prices.parquet'
if not out.exists():
 chunks=[]
 for x in pd.read_csv(B/'stock_nested_2009/recovery/wiki/WIKI_PRICES.csv',chunksize=500000):
  x=x[x.ticker.isin(symbols)&(x.date>='2007-01-01')];chunks.append(x)
 pd.concat(chunks,ignore_index=True).to_parquet(out,index=False)
w=pd.read_parquet(out);w['month']=w.date.str[:7];wm=w.sort_values('date').groupby(['ticker','month']).last().reset_index()
p=pd.read_parquet(B/'full_2009/crsp_allcodes_monthly_2007_2019.parquet');p['price']=p.prc.abs();by={m:g for m,g in p.groupby('month')};rows=[]
for sym,g in wm.groupby('ticker'):
 # Price fingerprints use several separated dates, not one coincidental quote.
 g=g.iloc[::6];sets=[]
 for z in g.itertuples():
  a=by[z.month];sets.append(set(a.loc[(a.price-z.close).abs()<max(.011,z.close*.0005),'permno'].astype(int)))
 counts={n:sum(n in s for s in sets) for n in set.union(*sets)} if sets else {}
 best=max(counts.values(),default=0);tops=[n for n,c in counts.items() if c==best]
 rows.append(dict(ticker=sym,price_dates=len(sets),matches=best,permnos='|'.join(map(str,tops)),first=g.date.min(),last=g.date.max()))
f=pd.DataFrame(rows);f.to_csv(M/'wiki_permno_fingerprints.csv',index=False);print(f.to_string(index=False))
