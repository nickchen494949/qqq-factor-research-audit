# QQQ 仓位拥挤诊断最终独立审计

审计日期：2026-08-29  
结论：**APPROVE_WITH_LIMITATIONS**

## 人话结论

修复已经真实生效。五条候选全部 `REJECT`、Gate D 不运行、复杂模型继续锁住，这个负面决定可以批准；未发现会把候选错误判成 REJECT 的代码、日期或门槛问题。

仍然不能把这批历史称为严格 point-in-time 或完整 vintage，因为 FINRA、BIS、MOF、EBP 和 CFTC 年度档本身会修订。这个限制已经在合同和来源矩阵披露，不影响“当前免费代理没有通过 Gate C”的结论。

## 最终快照

- 脚本：`db0af1916c7aff6ad34892b0b755f12f1c09152c44cfc8b6023b4e66a283c4f6`
- 冻结合同：`6bd4762e526f110e771b7150133023e64ee179d536a94d23b64cf8bd8ef588b6`
- 来源矩阵：`f775e83f629a3c70ee1ff4fc2e7cba3e0965b11e7715e914eb3c5e88d49d688e`
- CSV：`4202f0b50211bcfb2a1719b3ec9c160c92f7efb36106b4a53d9f1d7483968d4a`
- JSON：`dc91291fc77528ac736481020eebf1d2befea72ba992c5efc5017442c1d6e235`
- Markdown：`725fabc55d3a8080611aa4eda5abbe54e531f97fb8d4e9b6254a54f88eb71360`
- manifest v2：`8037b9a4e0a7364fbf0e84cca5f48d7f43d764f5fb8e4e141e818965ee6df685`

## 五项验收结果

1. **CFTC 修复数字：PASS。** 独立复算得到 rho `-0.0685553232`、2010–18 `-0.0013089853`、2019+ `-0.0297521240`、风险倍数 `0.421052632`，与 JSON 完全一致。
2. **五条 Gate C：PASS。** 五条全部 `REJECT`，没有门槛误判。
3. **停止规则：PASS。** 脚本只生成便宜诊断，没有 Gate D、拟合、预测或复杂模型执行路径；结果文件明确写明复杂模型锁定。
4. **manifest：PASS_WITH_LIMITATIONS。** 24条路径全部存在、无重复，24/24 的字节数和 SHA-256 正确；覆盖16个原始文件、5个依赖／合同文件和3个输出。
5. **影响负面决定的剩余错误：未发现。** 当前剩余问题都是 provenance 强度或文字版本管理，不会救活任何候选。

## 独立复算结果

没有调用脚本内的 `diagnose` 函数；Spearman、两时期、80分位高压组、严重下跌率、风险倍数和事件簇均另写逻辑从 CSV 复算。

| 候选 | rho | 2010–18 / 2019+ | 风险倍数 | 完整历史 / 2015+簇 | Gate C |
|---|---:|---:|---:|---:|---|
| `ndx_lev_net_oi` | -0.0686 | -0.0013 / -0.0298 | 0.421x | 21 / 17 | REJECT |
| `finra_margin_yoy` | -0.0116 | -0.0410 / +0.0220 | 1.133x | 21 / 17 | REJECT |
| `jpy_stock_flow_stress` | +0.0327 | -0.0323 / +0.0802 | 0.757x | 24 / 17 | REJECT |
| `ebp_level` | -0.0234 | +0.0664 / -0.1306 | 0.834x | 24 / 17 | REJECT |
| `vix_term` | +0.0514 | +0.1264 / -0.0306 | 1.394x | 17 / 17 | REJECT |

JSON 数字与独立计算最大误差小于 `3e-17`。五条全期 rho 都低于 0.10，风险倍数都低于1.5，且每条至少一个时期不符合预设正方向；所以即使完全不看事件簇，也已经全部失败。

从原始文件重建六个底层字段及 JPY 组合后，与最终 CSV 的最大绝对误差小于 `1e-16`。另在隔离临时目录完整运行脚本，生成的 CSV、JSON、Markdown 哈希与最终文件逐一相同。

## 修复项逐项核对

- `CFTC_RELEASE_OVERRIDES` 共18笔，18/18 原始报告日期均存在且映射唯一。2018-12-24 → 2019-02-01、2023-01-31 → 2023-02-24 两个旧反例已不再提前使用。
- BIS 已改为 `rolling(20, min_periods=20)`；MOF 已改为 `rolling(52, min_periods=52)`，与合同一致。
- 合同已明确：FINRA、BIS、MOF、EBP 是 current-vintage historical proxy；MOF 不读 `Net`，但保留2014范围断点披露。
- 事件簇已明确按 `trough_date` 排序，只有与上一谷底相隔 **超过28天** 才开新簇；高压区至少3簇，最大单簇占比只展示、不设隐藏门槛。
- 最终结果正确区分完整历史的17–24簇与2015+统一17簇，没有用完整历史夸大模型容量。
- manifest 生成顺序正确：先写三份输出，再记录哈希，最后写 manifest；不存在自引用或陈旧输出哈希。

## manifest 覆盖核对

已绑定脚本实际读取和生成的全部显式文件：

- 本分支16个 raw 文件；
- 上游 `QQQ_CARRY_WEEKLY_FEATURES.csv`；
- 跨分支 `VIXCLS.csv`；
- 合同、来源矩阵、分析脚本；
- 最终 CSV、JSON、Markdown。

原始来源均有对应官方 URL。当前 manifest 足以证明“这组本机文件没有漏件、没有被静默换掉”，但不等于完整 archival provenance：`retrieved_or_modified_at` 是本地文件修改时间，不是服务器签名的下载时间；也未记录 HTTP 状态、许可、运行环境、集合 aggregate hash，且上游 `QQQ_CARRY_WEEKLY_FEATURES.csv` 只有文件哈希，没有把其上游 manifest 继续串入本分支。

## 澄清修订与剩余限制

- **PASS：** 合同和来源矩阵现已准确写成“官方实际日期／公告补发日程重建”，并明确2019后续批次不是逐份服务器时间戳；先前文字过强的问题已经消除。
- **PASS：** 合同首页现已明确标注结果揭示后的 clarification amendment，并说明候选、方向和通过线没有改变；不存在把结果后澄清冒充原始冻结全文的问题。
- **REMAINS：** 免费包没有历史原始 vintage，所以严格 PIT 仍不可证明；这一点已在最终合同与来源矩阵诚实披露。
- **REMAINS：** manifest 的时间仍是本地修改时间，且没有服务器下载凭证、运行环境、集合 aggregate hash 或上游完整 lineage；这只限制档案级 provenance，不影响 Gate C 的负面决定。

## 未测试／不应测试

- 未逐日恢复所有历史修订前的原始版本；当前证据包没有这些 vintage。
- 未运行 Gate D、HMM、boosting、神经网络或交易回测。这是合同要求的正确停止，不是测试遗漏。

## 最安全决定

保留五条 `REJECT`，关闭本轮仓位拥挤历史挑战，不用复杂模型放大弱输入。若只想进一步提高档案质量，可另补一份逐笔 CFTC override 证据表和标准 transformation manifest；这属于证据整理，不构成重新开模理由。

```text
官方／冻结输入
  ├─ current-vintage限制已披露 .............. PASS_WITH_LIMITATION
  ├─ CFTC 18笔补发日 override ............... PASS
  ├─ BIS 20季／MOF 52周 ..................... PASS
  └─ 24文件 manifest 哈希 ................... PASS_WITH_LIMITATION

原始字段 → 周度 as-of 合并 → 五条固定公式
  └─ 隔离重跑输出哈希一致 ................... PASS
       └─ 独立复算 Gate C ................... PASS
            ├─ 五条全部 REJECT
            ├─ Gate D 不运行
            └─ 2015+ 只有17簇
                 └─ 复杂模型继续锁定

未来反馈：只补 provenance，不重新挑指标／阈值／模型
```

本次快速终审只更新本报告的最终快照与限制文字；未修改研究代码、合同、数据、manifest 或主结果。
