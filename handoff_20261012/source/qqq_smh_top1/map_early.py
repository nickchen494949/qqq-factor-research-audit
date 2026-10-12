from pathlib import Path
import pandas as pd,numpy as np,json,re
from collections import Counter
from difflib import SequenceMatcher
R=Path(__file__).resolve().parent;B=R.parent;M=R/'metadata'
def norm(s):
 s=re.sub(r'^.*?See accompanying Notes to Financial Statements which are an integral part of these financial statements\.','',str(s),flags=re.I)
 s=re.sub(r'^.*?\(continued\)\s*','',s,flags=re.I)
 return re.sub('[^a-z0-9]','',re.sub(r'\([^)]*\)','',s).lower()).replace('corporation','corp').replace('incorporated','inc').replace('limited','ltd')
x=pd.read_csv(M/'holdings_candidates.csv').fillna('');x=x[(x.report<'2020') & (x.total_match==True)].copy();x['key']=x.name.map(norm)
p=pd.read_parquet(B/'full_2009/crsp_allcodes_monthly_2007_2019.parquet');p['price']=p.prc.abs();pm={m:g for m,g in p.groupby('month')}
names=pd.read_csv(B/'full_2009/wrds_sp500_permno_names.csv').drop_duplicates(['PERMNO','Company','Ticker']);nd={};tick={}
for row in names.itertuples():
 for name in row.Company.split(';'):nd.setdefault(int(row.PERMNO),set()).add(norm(name))
 tick.setdefault(int(row.PERMNO),set()).update(str(row.Ticker).split(';'))
old=pd.read_csv(B/'full_2009/identity_proposals.csv');seeds={norm(r.example):int(r.permno) for r in old.itertuples() if r.status!='UNRESOLVED'}
manual_path=M/'manual_early_identities.json';manual=json.loads(manual_path.read_text()) if manual_path.exists() else {}
evidence=[];proposal=[]
for key,g in x.groupby('key'):
 g=g.drop_duplicates(['report','shares','value']);sets=[]
 for row in g.itertuples():
  value=row.value/row.shares;a=pm[row.report[:7]];choices=a[(a.price-value).abs()<=max(.015,value*.005)];ss=set(choices.permno.astype(int));sets.append(ss)
  evidence.append(dict(key=key,report=row.report,name=row.name,price=value,candidates='|'.join(map(str,sorted(ss)))))
 counts=Counter(n for ss in sets for n in ss);best=max(counts.values(),default=0);tops=[n for n,c in counts.items() if c==best]
 scores={n:max([SequenceMatcher(None,key,name).ratio() for name in nd.get(n,[])]+[0]) for n in tops};ordered=sorted(scores,key=lambda n:scores[n],reverse=True)
 chosen=manual.get(key,seeds.get(key,ordered[0] if ordered else None));status='UNRESOLVED'
 if key in manual:status='MANUAL_NAME_AND_PRICE'
 elif chosen is not None and all(chosen in ss for ss in sets):
  if chosen==seeds.get(key):status='EXISTING_AUDIT_IDENTITY'
  elif len(tops)==1 and len(sets)>=2:status='SEC_MULTIDATE_UNIQUE'
  elif scores.get(chosen,0)>.82:status='WRDS_NAME_AND_SEC_PRICE'
 proposal.append(dict(key=key,name=g.iloc[0]['name'],periods=len(sets),best_matches=best,top_count=len(tops),permno=chosen,name_similarity=scores.get(chosen,0),status=status,tickers='|'.join(sorted(tick.get(chosen,[]))),wrds_names=';'.join(sorted(nd.get(chosen,[]))),candidates='|'.join(map(str,tops))))
pd.DataFrame(proposal).to_csv(M/'early_identity_proposals.csv',index=False);pd.DataFrame(evidence).to_csv(M/'early_price_identity_evidence.csv',index=False)
d=pd.DataFrame(proposal);print(d.status.value_counts().to_string());print(d[d.status=='UNRESOLVED'][['key','name','periods','best_matches','top_count','permno','name_similarity','tickers','candidates']].to_string(index=False))
