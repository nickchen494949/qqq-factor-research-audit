from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;M=R/'metadata'
p=pd.read_parquet(R.parent/'full_2009/crsp_allcodes_monthly_2007_2019.parquet');pivot=p.pivot(index='month',columns='permno',values='gross')
out=[]
for f in sorted((R/'raw_prices').glob('*.json')):
 try:
  z=json.loads(f.read_text())['chart']['result'][0];a=pd.Series(z['indicators']['adjclose'][0]['adjclose'],index=pd.to_datetime(z['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()).dropna();v=a.resample('ME').last().pct_change(fill_method=None)+1;v.index=v.index.to_period('M').astype(str);v=v.reindex(pivot.index).dropna()
  if len(v)<6:continue
  # Ignore returns near zero: they carry little identifying information.
  v=v[(v-1).abs()>.015];s=pivot.loc[v.index];err=s.sub(v,axis=0).abs();count=(err<.001).sum();best=count.max();tops=count[count==best].index
  out.append(dict(ticker=f.stem,periods=len(v),matches=int(best),permnos='|'.join(map(str,tops))))
 except (KeyError,TypeError,ValueError):continue
x=pd.DataFrame(out);x.to_csv(M/'yahoo_permno_fingerprints.csv',index=False);print(x[x.ticker.isin('ADP TCOM ERIC LBTYA LBTYK SIRI CDW FOX FOXA BIDU'.split())].to_string(index=False))
