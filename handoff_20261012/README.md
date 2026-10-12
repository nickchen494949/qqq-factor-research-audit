# QQQ / SMH 选股回测交接（2026-10-12）

**当前要做的是：实际 EPS 超过公告前市场预期，随后按 EPS 同比增长率选 Top 1。该策略没有完成可信收益回测。**

**52.76% 是另一套“12–1M 动量＋绝对动量＋现金流质量”SMH 实验的年化，绝不是 EPS 策略的结果。**

本目录是独立交接快照，旧仓库根目录是更早的研究，不应混为同一实验。本交接保存本轮工作区的研究代码、冻结输入、逐月选择、净值、报告、历史交付包内容和已知问题。

## 给接手 AI 的阅读顺序

1. [HANDOFF_ZH.md](HANDOFF_ZH.md)：用户目标、确认事项、助手假设、已有结果、错误和缺口。
2. [NEXT_AI_PROMPT.txt](NEXT_AI_PROMPT.txt)：可直接粘贴的接手指令。
3. [DATA_AND_REPRODUCTION.md](DATA_AND_REPRODUCTION.md)：数据位置与复算入口。
4. [INTEGRITY.json](INTEGRITY.json)：实际文件数量、包完整性、检查结果。
5. [FILE_MANIFEST.json](FILE_MANIFEST.json)：逐文件 SHA-256 与所有原始路径。

## 直接浏览代码

[source/](source/) 展开当前研究源码与关键摘要，可直接在 GitHub 阅读。运行时仍需下方完整工作区的数据；不要仅下载 source 后声称缺数据。

## 恢复完整工作区

下载本分支或 git clone 后，进入本目录：

```bash
python restore_workspace.py --output workspace --include-archives
python -m pip install -r requirements.txt
cd workspace
python eps_growth/audit.py
```

`audit.py` 只重算数据覆盖和候选审计，不计算本策略收益。

全部研究文件采用去重数据包存储，多个历史版本保留独立路径。`parts/` 是二进制分片，不是缺失数据的占位符；恢复脚本检查每片、整个数据包、每个文件的 SHA-256。脚本默认拒绝覆盖内容不同的已有文件。

`workspace/` 恢复当前研究目录；`workspace/historical_archives/` 恢复以前正常 ZIP 的全部成员文件；`workspace/quarantine/` 保留四个不能通过 ZIP 格式检查的旧包原始字节。旧 ZIP 容器不重新伪造，内容和旧文件清单分别保留。使用解开的当前研究目录复算。

## 已有与没有

| 项目 | 状态 |
|---|---|
| ETF 池轮动、QQQ/SMH 12–1M Top1、Top3/5 | 已有探索性回测及代码/数据 |
| 绝对动量、年度上涨频率、相对 ETF 上涨频率 | 已有探索性回测及逐月结果 |
| EPS+营收双超预期过滤旧动量 Top1 | 已有不完整数据试验；不是当前要求 |
| 现金流质量及与绝对动量组合 | 已有试验；此前错误地当作当前任务，必须区分 |
| EPS 超预期＋EPS 同比增速 Top1 | 规则与全候选覆盖审计已有；收益回测未完成 |
| 2009 起完整可验证的公告前 EPS 共识 | 没有 |
| 精确逐月 PIT 成分库、完整开盘交易版、独立样本外证据 | 没有完成 |

所有已有收益都是特定冻结输入下的历史模拟，不是未来收益证明。原始材料中较乐观或陈旧的描述不能覆盖本交接的限制说明。
