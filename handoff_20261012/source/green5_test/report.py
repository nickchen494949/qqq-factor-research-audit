from pathlib import Path
import pandas as pd,json,shutil,zipfile,hashlib
R=Path(__file__).resolve().parent;B=R.parent
p=pd.read_csv(R/'performance.csv').set_index('strategy');names={'QQQ_original':'QQQ 原版','QQQ_five_year_history':'QQQ 仅五年历史','QQQ_green3of5':'QQQ 五年历史＋3/5上涨','QQQ_BH':'直接持有 QQQ','SMH_original':'SMH 原版','SMH_five_year_history':'SMH 仅五年历史','SMH_green3of5':'SMH 五年历史＋3/5上涨','SMH_BH':'直接持有 SMH'}
t=p.loc[list(names),['CAGR','MDD','Sharpe','Sortino','monthly_outperform']].copy();t.index=t.index.map(names)
for col in ['CAGR','MDD','monthly_outperform']:t[col]=t[col].map(lambda x:f'{100*x:.2f}%')
for col in ['Sharpe','Sortino']:t[col]=t[col].map(lambda x:f'{x:.3f}')
t.loc[['直接持有 QQQ','直接持有 SMH'],'monthly_outperform']='—';t.columns=['年化收益','最大回撤','Sharpe','Sortino','月度跑赢对应ETF']
s=pd.read_csv(R/'signals.csv');a=pd.read_csv(R/'annual_returns.csv',index_col=0);display=a[list(names)].rename(columns=names).map(lambda x:f'{100*x:.2f}%')
text='''结论：没有证据支持把“过去五年至少三年上涨”作为统一改进规则。QQQ相对原版的改善主要来自五年历史门槛；增加3/5过滤后收益略降、最大回撤加深。SMH增加3/5过滤后收益与风险调整表现均下降。属于探索性、回顾性研究，不是独立样本外验证。
规则：2009-01-02至2026-10-09；QQQ/SMH各自选12–1M动量第一名股票；月末排名，下月首交易日收盘交易，盈利亏损正常卖。单边0.1%，末日清仓0.1%，含分红拆股。与此前收盘版同口径，不是仍缺6个开盘价的开盘版。
历史过滤：交易年份Y只检查Y-5至Y-1五个完整日历年。必须有Y-6年12月底基准价及60个月收益。完整年度总回报>0算上涨。不得使用当年全年收益。例：2009选股检查2004–2008，2026检查2021–2025。
三个对照：原版；仅要求五年历史；五年历史且至少3年上涨。先过滤，再在全部合格候选中选动量最高者，不是把原版落选月份直接设为空仓。
现金：无候选时持现金，按滞后2日DFF年率/360计息；这是假设现金可获得该基准利率，非某只真实现金ETF。SMH过滤版2009年12个月全部为空仓，错过该年的市场反弹；其他版本无空仓。
月度跑赢率：2009年1月至2026年9月，共213个月；首月从2009-01-02收盘起算。2026年10月不完整，不纳入该统计。Sharpe/Sortino使用日收益，扣相同滞后DFF无风险收益，sqrt(252)年化；Sortino下行偏差按全部交易日计算。最大回撤按日末净值。
验证：过滤版428*2=856个基金-月份选择均已审计。年度原始收益缺口用独立Yahoo年回报交叉检查，18个证券-年份窗口通过；仍有11个待核的低排名历史窗口，均无法超过已确定入选者，因此未影响本次第一名选择。早期两个月歧义名称按两个身份分别评估，也不改变选择。所有实际持仓日价格齐全；四条新策略两套独立记账最大误差<1e-14；新引入Yahoo股票实际持有日期与CRSP交叉检查无大于0.5个百分点的日收益差异。
限制：早期QQQ使用有滞后的公开持仓名单，不是精确逐月指数成分。SMH早期为HOLDRS，2012最初两个月使用已公开的发行前指数名单。CRSP由公开第三方镜像获得，非持牌直接交付。这次补数覆盖候选证券2003年12月起历史，保留退市证券；没有解决此前研究的全部成分身份/披露时滞问题。原版曾披露的VRTX两个日收益源差异仍在。重复尝试过滤条件会增加过拟合风险，未做真正未来样本验证。
复算：reproduce.py从冻结价格和交易选择独立重建四条新策略NAV并核对。rank.py、replay.py、validate.py是原工作区完整研究脚本；其部分路径依赖前期研究目录，不应声称在此ZIP单独直接运行。候选逐月审计、年度收益、源月收益和实际持仓价格已随包提供。
来源：原有冻结候选名单与回测；Yahoo Chart缓存复权数据；https://www.kaggle.com/api/v1/datasets/download/meliodaz/crsp-with-mkt-ret-68-24/crsp_data_dump_daily.csv；DFF缓存。读取日期2026-10-11。
'''
(R/'README.txt').write_text(text)
html='<!doctype html><meta charset="utf-8"><title>五年三年上涨过滤回测</title><style>body{font:16px system-ui;max-width:1250px;margin:40px auto;line-height:1.7}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:8px;text-align:right}th{background:#e7eef7}h1,h2{color:#163b60}</style><h1>五年历史与3/5上涨：分别带来什么？</h1><p><b>QQQ改善主要来自五年历史门槛。额外3/5上涨条件没有改善收益与回撤；SMH反而明显退步。</b></p>'+t.to_html()+'<h2>规则、验证与限制</h2>'+''.join('<p>'+line+'</p>' for line in text.splitlines())+'<h2>逐年收益（2026截至10月9日）</h2>'+display.to_html()+'<h2>逐月选择</h2>'+s[['fund','variant','trade_month','name','asset','green_years','n_eligible']].to_html(index=False)
(R/'Green3of5_Report.html').write_text(html)
shutil.copy(B/'qqq_smh_top1/metadata/DFF.csv',R/'DFF.csv')
# Derive a small annual-source monthly panel from the frozen live price dataset.
y=pd.read_parquet(B/'qqq_smh_top1/metadata/yahoo_daily.parquet');out=[]
for asset,g in y.groupby('asset'):
 p=g.set_index('date').sort_index().adjclose.resample('ME').last();d=pd.DataFrame({'month':p.index.to_period('M').astype(str),'gross':p.pct_change(fill_method=None).values+1,'asset':asset});out.append(d)
pd.concat(out).to_parquet(R/'yahoo_source_monthly.parquet',index=False)
(R/'file_hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.iterdir() if f.is_file() and f.name!='file_hashes.json'},indent=2))
with zipfile.ZipFile(B/'Green3of5_Backtest.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in R.iterdir():
  if f.is_file():z.write(f,f.name)
print('ZIP bytes',(B/'Green3of5_Backtest.zip').stat().st_size)
