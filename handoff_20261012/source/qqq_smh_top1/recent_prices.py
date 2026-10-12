from pathlib import Path
import pandas as pd,json,re,urllib.request,urllib.parse,concurrent.futures,shutil
R=Path(__file__).resolve().parent;B=R.parent;P=R/'raw_prices';P.mkdir(exist_ok=True)
old=pd.read_csv(B/'credibility_audit/results/reviewed_candidate_identities.csv',dtype={'cusip':str}).fillna('')
cm=old.groupby('cusip').ticker.agg(lambda v:next(iter(v)) if len(set(v))==1 else '|'.join(set(v))).to_dict()
# Issuer-reviewed historical share-class mappings; prices checked against filing valuations separately.
pairs='''G25839104 CCEP
05464C101 AXON
311900104 FAST
49271V100 KDP
722304102 PDD
217204106 CPRT
02043Q107 ALNY
22788C105 CRWD
23804L103 DDOG
031162100 AMGN
126408103 CSX
22160K105 COST
594972408 MSTR
375558103 GILD
693718108 PCAR
69608A108 PLTR
92532F100 VRTX
025537101 AEP
25809K105 DASH
713448108 PEP
03831W108 APP
G7997R103 STX
46120E602 ISRG
931142103 WMT
30161N101 EXC
21037T109 CEG
N6596X109 NXPI
36266G107 GEHC
G54950103 LIN
45168D104 IDXX
N97284108 NBIS
58733R102 MELI
80004C200 SNDK
697435105 PANW
21873S108 CRWV
773121108 RKLB
609207105 MDLZ
98138H101 WDAY
N07059210 ASML
252131107 DXCM
884903881 TRI
43849R105 HONA
438516205 HON
98389B100 XEL
172908105 CTAS
679580100 ODFL
75886F107 REGN
82509L107 SHOP
61174X109 MNST
500754106 KHC
55024U109 LITE
457669307 INSM
438516106 HON
049468101 TEAM
22160N109 CSGP
98980G102 ZS
884903808 TRI
92345Y106 VRSK
046353108 AZN
N3168P101 FER
09062X103 BIIB
88339J105 TTD
G39387108 GFS
60937P106 MDB
86800U104 SMCI
256746108 DLTR
60770K107 MRNA
452327109 ILMN
384747101 GRAL
931427108 WBA
82968B103 SIRI
848637104 SPLK
549498103 LCID
47215P106 JD
81181C104 SGEN
98980L101 ZM
016255101 ALGN
76954A103 RIVN
G06242104 TEAM
056752108 BIDU
679295105 OKTA
64110W102 NTES
256163106 DOCU
70614W100 PTON
156782104 CERN
M22465104 CHKP
89677Q107 TCOM
45337C102 INCY
015351109 ALXN
G5876H105 MRVL
G5480U120 LBTYK
G5480U104 LBTYA
812578102 SGEN
09061G101 BMRN
G96629103 WTW
02376R102 AAL
910047109 UAL
N59465109 MYL
806407102 HSIC
445658107 JBHT
151020104 CELG
871503108 GEN
22943F100 TCOM'''
cm.update(dict(line.split() for line in pairs.splitlines()))
x=pd.read_csv(R/'metadata/holdings_candidates.csv',dtype={'cusip':str}).fillna('');x=x[(x.report>='2019-09-30') & (x.cusip!='')].copy();x['ticker']=x.cusip.map(cm).fillna('')
missing=x[x.ticker==''].drop_duplicates(['name','cusip']);print('UNMAPPED',missing[['name','cusip']].to_string(index=False),flush=True)
x[['name','cusip','isin','ticker']].drop_duplicates().to_csv(R/'metadata/recent_identity_map.csv',index=False)
symbols=sorted(set(x.ticker)-{''})
def fetch(sym):
 p=P/f'{sym}.json';sources=[B/'stock_nested_2009/raw_prices'/f'{sym}.json',B/'economic_pool/raw'/f'{sym}.json']
 if not p.exists():
  for candidate in sources:
   if candidate.exists():shutil.copyfile(candidate,p);break
 u='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(sym.replace('BRK/B','BRK-B'))+'?period1=946684800&period2=1791590400&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
 try:
  if not p.exists():p.write_bytes(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read())
  z=json.loads(p.read_text());g=z['chart']['result'][0];assert g.get('timestamp');return dict(ticker=sym,status='OK',n=len(g['timestamp']),longName=g.get('meta',{}).get('longName'),first=g['timestamp'][0],last=g['timestamp'][-1],source=u)
 except Exception as e:return dict(ticker=sym,status='ERROR',error=str(e),source=u)
out=[]
with concurrent.futures.ThreadPoolExecutor(4) as ex:
 for r in ex.map(fetch,symbols):
  out.append(r);(R/'metadata/recent_price_fetch.json').write_text(json.dumps(out,indent=2));print(r['ticker'],r['status'],r.get('error',''),flush=True)
