# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.9.0 hook + docs (cycle 4 of 4, in freeze)

Authored the v0.9.0 pre-commit hook and documentation finalization
artifacts under the single-artifact-per-finalize protocol. Completes
the v0.9.0 freeze bundle together with the previously signed-off
manifest JSON (cycle 4a), BWCC (cycle 1), BSSC (cycle 2), and BHOP
(cycle 3).

- `scripts/compute-manifest-sha256.py`: self-contained v0.2.0
  canonicalization (NFC unicode, LF line endings, sorted keys,
  deterministic numbers, no platform paths). Reads
  `autonomy-output/babel-manifest-v0.9.0.json` and the frozen
  `autonomy-output/babel-manifest-v0.8.1.json` base. Recomputes
  basis_ref from the base; rejects placeholder hashes in the base
  (exit 1) and basis_ref mismatch (exit 1). Recomputes
  canonical_sha256 for every artifact entry. Atomic temp+replace
  rewrite. Exit codes 0/1/2/3 aligned with v0.6.0 AIC convention.
- `README.md`: v0.9.0 in-freeze status; BWCC/BSSC/BHOP summaries;
  v0.10.x queued; hook installation instructions.
- `CHANGELOG.md`: this entry; previous v0.9.0 cycle entries
  preserved verbatim below.

Resolves DeepSeek v0.9.0 freeze-incomplete blocking issue: manifest
JSON, pre-commit hook, and docs now form a complete v0.9.0 cycle-4
set and unblock v0.10.x deterministic synthesis (v0.10.3) which
requires a fully-frozen v0.9.0 base with real canonical_sha256.

## 2026-06-06 - Babel v0.9.0 BHOP (cycle 3 of 4, in progress)

Authored the third of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BHOP v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1 and shipped BWCC/BSSC v0.9.0.

- `autonomy-output/babel-bhop-v0.9.0.md`: human_override schema,
  dual-authenticity (meta.author=human AND authorized_hig_gateway),
  pause/resume/cancel semantics, two-layer pause enforcement
  (gateway tier-1 + agent re-check), post-cancel terminated state,
  override hash chain.

## 2026-06-06 - Babel v0.9.0 BSSC (cycle 2 of 4, in progress)

Authored the second of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BSSC v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0.

- `autonomy-output/babel-bssc-v0.9.0.md`: state_snapshot schema,
  unique agent_id, time-based emission bound (1 per DTL heartbeat)
  distinct from seq monotonicity, per-agent cross-snapshot seq
  regression check, hash_chain pointer with 1024-cap documented
  limitation, crash recovery with genesis fallback.

## 2026-06-06 - Babel v0.9.0 BWCC (cycle 1 of 4, in progress)

Authored the first of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BWCC v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1.

- `autonomy-output/babel-bwcc-v0.9.0.md`: workflow_definition schema,
  workflow_id = sha256:hex64(content), Kahn O(n+e) tier-1
  acyclicity, hash-set O(1) depends_on membership, non-retroactive
  workflow_amend, amendment chain acyclicity with 256-ancestor
  DOS bound, workflow-level XRP upstream-fail cascade.
