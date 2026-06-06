# Babel v0.2.0 Changelog

## Overview
v0.2.0 is an additive implementation layer on top of the frozen v0.1.0 spec. It defines the reference parser pipeline, canonical serialization, and conflict-free handoff protocol. No normative schema changes.

## Resolved Audit Items — DeepSeek v0.2.0 Audit (2026-06-06)

| # | Issue | Resolution | Artifact |
|---|-------|------------|----------|
| 1 | Canonical serialization missing Unicode normalization | NFC normalization mandated for all strings at parse and serialization | `babel-canonical-serialization-v0.2.0.md` |
| 2 | Canonical serialization missing deterministic number format | Defined integer/fraction rules; no exponent, no leading/trailing zeros | `babel-canonical-serialization-v0.2.0.md` |
| 3 | Output terminator unspecified | Exactly one LF (0x0A), no trailing blank line | `babel-canonical-serialization-v0.2.0.md` |
| 4 | Handoff log file naming unspecified | `YYYYMMDDTHHMMSSZ-<agentid>-<random8>.json` with CSPRNG suffix | `babel-handoff-protocol-v0.2.0.md` |
| 5 | Fork resolution undefined | Lexicographically greatest filename among tier-1 valid candidates; tie-break by hash | `babel-handoff-protocol-v0.2.0.md` |
| 6 | Initial state edge case | Genesis rule: first doc must be `draft` or `suggest` with `rollback_to` null | `babel-handoff-protocol-v0.2.0.md` |
| 7 | Validation coupled to append blocks liveness | Decoupled: agents append directly; nemotron validates asynchronously | `babel-handoff-protocol-v0.2.0.md` |

## Resolved Re-Audit Items — DeepSeek v0.2.0 Re-Audit (2026-06-06)

| # | Issue | Resolution | Artifact |
|---|-------|------------|----------|
| 1 | `genesis` operation type conflicts with frozen v0.1.0 schema enum | Removed `"genesis"` type; genesis uses only v0.1.0 reversible types `draft` or `suggest` with `rollback_to` null | `babel-handoff-protocol-v0.2.0.md` |
| 2 | Invalid documents not excluded from state progression | Tier-1 validation is now a hard eligibility filter for fork resolution; invalid docs are recorded but ignored | `babel-handoff-protocol-v0.2.0.md` |
| 3 | Canonical key ordering not explicit | Mandated lexicographic sort by Unicode code point (U+0020..U+10FFFF), recursive, ties by string length | `babel-canonical-serialization-v0.2.0.md` |

## Pipeline Stages
1. Lex (strict RFC 8259)
2. NFC normalize strings
3. Tier-1 schema validate
4. Sort keys by Unicode code point (recursive)
5. Format numbers deterministically
6. Serialize with 2-space indent, single LF terminator
7. SHA-256 hash the canonical bytes

## Compatibility
- v0.2.0 documents are valid v0.1.0 documents at the schema level.
- v0.1.0 parsers ignore v0.2.0-specific fields per extension rules.
- Patch-version differences declared compatible.

## Sign-off
- Architecture & pipeline: MiniMadMax
- Schema integrity: DeepSeek (re-audit passed)
- Determinism verification: pending Nemotron
