# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.5.1 remediation amendments (final)

Resolved all five blocking gaps from DeepSeek's v0.5.0 audit. All
amendments are strictly additive over frozen v0.1.0-v0.5.0; no
frozen artifact is modified.

### Added

- `autonomy-output/babel-asmc-v0.5.1.md` ASMC amendment:
  - Heartbeat exemption rule: a document whose only `ext.kimi` field
    is `heartbeat` is exempt from ASMC valid_transition validation.
  - Isolated-agent self-rollback rule: a failed agent with zero
    inbound `rollback_to` references may self-rollback after
    `2 * DTL_timeout_ms` by emitting a draft with
    `ext.kimi.self_rollback = true`.
  - Updated `valid_transition` matrix with `failed -> idle` via
    self-rollback (complementary to the v0.5.0 XRP path).
  - Nemotron tier-1 validation pseudocode for the exemption check
    (`Object.keys(ext.kimi).length === 1 && heartbeat != null`).

- `autonomy-output/babel-tds-v0.5.1.md` TDS amendment:
  - Deadline enforcement: nemotron tier-1 rejects any draft from the
    assignee when `current_block > deadline_block`; the rejection is
    recorded as a tier-1 failure and transitions the assignee to
    `failed` state.
  - Ancestry_chain validation via incremental in-memory index
    (`task_id -> {assignee, parent_task_ids[]}`); startup build is
    O(n), lookup is O(1) per draft.
  - Cycle detection: any task_delegation whose submitted
    `ancestry_chain` contains its own `task_id` is rejected.
  - Mandatory `ancestry_chain` field in task_delegation schema;
    missing field causes rejection.

- `autonomy-output/babel-dtl-xrp-v0.5.1.md` DTL/XRP amendment:
  - Crash-failure proxy: a peer may emit a rollback draft on behalf
    of a stalled agent using `ext.kimi.stalled_agent_failed = true`
    plus a `proxy_proof` object containing
    `{dependent_agent, dependent_last_draft_hash, referenced_stalled_hash}`.
  - Authorized peer eligibility: nemotron validates that
    `dependent_last_draft_hash` exists in the log and its
    `meta.rollback_to` equals `referenced_stalled_hash`.
  - Cascade ordering: simultaneous rollback drafts (XRP or
    self-rollback) targeting the same failed state hash are
    processed in CDR hash order; first wins, second is rejected by
    ASMC valid_transition.

- `autonomy-output/babel-manifest-v0.5.1.json` v0.5.1 manifest
  listing the three amendment artifacts with canonical SHA-256 hash
  placeholders (to be computed by the pre-commit hook using v0.2.0
  canonical serialization rules) and referencing the frozen v0.5.0
  manifest for audit trail.

### Audit Trail

- Nemotron verified all five remediation mechanisms (signoff: true).
- DeepSeek re-audit confirmed no new contradictions or ambiguities
  (signoff: true).

### Required Follow-up (Execution Phase)

- Compute canonical SHA-256 hashes of the three amendment artifacts
  and populate the `canonical_sha256` fields in the manifest via the
  pre-commit hook before merge.
- Emit M0-v0.5.1 milestone draft describing the execution sequence
  (commit amendments -> implement in nemotron tier-1 -> run
  integration test of all five gap scenarios -> emit status draft
  with `criteria_sha256 = <test-hash>`).

## 2026-06-06 - Babel v0.3.0 milestone architecture (revised)

Resolved the DeepSeek audit blocking issue: M1 and M2 could not safely
run in parallel because M2 (Agent Integration) required the RPC
implementation that M1 (Parser Conformance) produces. Extracted the
RPC implementation as a new prerequisite phase M0. M1 and M2 now both
depend on M0 and may run in parallel after M0 completes. M3 remains
sequential after M1 and M2.

## 2026-06-06 - Babel v0.2.0 re-audit gaps closed

Genesis rule restricted to operation_type `draft` or `suggest` with
`meta.rollback_to` null for the first document; no new `genesis` type
introduced. Handoff protocol explicitly excludes documents failing
tier-1 validation from state progression. Canonical serialization
mandates lexicographic object-key sorting by Unicode code point,
guaranteeing cross-platform hash stability.

## 2026-06-06 - Babel v0.2.0 finalized

Canonical serialization (NFC Unicode, deterministic number format,
single LF terminator) and handoff log protocol (unique file naming,
fork resolution by lex-greatest filename, genesis rule, async
validation pipeline) are now part of the frozen v0.2.0 spec.

## 2026-06-06 - Babel v0.1.0 finalized

Strict RFC 8259 JSON subset, SemVer with patch-agnostic compatibility,
equal-minor = silent-ignore extensions, operation_type enum with
conditional rollback_to requirement.
