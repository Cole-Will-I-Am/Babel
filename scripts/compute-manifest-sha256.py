#!/usr/bin/env python3
"""Babel v0.9.0 pre-commit hook: finalize manifest hashes via v0.2.0 canonicalization.

Reads autonomy-output/babel-manifest-v0.9.0.json and the frozen v0.8.1 base
manifest. Recomputes basis_ref from the base, recomputes canonical_sha256 for
every artifact entry, and atomically rewrites the manifest.

Exit codes (aligned with v0.6.0 AIC convention):
  0 = success, manifest rewritten with computed hashes
  1 = validation failure (placeholder base, basis_ref mismatch, malformed)
  2 = missing manifest or artifact file
  3 = IO error during rewrite

Self-contained: re-implements v0.2.0 canonicalization in-line so the hook
runs in any pre-commit environment without an installable Python package.
"""
import sys
import os
import json
import hashlib
import unicodedata

PLACEHOLDER_PREFIX = "sha256:PENDING"

# --- v0.2.0 canonicalization (re-implemented; no platform paths, no os.path joins) ---

def canonical_json(obj):
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
    text = unicodedata.normalize("NFC", text)
    return text

def canonical_bytes(data):
    if isinstance(data, bytes):
        text = data.decode("utf-8")
    else:
        text = data
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")

def sha256_hex(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()

# --- manifest IO ---

def load_json(path):
    with open(path, "rb") as f:
        raw = f.read()
    canon = canonical_bytes(raw)
    obj = json.loads(canon.decode("utf-8"))
    return raw, canon, obj

def main():
    repo_root = os.environ.get("BABEL_REPO_ROOT", ".")
    target_version = "0.9.0"
    base_version = "0.8.1"
    target_path = os.path.join(repo_root, "autonomy-output",
                               "babel-manifest-v" + target_version + ".json")
    base_path = os.path.join(repo_root, "autonomy-output",
                             "babel-manifest-v" + base_version + ".json")

    if not os.path.exists(target_path):
        sys.stderr.write("ERROR: missing target manifest: " + target_path + "\n")
        return 2
    if not os.path.exists(base_path):
        sys.stderr.write("ERROR: missing base manifest: " + base_path + "\n")
        return 2

    try:
        _raw_target, _canon_target, target = load_json(target_path)
        _raw_base, canon_base, base = load_json(base_path)
    except (OSError, ValueError) as exc:
        sys.stderr.write("ERROR: failed to read manifest: " + str(exc) + "\n")
        return 3

    # --- gate 1: base must be fully hashed (no placeholders) ---
    for entry in base.get("artifacts", []):
        cs = entry.get("canonical_sha256", "")
        if not cs or cs.startswith(PLACEHOLDER_PREFIX):
            sys.stderr.write(
                "ERROR: base manifest v" + base_version
                + " has placeholder canonical_sha256 for "
                + entry.get("path", "<unknown>") + "\n")
            return 1

    # --- gate 2: basis_ref validation / population ---
    computed_basis = sha256_hex(canon_base)
    stated_basis = target.get("basis_ref", "")
    if not stated_basis or stated_basis.startswith(PLACEHOLDER_PREFIX):
        basis_ref = computed_basis
    elif stated_basis != computed_basis:
        sys.stderr.write(
            "ERROR: basis_ref mismatch: manifest=" + stated_basis
            + " computed=" + computed_basis + "\n")
        return 1
    else:
        basis_ref = stated_basis

    # --- recompute canonical_sha256 for every artifact ---
    artifacts = target.get("artifacts", [])
    for entry in artifacts:
        rel_path = entry.get("path", "")
        if not rel_path:
            sys.stderr.write("ERROR: artifact entry missing path\n")
            return 1
        full = os.path.join(repo_root, rel_path)
        if not os.path.exists(full):
            sys.stderr.write("ERROR: missing artifact file: " + rel_path + "\n")
            return 2
        try:
            with open(full, "rb") as f:
                raw = f.read()
            canon = canonical_bytes(raw)
            computed = sha256_hex(canon)
        except OSError as exc:
            sys.stderr.write("ERROR: read failed for " + rel_path + ": " + str(exc) + "\n")
            return 3
        existing = entry.get("canonical_sha256", "")
        if not existing or existing.startswith(PLACEHOLDER_PREFIX) or existing != computed:
            entry["canonical_sha256"] = computed

    # --- atomic rewrite ---
    target["basis_ref"] = basis_ref
    if not target.get("generated_at"):
        target["generated_at"] = "1970-01-01T00:00:00Z"
    new_bytes = canonical_json(target).encode("utf-8")
    tmp_path = target_path + ".tmp"
    try:
        with open(tmp_path, "wb") as f:
            f.write(new_bytes)
        os.replace(tmp_path, target_path)
    except OSError as exc:
        sys.stderr.write("ERROR: atomic rewrite failed: " + str(exc) + "\n")
        return 3

    sys.stdout.write("OK: basis_ref=" + basis_ref
                     + "; " + str(len(artifacts)) + " artifact hashes computed\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
