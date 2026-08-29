# Audit limitations

这是本机冻结研究的GitHub脱敏审计副本。为避免泄露活跃未来预测或误传受限数据，本仓库没有上传任何未来OOS协议、预测、账本及10份受限文件的字节。

## 这份发布可以核查

- 39份已分发证据的字节完整性，以及10份省略证据的原始哈希与原因。
- 研究合同、主要结果表、独立复算报告与最终结论是否互相矛盾。
- 论文有没有把 `BLOCK`、`PROXY`、`REJECT`、`WAITING` 写成 `PASS`。
- 月度主实验的预测和结果文件能否逐字节复核。

## 这份发布不能证明

- 免费代理具有真正历史 point-in-time／vintage 完整性。
- 选定证据等于全部原始网页、下载字节与所有实验代码。
- 单靠本仓库能从原始数据完整重跑所有模型。
- 内部独立复算等于外部学术复现、因果识别或未来有效性。
- 历史RMSE、rho、Sharpe或回撤改善必然可交易。

## 已知主要限制

1. 精确免费NDX／QQQ总体EPS、Forward EPS及revision历史真值仍然缺失。
2. 多个宏观来源是current-vintage快照；本地可复现不等于历史PIT有效。
3. 2009–2026历史已被反复查看，不是 untouched holdout。
4. 63日目标存在标签重叠；HAC与多重检验处理仍有限。
5. 季度组合只有39个合法OOS季度，低于冻结的40期最低门槛。
6. 真正未来EPS与实际利率账本尚未积累到正式评分数量。

## 审计判定

`BYTE_INTEGRITY: PASS`，适用于本包39份已分发证据。

`CLAIM_LEVEL_TRACEABILITY: PASS`，适用于论文13项核心结论到选定证据的映射。

`COMPUTATIONAL_REPRODUCIBILITY_FROM_THIS_REPOSITORY: NOT_PROVIDED`。

`HISTORICAL_PIT_VALIDITY: INCOMPLETE/BLOCK`。

`NEW_PRODUCTION_FACTOR_OR_STRATEGY: NONE`。

## GitHub省略与脱敏

E36月度特征表因上游再分发权未确认而未上传。E40–E45与E47–E49属于仍在进行的真实未来协议、预测、账本或来源包，全部未上传；清单仅保留原始哈希和省略原因。E03、E04与E46以脱敏衍生版发布，原始哈希保留在清单与 `REDACTIONS.md`。
