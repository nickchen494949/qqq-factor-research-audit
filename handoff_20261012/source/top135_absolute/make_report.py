from pathlib import Path
import pandas as pd,html,hashlib,zipfile
r=Path(__file__).resolve().parent
p=pd.read_csv(r/'performance.csv');table=p.copy()
for c in ['CAGR','total_return','MDD','monthly_win','rolling_36m_win','rolling_60m_win']:table[c]=table[c].map(lambda x:f'{x:.2%}')
for c in ['Sharpe','Sortino']:table[c]=table[c].map(lambda x:f'{x:.3f}')
legacy=(r/'README.txt').read_text()
notes='''本轮：Top 1/3/5 + 个股绝对动量，2009-01-02至2026-10-09。
结论：QQQ Top1/3完全不变，Top5略差；SMH Top1年化44.71%升至47.62%，但Top3从35.93%降至34.45%，Top5从30.76%降至28.09%。六组最大回撤均未改善。不能把SMH Top1上的收益改善推广成通用防跌效果。
规则：沿用冻结候选排名，每只入选证券12–1M动量必须严格大于0，否则其1/N份额留现金；不递补、不把现金重新分给其余股票。不加年度上涨频率或五年历史过滤。月末信号、下月首交易日收盘成交；原先要求的开盘成交仍未完成。月内不止损。单边实际交易成本0.1%，含分红拆股，现金按滞后DFF代理收益。
验证：全部六条未过滤策略及两个ETF基准与上轮逐日净值吻合；两条Top1绝对动量与此前结果吻合，误差均小于1e-9。12条策略收益账与股数现金账相符。过滤后没有持有非正动量的新目标，所有现金槽位可在filtered_holdings.csv复核。
过滤频率：QQQ Top1/3为0个月，Top5为1个月；SMH Top1/3/5分别为5/10/16个月，合计过滤5/25/54个证券槽位。整个研究含214个月调仓。
证据：上述为冻结数据的历史回放。推断：这条过滤并非普遍改善，且不能解决已出现的最大回撤。未知：未来是否有效。
限制：继承早期持仓披露滞后、SMH前身及指数代理、第三方CRSP镜像、ARM预告退市退出特例。不是精确完整PIT成员研究，也不是真正未来样本外验证。详见Inherited_Methodology.txt及sources.txt。
复算：安装pandas、numpy、pyarrow，运行replay.py。输入文件全部随包提供；baseline_crosscheck.csv保存与上轮逐日比较结果，原始外部采集过程不在本包重新执行。annual_comparison.csv含各年收益及年内回撤，2026仅至10月9日。
'''
(r/'Inherited_Methodology.txt').write_text(legacy)
(r/'README.txt').write_text(notes)
(r/'Top135_Absolute_Report.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>Top 1/3/5绝对动量对照</title><style>body{font:16px/1.6 sans-serif;max-width:1500px;margin:40px auto;padding:0 24px;color:#172333}table{border-collapse:collapse;font-size:14px}td,th{padding:9px;border:1px solid #cbd5e1;text-align:right}th{background:#e7eef7}pre{white-space:pre-wrap}h1{font-size:28px}</style><h1>绝对动量：没有降低最大回撤</h1><pre>'+html.escape(notes)+'</pre>'+table.to_html(index=False)+'<h2>完整沿用方法与限制</h2><pre>'+html.escape(legacy)+'</pre></html>')
(r/'hashes.json').write_text(__import__('json').dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(r.iterdir()) if f.is_file() and f.name!='hashes.json'},indent=2))
z=r.parent/'Top135_Absolute_Comparison.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
 for f in sorted(r.iterdir()):
  if f.is_file():out.write(f,'top135_absolute/'+f.name)
print(z, z.stat().st_size)
