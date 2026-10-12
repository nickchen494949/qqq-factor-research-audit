from pathlib import Path
import pandas as pd,json,urllib.request,concurrent.futures
R=Path(__file__).resolve().parent
m={v['ticker']:v for v in json.loads((R/'raw/tickers.json').read_text()).values()}
s=pd.read_csv(R.parent/'qqq_smh_top1/results/monthly_signals.csv');tick=sorted(set(s.ticker.dropna())-{'ALTR','ARM_OLD','SNDK_OLD'})
def get(t):
 if t not in m:return dict(ticker=t,status='not in current SEC mapping')
 z=m[t];cik=str(z['cik_str']).zfill(10);u=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json';f=R/'raw'/f'{t}.json'
 try:
  if not f.exists():
   req=urllib.request.Request(u,headers={'User-Agent':'Academic financial research contact research@example.com'})
   with urllib.request.urlopen(req,timeout=40) as rr:f.write_bytes(rr.read())
  j=json.loads(f.read_text());assert str(j['cik']).zfill(10)==cik
  return dict(ticker=t,cik=cik,title=z['title'],entity=j['entityName'],url=u,status='ok')
 except Exception as e:return dict(ticker=t,cik=cik,url=u,status=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 out=[]
 for v in ex.map(get,tick):out.append(v);print(v,flush=True)
pd.DataFrame(out).to_csv(R/'fetch_log.csv',index=False)
