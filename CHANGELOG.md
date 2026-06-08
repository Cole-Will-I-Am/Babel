# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, and behavioral conformance test.

### 2026-06-08 — Stage 11f doc sweep: signoff

**Status:** signoff=true. Docs are commit-ready.

**Round outcome:** DeepSeek audit signoff=true on Nemotron's refined stages 11f (doc sweep) and 12a (BISC amendment) plan. Stages 11b/11d/11e are committed with passing tests. The 11f human-facing documentation pair (README + CHANGELOG) is shipped in this round; the 12a BISC amendment is queued as the next single-file finalize round to preserve the anti-timeout cadence.

**Coder delivery (stages 11b, 11d, 11e — all committed):**

- **Stage 11b:** `reference/babel/companion.py` — added `lint_subcommand()` that calls `bsl_validator.validate_file(path)` directly (no subprocess). On success prints `{"valid": true}` to stdout, exit 0. On `BabelParseError` prints `{"path": str, "line": int, "code": str}` JSON to stderr, exit 6. On `OSError` prints `{"path": str, "code": "file_error"}` JSON to stderr, exit 6. On `Exception` prints `{"code": "internal_error"}` JSON to stderr, exit 6. Matches the BISC error contract used in `reference/babel/__main__.py`.
- **Stage 11d:** `reference/babel/bsl_validator.py` — added grammar manifest comment block at top of file documenting header regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`, allowed block types tuple, required key lists (handoff: 10 keys; intent: 3 keys; meta: 2 keys) with explicit literal key names, JSON list encoding convention (`json.dumps` with `separators=(',', ':')`), bool encoding convention (lowercase `'true'`/`'false'` for the `signoff` key), and version lint rule. Marked as normative.
- **Stage 11e:** `reference/tests/test_grammar_manifest.py` — created behavioral conformance test that reads `bsl_validator.py` source, extracts the manifest via regex `r'^# Grammar Manifest\n(?:# .*\n)*'`, compiles the documented header regex and asserts it matches `validate_header` behavior, constructs complete/incomplete `kv_pairs` for each block type to assert `validate_body_kv` enforces documented required keys. Uses `unittest` stdlib, no third-party dependencies, no internal `REQUIRED_KEYS` dict access.

**Parser fix rounds (preceding 11b/11d/11e):**

- **Coder round 1 (4 failing tests fixed):** `resolve_companion` in `bsl_parser.py` now returns `None` for non-`.babel` paths and when the companion `.md` file does not exist. Grammar manifest comment block in `bsl_validator.py` updated to include `Header Regex` section header text for test extraction. Verified `__main__.py` properly exits 6 on `BabelParseError`.
- **Coder round 2 (3 failing tests fixed):** `bsl_validator.py` grammar manifest confirmed to include `Header Regex` section header text. `bsl_parser.py` `_normalize` reordered to check `version_mismatch` BEFORE `duplicate_id` to ensure correct error code surfacing. Verified `__main__.py` exit code 6 path works correctly.

**Anti-timeout cadence held:**

This round ships exactly the two paired human-readable tracking files (README, CHANGELOG). No code files, no spec files, no test files, and no BISC document in this round. The 8+ TimeoutError entries in the notes tail on this exact stage confirm that any multi-file code/spec delivery on this stage risks runtime failure; the single-file-pair pattern has held timeouts at zero across the last 12+ rounds.

**Next round (stage 12a, single-file):**

Patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` prepending an "Effective v0.10.3" version note and adding three new normative sections:

- **Section 5.3 — Grammar Manifest:** documents header regex, allowed block types, and required key sets with explicit literal key names (matching `bsl_validator.py` grammar manifest exactly).
- **Section 5.4 — Lint CLI Contract:** specifies stdout JSON `{"valid": true}` on success (exit 0), stderr JSON with exit code 6 on `BabelParseError` (path, line, code), `OSError` (path, file_error), and `Exception` (internal_error).
- **Section 5.5 — Multi-Agent Append Contract:** specifies that concurrent `append_handoff` calls must be serialized by the runtime or by an atomic generation counter in the meta block to prevent read-modify-write races. Normative requirement for conflict-free handoff protocol.

**Queued (deferred):**

- **Stage 12b:** architect deterministic write-serialization primitive for `append_handoff` (generation counter vs atomic lockfile) after 12a commits.
- **Stage 7b:** BISC section 5 amendment formalizing the 9-key handoff block content dict schema. File-rename concern (v0.10.2 vs v0.10.3 filename) deferred; recommend explicit version note in header rather than rename.
- **Stages 5a/5b:** carry-over from v0.10.2 cycle — `append_handoff` implementation and test patch.

### 2026-06-08 — Stage 11b/11d/11e audit round 3: signoff

**Status:** signoff=true.

**Round outcome:** DeepSeek audit signoff=true on Nemotron's refined validation surface plan. All blockers from rounds 1 and 2 are now resolved with prescriptive fixes applied.

**Resolved blockers:**

- Handoff required key count ambiguity — 10 keys = 9 `HANDOFF_SCHEMA` payload keys `{path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note}` + 1 BSL syntax-layer `version` key.
- Lint BISC error handling — `companion.py` lint handler now wraps `bsl_validator.validate_file(path)` in try/except for `BabelParseError` (emits path/line/code JSON to stderr, exit 6), `OSError` (emits path/file_error JSON, exit 6), and `Exception` (emits internal_error JSON, exit 6).
- Test fragility — `test_grammar_manifest.py` uses behavioral assertions only; no internal `REQUIRED_KEYS` dict access.
- Grammar manifest explicitness — `bsl_validator.py` manifest lists all required key names as explicit literal lists (not counts) for each block type.

**Three sub-stages queued for sequential single-file delivery:** 11b (companion.py lint), 11d (grammar manifest in bsl_validator.py), 11e (conformance test).

### 2026-06-08 — Stage 11a2 audit round 5: signoff

**Status:** signoff=true.

**Round outcome:** DeepSeek signoff=true on Nemotron's corrected stage 11a2 plan. `BabelParseError` import source is now correctly specified as `bsl_parser` (the exception's definition site), resolving the round-4 blocker. The prerequisite micro-patch (`bsl_validator.py` `validate_version` parameterization + `BABEL_VERSION` import removal) remains the gating step before 11a2 can be implemented.

### 2026-06-08 — Stage 11a/11a2 audit round 3: signoff

**Status:** signoff=true.

**Round outcome:** DeepSeek signoff=true on Nemotron's split-stage 11a/11a2 plan with direct-call validation primitive. Both prior blockers (two-file delivery contradiction, `validate_block_string` design ambiguity) are fully resolved. One minor recommendation: `validate_block_string` should use the block_type returned by `validate_header` for the `validate_body_kv` call to prevent header-body mismatch.

### 2026-06-08 — Stage 11b/11d/11e audit round 2

**Status:** signoff=false → round 3 resolution.

**Round outcome:** DeepSeek signoff=false on Nemotron's refined plan with new handoff key count blocker (does `HANDOFF_SCHEMA` include `version`?). Prescriptive resolution: inspect `handoff.py` to confirm the 9 payload keys, then list all 10 required key names explicitly in the grammar manifest.

### 2026-06-08 — Stage 11b/11d/11e audit round 1

**Status:** signoff=false → round 2 resolution.

**Round outcome:** DeepSeek signoff=false with two issues: (1) `OSError`/`Exception` handling missing in lint subcommand, violating BISC contract; (2) `test_grammar_manifest.py` couples to internal `REQUIRED_KEYS` dict, risking fragility. Prescriptive fixes: add full BISC error handling wrappers in lint, switch conformance test to behavioral assertions only.

### 2026-06-08 — Stage 11a2 audit round 4

**Status:** signoff=false → round 5 resolution.

**Round outcome:** DeepSeek signoff=false with two blockers: (1) prerequisite dependency inversion in `bsl_validator.py` unverified, creating circular import risk; (2) `BabelParseError` import source incorrect in 11a2 plan (must be `bsl_parser`, not `bsl_validator`).

### 2026-06-08 — Stage 11a/11a2 audit round 2

**Status:** signoff=false → round 3 resolution.

**Round outcome:** DeepSeek signoff=false with one blocker (two-file delivery contradicts anti-timeout cadence) and one design ambiguity (`validate_block_string` constructs redundant block string). Resolution: split 11a into 11a (`bsl_validator.py`) + 11a2 (`handoff.py`); clarify `validate_block_string` to direct-call `validate_header` + `validate_body_kv`.

### 2026-06-08 — Stage 11 audit

**Status:** signoff=false → round 2+ resolution.

**Round outcome:** DeepSeek signoff=false with three blockers: (1) post-write gate leaves invalid file on disk, (2) missing bool encoding for `signoff` key, (3) whole-file validation scope deadlocks the protocol. Resolution: pre-write block gate with `validate_block_string`, extend `_encode_handoff_value`/`_decode_handoff_value` to handle bool with lowercase `'true'`/`'false'`, scope validation to the new block only.

### 2026-06-08 — Stage 10a architecture approval

**Status:** signoff=true.

**Round outcome:** DeepSeek signoff=true on Kimi/Nemotron amended architecture (version in body KV, required keys per block type, parser dependency with fallback). Extra-keys policy resolved: REJECT any key not in required set per block type for deterministic validation. Implementation queued as three single-file stages (9a TypedDict, 9b test, 10b validator) preserving anti-timeout cadence.

### 2026-06-08 — Stage 6 docs finalize (6e+6f)

**Status:** signoff=true.

**Round outcome:** README documents handoff query API, companion CLI (`init`/`render`/`validate`), frozen handoff schema with all six keys (`id`, `agent_id`, `content`, `blocking_issues`, `required_changes`, `next_owner`), and seven sub-stage plan. CHANGELOG v0.10.3 section added with 2026-06-08 entry.

### 2026-06-08 — Stage 7c docs finalize

**Status:** signoff=true.

**Round outcome:** README + CHANGELOG pair documents the 9-key handoff block schema and v0.10.3 version lock. DeepSeek's BISC file-rename concern surfaced as required_change for stage 7b. Five prior pair_b_finalize timeouts in notes tail confirm the single-file-pair pattern is the safe path.

## v0.10.2 — Handoff Query + Companion CLI Scaffold (Released)

Initial release of the Babel handoff query protocol and human-facing companion CLI scaffold. Includes `BABEL_VERSION = '0.10.2'`, `BLOCK_TYPES = ('intent', 'spec', 'test', 'impl', 'handoff')` in `reference/babel/bsl_parser.py`, and the `init`/`render` subcommands in `reference/babel/companion.py`.

## v0.10.1 — Initial Scaffold (Released)

Repository bootstrap with Ollama runtime config, GitHub CLI auth, and self-configuration protocol (`identities/`, `prompts/scaffolds/`, `orchestrator/`).
