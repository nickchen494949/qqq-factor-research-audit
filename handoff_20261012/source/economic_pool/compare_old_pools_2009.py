"""Fresh-capital, common-window replication of frozen legacy ETF universes.

Primary legacy specification: 12 complete months of fund history.
Predeclared sensitivity: 60 complete months, the recent economic-pool rule.
All funds are 1x; 12-1 total-return signals; monthly first-open execution.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
env = {'__file__': str(BASE / 'backtest.py')}
exec(compile((BASE / 'backtest.py').read_text().split('results={};ledger=[]')[0],
             str(BASE / 'backtest.py'), 'exec'), env)
OUT = BASE / 'old_pools_2009'
OUT.mkdir(exist_ok=True)
END = pd.Timestamp('2026-10-09')
POOLS = {
    'Legacy13': 'SMH SOXX XLE XLF XLK XLV XLY XLP XLI XLB XLU XLRE XLC'.split(),
    'Legacy24': 'SPY QQQ SMH SOXX IWM DIA MTUM SPMO QUAL USMV XBI ITA XRT XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC'.split(),
    'Legacy32': 'SPY QQQ SMH SOXX IWM DIA MTUM SPMO QUAL USMV XBI ITA XRT XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC EEM EFA GLD TLT IEF LQD HYG SGOV'.split(),
    'Economic22': env['POOL'],
}
assert [len(v) for v in POOLS.values()] == [13, 24, 32, 22]
assert set().union(*map(set, POOLS.values())) <= set(env['SYMS'])
C, O = env['C'], env['O'].copy()
# The shared engine liquidates at the final row's open. Substitute only that
# row with its close, for common terminal liquidation, never for the signal.
assert END in C.index
O.loc[END] = C.loc[END]
env['END'] = END
rates = pd.read_csv(BASE / 'raw/DFF.csv', index_col=0, parse_dates=True).iloc[:, 0].astype(float) / 100
rates = rates.reindex(pd.date_range(rates.index[0], END, freq='D')).ffill().shift(2)

def stats(v):
    r = v.pct_change()
    r.iloc[0] = v.iloc[0] - 1
    days = v.index.to_series().diff().dt.days.fillna(0)
    excess = r - rates.reindex(v.index) * days / 360
    assert excess.notna().all()
    # Include initial cash in the high-water mark.
    peak = np.maximum.accumulate(np.r_[1., v.to_numpy()])[1:]
    return dict(CAGR=v.iloc[-1] ** (365.25 / ((v.index[-1] - v.index[0]).days + 1)) - 1,
                MDD=(v.to_numpy() / peak - 1).min(),
                Sharpe=excess.mean() / excess.std(ddof=1) * np.sqrt(252),
                Sortino=excess.mean() / np.sqrt(np.mean(np.minimum(excess, 0) ** 2)) * np.sqrt(252),
                volatility=r.std(ddof=1) * np.sqrt(252), multiple=v.iloc[-1])

def independent_terminal(logs, v):
    # Reconstruct every monthly boundary using reported picks and raw adjusted
    # open ratios. This independently checks daily-engine terminal compounding.
    wealth = 1.
    values = {}
    for i, row in enumerate(logs):
        date = pd.Timestamp(row['date'])
        picks = row['holdings'].split()
        assert np.isclose(wealth, row['nav_open_before'], rtol=1e-10)
        # Solve transaction cost with zero target for outgoing positions.
        after = wealth
        for _ in range(20):
            after = wealth - .001 * sum(abs((after / len(picks) if s in picks else 0.) - values.get(s, 0.))
                                       for s in set(picks) | set(values))
        nxt = pd.Timestamp(logs[i+1]['date']) if i+1 < len(logs) else END
        values = {s: after / len(picks) * O.loc[nxt, s] / O.loc[date, s] for s in picks}
        wealth = sum(values.values())
    assert np.isclose(wealth * .999, v.iloc[-1], rtol=1e-10)

rows, navs, ledger = [], {}, []
for start in ['2009-01-02', '2017-02-01']:
    ix = C.loc[start:END].index
    env.update(IX=ix, CV=C.loc[ix].to_numpy(), OV=O.loc[ix].to_numpy(),
               REBAL={i: dt for i, dt in enumerate(ix) if i == 0 or dt.month != ix[i-1].month})
    for age in [12, 60]:
        for pool, tickers in POOLS.items():
            for k in [1, 3]:
                name = f'{pool}_Top{k}_{age}m_{start}'
                v, logs = env['run'](name, tickers, k, age, .001)
                assert logs[0]['date'] == start and logs[0]['nav_open_before'] == 1.
                for row in logs:
                    dt = pd.Timestamp(row['date'])
                    prev = dt.to_period('M') - 1
                    # Independently calculate signal from the two past month-end prices.
                    manual = {}
                    for s in tickers:
                        if prev.ordinal - env['FIRST'][s].ordinal < age:
                            continue
                        a = env['MC'].loc[(prev-1).to_timestamp('M'), s]
                        b = env['MC'].loc[(prev-12).to_timestamp('M'), s]
                        if pd.notna(a) and pd.notna(b):
                            manual[s] = a / b - 1
                    expected = sorted(manual, key=lambda s: (-manual[s], s))[:k]
                    assert row['holdings'].split() == expected
                independent_terminal(logs, v)
                rows.append(dict(strategy=name, pool=pool, k=k, age_months=age,
                                 start=start, end=str(END.date()), **stats(v)))
                navs[name] = v
                ledger.extend(logs)
    for asset in ['QQQ', 'SPY']:
        name = f'{asset}_{start}'
        v, logs = env['run'](name, [asset], 1, 0, .001, True)
        expected = C.loc[END, asset] / O.loc[ix[0], asset] / 1.001 * .999
        assert np.isclose(v.iloc[-1], expected, rtol=1e-12)
        rows.append(dict(strategy=name, pool=asset, k=0, age_months=0,
                         start=start, end=str(END.date()), **stats(v)))
        navs[name] = v
        ledger.extend(logs)

summary = pd.DataFrame(rows)
summary.to_csv(OUT / 'summary.csv', index=False)
nav = pd.DataFrame(navs)
nav.to_csv(OUT / 'daily_nav.csv')
pd.DataFrame(ledger).to_csv(OUT / 'holdings.csv', index=False)
annual = []
for name, v in navs.items():
    previous = 1.
    for dt, value in v.resample('YE').last().items():
        annual.append(dict(strategy=name, year=dt.year, return_=value / previous - 1))
        previous = value
pd.DataFrame(annual).to_csv(OUT / 'annual_returns.csv', index=False)
(OUT / 'frozen_pools.json').write_text(json.dumps(POOLS, indent=2))
# Reconciliation against the immediately preceding 2009 study.
old = pd.read_csv(BASE / 'comparison_2009/summary.csv').set_index('strategy')
for key, prior in [('Economic22_Top1_60m_2009-01-02', 'Top1_1x'),
                   ('Economic22_Top3_60m_2009-01-02', 'Top3_1x'),
                   ('QQQ_2009-01-02', 'QQQ_1x')]:
    row = summary.set_index('strategy').loc[key]
    assert np.allclose(row[['CAGR', 'MDD', 'Sharpe', 'Sortino']].astype(float),
                       old.loc[prior, ['CAGR', 'MDD', 'Sharpe', 'Sortino']].astype(float), atol=1e-12)
inputs = env['SYMS']
manifest = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [BASE/'raw'/f'{s}.json' for s in inputs] + [BASE/'raw/DFF.csv', BASE/'backtest.py', Path(__file__)]}
(OUT / 'SHA256.json').write_text(json.dumps(manifest, indent=2))
print(summary.to_string(index=False))
print('PASS: common dates; independent historical signal picks; monthly/daily wealth match; direct QQQ buy/hold formula; previous 2009 study reconciliation.')
