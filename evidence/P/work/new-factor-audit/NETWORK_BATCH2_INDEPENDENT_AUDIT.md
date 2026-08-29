# Network Batch 2｜最终独立审计

## 唯一结论

四条路线全部维持 `REJECT_STANDALONE`，没有资格进入增量模型：

| 路线 | 审计 | 全期 rho(R63) | 两时期 | 排除 2020/2022 | 最终决定 |
|---|---|---:|---:|---:|---|
| M3 科技订单－库存 | **DEFECT**：数字复算正确，但分子分母产业宇宙不一致 | +0.029193 | +0.075047 / +0.053695 | +0.051613 | `REJECT_STANDALONE` |
| SLOOS C&I 收紧 | **VERIFIED** | +0.221502 | +0.076660 / +0.301515 | +0.124840 | `REJECT_STANDALONE`：预设应为负，实际全为正 |
| QFR 经营利润率变化 | **VERIFIED** | -0.177409 | -0.107233 / -0.277620 | -0.120604 | `REJECT_STANDALONE`：预设应为正，实际全为负 |
| Z.1 券商杠杆增长 | **VERIFIED** | -0.120739 | -0.188104 / -0.154453 | -0.106484 | `REJECT_STANDALONE`：方向稳定但强度未达 0.15 |

两时期依次是 2009–2018 / 2019+。四条都是 current-vintage 形状筛查，不是历史当时版本回测。

## 共同底座复算

- 我从两份冻结 QQQ 日线原始输入重新合并：6,542 + 370，重叠 2 行且完全一致，最终 6,910 个交易日。
- 独立取每个自然季度最后一个真实交易日，并重新算 `past63`、未来第 63 个交易日回报 `R63`、途中最大跌幅 `W63`。得到 2009Q1–2026Q1 共 69 个 origin；2026Q2 因未来 63 日尚未完成，整季删除。
- 69 行的日期、收盘价、终点、R63、W63、past63 与冻结中央表最大误差都是 **0**。四条 signal 也从原始文件重算并重新 as-of 匹配，和各自 joined/features 最大误差都是 **0**。
- 可见日严格按冻结合同：M3/SLOOS 为参考期结束后 45 日，QFR/Z.1 为 90 日；每一行均满足 `available_date <= origin`。SLOOS 的 45 日是合同允许的固定保守回退，不等同于逐期真实发布日期。

## 四条身份与缺陷

### 1. M3：数字正确，来源定义有缺陷

固定信号确实是 `A34SNO` 新订单 log YoY − `A34STI` 总库存 log YoY。独立复算：W63 rho `+0.023760`，past63 rho `-0.096821`。

但官方材料明确显示：新订单没有/排除半导体；电脑与电子产品的库存汇总却包含半导体估计。因此它不是同一产业宇宙的“订单相对库存”。这个缺陷在看结果前已记录，不能用结果后换公式修补。

2010-04 断点前只有 5 个 origin，rho `-1.000000`；断点后 64 个，rho `+0.163416`。断点后看似过 0.15 也不能救活全样本门，而且前段太短、宇宙仍不匹配。审计状态为 **DEFECT**，最终仍是 `REJECT_STANDALONE`。

### 2. SLOOS：系列身份正确，但方向完全相反

原始 CSV 身份逐字核对为：

- ID：`SLOOS/SLOOS/SUBLPDCILS_N.Q`
- 定义：国内银行对大型和中型企业 C&I 贷款标准的净收紧百分比。

预注册要求“越收紧，未来 QQQ 回报越低”，所以 rho 应为负；实际全期、两时期、排除危机后全部为正。W63 rho `+0.004870`，past63 rho `+0.204164`。不能事后翻方向，故 **VERIFIED / REJECT**。

### 3. QFR：用的是经营利润，不是税前利润

身份核对通过：分子是 `QFR104COMUSNO` **Income (Loss) from Operations**，分母是 `QFR101COMUSNO` **Net Sales, Receipts, and Operating Revenues**。固定特征为本季经营利润率减四季前经营利润率（百分点）。没有使用 `QFR111` 税前利润；`QFR105` 利息支出只作描述，未进入门槛。

官方 Census 工作簿的 `OPERINC` / `SALES` / `INTEXP` 共 75 个字段-季度值与 FRED 全部相同，0 个不一致。W63 rho `-0.051750`，past63 rho `-0.020479`。预设正方向却在全期与各分段均为负，故 **VERIFIED / REJECT**。

### 4. Z.1：负方向有直接论文依据，但强度不够

身份与公式正确：`FL664090005.Q` 总金融资产、`FL664190005.Q` 总负债，杠杆为 `assets / (assets - liabilities)`，信号是相对四季前的 log 变化。

负方向不是事后解释。[纽约联储 Staff Report 422](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr422.pdf) 直接报告：券商年度杠杆增长越快，下一季度股票超额回报越低；[Staff Report 625](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr625.pdf) 又报告负的下一季度股票回报系数。它们与本轮固定四季 log 增长、负方向一致。

2016Q3 前 n=31、rho `-0.297409`；后 n=38、rho `-0.103639`。Fed 也明确说明该季因外国银行设立美国 IHC，券商部门的母公司投资和外国直接投资处理发生结构变化。[Fed 部门说明](https://www.federalreserve.gov/releases/z1/preview/html/table_desc_sectors.htm)

方向和三个稳定性分段都没翻，但全期 `abs(rho)=0.120739 < 0.15`，不能用断点前强结果救活，故 **VERIFIED / REJECT**。

## 门槛、停止与证据完整性

- 四条均有 n=69；两时期 n=40 / 29；排除 2020/2022 后 n=61，样本资格全部达标。
- 唯一合法 standalone 通过要求是：全期达到预设方向且 `abs(rho)>=0.15`，两个时期与排除危机后都不反向。M3、Z.1 失败在强度；SLOOS、QFR 失败在方向。
- `incremental_ran=false`；没有增量预测文件，QFR/Z.1 也没有第二关结果。因为在 standalone 已停止，训练集 purge 为 `NOT_APPLICABLE`，不是“漏查 purge”。
- 核心脚本行数：M3/SLOOS 264、QFR 250、Z.1 282；独立脚本 111 / 93，全部不超过 300 行软上限。
- 原始、特征、结果清单逐文件验证通过。关键 aggregate SHA-256：M3/SLOOS raw `02877bce…234c`、features `09760b72…e851`、results `9e379807…6f4`；QFR raw `827019a0…65e` 且 5/5 输出哈希匹配；Z.1 raw `7ccf97fe…82b0`、derived `bf8c1460…307b`、results `98b86fab…b9b`。

## PIT 结论上限

M3/SLOOS 是当前下载快照；QFR 数值来自当前 FRED 历史，Census 工作簿只做身份交叉核对；Z.1 只冻结了 2026-06-11 current release。都没有逐历史发布日期重建当时可见数值。因此，即使统计门通过也最多只能叫 `PROXY_PASS`；本轮四条连 standalone 都没过，不应继续花成本做 vintage 或复杂模型。

最终：**M3 = DEFECT + REJECT；SLOOS/QFR/Z.1 = VERIFIED + REJECT；incremental = NOT RUN。**
