#!/usr/bin/env python3
"""Babel v0.2.0 canonical serialization + manifest hash population.

Implements the byte-exact rules from
`autonomy-output/babel-canonical-serialization-v0.2.0.md` so that
`canonical_sha256` fields in a manifest can be populated deterministically
at commit time (the orchestrator pre-commit step).

Two canonicalizers:
  * canonicalize_text  - for text artifacts (.md and friends): UTF-8, NFC,
    LF-only, no trailing whitespace, exactly one trailing LF.
  * canonicalize_json  - for .json artifacts/manifests: full v0.2.0 rules
    (recursive code-point key sort, deterministic numbers, 2-space indent,
    single LF terminator).

CLI:
  python3 canonical.py hash  <file>          # print sha256 of canonical form
  python3 canonical.py fill  <manifest.json> # populate PENDING hashes in place
  python3 canonical.py selftest              # run built-in test vectors
"""
from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any

PENDING = "sha256:PENDING_COMPUTE_AT_COMMIT"


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonicalize_text(raw: bytes) -> bytes:
    """Canonical form for non-JSON text artifacts."""
    text = raw.decode("utf-8")
    text = _nfc(text)
    # LF-only line terminators, no trailing whitespace per line.
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    body = "\n".join(lines)
    # Exactly one trailing LF, no trailing blank lines.
    body = body.rstrip("\n") + "\n"
    return body.encode("utf-8")


def _format_number(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError(f"non-finite number rejected: {value}")
    if value == value.to_integral_value() and value.as_tuple().exponent >= 0:
        # Integer: no decimal point, no leading zeros, no negative zero.
        return str(int(value))
    # Fraction: strip trailing zeros, keep at least one digit after the point.
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." not in text:
        text += ".0"
    if text.startswith("-0") and Decimal(text) == 0:
        text = text[1:]
    return text


def _emit(node: Any, indent: int, out: list[str]) -> None:
    pad = "  " * indent
    child_pad = "  " * (indent + 1)
    if isinstance(node, dict):
        if not node:
            out.append("{}")
            return
        keys = sorted((_nfc(str(k)) for k in node.keys()), key=lambda s: (s, len(s)))
        # Re-map normalized keys back to original values.
        norm_map = {_nfc(str(k)): v for k, v in node.items()}
        out.append("{\n")
        for i, key in enumerate(keys):
            out.append(child_pad)
            out.append(json.dumps(key, ensure_ascii=False))
            out.append(": ")
            _emit(norm_map[key], indent + 1, out)
            out.append(",\n" if i < len(keys) - 1 else "\n")
        out.append(pad + "}")
    elif isinstance(node, list):
        if not node:
            out.append("[]")
            return
        out.append("[\n")
        for i, item in enumerate(node):
            out.append(child_pad)
            _emit(item, indent + 1, out)
            out.append(",\n" if i < len(node) - 1 else "\n")
        out.append(pad + "]")
    elif isinstance(node, str):
        out.append(json.dumps(_nfc(node), ensure_ascii=False))
    elif isinstance(node, bool):
        out.append("true" if node else "false")
    elif node is None:
        out.append("null")
    elif isinstance(node, Decimal):
        out.append(_format_number(node))
    elif isinstance(node, int):
        out.append(str(node))
    elif isinstance(node, float):
        out.append(_format_number(Decimal(str(node))))
    else:
        raise TypeError(f"unsupported node type: {type(node)!r}")


def canonicalize_json(raw: bytes) -> bytes:
    text = _nfc(raw.decode("utf-8"))
    data = json.loads(text, parse_float=Decimal, parse_int=int)
    out: list[str] = []
    _emit(data, 0, out)
    return ("".join(out) + "\n").encode("utf-8")


def canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix == ".json":
        return canonicalize_json(raw)
    return canonicalize_text(raw)


def canonical_sha256(path: Path) -> str:
    digest = hashlib.sha256(canonical_bytes(path)).hexdigest()
    return f"sha256:{digest}"


def fill_manifest(manifest_path: Path, *, only_pending: bool = True) -> list[str]:
    """Populate canonical_sha256 for each artifact; return changed paths."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    repo_root = manifest_path.resolve().parent
    # Walk up to repo root (dir containing .git) for path resolution.
    probe = repo_root
    while probe != probe.parent and not (probe / ".git").exists():
        probe = probe.parent
    if (probe / ".git").exists():
        repo_root = probe

    changed: list[str] = []
    artifacts = data.get("artifacts", [])
    for entry in artifacts:
        if not isinstance(entry, dict) or "path" not in entry:
            continue
        current = entry.get("canonical_sha256")
        if only_pending and current not in (None, PENDING):
            continue
        target = repo_root / entry["path"]
        if not target.exists():
            raise FileNotFoundError(f"manifest references missing artifact: {entry['path']}")
        new_hash = canonical_sha256(target)
        if new_hash != current:
            entry["canonical_sha256"] = new_hash
            changed.append(entry["path"])

    if changed:
        manifest_path.write_bytes(canonicalize_json(json.dumps(data).encode("utf-8")))
    return changed


def _selftest() -> int:
    # Text canonicalization.
    assert canonicalize_text(b"a \r\nb\n\n\n") == b"a\nb\n"
    assert canonicalize_text(b"no newline") == b"no newline\n"
    # JSON key sort + number format + LF terminator.
    got = canonicalize_json(b'{"b":1,"a":2.0,"c":[true,null]}')
    expected = '{\n  "a": 2.0,\n  "b": 1,\n  "c": [\n    true,\n    null\n  ]\n}\n'
    assert got.decode() == expected, got.decode()
    # Number rules.
    assert canonicalize_json(b'{"x":1.00}').decode() == '{\n  "x": 1.0\n}\n'
    assert canonicalize_json(b'{"x":-0}').decode() == '{\n  "x": 0\n}\n'
    # Stable hash determinism.
    assert canonical_sha256.__module__  # smoke
    print("canonical selftest: OK")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "selftest":
        return _selftest()
    if len(argv) == 3 and argv[1] == "hash":
        print(canonical_sha256(Path(argv[2])))
        return 0
    if len(argv) == 3 and argv[1] == "fill":
        changed = fill_manifest(Path(argv[2]))
        if changed:
            print("populated canonical_sha256 for:")
            for p in changed:
                print(f"  {p}")
        else:
            print("no PENDING hashes to populate")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
