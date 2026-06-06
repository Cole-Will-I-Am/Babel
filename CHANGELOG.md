# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.9.0 BSSC (cycle 2 of 4, in progress)

Authored the second of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BSSC v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0.

### Added: autonomy-output/babel-bssc-v0.9.0.md
- **State snapshot schema**: 4-tuple array
  (agent_id, ext.kimi.state, last_seen_seq, workflow_id|null)
  sorted lexicographically by agent_id per v0.2.0 canonical JSON.
  workflow_id is gateway-recommended but optional for non-workflow agents.
- **Unique agent_id constraint**: each agent_id MUST appear at most once
  within a snapshot array. Duplicate detection via O(n) hash-set.
  Rejection: BSSC_DUPLICATE_AGENT.
- **Time-based emission bound (DISTINCT from seq monotonicity)**: max 1
  state_snapshot submission per agent per DTL heartbeat interval.
  Enforced via gateway-side per-agent timestamp tracking. Rejection:
  BSSC_EMISSION_RATE_EXCEEDED. This is a separate check from seq
  monotonicity which prevents replay regardless of timing.
- **Per-agent cross-snapshot seq check**: compares each agent's
  last_seen_seq against the seq recorded in the immediate prior
  snapshot document for that same agent. Rejection:
  BSSC_CROSS_SNAPSHOT_REGRESSION. Catches regression that the in-array
  check may miss when the prior snapshot omitted that agent.
- **Hash chain pointer**: ext.kimi.previous_snapshot_sha256 references
  canonical SHA-256 of immediate prior snapshot document. Genesis uses
  null. Tier-1 rejects BSSC_HASH_MISMATCH on mismatch.
- **Crash recovery fallback**: tail-first hash_chain traversal capped
  at 1024 snapshots (~8.5 hours at 30s heartbeat). On broken link,
  fallback to last intact snapshot, then genesis replay. Reject
  BSSC_CHAIN_BROKEN if genesis is broken. Recovery reads log, not
  submit, so emission bound does not apply (no deadlock).
- **Documented 1024-cap limitation**: hash_chain integrity is guaranteed
  ONLY for the most recent 1024 snapshots. Older snapshots are NOT
  guaranteed intact. Implementations MUST document this trade-off.
- **Error codes**: BSSC_SCHEMA_INVALID, BSSC_DUPLICATE_AGENT,
  BSSC_EMISSION_RATE_EXCEEDED, BSSC_SEQ_REGRESSION,
  BSSC_CROSS_SNAPSHOT_REGRESSION, BSSC_HASH_MISMATCH, BSSC_CHAIN_BROKEN.

### Cross-References
- BWCC v0.9.0 workflow_id referenced in snapshot tuples (optional).
- BCRP v0.8.1 results pagination by (canonical_sha256, seq) covers
  snapshot documents in the same lex sort.
- BSS v0.6.0 grammar applies to snapshot documents.
- DTL v0.5.1 heartbeat interval defines the emission bound period.

## 2026-06-06 - Babel v0.9.0 BWCC (cycle 1 of 4, shipped)

Authored the first of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BWCC v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1. No frozen field is mutated.

### Added: autonomy-output/babel-bwcc-v0.9.0.md
- Static workflow envelope with content-addressed workflow_id.
- Kahn's algorithm O(n+e) tier-1 cycle detection.
- Hash-set O(1) depends_on membership.
- Non-retroactive workflow_amend: in-flight tasks under original
  workflow_id continue unchanged; amendment affects only pending and
  future invocations.
- Amendment chain acyclicity with 256-ancestor DOS bound.
- Workflow-level XRP cascade: BWCC_UPSTREAM_FAIL cancels transitive
  downstream tasks with status=cancelled.

## 2026-06-06 - Babel v0.8.1 remediation amendments (final, frozen)

Authored three additive amendment artifacts over frozen v0.1.0-v0.7.0 and
v0.8.0, resolving all three DeepSeek v0.8.1 audit blocking issues plus
the log-compaction clarification.

- **BCRP v0.8.1**: result ordering corrected to (canonical_sha256, seq)
  lexicographic sort; explicitly NOT append order. cursor_invalid error
  with restart-from-null required after log compaction loses seq index.
- **BRAP v0.8.1**: amend cycle bounded. After author submits revised
  document D', reviewer MUST issue approve or reject. No second amend.
  Three termination paths (author revision, timeout proxy, reviewer
  reject) unchanged with CDR hash ordering for concurrent resolution.
- **BSDC v0.8.1**: deterministic LCS tie-breaking rule. When multiple
  LCS of equal length exist, prefer the one retaining lexicographically
  earliest tuples in sorted key-path order. Four normative test vectors.
- **v0.8.1 manifest**: references frozen v0.8.0 manifest. canonical_sha256
  placeholders (sha256:PENDING_COMPUTE_AT_COMMIT) filled by pre-commit
  hook.
