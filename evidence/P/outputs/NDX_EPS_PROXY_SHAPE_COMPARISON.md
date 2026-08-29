# Nasdaq-100 EPS 代理形状核验

## 结论

大致通过：长期 Forward P/E 形状高度吻合，隐含 EPS 与后来实际 EPS 的大方向也吻合。

- MacroMicro Forward P/E vs History of Market Forward P/E（2009+）：形状相关 **0.940**；相邻转折同方向 **26/36（72.2%）**。
- GuruFocus 实际 EPS vs 我们同季隐含 Forward EPS（2023Q1–2026Q2）：水平相关 **0.968**；季度方向同向 **10/13（76.9%）**。
- 我们的隐含 Forward EPS 领先 GuruFocus 实际 EPS 四个季度：相关 **0.821**（10 对季度点）。

## 口径限制

1. MacroMicro 数值来自公开图表 SVG 路径的约 53 个半年度像素点，是形状核验，不是原始数据下载。
2. GuruFocus 是实际 EPS，我们的是价格÷Forward P/E 得出的隐含 Forward EPS；只能比较趋势，不能比较绝对数值。
3. 这能排除“曲线明显画错”的大问题，不能证明来源具备 PIT/vintage，也不能把代理升级为官方真值。

## 来源

- https://en.macromicro.me/series/23955/nasdaq-100-pe
- https://www.gurufocus.com/economic_indicators/5870/nasdaq-100-earnings-per-share
