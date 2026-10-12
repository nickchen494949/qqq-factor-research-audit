"""Full candidate-pool EPS surprise + YoY growth audit. No return claims.
Public historical web tables are NOT certified point-in-time estimate snapshots.
"""
from pathlib import Path
from io import StringIO
import pandas as pd
import numpy as np
import re,json
R=Path(__file__).resolve().parent
c=pd.read_csv(R/'candidates.csv')
def interval(x):
    x=str(x).replace(',','').replace('$','').strip()
    m=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)',x)
    if not m:return np.nan,np.nan
    n=float(m[1]);dec=len(m[1].split('.')[1]) if '.' in m[1] else 0
    h=.5*10**(-dec)
    return n-h,n+h
def tables(t,kind):
    p=R/'raw'/f'{t}_{kind}.html'
    if not p.exists():return []
    try:return pd.read_html(StringIO(p.read_text()),converters={'Expected':str,'Actual':str})
    except Exception:return []
events=[];errors=[]
for ticker in (sorted(c.ticker.dropna().unique()) if (R/'raw').exists() else []):
    hs=[t for t in tables(ticker,'history') if {'Earnings Date','Period'}.issubset(t.columns)]
    es=[t for t in tables(ticker,'surprises') if list(t.columns)==['Period','Expected','Actual','Surprise']]
    if not hs or len(es)!=2:
        errors.append(dict(ticker=ticker,error='no complete paired tables'));continue
    h=hs[0][['Period','Earnings Date']].copy()
    h['announced']=pd.to_datetime(h['Earnings Date'],errors='coerce')
    h=h.dropna(subset=['announced']).drop_duplicates('Period')
    e=es[0].drop_duplicates('Period').copy()
    g=h.merge(e,on='Period',how='left',validate='one_to_one')
    g['ticker']=ticker
    g['source_url']=f'https://www.nextearningsdate.com/{ticker.lower()}-earnings-surprises.html'
    events.extend(g.to_dict('records'))
e=pd.DataFrame(events) if (R/'raw').exists() else pd.read_csv(R/'events.csv',parse_dates=['announced'],dtype={'Actual':str,'Expected':str})
e.to_csv(R/'events.csv',index=False)
if (R/'raw').exists():pd.DataFrame(errors).to_csv(R/'source_errors.csv',index=False)
cache={t:g.sort_values('announced') for t,g in e.groupby('ticker')} if len(e) else {}
rows=[]
for z in c.itertuples(index=False):
    rec=z._asdict();cut=pd.Timestamp(z.trade_month)-pd.Timedelta(days=1)
    rec.update(cutoff=cut,decision='unknown',reason='missing identity or EPS tables',growth=np.nan,growth_low=np.nan,growth_high=np.nan)
    # A lack of 12-month PRICE history is not a reason to exclude an EPS candidate.
    if z.status in ['EXCLUDE_ENDED_TRADING_CHECK_EVENT','EXCLUDE_ACQUIRED_BEFORE_START']:
        rec.update(decision='not_tradable',reason=z.status);rows.append(rec);continue
    g=cache.get(z.ticker)
    if z.ticker in ['ALTR','SNDK_OLD','ARM_OLD']:g=None
    if g is None:rows.append(rec);continue
    p=g[g.announced<=cut]
    if not len(p):rec['reason']='no report by signal date';rows.append(rec);continue
    now=p.iloc[-1];rec.update(period=now.Period,announced=now.announced,actual=now.Actual,expected=now.Expected,source_url=now.source_url)
    if (cut-now.announced).days>150:rec['reason']='latest report stale';rows.append(rec);continue
    al,ah=interval(now.Actual);el,eh=interval(now.Expected)
    if not np.isfinite([al,ah,el,eh]).all():rec['reason']='missing EPS actual or estimate';rows.append(rec);continue
    if ah<=el:rec.update(decision='fail',reason='not above preannouncement estimate');rows.append(rec);continue
    if al<=eh:rec['reason']='surprise sign ambiguous after rounding';rows.append(rec);continue
    m=re.fullmatch(r'Q([1-4]) (\d{4})',str(now.Period))
    if not m:rec['reason']='unrecognized fiscal quarter';rows.append(rec);continue
    lastperiod=f'Q{m[1]} {int(m[2])-1}'
    before=p[p.Period.eq(lastperiod)&p.announced.lt(now.announced)]
    if len(before)!=1:rec['reason']='missing prior-year same-quarter EPS';rows.append(rec);continue
    prior=before.iloc[0];bl,bh=interval(prior.Actual)
    rec.update(prior_period=prior.Period,prior_announced=prior.announced,prior_actual=prior.Actual)
    if not np.isfinite([bl,bh]).all():rec['reason']='invalid prior-year EPS';rows.append(rec);continue
    if bh<=0:rec.update(decision='fail',reason='nonpositive base; turnaround separately excluded');rows.append(rec);continue
    if bl<=0:rec['reason']='near-zero base ambiguous after rounding';rows.append(rec);continue
    if ah<=bl:rec.update(decision='fail',reason='no positive YoY growth');rows.append(rec);continue
    if al<=bh:rec['reason']='growth sign ambiguous after rounding';rows.append(rec);continue
    rec.update(decision='pass',reason='positive surprise and positive YoY growth in displayed data',growth=(al+ah)/(bl+bh)-1,growth_low=al/bh-1,growth_high=ah/bl-1)
    rows.append(rec)
a=pd.DataFrame(rows);a.to_csv(R/'candidate_audit.csv',index=False)
out=[]
for (fund,month),g in a.groupby(['fund','trade_month']):
    active=g[g.decision.ne('not_tradable')];known=active.decision.isin(['pass','fail']);good=active[active.decision.eq('pass')].sort_values(['growth','ticker'],ascending=[False,True])
    r=dict(fund=fund,month=month,candidates=len(active),known=int(known.sum()),unknown=int((~known).sum()),eligible=len(good),coverage=known.mean(),public_table_complete=bool(known.all()),PIT_verified=False,status='BLOCKED_DATA')
    if len(good):
        w=good.iloc[0];others=good.iloc[1:];r.update(observed_subset_top=w.ticker,observed_top_growth=w.growth,ranking_robust_to_rounding=bool(not len(others) or w.growth_low>others.growth_high.max()))
    out.append(r)
o=pd.DataFrame(out);o.to_csv(R/'monthly_coverage.csv',index=False)
agg=o.assign(year=o.month.str[:4]).groupby(['fund','year']).agg(months=('month','size'),candidate_months=('candidates','sum'),known_candidate_months=('known','sum'),complete_months=('public_table_complete','sum'))
agg['coverage']=agg.known_candidate_months/agg.candidate_months;agg.to_csv(R/'annual_coverage.csv')
usable=e[pd.to_numeric(e.Actual,errors='coerce').notna()&pd.to_numeric(e.Expected,errors='coerce').notna()]
summary=dict(candidate_rows=len(c),event_tickers=int(e.ticker.nunique()),earliest_public_event=str(e.announced.min()),earliest_event_with_actual_and_estimate=str(usable.announced.min()),latest_public_event=str(e.announced.max()),verified_backtest_available=False)
(R/'summary.json').write_text(json.dumps(summary,indent=2))
print(summary)
print(agg.to_string())
