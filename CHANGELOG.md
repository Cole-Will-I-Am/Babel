# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.9.0 BWCC (cycle 1 of 4, in progress)

Authored the first of four v0.9.0 specification documents under the
single-artifact-per-finalize protocol. BWCC v0.9.0 is strictly
additive over frozen v0.1.0-v0.8.1.

- **BWCC v0.9.0 — Static Workflow Envelope**:
  - `workflow_definition` schema: `task_ids` (non-empty, unique,
    regex `^[a-zA-Z0-9_.-]{1,64}$`) and `depends_on`
    (`object<string,string[]>`) with all keys and values members of
    `task_ids`.
  - `workflow_id = "sha256:" + hex(SHA-256(canonical_json(workflow_definition)))`
    per v0.2.0 canonical serialization.
  - Tier-1 validation: schema check, Kahn's algorithm O(n+e) cycle
    detection, no self-loops. Reject codes `BWCC_CYCLE` and
    `BWCC_BAD_REFERENCE` with BSS exit 2.
  - `workflow_amend` is explicitly NON-RETROACTIVE: in-flight tasks
    under `previous_workflow_id` continue unchanged; amendment
    affects only pending tasks and future invocations of the new
    `workflow_id`.
  - Amendment chain acyclicity: ancestors traversed via
    `previous_workflow_id`; reject duplicate workflow_id in chain
    (`BWCC_AMEND_CYCLE`) and chains > 256 (`BWCC_CHAIN_TOO_LONG`).
  - Workflow-level XRP cascade: a task's XRP publishes only after
    all upstream `depends_on` tasks complete or fail; failed
    upstream propagates `BWCC_UPSTREAM_FAIL` to all transitive
    downstream tasks which emit `status: "cancelled"`.

## Process Note: single-artifact-per-finalize

v0.9.0 materialization adopts the single-artifact-per-finalize
protocol to bound model output and prevent `pair_b_finalize`
timeouts. Each cycle authors exactly one spec; ordering is BWCC,
BSSC, BHOP, manifest. README and CHANGELOG update in every cycle.

## 2026-06-06 - Babel v0.8.1 remediation amendments (frozen)

Authored three additive amendment artifacts over frozen v0.1.0-v0.7.0
and v0.8.0, resolving all three DeepSeek v0.8.1 audit blocking
issues plus the log-compaction clarification.

- **BCRP v0.8.1**: Composite cursor key `(canonical_sha256, seq)`
  sorted lexicographically (NOT append order). Cursor invalidation
  after log compaction emits `cursor_invalid` requiring restart
  from `cursor=null`.
- **BRAP v0.8.1**: Amend cycle bounded — after original author
  emits a revised document, the reviewer MUST issue `approve` or
  `reject`; no second `amend` decision is permitted per review per
  document.
- **BSDC v0.8.1**: Deterministic LCS tie-breaking preferring the
  lexicographically earliest tuples in sorted key-path order at the
  first differing index, with four normative test vectors.

## 2026-06-06 - Babel v0.8.0 base direction (frozen)

Added BCRP cursor pagination, BRAP review and amend protocol, and
BSDC structured diff as the v0.8.0 base layer.

## 2026-06-06 - Babel v0.7.0 toolchain, workspace, and integration tests (frozen)

Authored TIC (reproducible packaging with platform field and POSIX
self-check), WCP (gitignore and gitattributes for workspace
coexistence), and ITP (cross-platform acceptance testing with
schema-first then byte-compare validation order).
