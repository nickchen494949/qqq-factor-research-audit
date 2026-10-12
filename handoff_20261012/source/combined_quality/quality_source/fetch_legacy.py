from pathlib import Path
import urllib.request,concurrent.futures,json,pandas as pd
R=Path(__file__).resolve().parent
mapping={'ATML':872448,'SNDK_OLD':1000180,'CREE':895419,'GMCR':909954,'XLNX':743988,'ALXN':899866,'APOL':929887}
def get(pair):
 t,c=pair;u=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{c:010d}.json';p=R/'raw'/f'{t}.json'
 try:
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Academic financial research contact research@example.com'}),timeout=35) as z:p.write_bytes(z.read())
  j=json.loads(p.read_text());assert j['cik']==c
  return dict(ticker=t,cik=c,url=u,entity=j['entityName'],status='ok')
 except Exception as e:return dict(ticker=t,cik=c,url=u,status=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:out=list(e.map(get,mapping.items()))
pd.DataFrame(out).to_csv(R/'legacy_fetch_log.csv',index=False);print(out)
