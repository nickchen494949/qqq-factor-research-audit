from pathlib import Path
import pandas as pd,numpy as np,html,json,hashlib,zipfile
R=Path(__file__).resolve().parent
p=pd.read_csv(R/'performance.csv');s=pd.read_csv(R/'monthly_audit.csv');o=pd.read_csv(R/'outcome_summary.csv');coverage=s.groupby(['fund','filter_status']).size().unstack(fill_value=0);coverage['unknown_pct']=coverage.unknown/coverage.sum(axis=1);coverage.to_csv(R/'coverage.csv')
notes='''双超预期初步数据试验，2009-01-02至2026-10-09。
状态：已运行，但不能作为可信完整双超预期策略验证。公开第三方网页的预期数据缺失、历史拆股后EPS取整、缺乏可验证的当时快照，影响大量选股月份。结果不得宣传为已证明/否定该因子。
规则：保留原QQQ/SMH的12–1M Top1选股。信号日为调仓月份前一日；仅用信号日之前公布的最近季度，不跳过最新缺失财报去找上一份好财报；超过150天视为未知。营收与EPS均明确高于预期才为pass；至少一项明确低于预期为fail；其余unknown。以网页显示数值的舍入区间判断方向，区间重叠（含显示相等）不能断言真正达标/不达标。这是严格的可判定子样本，非所有财报。
两个缺失处理试验：unknown_keep只将明确fail月份持现金，unknown仍沿用股票；unknown_cash只买明确pass，unknown与fail均持现金。两者是不同缺失处理假设，绝非真实策略收益的上下界。现金不递补其他股。
执行：每月首交易日收盘调整；持仓相同不交易；股票交易额单边0.1%；末日卖出0.1%；分红拆股沿用原冻结数据；现金DFF代理利息。原先开盘成交仍未完成。两条未过滤基准逐日复现旧结果，两套持仓账本核对。
命中率诊断：signal_outcomes.csv按每个历史Top1信号，考察该股票此后12个月持有总回报是否>=100%，以及期末亏损<=-50%的概率；后者不是期间最大回撤。此诊断与每月换仓收益分开。完整12个月终点缺失则NA，未将缺失当作未翻倍。月份及前瞻窗口重叠，同一股票反复入选，并非独立样本；pass/fail的时间及股票构成不同，不能当因果或统计显著性结论。退市后缺少一年端点的案例可能造成诊断选择偏差，必须同时看n_12m与signal_months。
重要限制：本轮仅测试原Top1后加筛选，不是全候选池基本面重排，也没有完成G-score或双阶段飙涨分类模型。不得根据结果调阈值宣称样本外。早期ETF名单披露滞后、SMH前身和代理、第三方CRSP、公司身份等限制全部继承原研究。
来源：每个网页URL和获取状态在fetch_log.csv；季度表events.csv；逐月所用季度和分类在monthly_audit.csv。来源是nextearningsdate.com的earnings-surprises/history页面。该站的不同历史数据展示精度不同，不是经认证PIT数据服务。ALTR代码复用、旧ARM和旧SNDK等未直接复用现代同代码历史。
后续需要：包含已退市证券及身份映射、公告时间、公告前营收/EPS共识、同口径实际值、未取整数值及版本说明的数据。已查到Intrinio/Zacks相关接口，但未获得本任务可用的授权历史数据；未购买或假装已下载。
复算：pandas,numpy,pyarrow,lxml；replay.py从monthly_audit.csv与冻结价格复算。outcomes.py计算命中率。analyze.py/fetch.py是数据审计和获取脚本，实时重抓页面可能与冻结events不同；归档包保留提取的结构化数据，不含整站HTML。
'''
(R/'README.txt').write_text(notes)
display=p.copy()
for c in ['CAGR','total_return','MDD','monthly_win_rate','rolling_36m_win_rate','rolling_60m_win_rate']:display[c]=display[c].map(lambda x:f'{x:.2%}')
for c in ['Sharpe','Sortino']:display[c]=display[c].map(lambda x:f'{x:.3f}')
(R/'Earnings_Surprise_Trial.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>双超预期试验：覆盖不足</title><style>body{font:16px/1.6 sans-serif;max-width:1400px;margin:36px auto;padding:0 20px}table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #ccc;padding:8px}th{background:#eef2f8}pre{white-space:pre-wrap}</style><h1>已试跑；覆盖不足，不能认定有效</h1><pre>'+html.escape(notes)+'</pre><h2>覆盖率</h2>'+coverage.to_html()+'<h2>缺失处理敏感性：不是完整策略结论</h2>'+display.to_html(index=False)+'<h2>重叠信号的后续收益诊断</h2>'+o.round(4).to_html(index=False)+'</html>')
(R/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2))
z=R.parent/'Earnings_Surprise_Trial.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zz:
 for f in sorted(R.iterdir()):
  if f.is_file():zz.write(f,'earnings_trial/'+f.name)
print(coverage.to_string());print(z,z.stat().st_size)
