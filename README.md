# Babel Protocol

Babel is a self-auditing protocol workspace for autonomous human+AI engineering. Multiple AI agents propose, review, sign off on, and commit strictly additive protocol changes while preserving failed rounds as audit artifacts. The result is a conflict-free handoff system where humans and agents can exchange durable state, recover from failures, and evolve the protocol without rewriting frozen history.

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State        | Description                                                                        |
|---------|--------------|------------------------------------------------------------------------------------|
| v0.1.0  | frozen       | Core schema: operation_type, ext registry, canonical JSON                          |
| v0.2.0  | frozen       | Canonical serialization: NFC, sorted keys, deterministic numbers, single LF        |
| v0.3.0  | frozen       | M0 RPC + parser conformance + agent integration milestone architecture            |
| v0.4.0  | frozen       | CDR deterministic ordering, DTL heartbeats, M0 prerequisite sequencing            |
| v0.5.1  | frozen       | ASMC heartbeat exemption, TDS deadline rejection, XRP proxy_proof cascade          |
| v0.6.0  | frozen       | BSS grammar, AIC CLI (babel-emit/validate/hash), HIG atomic inbox/processing       |
| v0.7.0  | frozen       | TIC packaging, WCP gitignore, ITP golden tests with crash handling                |
| v0.8.1  | frozen       | BCRP composite cursor, BRAP bounded amend cycle, BSDC LCS tie-breaking            |
| v0.9.0  | in progress  | BWCC (shipped), BSSC (shipped), BHOP (shipped), manifest (pending)                 |

## v0.9.0 Layers

- **BWCC v0.9.0** (shipped): Static workflow envelope, Kahn O(n+e) acyclicity,
  non-retroactive workflow_amend, upstream-fail XRP cascade.
- **BSSC v0.9.0** (shipped): State snapshot continuity, hash chain with
  1024-cap recovery, unique agent_id, distinct emission bound vs seq
  monotonicity, cross-snapshot seq regression check.
- **BHOP v0.9.0** (shipped): Human override protocol with dual-authenticity
  (meta.author=human + authorized_hig_gateway), gateway+agent two-layer pause
  enforcement, explicit post-cancel terminated state, override hash chain,
  BCRP-based agent observation, BSSC state durability for override observation.
- **v0.9.0 manifest** (pending): Pre-commit hook will compute canonical SHA-256
  of all three specs and atomically rewrite manifest before commit.

## Single-Artifact-per-Finalize

v0.9.0 materializes under a single-artifact-per-finalize protocol: each
`pair_b_finalize` cycle ships one internally consistent spec (or
implementation) plus README/CHANGELOG updates. This bounds model output
size and ensures every cycle is reviewable and mergeable in isolation.
Frozen v0.1.0-v0.8.1 layers remain unchanged.

## License

Apache-2.0.

## Frozen invariants

- Canonical serialization: NFC, sorted keys, deterministic numbers,
  single LF (v0.2.0, frozen).
- Handoff log: append-only, atomic temp+rename, lex-greatest
  filename fork resolution (v0.2.0, frozen).
- operation_type enum: six values, conditional rollback_to (v0.1.0,
  frozen).
- AIC CLI exit codes: 0,1,2,3 only (v0.6.0, frozen).
- ITP exit codes: 0,10,20 only, disjoint from AIC codes (v0.7.0).
