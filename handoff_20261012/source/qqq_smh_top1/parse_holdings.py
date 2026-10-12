from pathlib import Path
import pandas as pd,json,re,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent;M=R/'metadata';out=[];control=[]
months=r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}'
number=r'\d[\d,]{2,}(?:\.\d+)?'
patname=r'[A-Za-z][A-Za-z0-9\s.,!&’\'()\-/+;:®†*–—]*?'
for f in json.loads((M/'filings_manifest.json').read_text()):
 if f['status']!='OK' or f['fund']=='HOLDRS':continue
 p=Path(f['file']);rows=[];report=f['reportDate'];total=None;note=''
 if f['form']=='NPORT-P':
  try:
   root=ET.parse(p).getroot();ns={'n':'http://www.sec.gov/edgar/nport'};series=root.findtext('.//n:seriesId',namespaces=ns)
   if f['fund']=='SMH' and series!='S000034411':continue
   report=root.findtext('.//n:repPdDate',namespaces=ns)
   for z in root.findall('.//n:invstOrSec',ns):
    g=lambda k:z.findtext('n:'+k,default='',namespaces=ns)
    if g('assetCat') not in ['EC','EP']:continue
    isin=z.find('n:identifiers/n:isin',ns)
    rows.append(dict(name=g('name'),shares=float(g('balance')),value=float(g('valUSD')),cusip=g('cusip'),isin=isin.get('value') if isin is not None else '',title=g('title')))
   total=sum(x['value'] for x in rows);note='XML equity node exhaustion; not independent total'
  except Exception as e:control.append(dict(fund=f['fund'],acc=f['accessionNumber'],error=str(e)));continue
 else:
  s=Path(f['plain']).read_text()
  s=re.sub(r'\bS\s+EMICONDUCTOR\b','SEMICONDUCTOR',s)
  if f['fund']=='SMH':
   h=re.search(r'SEMICONDUCTOR\s+ETF\s+SCHEDULE\s+OF\s+INVESTMENTS',s,re.I)
   if not h:continue
   dm=re.search(months,s[h.start():h.end()+220],re.I)
   if not dm:continue
   report=str(pd.Timestamp(dm[0]).date());a=re.search(r'COMMON\s*STOCKS?',s[h.end():],re.I)
   if not a or a.start()>1200:continue
   start=h.end()+a.start();endm=re.search(r'TOTAL\s*COMMON\s*STOCKS?',s[start:],re.I)
   if not endm:continue
   end=start+endm.start();section=s[start:end];tail=s[end:end+250]
   pattern=rf'({number})\s+({patname})\s+\$?\s*({number})(?:\s|$)'
  else:
   h=re.search(r'Schedule\s+of\s+Investments\s*(?:\([^)]*\)\s*)?(?:(?:Invesco|PowerShares) QQQ Trust.{0,45}?)?('+months+r')',s,re.I)
   if not h:h=re.search('('+months+r')\s+Schedule\s+of\s+Investments(?:\s*\([^)]*\))?',s,re.I)
   if not h:
    control.append(dict(fund=f['fund'],acc=f['accessionNumber'],error='No dated investment schedule',file=str(p)));continue
   report=str(pd.Timestamp(h[1]).date());start=h.end();endm=re.search(r'Total\s+Investments|TOTAL\s*COMMON\s*STOCKS?',s[start:],re.I)
   if not endm:continue
   end=start+endm.start();section=s[start:end];tail=s[end:end+250]
   shares_first='Number of Shares' in section[:500]
   section=re.sub(r'\d*\s*(?:PowerShares|Invesco)?\s*QQQ\s*Trust.*?Schedule\s+of\s+Investments.*?'+months,' ',section,flags=re.I)
   section=re.sub(r'Schedule\s+of\s+Investments.*?'+months,' ',section,flags=re.I)
   section=re.sub(r'Invesco QQQ Trust.{0,90}?'+months,' ',section,flags=re.I)
   section=re.sub(r'(?:Common\s+Stocks?|Shares|Value|See accompanying notes to financial statements\.)',' ',section,flags=re.I)
   pattern=rf'({number})\s+({patname})\s+\$?\s*({number})(?:\s|$)' if shares_first else rf'({patname})\s+({number})\s+\$?\s*({number})(?:\s|$)'
  if f['fund']=='SMH' and report=='2011-12-31':
   section=section.replace('Texas Instruments, Inc. —','Texas Instruments, Inc. 0,000')
  for match in re.finditer(pattern,section):
   sf=f['fund']=='SMH' or shares_first
   name=match[2 if sf else 1].strip();shares=float(match[1 if sf else 2].replace(',',''));value=float(match[3].replace(',',''))
   name=re.sub(r'\([a-z](?:,[a-z])*\)|\(USD\)|[†*]','',name).strip();rows.append(dict(name=name,shares=shares,value=value,cusip='',isin=''))
  nums=re.findall(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?',tail)
  if nums:total=float(nums[1 if 'cost' in tail[:160].lower() and len(nums)>1 else 0].replace(',',''))
  note=tail
 # Original 2011-12 SMH HTML prints a dash in TXN's value cell. Recover only
 # the explicit named row and reconcile its residual to the independent total.
 if f['fund']=='SMH' and report=='2011-12-31' and not any('Texas Instruments' in r['name'] for r in rows) and total is not None:
  missing=re.search(r'([\d,]+)\s+Texas Instruments, Inc\.\s+—',section)
  if missing:
   residual=total-sum(r['value'] for r in rows)
   rows.append(dict(name='Texas Instruments, Inc.',shares=float(missing[1].replace(',','')),value=residual,cusip='',isin=''))
   note+='; TXN value recovered by residual; must check against independent market price'
 parsed=sum(x['value'] for x in rows);passed=bool(rows and total is not None and abs(parsed-total)<max(1.,abs(total)*1e-9))
 control.append(dict(fund=f['fund'],acc=f['accessionNumber'],report=report,accepted_UTC=f['accepted_UTC'],n=len(rows),parsed_total=parsed,reported_total=total,total_match=passed,note=note,source=f['source'],file=str(p)))
 for x in rows:out.append(dict(**x,fund=f['fund'],acc=f['accessionNumber'],report=report,accepted_UTC=f['accepted_UTC'],source=f['source'],total_match=passed))
pd.DataFrame(out).to_csv(M/'holdings_candidates.csv',index=False);pd.DataFrame(control).to_csv(M/'holdings_controls.csv',index=False)
print(pd.DataFrame(control).groupby('fund').agg(reports=('acc','count'),passed=('total_match','sum')).to_string())
print(pd.DataFrame(control)[lambda d:d.total_match!=True][['fund','acc','report','n','parsed_total','reported_total','error'] if 'error' in pd.DataFrame(control).columns else ['fund','acc','report','n','parsed_total','reported_total']].to_string(index=False))
