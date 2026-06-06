# Babel v0.3.0 Changelog

## Overview
v0.3.0 is an additive implementation layer on top of frozen v0.1.0 schema
and v0.2.0 canonical serialization and handoff protocol. It defines the
Reference Parser Contract (RPC), Deterministic Test Harness (DTH), Agent
Integration Pattern (AIP), and the human+AI collaboration bridge. No
normative schema changes.

## Resolved Audit Items (DeepSeek v0.3.0 audit, 2026-06-06)

| # | Issue | Resolution | Artifact |
|---|-------|------------|----------|
| 1 | M1/M2 parallel execution unsafe because M2 requires the RPC implementation that M1 was expected to produce | Extract RPC implementation as a new prerequisite phase M0. M1 and M2 both depend on M0 and may run in parallel after M0 completes. M3 remains sequential. | babel-milestones-v0.3.0.md |

## Additive Contracts (no schema changes)

### Reference Parser Contract (RPC)
Three pure functions: `canonicalize`, `validate_tier1`, `hash_state`. No I/O
or shared mutable state. Reference implementation in Python 3.11+ is
authoritative for cross-language conformance. Byte-exact output and
identical hash output are the only valid conformance metrics.

### Deterministic Test Harness (DTH)
Nemotron-owned golden file matrix in
`autonomy-output/dth-golden-v0.3.0/` covering: Unicode NFC edge cases,
floating-point normalization, nested lexicographic key sorting, invalid
document rejection, and `ext.human.intent` array order preservation.
Implementations must pass 100% of golden pairs before handoff log
eligibility.

### Agent Integration Pattern (AIP)
Local self-check before handoff log append: agents must assert
`hash_state(canonicalize(emitted_bytes)) == hash_state(emitted_bytes)`.
Mismatches are rejected locally without retry; the agent must emit a
corrected new document with a fresh sequence id. This guarantees that the
agent's internal representation never drifts from the canonical form.

### Human+AI Collaboration Bridge
Human intent is captured exclusively via `ext.human.intent` string arrays in
standard Babel documents with `operation_type: suggest` and `meta.author:
human`. Humans never touch handoff log files directly. Agents may only
append `draft` or `commit` documents that reference the human suggestion
hash in `meta.rollback_to`, preserving the append-only invariant and the
immutable audit trail of intent.

## Backward Compatibility
All v0.3.0 contracts are strictly additive over frozen v0.1.0 schema and
v0.2.0 protocol. The v0.1.0 extension registry, `operation_type` enum, and
conditional `rollback_to` rule are unchanged. v0.2.0 canonical serialization
(NFC, deterministic numbers, single LF, Unicode code point key sorting) is
preserved as the input format for the RPC.

## Execution Prerequisites
The following artifacts must exist before M0 begins:
- `autonomy-output/babel-manifest-v0.2.0.json` — manifest of v0.2.0
  artifacts with canonical SHA-256 hashes.
- `autonomy-output/dth-golden-v0.3.0/` — golden file matrix used by M0,
  M1, and M2 acceptance.
