from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parent;B=R.parent
p=pd.read_parquet(R/'prices.parquet');ix=p.index;c=pd.read_parquet(B/'green5_test/crsp_history_daily.parquet');c.date=pd.to_datetime(c.date);pg={int(n):g.set_index('date').sort_index() for n,g in c.groupby('permno')}
original=pd.read_parquet(B/'qqq_smh_top1/metadata/trading_prices.parquet');orig={t:g.set_index('date').sort_index() for t,g in original.groupby('asset')}
costfrac=pd.DataFrame(1.,index=ix,columns=p.columns);events=[]
def cash(asset,pn,date,amount):
 dt=pd.Timestamp(date);last=p.loc[p.index<dt,asset].last_valid_index();raw=pg[pn].loc[last,'prc'];p.loc[dt:,asset]=p.loc[last,asset]*amount/abs(raw);costfrac.loc[dt:,asset]=0.;events.append(dict(asset=asset,date=date,kind='cash_merger',cash=amount,last_raw=raw))
cash('ALTR',75577,'2015-12-28',54.);cash('NSM',51377,'2011-09-26',25.);cash('SGEN',88949,'2023-12-14',229.)
def rawquote(t):
 j=json.load(open(R/(t+'.json')))['chart']['result'][0];return pd.Series(j['indicators']['quote'][0]['close'],index=pd.to_datetime(j['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize())
def bundle(asset,pn,date,cash,legs):
 dt=pd.Timestamp(date);end=ix[ix>=dt][:35][-1];days=ix[(ix>=dt)&(ix<=end)];last=p.loc[p.index<dt,asset].last_valid_index();raw=abs(pg[pn].loc[last,'prc']);val=pd.Series(cash,index=days);stock=pd.Series(0.,index=days)
 for coef,q in legs:
  z=q.reindex(days);assert z.notna().all();stock+=coef*z
 val+=stock;p.loc[days,asset]=p.loc[last,asset]/raw*val;costfrac.loc[days,asset]=stock/val;events.append(dict(asset=asset,date=date,kind='successor_basket',cash=cash,last_raw=raw))
bundle('P_89644',89644,'2013-06-10',17.5,[(.2582,pg[90227].prc.abs()),(.1928,pg[90866].prc.abs())])
bundle('P_77668',77668,'2018-12-21',48.75,[(.2434,rawquote('CI'))])
# Hold both actual successor share entitlements across the March 19 spin-off.
fox=orig.get('FOX')
if fox is None:
 yy=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');fox=yy[yy.asset.eq('FOX')].set_index('date')
start=pd.Timestamp('2019-03-19');last=pd.Timestamp('2019-03-18');days=ix[(ix>=start)&(ix<=pd.Timestamp('2019-04-15'))]
parent=pd.Series(.736817*.4517*rawquote('DIS').reindex(days),index=days);parent.loc[start]=.736817*49.61
value=parent+fox.close.reindex(days)/3;assert value.notna().all()
p.loc[days,'P_90442']=p.loc[last,'P_90442']/abs(pg[90442].loc[last,'prc'])*value
events.append(dict(asset='P_90442',date='2019-03-19',kind='FOX_distribution_and_DIS_default_stock',cash=0,last_raw=abs(pg[90442].loc[last,'prc'])))
bundle('P_85963',85963,'2016-02-01',51.4829,[(.0242,pg[93002].prc.abs())])
# ADR foreign-currency settlement unavailable: pre-announced liquidation on last session.
# MIAX notice Sep 2 2016 15:14 ET, before market close, confirms Sep 6 delisting.
dt=pd.Timestamp('2016-09-06');last=pd.Timestamp('2016-09-02');p.loc[dt:,'ARM_OLD']=p.loc[last,'ARM_OLD']*.999;costfrac.loc[dt:,'ARM_OLD']=0.;events.append(dict(asset='ARM_OLD',date='2016-09-06',kind='announced_exit_prior_close',cash=None,last_raw=abs(pg[85961].loc[last,'prc'])))
p.to_parquet(R/'prices_events.parquet');costfrac.to_parquet(R/'cost_fraction.parquet');pd.DataFrame(events).to_csv(R/'events.csv',index=False)
print(pd.DataFrame(events).to_string(index=False))
