from pathlib import Path
import urllib.request,concurrent.futures,pandas as pd,json,time
R=Path(__file__).resolve().parent
s=pd.read_csv(R.parent/'qqq_smh_top1/results/monthly_signals.csv');tick=sorted(set(s.ticker.dropna())-{'SNDK_OLD','ARM_OLD','ALTR'})
def fetch(job):
 t,kind=job;u=f'https://www.nextearningsdate.com/{t.lower()}-earnings-{kind}.html';p=R/'raw'/f'{t}_{kind}.html'
 try:
  if not p.exists():
   with urllib.request.urlopen(u,timeout=35) as res:p.write_bytes(res.read())
  return dict(ticker=t,kind=kind,url=u,bytes=p.stat().st_size,status='ok')
 except Exception as e:return dict(ticker=t,kind=kind,url=u,status=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 out=[]
 for r in ex.map(fetch,[(t,k) for t in tick for k in ['surprises','history']]):
  out.append(r);print(r['ticker'],r['kind'],r['status'],flush=True)
pd.DataFrame(out).to_csv(R/'fetch_log.csv',index=False)
