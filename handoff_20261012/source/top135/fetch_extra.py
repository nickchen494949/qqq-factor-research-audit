import urllib.request,json
from pathlib import Path
for t in ['CI','DIS']:
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=1514764800&period2=1577836800&interval=1d&events=div%2Csplits'
 try:
  d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read();assert json.loads(d)['chart']['result'];Path('top135/'+t+'.json').write_bytes(d);print(t,len(d),flush=True)
 except Exception as e:print(t,e,flush=True)
