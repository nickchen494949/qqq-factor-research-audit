"""Monthly candidate audit. Unresolved candidates BLOCK performance publication."""
from pathlib import Path
import pandas as pd,numpy as np,json,re,exchange_calendars as xc
R=Path(__file__).resolve().parent;B=R.parent;M=R/'metadata';O=R/'results'
ns={'__file__':str(R/'map_early.py')};src=(R/'map_early.py').read_text();exec(src[:src.index('x=pd.read_csv')],ns);norm=ns['norm']
cal=xc.get_calendar('XNYS',start='2006-01-01',end='2026-12-31')
h=pd.read_csv(M/'holdings_candidates.csv',dtype={'cusip':str}).fillna('');h=h[h.total_match.eq(True)].copy();h['key']=h.name.map(norm)
ids=pd.read_csv(M/'early_identity_proposals.csv').fillna('');km={r.key:int(r.permno) for r in ids.itertuples() if r.status!='UNRESOLVED'}
manual={'automaticdataprocessingincwhenissued':44644,'baiducom':90857,'microsoftcorp':10107,'texasinstrumentsinc':15579,'fastenalcompany':11618,'directvclassa':89954,'kraftfoodsincclassa':89006,'lamaradvertisingco':83879,'lamaradvertisingcompany':83879,'libertyglobalincclassa':90227,'libertyglobalplcseriesa':90227,'libertyglobalseriesa':90227,'libertyinteractivecorpqvcgroupclassa':91277,'libertyinteractivecorpqvcgroupseriesa':91277,'libertymediacorp':91277,'qurateretailinc':91277,'millicomintlcellularsa':79996,'pattersonutienergyinc':79857,'seattlegeneticsinc':88949,'siriussatelliteradioinc':80924,'splunkinc':13379,'ctripcominternationalltd':89927,'tripcomgroupltd':89927,'foxcorpclassa':18420,'foxcorpclassb':18421,'asmlholdingnv':81472,'armholdingsplcadr':85961,'taiwansemiconductormanufacturingcoltdadr':85442,'cabotmicroelectronicscorp':88152}
km.update(manual)
km['pharmaceuticalproductdevelopmentinc']=82837
km.update({'focusmediaholdingltd':90810,'leapwirelessinternationalinc':90733,'sepracorinc':76845})
fps=pd.read_csv(M/'yahoo_permno_fingerprints.csv');tm={r.ticker:int(r.permnos) for r in fps.itertuples() if '|' not in str(r.permnos) and r.matches>=6 and r.matches/r.periods>.7}
tm.update({'ALXN':83111,'ANSS':83621,'ATVI':79678,'CELG':11552,'CERN':10909,'CTXS':82686,'MYL':69550,'WBA':19502,'SGEN':88949,'SPLK':13379,'MXIM':11896,'XLNX':76201,'ARM_OLD':85961,'NVLS':12067,'NSM':51377,'AMKR':86047,'ATML':76584,'CREE':78875,'AAL':21020,'GOOG':14542})
names=pd.read_csv(B/'full_2009/wrds_sp500_permno_names.csv')
for r in names.itertuples():
 for t in re.split(r'[,;]\s*',str(r.Ticker)):
  if t not in tm:tm[t]=int(r.PERMNO)
# Use exact CUSIP identity when available; blank/placeholder CUSIPs never identify securities.
ci=pd.read_csv(M/'recent_identity_map.csv',dtype=str).fillna('');cm={r.cusip:r.ticker for r in ci.itertuples() if r.cusip and '|' not in r.ticker and r.ticker};nk={norm(r.name):r.ticker for r in ci.itertuples() if r.ticker and '|' not in r.ticker}
nk.update({'ferrovialse':'FER','ferrovialnv':'FER','alphabetincclassc':'GOOG','lmericssontelephonecompany':'ERIC'})
for r in h.to_dict('records'):
 k=r['key'];base=re.sub(r'(?:adr|class[abc]|series[abc])+$','',k)
 if k not in nk and base in nk:nk[k]=nk[base]
nk.update({'strategyincclassa':'MSTR','tradedeskinctheclassa':'TTD','cocacolaeuropacificpartnersplc':'CCEP','gehealthcaretechnologiesinc':'GEHC'})
for k,t in nk.items():
 if t in tm and k not in km:km[k]=tm[t]
# CRSP is the primary historical total-return panel, Yahoo is the later live panel.
p=pd.read_parquet(B/'full_2009/crsp_allcodes_monthly_2007_2019.parquet');late=pd.read_parquet(M/'CRSP_domestic_monthly_2019_2024.parquet');p=pd.concat([p,late]).drop_duplicates(['permno','month'],keep='first');pg={int(n):g.set_index('month').sort_index() for n,g in p.groupby('permno')}
yg={};daily=[]
for f in (R/'raw_prices').glob('*.json'):
 try:
  z=json.loads(f.read_text())['chart']['result'][0];q=z['indicators']['quote'][0];ix=pd.to_datetime(z['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize();d=pd.DataFrame({'date':ix,'open':q['open'],'close':q['close'],'adjclose':z['indicators']['adjclose'][0]['adjclose']}).dropna();d['adjopen']=d.open*d.adjclose/d.close;d['asset']=f.stem;daily.append(d);a=d.set_index('date');v=a.resample('ME').agg(first=('adjclose',lambda x:x.index.min()),last=('adjclose',lambda x:x.index.max()),prc=('close','last'),adj=('adjclose','last'),n=('adjclose','count'));v['gross']=v.adj.pct_change(fill_method=None)+1;v['rows']=v.n;v.index=v.index.to_period('M').astype(str);v['first']=v['first'].astype(str);v['last']=v['last'].astype(str);yg[f.stem]=v
 except (KeyError,TypeError,ValueError):pass
pd.concat(daily,ignore_index=True).to_parquet(M/'yahoo_daily.parquet',index=False)
# Existing archived monthly quotes retain acquired names after Yahoo removes them.
raw=json.loads((B/'credibility_audit/results/corrected_monthly_raw_prices.json').read_text());acts=json.loads((B/'credibility_audit/results/corporate_actions_used.json').read_text())
for line in (B/'stock_nested_2009/drive_inputs/PIT_ALPACA_DELISTED_HISTORY_TRANSFER_20261009.txt').read_text(encoding='utf-8-sig').splitlines():
 try:z=json.loads(line)
 except ValueError:continue
 for g in z.get('data',[]):
  for t,rs in g.get('bars',{}).items():raw.setdefault(t,{}).update({r['timestamp'][:7]:r['close'] for r in rs})
  for kind,rs in g.get('actions',{}).items():
   for r in rs:
    if r.get('symbol'):acts.setdefault(r['symbol'],[]).append(dict(r,kind=kind))
ag={}
for t,rs in raw.items():
 es=[];seen=set()
 for e in acts.get(t,[]):
  k=(e.get('kind'),e.get('ex_date'),e.get('rate'),e.get('old_rate'),e.get('new_rate'),e.get('special'))
  if k not in seen:es.append(e);seen.add(k)
 rows=[]
 for m,q in sorted(rs.items()):
  prev=str(pd.Period(m,'M')-1)
  if prev not in rs:continue
  shares=1.;cash=0.
  for e in sorted([e for e in es if e.get('ex_date','')[:7]==m],key=lambda e:(e['ex_date'],0 if 'splits' in e['kind'] else 1)):
   if e['kind'] in ['forward_splits','reverse_splits']:shares*=float(e['new_rate'])/float(e['old_rate'])
   elif e['kind']=='cash_dividends':cash+=shares*float(e['rate'])
  rows.append(dict(month=m,gross=(q*shares+cash)/rs[prev],prc=q))
 if rows:ag[t]=pd.DataFrame(rows).set_index('month')

def identify(r):
 k=r['key'];sym=cm.get(r['cusip'],'') or nk.get(k,'');pn=km.get(k)
 if pn is None and sym in tm:pn=tm[sym]
 if k=='armholdingsplcadr' and r['report']>'2020':pn=None;sym='ARM'
 if k=='cdwcorp':pn=13949 if r['report']>'2013' else None
 if k=='comcastcorpclassa':pn=89565 if r['report']=='2015-09-30' and r['value']/r['shares']>57 else 89525
 if k=='libertyglobalplc':pn={'G5480U104':90227,'G5480U120':90866}.get(r['cusip'],pn)
 if k=='foxcorp':pn={'35137L105':18420,'35137L204':18421}.get(r['cusip'],pn)
 if k=='discoverycommunicationsinc':pn=90805
 if pn is None:
  matches=[v for key,v in km.items() if len(key)>10 and k.endswith(key)]
  if len(set(matches))==1:pn=matches[0]
 if not sym and pn is not None:
  syms=[t for t,n in tm.items() if n==pn and t in yg]
  if syms:sym=sorted(syms)[0]
 return pn,sym

legacy='AMD ALTR AMKR ADI AMAT ATML BRCM INTC KLAC LLTC LSI MU NSM NVLS SNDK TER TXN XLNX'.split()
tm['SNDK_OLD']=tm.get('SNDK',None)
# Old SanDisk PERMNO obtained from WRDS identity; today's SNDK is a 2025 spin-off.
for r in names[names.Ticker.eq('SNDK')].itertuples():tm['SNDK_OLD']=int(r.PERMNO)
legacy[legacy.index('SNDK')]='SNDK_OLD'
new_index='AMD ALTR ADI AMAT ARM_OLD ASML ATML AVGO BRCM CREE INTC KLAC LRCX LLTC MRVL MXIM MCHP MU NVDA ON SWKS TSM TER TXN XLNX'.split()
closed={'beasystemsinc':'2008-04-29','checkfreecorp':'2007-12-03','xmsatelliteradioholdingsinc':'2008-07-29'}
special_choices={'novellussysteminc':[12067,86580]}
wg={}
if (M/'wiki_extra.parquet').exists():
 w=pd.read_parquet(M/'wiki_extra.parquet');w['date']=pd.to_datetime(w.date)
 for t,g in w.groupby('ticker'):
  v=g.set_index('date').adj_close.resample('ME').last().pct_change(fill_method=None)+1;v.index=v.index.to_period('M').astype(str);wg[t]=v
ev=pd.read_csv(M/'early_price_identity_evidence.csv').fillna('');evmap={(r.key,r.report):[int(v) for v in str(r.candidates).split('|') if v] for r in ev.itertuples()}
allrows=[];checks=[];maps=[]
for fund in ['QQQ','SMH']:
 for trade in pd.period_range('2009-01','2026-10',freq='M'):
  sig=trade-1;siglast=cal.sessions_in_range(sig.start_time,sig.end_time.normalize())[-1];cut=cal.session_close(siglast);first=cal.sessions_in_range(trade.start_time,trade.end_time.normalize())[0];base=str(sig-12);months=[str(sig-j) for j in range(11,0,-1)]
  avail=h[(h.fund==fund)&(pd.to_datetime(h.accepted_UTC,utc=True)<cut)]
  if fund=='SMH' and str(trade)<'2012-01':
   syms=[t for t in legacy if t!='NSM' or str(trade)<'2011-10'];g=[dict(name=t,key=norm(t),ticker=t,permno=tm.get(t),report='2008-09-30',acc='HOLDRS_2008_09',cusip='',shares=0,value=0) for t in syms];mode='HOLDRS'
  elif fund=='SMH' and str(trade)<'2012-03':
   g=[dict(name=t,key=norm(t),ticker=t,permno=tm.get(t),report='2011-09-19',acc='PUBLIC_PRELAUNCH_INDEX',cusip='',shares=0,value=0) for t in new_index];mode='PRELAUNCH_INDEX_PROXY'
  else:
   if avail.empty:checks.append(dict(fund=fund,trade_month=str(trade),blocked='NO_PUBLIC_REPORT'));continue
   # Prefer freshest report period, then earliest publication of that period.
   report=avail.report.max();a=avail[avail.report.eq(report)].sort_values('accepted_UTC').iloc[0];g=avail[avail.acc.eq(a.acc)].to_dict('records');mode='LATEST_PUBLIC_REPORT'
  monthrows=[]
  for r in g:
   pn,sym=(r['permno'],r['ticker']) if 'ticker' in r else identify(r);k=r['key'];status='';score=np.nan
   d=dict(fund=fund,trade_month=str(trade),signal_month=str(sig),trade_date=str(first.date()),report=r['report'],acc=r['acc'],name=r['name'],key=k,permno=pn,ticker=sym,mode=mode)
   if k in closed or (k=='cdwcorp' and r['report']<'2013'):
    d.update(status='EXCLUDE_ACQUIRED_BEFORE_START',momentum=score);monthrows.append(d);continue
   choices=special_choices.get(k,evmap.get((k,r['report']),[])) if pn is None else [pn]
   if pn is None and not (str(sig)>='2020-01' and sym in yg):
    # Bounds cannot certify identity; used only to identify non-winning ambiguities.
    vals=[]
    for n in choices:
     if n in pg and base in pg[n].index and all(m in pg[n].index for m in months):vals.append(float(pg[n].loc[months,'gross'].prod()-1))
    d.update(status='BLOCK_IDENTITY',momentum=np.nan,bound_upper=max(vals) if vals else np.nan);monthrows.append(d);continue
   if str(sig)<'2020-01':a=pg.get(pn);source='CRSP'
   elif sym in yg:a=yg[sym];source='YAHOO'
   elif pn in pg and str(sig)<='2024-12':a=pg[pn];source='CRSP'
   elif sym in ag:a=ag[sym];source='ARCHIVED_ALPACA'
   else:a=None;source='NONE'
   if a is None:status='BLOCK_PRICE_SERIES'
   elif str(sig)>a.index.max() or (source=='CRSP' and str(sig) in a.index and pd.isna(a.loc[str(sig),'prc'])) or (source in ['CRSP','YAHOO'] and str(sig) in a.index and str(a.loc[str(sig),'last'])[:10]<str(siglast.date()) and str(sig)==a.index.max()):status='EXCLUDE_ENDED_TRADING_CHECK_EVENT'
   elif base<a.index.min():status='EXCLUDE_SHORT_HISTORY'
   elif not all(m in a.index for m in months):status='BLOCK_MONTH_GAP'
   elif a.loc[months,'gross'].isna().any():status='BLOCK_RETURN_GAP'
   else:
    v=a.loc[months];score=float(v.gross.prod()-1);status='RANKED'
    if source=='CRSP' and (v.n!=v.rows).any():
     allowed={(76614,'2015-06'),(76744,'2015-05')}
     gaps=[m for m in months if a.loc[m,'n']!=a.loc[m,'rows'] and (pn,m) not in allowed]
     if gaps:
      if sym in yg and all(m in yg[sym].index and pd.notna(yg[sym].loc[m,'gross']) for m in months):
       good=[m for m in months if m not in gaps];error=max([abs(a.loc[m,'gross']-yg[sym].loc[m,'gross']) for m in good]+[0])
       if error<.003:score=float(yg[sym].loc[months,'gross'].prod()-1);source='YAHOO_CROSSCHECKED_CRSP_GAP'
       else:status='BLOCK_DAILY_RETURN_GAP'
      elif 'wg' in globals() and sym in wg and all(m in wg[sym].index for m in months):score=float(wg[sym].loc[months].prod()-1);source='WIKI_CRSP_GAP'
      else:status='BLOCK_DAILY_RETURN_GAP'
   d.update(status=status,momentum=score,price_source=source);monthrows.append(d)
  mr=pd.DataFrame(monthrows);rank=mr[mr.status.eq('RANKED')].sort_values(['momentum','name'],ascending=[False,True]);top=rank.iloc[0] if len(rank) else None
  # Do not discard unknown names; prove their entire price-matching upper bound loses.
  if top is not None and 'bound_upper' in mr:
   bounded=mr.status.eq('BLOCK_IDENTITY')&mr.bound_upper.notna()&(mr.bound_upper<top.momentum);mr.loc[bounded,'status']='BOUNDED_NONWINNER_IDENTITY_UNRESOLVED'
  blocked=mr[mr.status.str.startswith('BLOCK')];allrows+=mr.to_dict('records');checks.append(dict(fund=fund,trade_month=str(trade),trade_date=str(first.date()),report=g[0]['report'],mode=mode,ticker=top.ticker if top is not None else '',permno=top.permno if top is not None else '',name=top['name'] if top is not None else '',momentum=top.momentum if top is not None else np.nan,n_candidates=len(mr),n_ranked=len(rank),n_blocked=len(blocked),blocked='|'.join(blocked.name)))
pd.DataFrame(allrows).to_csv(O/'candidate_rankings.csv',index=False);f=pd.DataFrame(checks);f.to_csv(O/'monthly_selection_audit.csv',index=False);(M/'ticker_permno.json').write_text(json.dumps(tm,indent=2));(M/'manual_name_identities.json').write_text(json.dumps(manual,indent=2))
print(f.groupby('fund').agg(months=('trade_month','size'),blocked_months=('n_blocked',lambda x:(x>0).sum())).to_string());print(pd.DataFrame(allrows).query("status.str.startswith('BLOCK')",engine='python').groupby(['fund','name','status']).size().to_string())
