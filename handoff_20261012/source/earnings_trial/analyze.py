from pathlib import Path
from io import StringIO
import pandas as pd,numpy as np,re,json
R=Path(__file__).resolve().parent
s=pd.read_csv(R.parent/'qqq_smh_top1/results/monthly_signals.csv');cache={};events=[];errors=[]
def tables(t,k):
 f=R/'raw'/f'{t}_{k}.html'
 if not f.exists():return []
 try:return pd.read_html(StringIO(f.read_text()),converters={'Expected':str,'Actual':str})
 except Exception:return []
def interval(x):
 x=str(x).replace(',','').replace('$','').strip();m=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)([BMK]?)',x)
 if not m:return (np.nan,np.nan)
 val=float(m[1]);fac={'B':1e9,'M':1e6,'K':1e3,'':1}[m[2]];dec=len(m[1].split('.')[1]) if '.' in m[1] else 0
 half=.5*10**(-dec)*fac
 return val*fac-half,val*fac+half
def classify(row):
 # Inference only where displayed rounding intervals imply an unambiguous sign.
 e=interval(row.Expected);a=interval(row.Actual)
 if not np.isfinite(e+a).all():return 'unknown'
 if a[0]>e[1]+1e-10:return 'positive'
 if a[1]<e[0]-1e-10:return 'negative'
 return 'unknown'
for t in sorted(s.ticker.dropna().unique()):
 hs=[x for x in tables(t,'history') if 'Earnings Date' in x.columns and 'Period' in x.columns]
 es=[x for x in tables(t,'surprises') if list(x.columns)==['Period','Expected','Actual','Surprise']]
 if not hs or len(es)!=2:errors.append(dict(ticker=t,error='missing tables'));continue
 h=hs[0][['Period','Earnings Date']].copy();h['announced']=pd.to_datetime(h['Earnings Date'],errors='coerce');h=h.dropna(subset=['announced']).drop_duplicates('Period')
 for i,kind in enumerate(['eps','revenue']):
  e=es[i].copy();e[kind+'_sign']=[classify(z) for z in e.itertuples()];e=e.rename(columns={c:kind+'_'+c for c in ['Expected','Actual','Surprise']});h=h.merge(e,on='Period',how='left',validate='one_to_one')
 h['ticker']=t;cache[t]=h.sort_values('announced');events.extend(h.to_dict('records'))
rows=[]
for z in s.itertuples():
 cutoff=pd.Timestamp(z.trade_month)-pd.Timedelta(days=1);g=cache.get(z.ticker,pd.DataFrame());status='unknown';reason='no historical identity or tables';record={}
 if z.asset in ['ARM_OLD','SNDK_OLD'] or (str(z.asset).startswith('P_')):g=pd.DataFrame()
 if len(g):
  prior=g[g.announced<=cutoff]
  if len(prior):
   last=prior.iloc[-1];record=last.to_dict();age=(cutoff-last.announced).days;eps=last.get('eps_sign');rev=last.get('revenue_sign')
   if age>150:reason='report older than 150 days'
   elif eps=='negative' or rev=='negative':status='fail';reason='at least one clear miss'
   elif eps=='positive' and rev=='positive':status='pass';reason='both clearly above estimates'
   else:reason='rounded or missing surprise'
  else:reason='no published report by signal date'
 rows.append({**z._asdict(),**{'signal_cutoff':cutoff,'filter_status':status,'reason':reason},**{k:v for k,v in record.items() if k not in ['ticker']}})
out=pd.DataFrame(rows);out.to_csv(R/'monthly_audit.csv',index=False);pd.DataFrame(events).to_csv(R/'events.csv',index=False);pd.DataFrame(errors).to_csv(R/'source_errors.csv',index=False)
print(out.groupby(['fund','filter_status']).size().to_string());print(out[out.trade_month>='2020-01'].groupby(['fund','filter_status']).size().to_string())
