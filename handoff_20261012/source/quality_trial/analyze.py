from pathlib import Path
from collections import defaultdict
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent
s=pd.read_csv(R/'signals_input.csv');events=[];issues=[]
configs={'us-gaap':{'income':['NetIncomeLoss','ProfitLoss'],'cash':['NetCashProvidedByUsedInOperatingActivities']},'ifrs-full':{'income':['ProfitLoss'],'cash':['CashFlowsFromUsedInOperatingActivities']}}
for path in sorted((R/'raw').glob('*.json')):
 if path.stem=='tickers':continue
 j=json.loads(path.read_text());facts=j.get('facts',{});reports={};bag=defaultdict(list)
 for ns,tags in facts.items():
  if ns not in configs:continue
  for tag,content in tags.items():
   for unit,series in content.get('units',{}).items():
    if unit not in ['USD','EUR','CNY','TWD','GBP','JPY']:continue
    for v in series:
     if v.get('form') not in ['10-K','20-F'] or v.get('fp')!='FY' or 'start' not in v:continue
     start=pd.Timestamp(v['start']);end=pd.Timestamp(v['end']);filed=pd.Timestamp(v['filed'])
     if not 320<=(end-start).days<=400 or end>=filed:continue
     acc=v['accn'];entry=reports.get(acc)
     if entry is None or end>entry['end']:reports[acc]=dict(ticker=path.stem,cik=j['cik'],entity=j['entityName'],accn=acc,filed=filed,end=end,start=start,form=v['form'])
     for metric,candidates in configs[ns].items():
      if tag in candidates:bag[(acc,metric)].append(dict(start=start,end=end,unit=unit,value=v['val'],namespace=ns,tag=tag,priority=candidates.index(tag)))
 for acc,rep in reports.items():
  vals={}
  for metric in ['income','cash']:
   candidates=[x for x in bag[(acc,metric)] if x['end']==rep['end'] and x['start']==rep['start']]
   candidates=sorted(candidates,key=lambda x:(x['priority'],x['unit']!='USD',x['namespace']!='us-gaap'))
   if candidates:vals[metric]=candidates[0]
  for key,v in vals.items():rep[key]=v['value'];rep[key+'_tag']=v['namespace']+':'+v['tag'];rep[key+'_unit']=v['unit']
  if len(vals)==2 and vals['income']['unit']==vals['cash']['unit']:
   rep['unit']=vals['income']['unit'];rep['status']='ok'
  else:rep['status']='missing matching total income/cash values'
  events.append(rep)
e=pd.DataFrame(events);e.to_csv(R/'annual_filings.csv',index=False);out=[]
for z in s.itertuples():
 cutoff=pd.Timestamp(z.trade_month)-pd.Timedelta(days=1);key=z.asset if z.asset in set(e.ticker) else z.ticker;g=e[(e.ticker==key)&(e.filed<=cutoff)].sort_values(['end','filed']);rec={};state='unknown';reason='no identified filing available';profit='unknown'
 if str(z.asset).startswith('P_') or z.asset in ['ARM_OLD','ALTR']:g=g.iloc[:0]
 if len(g):
  rec=g.iloc[-1].to_dict()
  if (cutoff-rec['end']).days>550:reason='annual financial period older than 550 days'
  elif rec['status']!='ok':
   reason='latest annual filing lacks matching facts'
   if pd.notna(rec.get('income',np.nan)):profit='pass' if rec['income']>0 else 'fail'
  else:
   assert rec['filed']<=cutoff
   profit='pass' if rec['income']>0 else 'fail';state='pass' if rec['income']>0 and rec['cash']>=rec['income'] else 'fail';reason='classified from same filing and currency'
 out.append({**z._asdict(),**{k:v for k,v in rec.items() if k!='ticker'},'cutoff':cutoff,'filter_status':state,'profit_status':profit,'reason':reason})
a=pd.DataFrame(out);a.to_csv(R/'monthly_audit.csv',index=False);print(a.groupby(['fund','filter_status']).size().to_string())
