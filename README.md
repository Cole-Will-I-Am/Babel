# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State        | Description                                                                                  |
|---------|--------------|----------------------------------------------------------------------------------------------|
| v0.1.0  | frozen       | Document schema, operation_type enum, extension registry, canonical serialization           |
| v0.2.0  | frozen       | Canonical JSON serialization, append-only handoff log, async validation                      |
| v0.3.0  | frozen       | M0/M1/M2/M3 milestone architecture with M0 RPC as strict prerequisite                        |
| v0.4.0  | frozen       | CDR (Conflict Detection and Resolution) ordered by canonical SHA-256                         |
| v0.5.0  | frozen       | DTL, XRP, TDS, ASMC heartbeat, timeout, and state-machine contracts                          |
| v0.5.1  | frozen       | Heartbeat sole-field exemption, isolated self-rollback, tier-1 deadline rejection            |
| v0.6.0  | frozen       | BSS strict JSON5 subset, AIC CLI tools (babel-emit/validate/hash), HIG atomic inbox          |
| v0.7.0  | frozen       | TIC reproducible packaging, WCP workspace coexistence, ITP integration tests                 |
| v0.8.0  | frozen       | BCRP cursor pagination, BRAP review and amend protocol, BSDC structured diff                 |
| v0.8.1  | frozen       | Composite (sha256, seq) cursors, bounded amend cycle, deterministic LCS tie-breaking         |
| v0.9.0  | in progress  | BWCC static workflow envelope, BSSC snapshot integrity, BHOP human override                  |

## Materialization Protocol

v0.9.0 onward uses the **single-artifact-per-finalize** protocol:
each `pair_b_finalize` cycle authors exactly one specification
document to bound model output and prevent timeouts. The manifest is
produced in a separate cycle after all specs in the version are
committed. Ordering for v0.9.0: BWCC, BSSC, BHOP, manifest.

## Versioning Rules

- Each version is strictly additive over the previous frozen version.
- No frozen field is ever mutated.
- `frozen_manifest_ref` chains each manifest to the prior frozen one.
- `canonical_sha256` is computed at commit time by a pre-commit hook
  and atomically rewrites the manifest.

## Repository Layout

- `autonomy-output/` — All Babel specification documents and
  manifests, named `babel-<spec>-v<version>.md` and
  `babel-manifest-v<version>.json`.
- `human-src/` — Human-authored `.babel` source files (BSS v0.6.0).
- `autonomy-output/handoff-log/` — Append-only gateway handoff log.
