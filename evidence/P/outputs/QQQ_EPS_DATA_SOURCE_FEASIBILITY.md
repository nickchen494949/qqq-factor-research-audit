# Nasdaq-100 / QQQ 总体 EPS 数据来源闸门

日期：2026-08-28（Asia/Kuala_Lumpur）

## 结论

**BLOCK：目前没有找到一个免费的 Nasdaq-100／QQQ 总体 EPS、Forward EPS 或盈利修正序列，同时满足 2009 至今、至少月频、当时版本可追溯、方法清楚、可导出和许可明确。**

**用户决策（2026-08-28）：接受“大概就好”的免费代理。** 因此数据闸门按 `PROXY_ACCEPTED` 条件通过：History of Market 作为长历史主代理，MacroMicro 和 GuruFocus 只负责形状对照。这个决定允许继续做探索性关系诊断，但不改变“免费精确真值仍为 BLOCK”的事实。

## 已生成的可用代理

- 公式：`隐含 Forward EPS = Nasdaq 官方 NDX 收盘 ÷ History of Market Forward P/E`。
- 覆盖：2009-01-02 至 2026-08-05，共 919 个周度点。
- 日期处理：P/E 日期只向后匹配最近 NDX 交易日，绝不使用未来价格；最大滞后 1 天。
- 完整性：隐含 EPS 缺失 0；Excel 公式错误扫描为 0。
- 最新值：隐含 Forward EPS 约 1318.18；最近 13 周变化约 +9.43%，方向标为“上调”。
- 输出：`NDX_IMPLIED_FORWARD_EPS_PROXY_SINCE_2009.csv`、`.xlsx`、`.png`。

这条数据可用于“大致方向／形状”的探索。它仍混合了 NTM 自然滚动、指数换股、P/E 来源误差和可能的历史改写，不能称为官方分析师 revision。

## 跨来源形状对照（已完成）

- 同类核验：MacroMicro Nasdaq-100 Forward P/E 的公开图表形状，对照 History of Market Forward P/E。2009 年以后 37 个约半年度点，形状相关 **0.940**；36 次相邻转折中 **26 次同方向（72.2%）**。
- 盈利核验：GuruFocus Nasdaq-100 实际 EPS，对照我们的隐含 Forward EPS。2023Q1–2026Q2 共 14 个季度点，同季水平相关 **0.968**，13 次季度方向中 **10 次同方向（76.9%）**。
- 领先关系：用我们的隐含 Forward EPS 领先 GuruFocus 实际 EPS 四个季度，10 对季度点相关 **0.821**。

**判定：大致通过。** 曲线没有出现明显反向或数量级错误，足够支持“70 分左右的免费形状代理”。但 MacroMicro 是从公开 SVG 图形读取的像素形状，GuruFocus 又是实际 EPS 而非 Forward EPS；因此这项核验不能解决 PIT/vintage、方法和许可问题。

输出：`NDX_EPS_PROXY_SHAPE_COMPARISON.csv`、`.svg`、`.png`、`.md`。

找到的不是完全没用，而是各自缺一块：

- GuruFocus：有 **Nasdaq-100 总体 actual EPS**，但不是 forward/revision，下载收费，方法和历史版本不透明。
- MacroMicro：有 **Nasdaq-100 Forward P/E**，但公开页面不披露上游来源和算法；旧 Forward EPS 页面已不可公开访问。
- History of Market：有很长的 NDX Forward P/E JSON，但没有供应商字段和 vintage，且与 Nasdaq 官方锚点约差 4%–5%。
- LSEG I/B/E/S Global Aggregates：产品能力最接近正式答案，但公开资料没有明确确认 NDX，且为商业报价产品。

旧负面证据已先读完；已完成的公开 Nasdaq 有界搜索没有重复。没有继续公司级身份／成分重建，也没有开始模型或回测。

## 通过标准

候选必须同时做到：

1. 宇宙明确为 Nasdaq-100（NDX）或 QQQ，而不是 S&P 500、泛科技或若干代表公司。
2. 历史至少覆盖 2009 至今，频率至少月度。
3. 能回答“当时市场知道什么”，并说明旧值会不会被后来资料改写。
4. 披露 EPS、Forward EPS 或 revision 的计算定义与成分处理。
5. 能导出原始历史序列。
6. 免费或价格、留存、研究发表权明确。

## 决策矩阵

| 来源 | 宇宙／定义 | 历史／频率 | Vintage | 方法 | 导出 | 价格／许可 | 判定 |
|---|---|---|---|---|---|---|---|
| **LSEG I/B/E/S Global Aggregates** | 指数级预测、估值、revision；公开页未明确列出 NDX | 月度 1985 起；周度 2006 起 | 历史很长，但公开页不足以确认 NDX 旧值保留规则 | 16 measures、112+ datatypes；公开描述聚合自指数成分与权重 | Excel、API、Web Service、Cloud、FTP、Bulk | 商业报价；NDX entitlement 未知 | **BLOCK**：最接近正式解，但要供应商确认 NDX mnemonic、样本、vintage 和报价 |
| **GuruFocus Nasdaq 100 Earnings per Share** | 直接 Nasdaq-100 actual EPS | 季频，83 个点，约 2005/06 至今 | 未披露历史快照／修订保存 | 页面来源只写 GuruFocus；聚合法未披露 | 数据下载标 Premium | 看图免费；下载收费；再使用边界不清 | **PROXY**：可对照总体 actual EPS 形状，不能当 PIT forward/revision |
| **MacroMicro Nasdaq-100 Forward P/E** | 直接 Nasdaq-100 Forward P/E；不是 EPS 本身 | 月频，2001-01 至 2026-08 | 未披露历史版本 | 未披露供应商、field code、亏损公司和换股处理 | 页面存在 CSV 下载窗口，但公开操作只显示图片导出；旧 Forward EPS 链接已重定向 | 看图免费；原始数据权限／条款不清 | **PROXY**：可看形状，不能当可审计 Forward EPS 真值 |
| **History of Market NDX Forward P/E JSON** | 声称 NDX 12M blended-forward P/E | 1,239 个周点，2001-04 至 2026-08；中间有断档 | 单次当前快照；无修订日志 | 只写 terminal data；供应商和字段未知 | JSON 可取 | 网页内容许可与上游数据权冲突未解决 | **PROXY**：长历史探索可用；正式证据不通过 |
| **Siblis 免费 API** | NDX forward P/E | 免费层仅 8 个日期，2023-12 至 2026-06 | 未验证 | 方法证据不足 | API 可导出 | 免费层非商业使用 | **REJECT**：历史不足 |
| **Nasdaq 官方公开资料** | 官方 NDX 图表和零散 Forward EPS／P/E 锚点 | 只有若干报告窗口，没有连续历史下载 | 单篇报告当时值可信 | 图表常引用 Bloomberg／FactSet | 无连续 EPS 序列导出 | 公开阅读；指数数据再用需许可 | **REJECT**：适合验锚点，不是可用时间序列 |
| **Zacks / Nasdaq Data Link ZEE** | 约 5,000 家公司的逐股共识，不是指数 aggregate | 公司级长期历史，日更 | 产品有历史，但本闸门未取得 NDX aggregate | 公司级 consensus 方法 | API／bulk／SFTP | Premium／报价 | **REJECT**：方向不对，不是总体序列 |
| **FactSet PIT / LSEG PIT 公司级 + Nasdaq 历史权重** | 可重建可信 NDX revision，但不是直接 aggregate 产品 | PIT 历史足够 | 强 | 公司级 PIT 和官方权重方法可审计 | 商业交付 | 双重商业授权 | **REJECT（本闸门）**：理论可行，但会重新进入公司级重建，违反当前边界 |

## 为什么不能把三个免费页面直接当真值

```text
看到一条 Nasdaq-100 总体曲线
  ├─ 只看得到图，没有原始数据？ → 不能回测
  ├─ 不知道谁提供、怎么算？       → 无法确认同一个定义
  ├─ 不知道旧值会不会被覆盖？     → 可能把今天知道的东西塞回过去
  └─ 不知道使用权？               → 无法稳定保存和发布

以上任何一项缺失
  ↓
只能标 PROXY，不能标 PASS
```

## 当前可选路线

### 1. 免费代理继续

只把 History of Market／MacroMicro／GuruFocus 当形状和方向代理。优点是免费、马上可用；缺点是不能宣称“真实 PIT Nasdaq-100 Forward EPS”，正式回测结论上限仍很低。

### 2. 商业样本验证

先向 LSEG 要，不直接购买：

- NDX 的具体 mnemonic／series ID；
- 2009、2020、2022 和最近日期的样本；
- EPS、Forward EPS、revision ratio 定义；
- 历史值是否保留当时版本；
- CSV/API 导出、留存、图表发表许可与报价。

只有样本全部通过，LSEG 才能由 BLOCK 改为 PASS。

### 3. 停止 EPS 分支

如果不接受代理，也不购买／试用商业数据，就停止这条分支。不能为了继续而把公司样本包装成 Nasdaq-100 总体 EPS。

## 最终工作流

```text
目标：Nasdaq-100／QQQ 总体盈利预期
  ↓
先查免费直接 aggregate
  ├─ Nasdaq 官方连续序列        → 没有 → REJECT
  ├─ GuruFocus actual EPS       → 无 vintage／下载收费 → PROXY
  ├─ MacroMicro Forward P/E     → 无来源／Forward EPS 隐藏 → PROXY
  ├─ History of Market JSON     → 无 PIT／官方锚点有偏差 → PROXY
  └─ Siblis 免费 API            → 只有 8 个日期 → REJECT
  ↓
再查信誉商业 aggregate
  └─ LSEG Global Aggregates     → 产品能力够，但 NDX 未公开确认／收费 → BLOCK
  ↓
GATE 0 结果：BLOCK_FREE_EXACT_AGGREGATE
  ├─ proxy：接受降级后才继续探索
  ├─ buy：先索取 LSEG 样本，不盲买
  └─ stop：停止 EPS 分支

禁止：公司级重建、模型、回测、修改生产策略
```

## 主要来源

- [LSEG I/B/E/S Global Aggregates](https://www.lseg.com/en/data-catalogue/company-data/ibes-estimates/global-aggregates)
- [GuruFocus Nasdaq 100 Earnings per Share](https://www.gurufocus.com/economic_indicators/5870/nasdaq-100-earnings-per-share)
- [MacroMicro Nasdaq-100 Forward P/E](https://en.macromicro.me/series/23955/nasdaq-100-pe)
- [Nasdaq Data Link：数据产品组织说明](https://docs.data.nasdaq.com/docs/data-organization)
- [Zacks Consensus Data](https://zacksdata.com/datasets/consensus-data/)
- [Nasdaq Global Index Watch：NDX History](https://indexes.nasdaq.com/Index/History/NDX)

**一句话：免费能看到 Nasdaq-100 总体盈利相关曲线，但找不到既能下载、又能证明来源和当时版本的合格数据，所以现在必须诚实停在 BLOCK。**
