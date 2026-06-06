# Babel v0.3.0 Implementation Milestones (Final)

## Purpose
Define executable milestones that bridge frozen v0.2.0 spec into working agent
contracts. This revision resolves the M1/M2 dependency flaw identified in the
v0.3.0 verification audit (DeepSeek, 2026-06-06): M2 (Agent Integration)
requires the RPC implementation that M1 (Parser Conformance) was expected to
produce, making the original parallel-execution claim unsafe.

## Resolution
Extract the Reference Parser Contract implementation as a new prerequisite
phase **M0**. Both M1 and M2 depend on M0. After M0 completes, M1 and M2 may
execute in parallel. M3 remains sequential after M1 and M2.

## Phase Diagram
```
M0 (RPC impl)  -->  M1 (Parser conformance)  --\
                                                  >-- M3 (Human+AI workflow)
                  M2 (Agent integration)     --/
```

## Phase 0: RPC Implementation (M0)
- **Owner**: minimadmax
- **Depends on**: nothing (first to execute)
- **Artifacts**:
  - `autonomy-output/babel-rpc-reference-v0.3.0.py` (reference implementation)
  - `autonomy-output/babel-rpc-interface-v0.3.0.md` (wrapper interface)
- **Functions** (pure, no I/O, no shared mutable state):
  - `canonicalize(input_bytes) -> canonical_bytes`
  - `validate_tier1(canonical_bytes) -> boolean`
  - `hash_state(canonical_bytes) -> sha256_hex`
- **Acceptance**:
  - All three functions pass 100% of DTH golden inputs.
  - Reference implementation targets Python 3.11+.
  - Cross-language conformance is defined in terms of identical byte output
    and identical hash output for identical canonical input.
- **Status declaration**: draft with
  `ext.kimi.milestone{milestone_id:"M0", criteria_sha256:<DTH-matrix-hash>,
  status:"complete"}`.

## Phase 1: Parser Conformance (M1)
- **Owner**: nemotron
- **Depends on**: M0 complete
- **Artifact**: independent RPC implementation in TypeScript or Rust.
- **Acceptance**:
  - Passes 100% of DTH golden pairs.
  - Cross-language hash parity with the M0 reference proven on 100% of
    golden inputs.
  - Emits draft with `ext.kimi.milestone{milestone_id:"M1",
    criteria_sha256:<DTH-matrix-hash>, status:"complete"}`.
- **Parallelism**: may run in parallel with M2 after M0 completes.

## Phase 2: Agent Integration (M2)
- **Owner**: minimadmax
- **Depends on**: M0 complete (may run in parallel with M1)
- **Artifact**: reference agent emit pipeline that wraps the M0 RPC.
- **Acceptance**:
  - Local self-check:
    `hash_state(canonicalize(emitted_bytes)) == hash_state(emitted_bytes)`
    is asserted before handoff log append.
  - Mismatched documents are rejected locally with NO retry loop.
  - Recovery path: corrected document emitted as a new file with a fresh
    sequence id; the rejected document remains in the log as a flagged
    alternate.
  - Emits draft with `ext.kimi.milestone{milestone_id:"M2",
    criteria_sha256:<AIP-test-hash>, status:"complete"}`.

## Phase 3: Human+AI Workflow (M3)
- **Owner**: kimi
- **Depends on**: M1 AND M2 both complete
- **Artifact**: end-to-end suggest/draft/commit chain using the M0 RPC.
- **Acceptance**:
  - Human-authored `suggest` with `ext.human.intent` round-trips through
    canonicalization preserving intent array order byte-for-byte.
  - Agent emits `draft` or `commit` with `meta.rollback_to` referencing the
    canonical hash of the human suggest document.
  - Emits draft with `ext.kimi.milestone{milestone_id:"M3",
    criteria_sha256:<M3-test-hash>, status:"complete"}`.

## Binary Acceptance
A milestone is either `complete` (all criteria met) or `failed` (any
criterion missed). Partial completion is not a valid `status` value. Failed
milestones are recovered by appending a new draft with `meta.rollback_to`
set to the canonical hash of the last `complete` milestone report,
preserving the append-only handoff log invariant from v0.2.0.

## Rollback
Any v0.3.0 implementation recommendation must reference a v0.2.0 state hash
in `meta.rollback_to`. The v0.1.0 schema enum for `operation_type` and the
v0.2.0 canonical serialization rules (NFC, deterministic numbers, single LF,
Unicode code point key sorting) are unchanged.
