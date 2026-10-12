import pathlib,urllib.request,json,concurrent.futures
ROOT=pathlib.Path(__file__).parent
SYMBOLS='SSO UPRO QLD TQQQ ROM TECL USD SOXL DIG UGL UBT UST UYM UWM UYG UCC UXI UGE RXL UPW URE UJB'.split()
def fetch(s):
 p=ROOT/'raw'/f'{s}.json'
 if p.exists():return s,'cached'
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1=631152000&period2=1791676800&interval=1d&events=div,splits&includeAdjustedClose=true'
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read()
  j=json.loads(b)['chart']['result'][0];assert len(j['timestamp'])>200;p.write_bytes(b)
  return s,len(j['timestamp'])
 except Exception as e:return s,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for r in ex.map(fetch,SYMBOLS):print(r,flush=True)
