from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
e=pd.read_csv(R/'top1_episodes.csv');top=e.sort_values('log_contribution',ascending=False).groupby('fund').head(5)
c=pd.read_parquet(B/'green5_test/crsp_history_daily.parquet');c.date=pd.to_datetime(c.date);checks=[]
for r in top.itertuples():
 if pd.notna(r.permno):
  a=c[c.permno.eq(int(r.permno))&c.date.gt(pd.Timestamp(r.start))&c.date.le(pd.Timestamp(r.end))]
  if len(a) and a.date.max()==pd.Timestamp(r.end) and a.ret.notna().all():
   alt=(1+a.ret).prod()*.999/1.001-1;checks.append(dict(fund=r.fund,asset=r.asset,start=r.start,end=r.end,primary=r.net_return,independent=alt,error=alt-r.net_return,source='CRSP total returns'))
j=json.load(open(R/'alpaca_2026.json'));j=j.get('structuredContent') or json.loads(j['content'][0]['text']);y=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');pricechecks=[]
for t,rs in j['bars'].items():
 a=pd.DataFrame(rs);a['date']=pd.to_datetime(a.timestamp,utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize();b=y[y.asset.eq(t)];comp=a.merge(b,on='date',suffixes=('_sip','_yahoo'));err=(comp.close_sip/comp.close_yahoo-1).abs();pricechecks.append(dict(asset=t,observations=len(comp),max_close_relative_error=err.max(),source='Alpaca SIP vs cached Yahoo split-adjusted close; no split during checked range'))
pd.DataFrame(checks).to_csv(R/'winner_crosscheck.csv',index=False);pd.DataFrame(pricechecks).to_csv(R/'recent_price_crosscheck.csv',index=False)
print(pd.DataFrame(checks).to_string(index=False));print(pd.DataFrame(pricechecks).to_string(index=False))
