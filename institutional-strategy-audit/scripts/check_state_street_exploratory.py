#!/usr/bin/env python3
import csv
import math
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'data' / 'state_street_mri_exploratory.csv'
rows = list(csv.DictReader(p.open()))

# Formal correlation intentionally excludes the ambiguous 2025-07-22 row (signal_code=0).
usable = [r for r in rows if float(r['signal_code']) != 0]


def corr(xs, ys):
    mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
    return num/den if den else float('nan')

x = [float(r['signal_code']) for r in usable]
y3 = [float(r['spy_3m_return_pct']) for r in usable]
y6 = [float(r['spy_6m_return_pct']) for r in usable]

print({'n': len(usable), 'corr_3m': corr(x,y3), 'corr_6m': corr(x,y6)})
print('WARNING: exploratory only; tiny sample, subjective stance coding, not a valid inference test.')
