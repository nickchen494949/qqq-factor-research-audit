#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RELEASE_ROOT = HERE.parent
manifest = json.loads((RELEASE_ROOT / "EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
rows = []
ok = True
for item in manifest["files"]:
    path = RELEASE_ROOT / manifest["roots"][item["root"]] / item["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    good = path.is_file() and path.stat().st_size == item["bytes"] and digest == item["sha256"]
    ok &= good
    rows.append({
        "id": item["id"],
        "ok": good,
        "path": path.relative_to(RELEASE_ROOT).as_posix(),
        "sha256": digest,
    })
payload = "".join(
    f"{x['id']}\0{x['root']}\0{x['path']}\0{x['bytes']}\0{x['sha256']}\n"
    for x in manifest["files"]
)
aggregate = hashlib.sha256(payload.encode()).hexdigest()
ok &= aggregate == manifest["aggregate_sha256"]
print(json.dumps({"ok": ok, "aggregate_sha256": aggregate, "files": rows}, indent=2))
raise SystemExit(0 if ok else 1)
