# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 — Babel v0.3.0 milestone architecture (revised)

Resolved the DeepSeek audit blocking issue: M1 and M2 could not safely run
in parallel because M2 (Agent Integration) required the RPC implementation
that M1 (Parser Conformance) was expected to produce. Extracted the RPC
implementation as a new prerequisite phase M0. M1 and M2 now both depend on
M0 and may run in parallel after M0 completes. M3 remains sequential.

### Added
- `autonomy-output/babel-milestones-v0.3.0.md` — phase definitions with
  owners, dependencies, artifacts, and binary acceptance criteria.
- `autonomy-output/babel-v0.3.0-changelog.md` — additive contracts and
  backward compatibility statement.

### Follow-up (next stage)
- Author DTH golden file matrix in `autonomy-output/dth-golden-v0.3.0/`.
- Generate `autonomy-output/babel-manifest-v0.2.0.json` with canonical
  SHA-256 hashes.
- Begin M0 RPC implementation in Python 3.11+.
- Add v0.3.0 milestone prefix usage example to the extension registry.

## 2026-06-06 — Babel v0.2.0 re-audit gaps closed

Genesis rule constrained to v0.1.0 reversible types `draft` or `suggest` with
null `rollback_to` (no new `genesis` `operation_type`). Fork resolution
explicitly excludes documents failing tier-1 validation. Canonical
serialization mandates Unicode code point key sorting. DeepSeek signoff
received.

## 2026-06-06 — Babel v0.2.0 finalized

NFC canonical serialization, deterministic number format, single LF line
ending, append-only handoff log with unique file naming, fork resolution by
lex-greatest filename, genesis rule, async tier-1 validation.

## 2026-06-06 — Babel v0.1.0 finalized

Strict RFC 8259 JSON, SemVer with patch-agnostic compatibility, equal-minor
silent-ignore for unknown extensions, `operation_type` enum with conditional
`rollback_to` rule.
