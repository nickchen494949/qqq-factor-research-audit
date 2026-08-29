#!/usr/bin/env python3
"""Build and verify deterministic SHA-256 manifests for frozen source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SCHEMA_VERSION = "research-provenance/v1"
SENSITIVE_QUERY_KEYS = {
    "access_key",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credential",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_url(value: str | None) -> str | None:
    if not value:
        return None
    parts = urlsplit(value)
    if not parts.scheme:
        raise ValueError("source URL must be absolute")
    clean_query = []
    for key, item in parse_qsl(parts.query, keep_blank_values=True):
        clean_query.append((key, "REDACTED" if key.lower() in SENSITIVE_QUERY_KEYS else item))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(clean_query), ""))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path, excluded: set[Path]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        resolved = path.resolve()
        if resolved in excluded:
            continue
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in frozen sources: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        records.append({"path": relative, "bytes": size, "sha256": hash_file(path)})
    return records


def aggregate_digest(records: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        line = f"{record['path']}\0{record['bytes']}\0{record['sha256']}\n"
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def build_manifest(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    output = Path(args.out).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    created_at = utc_now()
    records = collect_files(root, {output})
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": created_at,
        "root_label": args.root_label or root.name,
        "source": {
            "label": args.source_label,
            "url": sanitize_url(args.source_url),
            "retrieved_at_utc": args.retrieved_at or created_at,
            "notes": args.notes or None,
        },
        "hash_algorithm": "sha256",
        "file_count": len(records),
        "total_bytes": sum(int(record["bytes"]) for record in records),
        "aggregate_sha256": aggregate_digest(records),
        "files": records,
    }
    write_json_atomic(output, payload)
    print(json.dumps({key: payload[key] for key in ("file_count", "total_bytes", "aggregate_sha256")}, sort_keys=True))
    return 0


def verify_manifest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema: {payload.get('schema_version')}")
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")

    expected_records = payload.get("files")
    if not isinstance(expected_records, list):
        raise ValueError("manifest files must be a list")
    failures: list[str] = []
    expected_paths: set[str] = set()
    actual_records: list[dict[str, object]] = []
    for record in expected_records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            failures.append("malformed file record")
            continue
        relative = record["path"]
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            failures.append(f"path escapes root: {relative}")
            continue
        expected_paths.add(relative)
        if not candidate.is_file() or candidate.is_symlink():
            failures.append(f"missing or unsupported file: {relative}")
            continue
        size = candidate.stat().st_size
        digest = hash_file(candidate)
        actual_records.append({"path": relative, "bytes": size, "sha256": digest})
        if size != record.get("bytes"):
            failures.append(f"size mismatch: {relative}")
        if digest != record.get("sha256"):
            failures.append(f"hash mismatch: {relative}")

    if not args.allow_extra:
        excluded = {manifest_path} if manifest_path.is_relative_to(root) else set()
        current_paths = {str(record["path"]) for record in collect_files(root, excluded)}
        for relative in sorted(current_paths - expected_paths):
            failures.append(f"unexpected file: {relative}")

    actual_records.sort(key=lambda record: str(record["path"]))
    if len(actual_records) == len(expected_records):
        actual_aggregate = aggregate_digest(actual_records)
        if actual_aggregate != payload.get("aggregate_sha256"):
            failures.append("aggregate hash mismatch")

    result = {
        "ok": not failures,
        "checked_files": len(actual_records),
        "aggregate_sha256": payload.get("aggregate_sha256"),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="create a manifest")
    build.add_argument("--root", required=True)
    build.add_argument("--out", required=True)
    build.add_argument("--source-label", required=True)
    build.add_argument("--source-url")
    build.add_argument("--retrieved-at")
    build.add_argument("--root-label")
    build.add_argument("--notes")
    build.set_defaults(function=build_manifest)

    verify = commands.add_parser("verify", help="verify a manifest")
    verify.add_argument("--root", required=True)
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--allow-extra", action="store_true")
    verify.set_defaults(function=verify_manifest)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        return int(args.function(args))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
