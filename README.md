# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version      | State        | Description                                                                  |
| ------------ | ------------ | ---------------------------------------------------------------------------- |
| v0.1.0-v0.8.1 | Frozen       | Prior protocol layers; immutable.                                            |
| v0.9.0       | Frozen       | BWCC, BSSC, BHOP specs and manifest. Pre-commit hook finalizes manifest hashes. |
| v0.10.0      | Frozen       | Reserved.                                                                    |
| v0.10.1      | Frozen       | Reserved.                                                                    |
| v0.10.2      | In progress  | BWSS, BISC, BCPR specs queued; procedural synthesis follows template registry. |
| v0.10.3      | In progress  | Bootstrap spec shipped (cycle 1/7); template registry, BWSS, BISC, BCPR, spec-index, synthesis follow. |

## Current Cycle

v0.10.3 cycle 1 of 7: bootstrap spec shipped. The recursive
basis_ref traversal procedure is now defined for aggregating v0.1.0-
v0.9.0 canonical_sha256 into the v0.10.3 spec-index. Cycle 2 (template
registry), cycles 3-5 (BWSS/BISC/BCPR), cycle 6 (spec-index +
validate-spec-index.py), and cycle 7 (procedural synthesis) follow
under the single-artifact-per-finalize protocol.

## v0.9.0 Freeze

Complete. BWCC (static workflow envelope, non-retroactive amend, Kahn
acyclicity), BSSC (state snapshots, unique agent_id, 1024-cap
recovery), BHOP (dual-auth human_override, two-layer pause, post-cancel
terminated state). Pre-commit hook `scripts/compute-manifest-sha256.py`
enforces basis_ref validation, rejects placeholder base, and atomically
rewrites manifest hashes via v0.2.0 canonicalization. The v0.9.0 base
is the foundation for v0.10.x deterministic synthesis.

## v0.10.x Roadmap

  - v0.10.2 BWSS: workflow submission service (grammar, compilation,
    edge-case test vectors).
  - v0.10.2 BISC: build/integration state continuity (task_commit,
    cross-log update semantics, CDR v0.4.0 hash tie-break).
  - v0.10.2 BCPR: build/ci pull-request protocol (escalation docs,
    Pair-B precedence, failed-state transition).
  - v0.10.3: bootstrap procedure (shipped), template registry, spec-
    index with composite unique constraint, validate-spec-index.py
    bidirectional gate, procedural synthesis of v0.9.0 and v0.10.2
    README/CHANGELOG via template registry.

## Operational Notes

  - Single-artifact-per-finalize: each cycle ships one normative spec
    or one procedural batch, never a mix of unrelated edits.
  - All artifacts are strictly additive. Frozen fields are never
    mutated.
  - Canonical JSON serialization follows v0.2.0: NFC, LF, sorted keys,
    deterministic numbers.
  - Manifests chain via basis_ref; the pre-commit hook recomputes and
    validates the chain on every commit.
  - See CHANGELOG.md for per-cycle history.
