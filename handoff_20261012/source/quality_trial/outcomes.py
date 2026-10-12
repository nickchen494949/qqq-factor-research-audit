from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent
s=pd.read_csv(R/'monthly_audit.csv');p=pd.read_parquet(R/'prices.parquet');d={a:g.set_index('date').sort_index().adjclose for a,g in p.groupby('asset')};ix=pd.read_csv(R/'reference_nav.csv',index_col=0,parse_dates=True).index;end=ix[-1]
rows=[]
for fund,g in s.groupby('fund'):
 g=g.sort_values('trade_date').reset_index(drop=True)
 for i,z in enumerate(g.itertuples()):
  dt=pd.Timestamp(z.trade_date);series=d[z.asset];row=z._asdict();one=pd.Timestamp(g.iloc[i+1].trade_date) if i+1<len(g) else pd.NaT
  row['one_month_stock_return']=series.get(one,np.nan)/series.get(dt,np.nan)-1
  target=dt+pd.DateOffset(years=1);j=ix.searchsorted(target);last=ix[j] if j<len(ix) else pd.NaT
  row['twelve_month_stock_return']=series.get(last,np.nan)/series.get(dt,np.nan)-1
  row['forward_12m_end']=last;rows.append(row)
o=pd.DataFrame(rows);o.to_csv(R/'signal_outcomes.csv',index=False)
rows=[]
for (f,k),g in o.groupby(['fund','filter_status']):
 a=g.one_month_stock_return.dropna();b=g.twelve_month_stock_return.dropna();rows.append(dict(fund=f,status=k,signal_months=len(g),n_monthly=len(a),monthly_avg=a.mean(),monthly_positive=(a>0).mean(),n_12m=len(b),double_rate=(b>=1).mean(),half_loss_rate=(b<=-.5).mean(),mean_12m=b.mean()))
pd.DataFrame(rows).to_csv(R/'outcome_summary.csv',index=False);print(pd.DataFrame(rows).round(4).to_string(index=False))
