from pathlib import Path
import pandas as pd,numpy as np,json,html,zipfile,hashlib,shutil
R=Path(__file__).resolve().parent;B=R.parent;O=R/'results';M=R/'metadata'
v=pd.read_csv(O/'daily_nav.csv',index_col=0,parse_dates=True);perf=pd.read_csv(O/'performance.csv');s=pd.read_csv(O/'monthly_signals.csv');r=pd.read_csv(O/'candidate_rankings.csv')
labels={'QQQ_close':'QQQ 内 Top 1 股票','SMH_close':'SMH 内 Top 1 股票（含旧 HOLDRS）','QQQ_BH_close':'QQQ 买入持有','SPY_BH_close':'SPY 买入持有','QQQ_open':'QQQ 内 Top 1 股票 · 开盘版','QQQ_BH_open':'QQQ 买入持有 · 开盘版','SPY_BH_open':'SPY 买入持有 · 开盘版'}
summary=perf.copy();summary['策略']=summary.strategy.map(labels)
for c in ['CAGR','MDD']:summary[c]=summary[c].map(lambda x:f'{x:.2%}')
for c in ['Sharpe','Sortino','multiple']:summary[c]=summary[c].map(lambda x:f'{x:.2f}')
summary=summary[['策略','CAGR','MDD','Sharpe','Sortino','multiple']].rename(columns={'CAGR':'年化收益','MDD':'最大回撤','multiple':'期末倍数'})
annual=v.resample('YE').last();annual=annual.div(annual.shift(1).fillna(1))-1;annual.index=annual.index.year;annual.to_csv(O/'annual_returns.csv')
monthly=v.resample('ME').last();monthly=monthly.div(monthly.shift(1).fillna(1))-1;monthly.to_csv(O/'monthly_returns.csv')
stats=[];cuts=[]
for c in v:
 a=monthly[c];wins=a[a>0];loss=a[a<0];stats.append(dict(strategy=c,monthly_win_rate=(a>0).mean(),average_positive_month=wins.mean(),average_negative_month=loss.mean(),monthly_win_loss_ratio=wins.mean()/abs(loss.mean()),monthly_profit_factor=wins.sum()/abs(loss.sum())))
 for stop in ['2019-12-31','2025-12-31','2026-10-09']:
  a=v.loc[:stop,c];cuts.append(dict(strategy=c,end=str(a.index[-1].date()),CAGR=a.iloc[-1]**(365.25/((a.index[-1]-a.index[0]).days+1))-1))
pd.DataFrame(stats).to_csv(O/'monthly_win_loss_statistics.csv',index=False);pd.DataFrame(cuts).to_csv(O/'endpoint_sensitivity.csv',index=False)
hold=s.pivot(index='trade_month',columns='fund',values='asset');hold.to_csv(O/'QQQ_SMH_monthly_holdings.csv')
age=[]
for row in s.itertuples():age.append(dict(fund=row.fund,trade_month=row.trade_month,report=row.report,age_days=(pd.Timestamp(row.trade_date)-pd.Timestamp(row.report)).days,mode=row.mode))
pd.DataFrame(age).to_csv(O/'holdings_age.csv',index=False)
sources=[
('旧 SMH：2008 年完整 18 股名单','https://www.sec.gov/Archives/edgar/data/1110511/000094787108000596/ss50403_ex9901-semi.htm'),
('2011 年 SMH 换基金文件及预先公开的新指数 25 股名单','https://www.sec.gov/Archives/edgar/data/1110511/000093041311006395/c66640_ex-a4.htm'),
('Expedia / TripAdvisor 分拆','https://ir.tripadvisor.com/ir-resources/investor-faqs'),
('ASML 2012 资本返还与缩股','https://www.sec.gov/Archives/edgar/data/937966/000119312512470856/d439738dex991.htm'),
('PPDI 收购与退市','https://www.sec.gov/Archives/edgar/data/1003124/000119312511330317/d265257d8k.htm'),
('Focus Media 收购与退市','https://www.sec.gov/Archives/edgar/data/1330017/000130901413000380/exhibit1.htm'),
('Leap Wireless 收购与退市','https://www.sec.gov/Archives/edgar/data/1065049/000089882214000121/body.htm'),
('Sepracor 收购','https://www.sec.gov/Archives/edgar/data/877357/000110465909059514/a09-31847_1sctota.htm'),
('WRDS 股票身份历史','https://wrds-www.wharton.upenn.edu/classroom/sp500-introduction/over-time/'),
('历史 CRSP 数据的第三方镜像（非直接供应商交付）','https://www.kaggle.com/datasets/meliodaz/crsp-with-mkt-ret-68-24'),
('2020 年保存的 Yahoo 日线档案','https://www.kaggle.com/datasets/jacksoncrow/stock-market-dataset')]
text='''QQQ / SMH 各自选 Top 1 股票：2009–2026 研究回测
更新：2026-10-11；区间：2009-01-02 至 2026-10-09。

【结论】同期间、相同收盘成交规则下，SMH Top 1 的历史收益较高；QQQ Top 1 的风险调整后表现弱于直接持有 QQQ，最大回撤约 84%。这些数字属于“当时已披露持仓版”，不能冒充每日精确历史成分股版。

【同口径结果：下月首个交易日收盘成交】
'''+summary.iloc[:4].to_string(index=False)+'''

【已完成的开盘版本】
'''+summary.iloc[4:].to_string(index=False)+'''

【重要限制，读收益前必须理解】
1. 原先约定的 SMH 开盘成交版尚未完成：缺旧 LSI 两个、旧 ARMH 四个真实成交开盘价，详见 execution_coverage.csv。没有用收盘价伪造开盘价。主表明确改用收盘成交，全部策略及基准一致；这是一项另列的执行敏感性研究，不是原开盘版已经完成。
2. QQQ 早期取自年度持仓申报，候选池使用信号时已经公开的最新报告。股票池有明显滞后，不能称为当时每日实际 QQQ / Nasdaq-100 成分股。它可表达“用已披露名单选股”的规则，但不能验证更及时更新的名单策略。
3. SMH 2009–2011 使用 Semiconductor HOLDRS 历史名单；2011 年底以后切换到新基金。2012 年 1–2 月使用成立前已公开的目标指数名单做代理，从 2012 年 3 月开始使用已公开的基金持仓。全期结果是明确拼接的研究策略，不是现行 VanEck 基金自 2009 年已存在。
4. 原始 QQQ 2007 报告有 Novellus 名称与估值不一致的问题。对可能的 NVLS 与 NVDA 都检验后，两者在受影响的 2009 年 1–2 月均不是赢家，故不影响 Top 1；仍保留原文歧义，未篡改原始持仓。
5. 早期总回报来自 CRSP 的公开第三方镜像，并用 WIKI / Yahoo 日线交叉核对，未获得商业供应商对整套数据的认证。普通分红、拆股和特殊分拆不能只看未经复权的价格。Expedia 2011 分拆与 ASML 2012 资本返还使 Yahoo 与 CRSP 的回看窗口回报有显著差异；排名使用包含分配的 CRSP 总回报。
6. 这仍是事后设计的历史研究，没有前瞻样本外验证。2026 年迄今的强劲表现明显抬高全期年化；不能把这些 CAGR 当作未来预期。

【固定规则】
每条策略只在自己的候选池内选 1 只股票；不先比较 QQQ 和 SMH。
月末 t 的分数 = t-12 月末到 t-1 月末的总回报；跳过最近一个月。
月末信号；下月首个 NYSE 交易日成交。报告主表使用收盘；另列已完成的 QQQ 开盘版。
1 倍、100% 单只股票、不加杠杆、不做负动量过滤；盈利亏损都按下一次排名正常换仓。
只有持仓改变才收取买卖费用；每次买或卖 10 bp，末日按卖出计费。未扣个人税费、融资费用，也未模拟 50 万美元订单的真实市场冲击。
月度历史资格至少覆盖基准月末与随后的 11 个回报月；已退市或尚未形成足够历史的股票不可买。候选股数据不明会阻塞信号，不能静默删除。
最大回撤由每日净值计算；Sharpe 使用每日超额收益均值 / 标准差 × √252；Sortino 使用每日超额收益均值 / 全体交易日下行偏差 × √252。无风险基准为滞后联邦基金利率，按实际天数 / 360 扣除。
现金分配按总回报序列再投资，允许小数份额。月度胜率/赚赔比见 monthly_win_loss_statistics.csv，指日历月净值收益，不是逐笔交易胜率。

【核验与修正】
428 条月度信号（每条策略 214 条）；已取得 169 份相关申报文件，逐份保留来源与披露时间。
按基金披露时间过滤，不能将期末持仓在尚未公开时用于排名。
识别旧/新 SNDK、旧/新 ARM、旧 LSI 与后来同代码房地产公司；LSI 同代码误接已在交叉核验中修正。
SIRI 2010 年当前复权数据的价格精度损失已用历史 WIKI 原始报价纠正。
独立“份额账本”与“收益连乘”两种净值算法一致，最大相对误差小于 1e-10。
早期实际持仓日收益的跨源检查剩下 VRTX 2009-03-24 / 25 两天报价差异（约 0.47 个百分点、次日抵消）；保留 Yahoo 与 WIKI 一致的报价。相关日期没有换仓。差异表随包提供，不声称逐笔数据零误差。

【复算】
压缩包的 replay_frozen.py 仅需要所附冻结日线、逐月信号和无风险利率即可复算主表，不需联网。
原始获取/解析/身份核验脚本及原始资料另附；这些研究阶段脚本引用上一项研究的大型资料，不能声称整个历史数据供应链都可脱离原档案独立重建。
主表、每年/每月收益、完整逐月选股、成交记录、数据差异、开盘价缺口均保留。

【来源】
'''+ '\n'.join(a+'\n'+u for a,u in sources)
(O/'QQQ_SMH_Status.txt').write_text(text)
cut=pd.DataFrame(cuts);cut=cut[cut.strategy.isin(labels.keys()) &cut.strategy.str.endswith('_close')].pivot(index='strategy',columns='end',values='CAGR');cut.index=cut.index.map(labels)
fmt=lambda f:f.map(lambda z:f'{z:.2%}')
ann=annual[['QQQ_close','SMH_close','QQQ_BH_close','SPY_BH_close']].rename(columns=labels)
css='body{font-family:system-ui,-apple-system,sans-serif;max-width:1120px;margin:40px auto;padding:0 24px;line-height:1.65;color:#182435;background:#f7f9fc}h1{font-size:30px}h2{margin-top:32px}table{border-collapse:collapse;width:100%;background:white;margin:18px 0;font-size:14px}th,td{padding:9px 12px;border-bottom:1px solid #dce3ec;text-align:right}th:first-child,td:first-child{text-align:left}th{background:#e8eef7}p{max-width:950px}.notice{padding:16px 20px;background:#fff0dd;border-left:5px solid #c78324}.good{padding:16px 20px;background:#e8f0f6}.details{white-space:pre-wrap;font-size:14px}a{color:#17568d}summary{cursor:pointer;font-weight:650}small{color:#586779}'
body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QQQ / SMH Top 1 · 2009–2026 研究回测</title><style>{css}</style><body><small>历史研究 · 2009-01-02 → 2026-10-09 · 2026-10-11 更新</small><h1>QQQ 与 SMH，各自只买动量第一股票</h1><div class="notice"><b>这是已披露持仓、收盘成交版。</b>QQQ 早期名单来自年度申报，有披露滞后；SMH 含旧 HOLDRS 和两个月公开指数代理。SMH 原约定开盘版尚缺 6 个真实开盘价，不能称为全部完成。</div><p>同口径研究中，SMH Top 1 收益较高。QQQ Top 1 虽提高了年化收益，最大回撤却达到约 84%，Sharpe 和 Sortino 均低于直接持有 QQQ。</p><h2>同期间、同成交规则</h2><p>12–1M 总回报排名；每月换仓；下月首个交易日收盘成交；每次实际买卖各 10 bp；无杠杆。所有基准同日起止。</p>{summary.iloc[:4].to_html(index=False,border=0)}<h2>去掉最近一年，再看结论</h2><p>下表均从 2009-01-02 开始，显示不同截止日的年化收益。2026 的大涨明显提高了全期数字。</p>{fmt(cut).to_html(border=0)}<h2>已完成的 QQQ 开盘版</h2>{summary.iloc[4:].to_html(index=False,border=0)}<h2>逐年收益</h2><p>2026 为截至 10 月 9 日的年内收益；2009 从首个交易日收盘投入。</p>{fmt(ann).to_html(border=0)}<h2>每个月实际选了谁</h2><p>ARM_OLD、SNDK_OLD 明确指旧上市主体；LSI 为旧半导体公司。这里只列月度目标，连续同一股票不额外换手。</p>{hold.to_html(border=0)}<h2>完整方法、验证和限制</h2><div class="details">{html.escape(text)}</div></body></html>'''
(B/'QQQ_SMH_2009_2026_Report.html').write_text(body)
# Standalone replay uses only frozen inputs and an independent shares ledger.
shutil.copyfile(B/'economic_pool/raw/DFF.csv',M/'DFF.csv')
repro='''from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;O=R/'results';M=R/'metadata'
s=pd.read_csv(O/'monthly_signals.csv');d=pd.read_parquet(M/'trading_prices.parquet');data={t:g.set_index('date').sort_index() for t,g in d.groupby('asset')};reference=pd.read_csv(O/'daily_nav.csv',index_col=0,parse_dates=True);ix=reference.index
rates=pd.read_csv(M/'DFF.csv',index_col=0,parse_dates=True).iloc[:,0]/100;rates=rates.reindex(pd.date_range(rates.index.min(),ix[-1])).ffill().shift(2)
out=[]
for label in reference:
 f,execution=label.rsplit('_',1);a=s[s.fund.eq(f)];sig=a.set_index(pd.to_datetime(a.trade_date)).asset.to_dict() if not f.endswith('_BH') else {ix[0]:f[:-3]};qty=0.;cash=1.;old='CASH';nav=[]
 for dt in ix:
  new=sig.get(dt,old)
  if new!=old:
   key='adjopen' if execution=='open' else 'adjclose'
   if old!='CASH':cash=qty*data[old].loc[dt,key]*.999
   qty=cash/1.001/data[new].loc[dt,key];old=new
  val=qty*data[old].loc[dt,'adjclose'];nav.append(val*.999 if dt==ix[-1] else val)
 v=pd.Series(nav,index=ix);error=float(np.max(np.abs(v/reference[label]-1)));assert error<1e-10
 ret=v.pct_change();ret.iloc[0]=v.iloc[0]-1;ex=ret-rates.reindex(ix)*ix.to_series().diff().dt.days.fillna(0)/360;a=np.r_[1,v.to_numpy()]
 out.append(dict(strategy=label,CAGR=v.iloc[-1]**(365.25/((ix[-1]-ix[0]).days+1))-1,MDD=(a/np.maximum.accumulate(a)-1).min(),Sharpe=ex.mean()/ex.std(ddof=1)*252**.5,Sortino=ex.mean()/np.sqrt(np.minimum(ex,0).pow(2).mean())*252**.5,max_nav_error=error))
print(pd.DataFrame(out).to_string(index=False))
'''
(R/'replay_frozen.py').write_text(repro)
files=[f for f in R.rglob('*') if f.is_file() and '__pycache__' not in str(f)]
manifest={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files};(O/'artifact_hashes.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(B/'QQQ_SMH_Research_Checkpoint.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in R.rglob('*'):
  if f.is_file() and '__pycache__' not in str(f):z.write(f,str(f.relative_to(B)))
 z.write(B/'QQQ_SMH_2009_2026_Report.html','QQQ_SMH_2009_2026_Report.html')
print('REPORT',len(body),'ZIP',(B/'QQQ_SMH_Research_Checkpoint.zip').stat().st_size);print(summary.to_string(index=False))
