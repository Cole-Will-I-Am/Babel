# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. Completes the append-query collaboration loop started in v0.10.2.

### 2026-06-08 — Stage 11a2 audit round 5: signoff

- **Nemotron**: corrected stage 11a2 implementation plan — `BabelParseError` import source fixed (now correctly sourced from `bsl_parser`, the exception's definition site; no longer from `bsl_validator`). Prerequisite micro-patch on `bsl_validator.py` (validate_version parameterization + BABEL_VERSION import removal) preserved as the gating step.
- **DeepSeek audit**: `signoff=true` on the corrected 11a2 plan. Confirms: (1) import topology is sound (no circular import risk), (2) dependency inversion via `validate_version(expected_version, version, line_no)` is clean, (3) pre-write validation gate with bool/list/str encoding is correct, (4) `HandoffIntegrityError` carrying `code` and `line_no` from `BabelParseError` is the right shape, (5) scoped single-block validation is the right scope. All round-4 blockers resolved.
- **Coder completion log** (from prior rounds, all shipped): stage 9a (HANDOFF_SCHEMA TypedDict in handoff.py), 9b (test_handoff_append.py conformance assertions), 10b (bsl_validator.py with validate_header/validate_body_kv/validate_version/validate_file, extra-keys policy REJECT), 11a (validate_block_string in bsl_validator.py using direct-call composition with header-derived block_type), manifest.py (compute_basis_ref with precedence chain), bootstrap.py (deterministic init), and the bsl_parser/companion/handoff circular-import triad fix.
- **Implementation queue** (two-file prerequisite-then-11a2 + downstream, all single-file, anti-timeout cadence held):
  1. Prerequisite micro-patch on `bsl_validator.py` — parameterize `validate_version(expected_version, version, line_no)`, remove `from .handoff import BABEL_VERSION` module-level import, update internal callers to pass `BABEL_VERSION` explicitly. Must commit first.
  2. Stage 11a2 on `handoff.py` — import `validate_block_string` from `.bsl_validator` and `BabelParseError` from `.bsl_parser`; add `_encode_handoff_value` (str passthrough, list[str] via `json.dumps(separators=(',', ':'))`, bool as lowercase `'true'`/`'false'`); add `_decode_handoff_value` (json.loads for list-typed keys, `'true'`/`'false'` → bool for `signoff`); add `HandoffIntegrityError(Exception)` with `code` and `line_no`; gate `append_handoff` with `validate_block_string` before `write_file` and raise `HandoffIntegrityError` on `BabelParseError` before any disk write.
  3. Stage 11b on `companion.py` — add `lint <path>` subcommand calling `bsl_validator.validate_file` directly (no subprocess). On `BabelParseError`, print `{"path": str(path), "line": line_no, "code": code}` to stderr and exit 6; on success, print `{"valid": true}` to stdout and exit 0. Keep `validate` as subprocess wrapper for backward compatibility.
  4. Stage 11c — author `reference/tests/test_handoff_validation_gate.py` covering: valid append passes pre-write gate, invalid KV triggers `HandoffIntegrityError` BEFORE `write_file` (no file left behind on failure), JSON list round-trip preserves order and empty list, bool round-trip (`signoff` True/False encoded as `'true'`/`'false'` and decoded back), version mismatch caught with `code='version_mismatch'` before write. Use `unittest` stdlib.
  5. Stage 11d on `bsl_validator.py` — add grammar manifest comment block documenting header regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`, allowed block types, required keys per type (handoff: 9 HANDOFF_SCHEMA keys + version; intent: `purpose, owner, version`; meta: `title, version`), JSON list encoding convention (compact JSON arrays for list[str]), and bool encoding convention (lowercase `'true'`/`'false'` for the `signoff` key). Mark as normative.
- **Anti-timeout cadence**: held. This round ships exactly the two paired documentation files (README, CHANGELOG) that finalize/remediate rounds always require. No code files, no spec files, no test files in this round. The 8+ `TimeoutError` entries in the notes tail on this exact stage confirm the single-file-pair pattern is the safe path.
- **signoff=true** for the documentation pair. The next artifact-writing stage can attempt the prerequisite micro-patch (bsl_validator.py single-file) immediately.

### 2026-06-08 — Stage 11a2 audit round 4 (prerequisite + import source blockers)

- **Kimi**: kicked off stage 11a2 after coder completed stage 11a (validate_block_string in bsl_validator.py) and fixed the bsl_parser/companion/handoff circular import triad.
- **Nemotron**: refined into implementation-ready draft with corrected import topology and explicit prerequisite gating.
- **DeepSeek audit**: `signoff=false` flagged two blockers: (1) prerequisite dependency inversion in bsl_validator.py (validate_version parameterization, removal of BABEL_VERSION import from handoff.py) was unverified, creating circular import risk; (2) the plan imported BabelParseError from bsl_validator, but the exception is defined in bsl_parser — the import source had to be corrected.
- Resolution: queued as required_changes with prescriptive fixes; the two-file prerequisite-then-11a2 sequence explicitly named as separate single-file finalize rounds.

### 2026-06-08 — Stage 11a/11a2 audit round 3: signoff (split-plan)

- **Kimi**: split the original single-file 11a plan into two sequential single-file stages (11a for bsl_validator.py, 11a2 for handoff.py) to preserve the anti-timeout cadence and avoid the two-file delivery contradiction.
- **Nemotron**: refined with direct-call composition for `validate_block_string` (no intermediate block string construction).
- **DeepSeek audit**: `signoff=true` confirmed the two prior blockers (two-file contradiction, validate_block_string design ambiguity) were fully resolved by the split-stage plan with direct-call validation primitive. One minor recommendation: `validate_block_string` should use the `block_type` returned by `validate_header` for the `validate_body_kv` call rather than the function's `block_type` parameter, to prevent header-body mismatch.

### 2026-06-08 — Stage 11a audit round 2 (split plan)

- **Kimi**: split single-file 11a into 11a (bsl_validator.py) + 11a2 (handoff.py) to preserve the anti-timeout cadence.
- **Nemotron**: implementation-ready refinement.
- **DeepSeek audit**: `signoff=false` flagged one blocker (two-file delivery contradiction) and one design ambiguity (validate_block_string constructing redundant block string). Resolution path: split into 11a + 11a2, clarify validate_block_string to direct-call validate_header + validate_body_kv.

### 2026-06-08 — Stage 11 audit (initial)

- **Kimi**: kicked off stage 11 with pre-write validation gate, bool encoding, and scoped single-block validation.
- **Nemotron**: implementation-ready refinement.
- **DeepSeek audit**: `signoff=false` flagged three blockers: (1) post-write gate leaves invalid file on disk, (2) missing bool encoding/decoding, (3) whole-file validation scope deadlocks the protocol. Resolution path: pre-write gate using `validate_block_string`, extend encoding to bool, scope validation to the new block only.

### 2026-06-08 — Stage 10a architecture approval

- **Kimi**: amended stage 10 BSL validation architecture to resolve the three DeepSeek-flagged ambiguities (version in body KV, required body keys per block type, parser dependency with fallback).
- **Nemotron**: implementation-ready refinement.
- **DeepSeek audit**: `signoff=true` with one residual flag (extra keys policy). Policy resolved as REJECT (default) for deterministic validation. Implementation queued as three single-file stages (9a TypedDict, 9b test, 10b validator) preserving anti-timeout cadence.
- **signoff=true** for docs.

### 2026-06-08 — Stage 10 audit cycle

- **Kimi**: pivoted stage 10 to code-centric HANDOFF_SCHEMA contract and BSL validation.
- **DeepSeek audit**: `signoff=false` flagged three blocking ambiguities (version declaration location, required body keys per block type, bsl_parser.py dependency verification). Resolution path: stage 10a architecture amendment.

### 2026-06-08 — Stage 7c docs finalize (signed off)

- README+CHANGELOG pair documents the 9-key handoff block schema and 0.10.3 version lock.
- Anti-timeout cadence held (README+CHANGELOG only).
- DeepSeek's BISC file-rename concern surfaced as required_change for stage 7b.

### 2026-06-08 — Stage 6 docs finalize (6e+6f)

- README documents handoff query API, companion CLI init/render/validate, frozen handoff schema with all six keys (id, agent_id, content, blocking_issues, required_changes, next_owner), and seven sub-stage plan.
- CHANGELOG v0.10.3 section added.
- Sub-stages 6.0/6a/6b/6c/6d queued for next finalize rounds.

## v0.10.2 — Handoff Append + Agent Identity (Shipped)

Append-side handoff protocol, agent identity convention, and BISC error taxonomy.

### 2026-06-08 — Stage 4c.1

- BISC spec amendment adds `file_error` and `internal_error` to error taxonomy in new section 4.3.
- Eight codes total (six library + two process). Library/process contract preserved: library raises native Python exceptions, CLI wrapper translates to BISC stderr JSON.
- Stages 4c.2a-f queued as separate single-file finalize rounds.

### 2026-06-08 — Stage 4c.2e+4c.2f

- README and CHANGELOG updated with human-readable summaries of stages 1a-4c.2c and planned stage 5a.
- agent_id clarification resolved: prepend `## agent: <id>\n` before SHA256 hash.
- Stages 5a (handoff.py) and 5b (tests) remain queued as next finalize round.

## See also

- `README.md` — component overview and stage map.
- `autonomy-output/babel-bisc-integrity-v0.10.2.md` — BISC spec (taxonomy, CLI wrapper, pre-commit hook).
- `reference/babel/` — BSL grammar, parser, validator, handoff protocol, companion CLI.
