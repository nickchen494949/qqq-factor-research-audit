import urllib.request,json,concurrent.futures,pathlib,time
ROOT=pathlib.Path(__file__).parent
POOL='SPY IWM XLK SMH XLC XLY XLI XLRE XLF HYG XLE XLB PDBC XLP XLV XLU IEF TLT TIP GLD UUP SGOV'.split()
EXTRA='QQQ BIL EFA EEM VEA VWO VNQ LQD SHY AGG DBC SLV GDX SOXX XBI ITA XRT DIA MTUM SPMO QUAL USMV IWD IWF IWN IWO EMB BWX'.split()
def fetch(s):
 p=ROOT/'raw'/f'{s}.json'
 if p.exists(): return s,'cached'
 u=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1=631152000&period2=1791676800&interval=1d&events=div,splits&includeAdjustedClose=true'
 for i in range(3):
  try:
   data=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()
   j=json.loads(data)['chart']['result'][0]
   assert len(j['timestamp'])>200
   p.write_bytes(data)
   return s,len(j['timestamp'])
  except Exception as e:
   if i==2:return s,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 for r in ex.map(fetch,sorted(set(POOL+EXTRA))):print(r,flush=True)
