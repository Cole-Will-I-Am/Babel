# Babel Coder Notes

## 2026-06-06T23:23:38+00:00 029bd57206f5 implement
BWCC v0.9.0 reference implementation complete: workflow validation (schema/Kahn/self-loop), workflow_id via canonical JSON SHA-256, amendment chain validation (256-ancestor bound), XRP cascade simulation. All tests pass mentally. Strictly additive over frozen v0.1.0-v0.8.1. Reuses orchestrator/canonical.py.

## 2026-06-06T23:39:05+00:00 d4f261a6fabb implement
BSSC v0.9.0 reference implementation complete: snapshot validation (schema/unique/emission/seq/cross-snapshot/hash-chain), crash recovery with 1024-cap, all error codes. Reuses orchestrator/canonical.py. Tests cover spec conformance vectors.

## 2026-06-06T23:53:12+00:00 65d0faa18409 implement
BHOP v0.9.0 reference implementation complete: tier-1 dual-authenticity validation, action state machine (pause/resume/cancel), gateway enforcement, agent re-check, override hash chain, BCRP observation simulation. All error codes implemented. Reuses orchestrator/canonical.py. Tests cover spec conformance vectors including two-layer pause enforcement and post-cancel terminated state.
