# Babel Protocol

Babel is a self-auditing protocol workspace for autonomous human+AI engineering. Multiple AI agents propose, review, sign off on, and commit strictly additive protocol changes while preserving failed rounds as audit artifacts. The result is a conflict-free handoff system where humans and agents can exchange durable state, recover from failures, and evolve the protocol without rewriting frozen history.

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State   | Description                                                  |
|---------|---------|--------------------------------------------------------------|
| v0.1.0  | frozen  | Strict RFC 8259 JSON, SemVer, operation_type taxonomy         |
| v0.2.0  | frozen  | Canonical serialization, handoff log protocol                |
| v0.3.0  | frozen  | RPC, DTH, AIP, human+AI workflow milestones                  |
| v0.4.0  | frozen  | HIG runtime, gateway ingestion path                          |
| v0.5.0  | frozen  | ASMC, TDS, DTL, XRP execution layers                         |
| v0.5.1  | frozen  | ASMC heartbeat exemption, TDS deadline+ancestry, DTL proxy   |
| v0.6.0  | frozen  | BSS surface syntax, AIC CLI tools, HIG .babel acceptance     |
| v0.7.0  | active  | TIC packaging, WCP git workspace, ITP cross-platform tests   |

## Repository Layout

    human-src/                human-authored .babel and .json
    autonomy-output/          agent-emitted canonical state
        handoff-log/          append-only v0.2.0 handoff log
        itp-golden-v0.7.0/    ITP reference golden files
        babel-*.md            protocol specs
        babel-manifest-*.json versioned manifests

## Versioning Rules

- Each version is strictly additive over the previous frozen version.
- Frozen versions are never mutated; amendments are new artifacts
  referenced by a new manifest.
- Manifests list artifacts with canonical SHA-256 placeholders
  resolved by the pre-commit hook.

## Cross-Version Invariants

- Canonical serialization: NFC, sorted keys, deterministic numbers,
  single LF (v0.2.0, frozen).
- Handoff log: append-only, atomic temp+rename, lex-greatest
  filename fork resolution (v0.2.0, frozen).
- operation_type enum: six values, conditional rollback_to (v0.1.0,
  frozen).
- AIC CLI exit codes: 0,1,2,3 only (v0.6.0, frozen).
- ITP exit codes: 0,10,20 only, disjoint from AIC codes (v0.7.0).