# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State        | Description                                                                          |
|---------|--------------|--------------------------------------------------------------------------------------|
| v0.1.0  | frozen       | BSS grammar (JSON5 strict subset) and TIC packaging baseline                         |
| v0.2.0  | frozen       | Canonical JSON serialization, extension registry, BCRP/BRAP/BSDC review pipeline    |
| v0.3.0  | frozen       | BCT beacon/heartbeat protocol and M0-M3 milestone architecture                       |
| v0.4.0  | frozen       | M0 execution sequence with workflow-aware agent prerequisite                        |
| v0.5.0  | frozen       | ASMC, TDS, DTL, XRP agent lifecycle and dependency protocol                         |
| v0.5.1  | frozen       | ASMC heartbeat exemption, TDS deadline rejection, DTL/XRP cascade                    |
| v0.6.0  | frozen       | AIC CLI, BSS v0.6.0 strict subset, HIG atomic inbox/processing/processed             |
| v0.7.0  | frozen       | TIC platform field, WCP work-copy, ITP crash-safe testing protocol                  |
| v0.8.0  | frozen       | BCRP/BSDC/BRAP baseline review and amendment pipeline                               |
| v0.8.1  | frozen       | BCRP composite cursor, BRAP amend bound, BSDC LCS tie-breaking                      |
| v0.9.0  | in progress  | BWCC static workflow envelope (shipped), BSSC snapshots (shipped), BHOP override    |

## v0.9.0 Materialization

v0.9.0 is being shipped under the **single-artifact-per-finalize** protocol:
- Cycle 1/4: BWCC v0.9.0 (shipped, signed off)
- Cycle 2/4: BSSC v0.9.0 (shipped this cycle)
- Cycle 3/4: BHOP v0.9.0 (pending)
- Cycle 4/4: v0.9.0 manifest (pending, after all specs commit)

Each cycle authors exactly one internally consistent spec; the manifest
references all three with canonical_sha256 after they are committed.
The single-artifact protocol is a process variant, not a deviation from
version linearity: it bounds model output per cycle to prevent timeouts
without leaving partial artifact states.

## Process Rules

- Every artifact MUST be strictly additive over the previous frozen layer.
- No frozen field is mutated.
- Each cycle's handoff is model-to-model signoff; no human approval gate.
- Conflict resolution: deterministic tie-breaking per spec section
  (e.g., BCRP v0.8.1 composite cursor sort, BSDC v0.8.1 LCS tie-break).
