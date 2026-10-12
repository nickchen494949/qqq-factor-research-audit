from pathlib import Path
import urllib.request,time,json,pandas as pd,pyarrow as pa,pyarrow.parquet as pq
R=Path(__file__).resolve().parent;B=R.parent
c=pd.read_csv(B/'qqq_smh_top1/results/candidate_rankings.csv');ids=set(c.permno.dropna().astype(int))|{12067,86580}
u='https://www.kaggle.com/api/v1/datasets/download/meliodaz/crsp-with-mkt-ret-68-24/crsp_data_dump_daily.csv'
t=time.time();out=[];writer=None
with urllib.request.urlopen(u,timeout=90) as stream:
 for i,d in enumerate(pd.read_csv(stream,chunksize=500000,dtype={'PERMNO':'int32','RET':'str'})):
  d.columns=d.columns.str.lower();d=d[d.permno.isin(ids)&(d.date>='2003-12-01')].copy()
  if len(d):
   d['ret']=pd.to_numeric(d.ret,errors='coerce')
   tab=pa.Table.from_pandas(d,preserve_index=False)
   if writer is None:writer=pq.ParquetWriter(R/'crsp_history_daily.parquet',tab.schema,compression='zstd')
   writer.write_table(tab)
   d['month']=d.date.str[:7];d['gross']=1+pd.to_numeric(d.ret,errors='coerce')
   out.append(d.groupby(['permno','month'],sort=False).agg(first=('date','min'),last=('date','max'),prc=('prc','last'),gross=('gross','prod'),n=('gross','count'),rows=('date','size')).reset_index())
  if i%30==0:print('chunk',i,'seconds',round(time.time()-t),flush=True)
if writer:writer.close()
a=pd.concat(out).sort_values(['permno','month','first']).groupby(['permno','month'],sort=False).agg(first=('first','min'),last=('last','max'),prc=('prc','last'),gross=('gross','prod'),n=('n','sum'),rows=('rows','sum')).reset_index();a.to_parquet(R/'crsp_history_monthly.parquet',index=False)
print('DONE',a.shape,round(time.time()-t),flush=True)
