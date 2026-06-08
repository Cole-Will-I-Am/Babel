# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. Continues the append-query collaboration loop from v0.10.2.

### 2026-06-08 — Stage 11b/11d/11e audit round 3: signoff

DeepSeek signoff=true on Nemotron's refined stages 11b/11d/11e validation surface plan. The handoff required key ambiguity is fully resolved: `HANDOFF_SCHEMA` (stage 9a TypedDict) contains exactly 9 payload keys, and the BSL syntax layer requires a 10th `version` body KV. Lint subcommand has full BISC error handling matching the contract in `reference/babel/__main__.py`. Conformance test uses behavioral assertions only, with no internal `REQUIRED_KEYS` dict access. Grammar manifest is explicit with literal key name lists for handoff (10), intent (3), and meta (2). Three single-file stages queued for sequential delivery:

- **11b**: `reference/babel/companion.py` — add `lint <path>` subcommand with `BabelParseError` + `OSError` + `Exception` handlers, all emitting JSON to stderr and exiting 6. Single-file, gated on stage 11a2.
- **11d**: `reference/babel/bsl_validator.py` — add normative grammar manifest comment block with explicit key names, encoding conventions, version lint rule. Single-file, gated on stage 11a.
- **11e**: `reference/tests/test_grammar_manifest.py` — author behavioral conformance test that parses the manifest via regex, compiles the documented header regex, and asserts required key sets via `validate_body_kv` calls. Single-file, gated on stage 11d.

Anti-timeout cadence held (README + CHANGELOG only). Coder completion recorded for stages 9a (HANDOFF_SCHEMA), 9b (test_handoff_append.py), 10b (bsl_validator.py), 11a (validate_block_string), and 11a2 (handoff.py pre-write gate). All blockers and issues from rounds 1 and 2 are now resolved. signoff=true; the next artifact-writing stage can attempt stage 11b immediately.

### 2026-06-08 — Stage 11b/11d/11e audit round 2: handoff keys

DeepSeek signoff=false on Nemotron's refined plan: round-1 issues (OSError/Exception handling, test fragility) are now approved; new blocker is the handoff required key count ambiguity ("9 HANDOFF_SCHEMA keys + version" is unclear whether `version` is already in `HANDOFF_SCHEMA`). Docs surface the round-1 resolution and the new blocker with prescriptive fix (inspect `handoff.py`, list 10 explicit key names for handoff, 3 for intent, 2 for meta). Three sub-stages queued with gate dependencies. signoff=false.

### 2026-06-08 — Stage 11b/11d/11e audit round 1: issues

DeepSeek signoff=false on Nemotron's refined validation surface plan: two issues (missing BISC-compliant OSError/Exception handling in lint subcommand, test fragility from internal `REQUIRED_KEYS` dict access). Coder completion recorded for stages 9a/9b/10b/11a/11a2 and prerequisite micro-patch. Anti-timeout cadence held. Three single-file stages queued as separate finalize rounds gated on the prescribed amendments. signoff=false.

### 2026-06-08 — Stage 11a2 audit round 5: signoff

DeepSeek signoff=true on Nemotron's corrected 11a2 plan: `BabelParseError` now correctly sourced from `bsl_parser` (the exception's definition site). Dependency inversion via `validate_version(expected_version, version, line_no)` parameterization approved. Pre-write gate with bool/list/str encoding approved. Prerequisite micro-patch (`bsl_validator.py` single-file) remains the gating step before 11a2. Coder completion recorded for stages 9a/9b/10b/11a/manifest/bootstrap/circular-imports. Anti-timeout cadence held. signoff=true.

### 2026-06-08 — Stage 11a2 audit round 4: blockers

DeepSeek signoff=false: two blockers (unverified prerequisite dependency inversion in `bsl_validator.py`, `BabelParseError` import source incorrect in 11a2 plan). Coder completion recorded. Two-file prerequisite+11a2 sequence queued. signoff=false.

### 2026-06-08 — Stage 11a/11a2 audit round 3: signoff

DeepSeek signoff=true: both prior blockers (two-file contradiction, `validate_block_string` design ambiguity) fully resolved by split-stage direct-call composition. One minor recommendation: `validate_block_string` should use `block_type` returned by `validate_header` for `validate_body_kv` to prevent header-body mismatch. Five sub-stages queued as single-file rounds. signoff=true.

### 2026-06-08 — Stage 11a audit round 2: split required

DeepSeek signoff=false: stage 11a claims single-file but requires two files (handoff.py + bsl_validator.py), contradicting the anti-timeout cadence. `validate_block_string` design ambiguity: should direct-call `validate_header` + `validate_body_kv` without constructing intermediate block string. Resolution: split into 11a (bsl_validator.py) + 11a2 (handoff.py); clarify direct-call primitive. signoff=false.

### 2026-06-08 — Stage 11 audit: 3 blockers

DeepSeek signoff=false on Nemotron's refined plan: three blockers (post-write validation gate persistence, missing bool encoding, whole-file validation scope) require amendment before 11a-11d implementation. 9a/9b/10b completion recorded. Four sub-stages queued. signoff=false.

### 2026-06-08 — Stage 10a architecture approval

DeepSeek signoff=true on Kimi/Nemotron amended architecture (version in body KV, required keys per block type, parser dependency with fallback). Extra keys policy resolved: reject any key not in required set per block type. Implementation queued as three single-file stages (9a TypedDict, 9b test, 10b validator) preserving anti-timeout cadence. signoff=true.

### 2026-06-08 — Stage 7c docs finalize

README+CHANGELOG pair documents the 9-key handoff block schema and 0.10.3 version lock. Anti-timeout cadence held. DeepSeek's BISC file-rename concern surfaced as required_change for stage 7b. signoff=true.

### 2026-06-08 — Stage 6 docs finalize (6e+6f)

README.md documents handoff query API, companion CLI init/render/validate, frozen handoff schema with all six keys (id, agent_id, content, blocking_issues, required_changes, next_owner), and seven sub-stage plan. CHANGELOG.md v0.10.3 section added. Anti-timeout cadence held. Stages 5a/5b still pending in broader pipeline.

## v0.10.2 — Handoff Block Append + BISC Contract (Released)

Append-only handoff block protocol with BISC integrity contract, BCPR prompt protocol, and end-to-end append-query collaboration loop.
