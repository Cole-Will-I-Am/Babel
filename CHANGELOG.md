# Changelog

All notable changes to the Babel protocol artifacts are recorded here.
New entries are strictly additive; frozen entries are preserved verbatim.

## 2026-06-07 - Babel v0.10.3 bootstrap (cycle 1 of 7, in progress)

Authored the first of seven v0.10.3 specification documents under the
single-artifact-per-finalize protocol. The bootstrap spec is strictly
additive over the v0.9.0 freeze (BWCC, BSSC, BHOP) and all frozen
v0.1.0-v0.8.1 artifacts. It defines the recursive basis_ref traversal
procedure from the v0.9.0 manifest back to the v0.1.0 genesis
manifest, the hash aggregation rule (one spec-index seed tuple per
artifact entry), the gap detection gates (BOOTSTRAP_MISSING_MANIFEST,
BOOTSTRAP_PLACEHOLDER_HASH, BOOTSTRAP_INVALID_BASIS_REF,
BOOTSTRAP_BASIS_MISMATCH, BOOTSTRAP_GENESIS_HAS_BASIS,
BOOTSTRAP_BAD_PATH, BOOTSTRAP_DUPLICATE_KEY), and the output JSON
format consumed by the v0.10.3 spec-index author in cycle 6.

The composite unique constraint on (version, type) is enforced as a
hard schema rule, not a tie-breaker. The manifest-specific error code
SPECINDEX_MANIFEST_DUPLICATE is delegated to the v0.10.3 spec-index
validator. Cycle 7 synthesis paths are now frozen: v0.9.0 README/
CHANGELOG at repo root; v0.10.2 manifest at autonomy-output/babel-
manifest-v0.10.2.json; hook at scripts/compute-manifest-sha256.py;
v0.10.2 README/CHANGELOG at repo root. validate-spec-index.py is
assigned to cycle 6 alongside spec-index authoring (exit codes 0/1/2/3/4
explicit; exclusion list for .git/, __pycache__/, *.pyc, *.swp,
.DS_Store, *.local.json). v0.10.2 BWSS/BISC/BCPR normative specs are
decoupled from the template registry: BWSS may begin once bootstrap
(cycle 1) signs off; template registry signoff is not a precondition.

## 2026-06-06 - Babel v0.9.0 hook + docs (cycle 4 of 4, in freeze)

Authored the v0.9.0 pre-commit hook and documentation finalization
artifacts under the single-artifact-per-finalize protocol. Completes
the v0.9.0 freeze. The hook recomputes basis_ref from the frozen v0.8.1
manifest via v0.2.0 canonicalization, rejects any placeholder or
empty canonical_sha256 in the base manifest, recomputes
canonical_sha256 for every artifact entry, and atomically rewrites
the manifest before commit. Exit codes: 0=ok, 1=validation failure,
2=missing file, 3=IO error. README and CHANGELOG updated to reflect
the v0.9.0 freeze; v0.10.x deterministic synthesis is unblocked.

## 2026-06-06 - Babel v0.9.0 BHOP (cycle 3 of 4, in progress)

Authored the third of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BHOP v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0 and BSSC v0.9.0.
Defines a deterministic runtime human intervention protocol with
dual-authenticity (meta.author=human AND authorized_hig_gateway),
gateway+agent two-layer pause enforcement, explicit post-cancel
terminated state, target_workflow_id sha256:hex64 validation, override
hash chain, HIG ingestion, and BCRP-based agent observation.

## 2026-06-06 - Babel v0.9.0 BSSC (cycle 2 of 4, in progress)

Authored the second of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BSSC v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0. Defines a
deterministic checkpoint protocol with state_snapshot schema, unique
agent_id, time-based emission bound (distinct from seq monotonicity),
per-agent cross-snapshot seq regression check, hash_chain pointer with
explicitly documented 1024-cap limitation, and crash recovery with
genesis fallback.

## 2026-06-06 - Babel v0.9.0 BWCC (cycle 1 of 4, in progress)

Authored the first of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BWCC v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1. Defines a static workflow envelope with
content-addressed workflow_id (sha256:hex64 via v0.2.0), Kahn O(n+e)
tier-1 acyclicity, hash-set O(1) depends_on membership, non-retroactive
workflow_amend, amendment chain acyclicity with 256-ancestor DOS bound,
and XRP upstream-fail cascade propagation.

## 2026-06-06 - Babel v0.8.1 freeze (complete)

Shipped BCRP v0.8.1 (corrected lex sort by (sha256, seq), cursor
invalidation and restart after compaction), BRAP v0.8.1 (amend cycle
bounded: reviewer approves or rejects after author revision; CDR
ordering preserved), BSDC v0.8.1 (deterministic LCS tie-break
preferring earlier sorted tuples; four test vectors), and the v0.8.1
manifest referencing the frozen v0.8.0 base. All three DeepSeek v0.8.1
audit blocking issues resolved.
