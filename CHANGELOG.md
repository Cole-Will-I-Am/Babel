# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.9.0 BHOP (cycle 3 of 4, in progress)

Authored the third of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BHOP v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0 and BSSC v0.9.0.

Resolves both DeepSeek v0.9.0 BHOP audit blocking issues and all five
required changes:

- Pause enforcement is two-layer: gateway tier-1 rejects new
  `task_delegation` drafts for paused workflows with `BHOP_WORKFLOW_PAUSED`
  AND agents re-check pause state immediately before acceptance (race
  condition prevention; rogue-agent bypass eliminated).
- Post-cancel workflow state is explicitly `terminated`: gateway rejects
  new `task_delegation` drafts with `BHOP_WORKFLOW_TERMINATED`; reactivation
  requires a new `human_override` with action `resume` or genesis restart.
- `authorized_hig_gateway` list is genesis-configured and immutable in
  v0.9.0; documented as a trust assumption with no revocation mechanism
  (gateway compromise requires genesis restart).
- `target_workflow_id` is validated as `^sha256:[0-9a-f]{64}$`
  (`BHOP_INVALID_WORKFLOW` on malformed) and existence-checked
  (`BHOP_UNKNOWN_WORKFLOW` on well-formed but absent).
- Override hash chain via `previous_override_sha256` with
  `BHOP_CHAIN_BROKEN` rejection ensures deterministic override history.

HIG ingestion via v0.4.0 gateway compilation; agent observation via
BCRP v0.8.1 composite cursor; state durability via BSSC v0.9.0
`ext.kimi.state` opaque blob. Reference implementation and v0.9.0
manifest deferred to subsequent cycles.

## 2026-06-06 - Babel v0.9.0 BSSC (cycle 2 of 4, in progress)

Authored the second of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BSSC v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1 and shipped BWCC v0.9.0.

Resolves all four DeepSeek v0.9.0 BSSC audit required changes:
emission bound (time-based rate limit) is distinct from seq monotonicity;
1024-snapshot traversal cap limitation is explicitly documented;
per-agent cross-snapshot seq regression check; unique agent_id
constraint within `state_snapshot` array.

## 2026-06-06 - Babel v0.9.0 BWCC (cycle 1 of 4, in progress)

Authored the first of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BWCC v0.9.0 is strictly additive
over frozen v0.1.0-v0.8.1.

Resolves all DeepSeek v0.9.0 clarifications: workflow_amend is
explicitly non-retroactive; Kahn's algorithm O(n+e) tier-1 cycle
detection; hash-set O(1) depends_on membership; amendment chain
acyclicity with 256-ancestor DOS bound; workflow_id is
`sha256:` + hex of canonical JSON SHA-256.

## 2026-06-06 - Babel v0.8.1 remediation amendments (final)

Authored three additive amendment artifacts over frozen v0.1.0-v0.7.0
and v0.8.0, resolving all three DeepSeek v0.8.1 audit blocking issues
plus the log-compaction clarification:

- BCRP v0.8.1: result ordering corrected to lex sort by composite key
  `(canonical_sha256, seq)`; this is NOT append order. Cursor invalidation
  after log compaction defined as `cursor_invalid` with restart from
  `cursor=null`.
- BRAP v0.8.1: amend cycle bounded. Reviewer MUST issue `approve` or
  `reject` after author revision; no second amend permitted. Three
  termination paths unchanged with CDR hash ordering for concurrent
  resolution.
- BSDC v0.8.1: deterministic LCS tie-breaking preferring lex-earliest
  tuples in sorted key-path order; four normative test vectors.

v0.8.1 manifest references frozen v0.8.0 manifest; canonical_sha256
placeholders filled by pre-commit hook.
