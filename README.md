# QQQ Factor Research Audit

这是一份可审计的负面研究，不是一个已经找到有效交易模型的项目。

本仓库提供结论到选定证据的追踪与字节完整性核验；它没有提供全部原始输入和全部计算代码，因此不能单靠本仓库完整重跑所有模型。

## 发布状态：PRIVATE AUDIT COPY

仓库已移除本机绝对路径、尚未评分的具体未来预测和再分发权未确认的数据字节。为避免第三方数据许可误判，当前仍保持私有。

## 一句话结论

在本轮冻结规则下，没有新增因子或复杂模型同时通过数据资格、样本量、增量预测、跨时期稳定性、时点稳健性与策略价值门槛；免费、精确、具有历史时点版本的 Nasdaq-100／QQQ 总体 EPS、Forward EPS 或 revision 数据仍然 `BLOCK`。

## 这里有什么

- `paper/`：中文论文的GitHub脱敏版，PDF和DOCX。
- `EVIDENCE_MANIFEST.json`：13项核心结论到39份已分发证据＋10份仅保留哈希的受限证据的映射及SHA-256。
- `evidence/P/`：研究合同、历史结果与审计；未来OOS协议和账本未上传。
- `evidence/S/`：最小重启的源头合同与历史负面证据。
- `REDACTIONS.md`：脱敏范围及原始哈希到衍生版哈希的映射。
- `scripts/verify_evidence_manifest.py`：核验39份已分发证据。
- `scripts/provenance_manifest.py`：核验整个GitHub发布包。
- `AUDIT_LIMITATIONS.md`：这份发布可以证明什么、不能证明什么。

## 最短核验方法

```bash
python3 scripts/verify_evidence_manifest.py
python3 scripts/provenance_manifest.py verify \
  --root . \
  --manifest RELEASE_MANIFEST.json \
  --allow-extra
```

第一条应返回 `"ok": true`。本仓库的证据aggregate SHA-256见 `EVIDENCE_MANIFEST.json`；GitHub脱敏论文和全部发布文件的SHA-256见 `CHECKSUMS.txt` 与 `RELEASE_MANIFEST.json`。

## 研究决定

1. 停止继续优化已反复查看的历史代理。
2. 不把局部复杂模型改善写成正式PASS。
3. 不修改生产策略。
4. 未来OOS由本机独立维护，未包含在本仓库；或购买合格的direct aggregate PIT数据后重新开题。

## 审计入口

先读 `paper/QQQ_AUDITABLE_RESEARCH_PAPER_GITHUB_REDACTED.pdf`，再按论文结论编号在 `EVIDENCE_MANIFEST.json` 查对应证据ID和文件哈希。

本仓库未授予第三方数据的再许可；引用或再分发前应核对原始来源条款。
