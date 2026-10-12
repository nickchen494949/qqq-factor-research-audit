from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,re,hashlib,shutil
import pandas as pd
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent;B=R.parent;RAW=R/'raw_sec';META=R/'metadata'
def get(url,p):
 if not p.exists():p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HistoricalResearch analyst@example.com'}),timeout=50).read())
 return p.read_bytes()
jobs={}
def add(fund,cik,row):
 a=row['accessionNumber'];doc=row['primaryDocument'].split('/')[-1]
 jobs[(fund,a)]=dict(row,fund=fund,cik=str(cik),primaryDocument=doc)
q=pd.DataFrame(json.loads((META/'QQQ_submissions.json').read_text())['filings']['recent'])
for row in q.to_dict('records'):
 if row['filingDate']>='2008-01-01' and row['form'] in ['N-30B-2','NPORT-P','NPORT-EX','N-CSRS']:add('QQQ',1067839,row)
 if row['accessionNumber']=='0001206774-08-000229':add('QQQ',1067839,row)
v=json.loads((B/'stock_nested_2009/raw_sec/1137360_filing_inventory.json').read_text())
for row in v:
 if row['form'] in ['N-CSR','N-CSRS','N-Q'] and '2011-12-01'<=row['reportDate']<'2019-10' and row['reportDate'][5:7] in ['03','06','09','12']:add('SMH',1137360,row)
# Existing source archives preserve the specific series/accession identity.
for row in json.loads((B/'credibility_audit/sec_manifest.json').read_text()):
 if row['fund']=='SMH':add('SMH',1137360,dict(accessionNumber=row['acc'],primaryDocument='primary_doc.xml',filingDate='',reportDate=row['period'],form='NPORT-P'))
v=pd.read_csv(B/'stock_pit_inputs/PIT_13_ETF_Research_Package/PIT_13_ETF_Research/SMH_20_vintages_archive_audit.csv')
for row in v.to_dict('records'):add('SMH',1137360,dict(accessionNumber=row['accession'],primaryDocument='primary_doc.xml',filingDate=row['filing_public_date'],reportDate=row['report_date'],form='NPORT-P'))
if (META/'SMH_efts_2019_2021.json').exists():
 for hit in json.loads((META/'SMH_efts_2019_2021.json').read_text()).get('hits',{}).get('hits',[]):
  z=hit['_source'];a=hit['_id'].split(':')[0];add('SMH',1137360,dict(accessionNumber=a,primaryDocument='primary_doc.xml',filingDate=z.get('file_date',''),reportDate=z.get('period_ending',''),form='NPORT-P'))
h=pd.DataFrame(json.loads((META/'HOLDRS_submissions.json').read_text())['filings']['recent'])
for row in h.to_dict('records'):
 if row['form'] in ['8-K','SC TO-T'] and row['filingDate']>='2008-01-01':add('HOLDRS',1110511,row)
def fetch(row):
 a=row['accessionNumber'];base=f"https://www.sec.gov/Archives/edgar/data/{row['cik']}/{a.replace('-','')}/";p=RAW/f"{row['fund']}_{a}_{row['primaryDocument']}";ip=RAW/f"{row['fund']}_{a}_index.html"
 try:
  # Reuse exact original files, rather than fetching large fund reports twice.
  if not p.exists():
   candidates=[B/'stock_nested_2009/raw_sec'/f"{row['cik']}_{row['filingDate']}_{row['primaryDocument']}"]+list((B/'credibility_audit/raw_sec').glob(f"{row['fund']}_*_{a}.xml"))
   for c in candidates:
    if c.exists():shutil.copyfile(c,p);break
  b=get(base+row['primaryDocument'],p)
  soup=BeautifulSoup(get(base+a+'-index.html',ip),'lxml');st=soup.get_text(' ',strip=True);m=re.search(r'Accepted\s+(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)',st);assert m,st[:400]
  accepted=pd.Timestamp(m[1],tz='America/New_York').tz_convert('UTC')
  row.update(source=base+row['primaryDocument'],file=str(p),index_file=str(ip),accepted_UTC=str(accepted),filingDate=str(accepted.date()),sha256=hashlib.sha256(b).hexdigest(),status='OK')
  if row['form']!='NPORT-P':
   plain=re.sub(r'\s+',' ',BeautifulSoup(b,'lxml').get_text(' ',strip=True));pp=p.with_suffix('.plain.txt');pp.write_text(plain);row['plain']=str(pp)
  if row['fund']=='HOLDRS':
   exhibits=[]
   for tr in soup.select('table.tableFile tr'):
    td=tr.find_all('td')
    if len(td)>=4 and td[3].get_text(strip=True).startswith('EX-99') and td[2].find('a'):
     href=td[2].find('a')['href'];u='https://www.sec.gov'+href if href.startswith('/') else base+href;ep=RAW/f"HOLDRS_{a}_{href.split('/')[-1]}";eb=get(u,ep);ep.with_suffix('.plain.txt').write_text(re.sub(r'\s+',' ',BeautifulSoup(eb,'lxml').get_text(' ',strip=True)));exhibits.append(dict(source=u,file=str(ep)))
   row['exhibits']=exhibits
 except Exception as e:row.update(status='ERROR',error=str(e))
 return row
print('JOBS',len(jobs),flush=True);out=[]
with ThreadPoolExecutor(3) as ex:
 for row in ex.map(fetch,jobs.values()):
  out.append(row);(META/'filings_manifest.json').write_text(json.dumps(out,indent=2));print(row['fund'],row['reportDate'],row['form'],row['status'],row.get('error',''),flush=True)
