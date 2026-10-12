from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
c=pd.read_csv(B/'green5_test/candidate_audit.csv');base=pd.read_csv(B/'qqq_smh_top1/results/monthly_signals.csv');raw=pd.read_csv(B/'qqq_smh_top1/results/candidate_rankings.csv')
yg=set(pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet').asset)
old_map={int(r.permno):r.asset for r in base[base.trade_month<'2020'].itertuples() if pd.notna(r.permno)}
etf={};thresholds=[]
for f in ['QQQ','SMH']:
 j=json.loads((R/(f+'.json')).read_text())['chart']['result'][0];p=pd.Series(j['indicators']['adjclose'][0]['adjclose'],index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize());etf[f]=p
 ar=p.resample('YE').last().pct_change();ar.index=ar.index.year
 for yr in range(2009,2027):
  a=ar.loc[list(range(yr-5,yr))];assert a.notna().all() and len(a)==5
  thresholds.append(dict(fund=f,trade_year=yr,required_green=int((a>0).sum()),years=f'{yr-5}-{yr-1}',annual_returns=json.dumps(a.to_list())))
th=pd.DataFrame(thresholds);th.to_csv(R/'etf_thresholds.csv',index=False)
pd.DataFrame(etf).to_csv(R/'etf_adjusted_prices.csv')
rows=[];blocked=[]
for (f,m),g in c.groupby(['fund','trade_month'],sort=False):
 year=int(m[:4]);n=int(th[(th.fund==f)&(th.trade_year==year)].required_green.iloc[0]);rank=g.sort_values(['momentum','name'],ascending=[False,True]);eligible=rank[rank.history_status.eq('COMPLETE')&(rank.green_years>=n)];top=eligible.iloc[0] if len(eligible) else None;score=top.momentum if top is not None else -np.inf
 # Missing annual data must not be silently dropped if it could affect the winner.
 un=rank[rank.history_status.str.startswith(('UNKNOWN','REVIEW'))&(rank.momentum>=score)]
 if len(un):blocked+=un.to_dict('records')
 amb=raw[(raw.fund==f)&(raw.trade_month==m)&raw.status.eq('BOUNDED_NONWINNER_IDENTITY_UNRESOLVED')]
 if len(amb) and (amb.bound_upper>=score).any():blocked.append(dict(fund=f,trade_month=m,name='AMBIGUOUS_EARLY_IDENTITY'))
 orig=base[(base.fund==f)&(base.trade_month==m)].iloc[0]
 asset='CASH' if top is None else (str(top.ticker) if year>=2020 and top.ticker in yg else old_map.get(int(top.permno),str(top.ticker) if pd.notna(top.ticker) else 'P_'+str(int(top.permno))))
 rows.append(dict(fund=f,trade_month=m,trade_date=orig.trade_date,variant='relative_green',ticker=top.ticker if top is not None else 'CASH',permno=top.permno if top is not None else np.nan,name=top['name'] if top is not None else 'CASH',asset=asset,momentum=score,green_years=top.green_years if top is not None else np.nan,etf_green_years=n,n_eligible=len(eligible),stock_annual_returns=top.annual_returns if top is not None else '[]',original_asset=orig.asset))
pd.DataFrame(rows).to_csv(R/'signals.csv',index=False);pd.DataFrame(blocked).to_csv(R/'blocked.csv',index=False)
print('BLOCKED',len(blocked));print(pd.DataFrame(blocked).to_string(index=False));print(th[['fund','trade_year','required_green']].to_string(index=False));assert not blocked
