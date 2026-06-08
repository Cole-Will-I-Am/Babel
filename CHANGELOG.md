# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. Completes the append-query collaboration loop started in v0.10.2. Stage 7 locks the handoff schema; stage 10b ships the validator module; stage 11 wires it into the write path.

### 2026-06-08 — Stage 11a/11a2 audit round 3 signoff

- **Kimi split-stage kickoff:** Resolved the two prior round-2 blockers by splitting stage 11a into two sequential single-file stages (11a for `bsl_validator.py`, 11a2 for `handoff.py`). Preserves the anti-timeout single-file cadence.
- **Nemotron implementation-ready refinement:** Confirmed `validate_block_string` belongs in `bsl_validator.py` as direct composition of `validate_header` and `validate_body_kv` (no intermediate block string construction). Verified `bsl_parser` treats all body values as opaque raw strings, so lowercase `'true'`/`'false'` bool encoding does not conflict with any bareword parsing rules.
- **DeepSeek audit signoff=true:** Both prior blockers (two-file delivery contradiction, `validate_block_string` design ambiguity) are fully resolved by the split-stage plan with direct-call composition. No blocking issues remain.
- **Minor consistency refinement (normative):** `validate_block_string` MUST capture the `block_type` returned by `validate_header(header, line_no=0)` and pass it to `validate_body_kv` instead of the function's `block_type` parameter. The parameter is retained for API symmetry, but body validation uses the actual header type to prevent header-body mismatch if a caller passes an inconsistent `block_type`.
- **Five sub-stages queued as separate single-file finalize rounds (anti-timeout cadence preserved):** 11a (`bsl_validator.py` `validate_block_string` with direct-call composition), 11a2 (`handoff.py` pre-write gate, encoding helpers, `HandoffIntegrityError`), 11b (`companion.py` `lint <path>` subcommand), 11c (`tests/test_handoff_validation_gate.py`), 11d (`bsl_validator.py` grammar manifest comment block). Gates: 11a2 on 11a; 11b/11c on 11a2; 11d on 11a.
- **Signoff=true for this documentation pair:** the README and CHANGELOG entries are internally consistent, additive to the prior 11a round-2 surface, and reflect the completed audit chain. The next artifact-writing stage can attempt stage 11a immediately.

### 2026-06-08 — Stage 11a audit round 2 (docs-only finalize)

- DeepSeek round-2 audit signoff=false on Nemotron's refined plan: one blocker (two-file delivery contradicts anti-timeout cadence) and one design ambiguity (`validate_block_string` constructs redundant block string). Resolution path: split 11a into 11a + 11a2, direct-call `validate_block_string`. Stages 9a/9b/10b complete per coder.

### 2026-06-08 — Stage 11 audit (docs-only finalize)

- DeepSeek audit signoff=false on Nemotron's stage 11 implementation-ready plan: three blockers (post-write gate persistence, missing bool encoding, whole-file validation scope) require architecture amendment. Stages 9a/9b/10b complete per coder.

### 2026-06-08 — Stage 10a architecture approval (docs-only finalize)

- DeepSeek audit signoff=true on Kimi/Nemotron amended BSL validation architecture. Version declared in body KV (not header), required keys per block type specified, parser dependency verified with fallback. Extra keys policy resolved as `reject` (deterministic default). Stages 9a/9b/10b queued as single-file sub-stages.

### 2026-06-08 — Stage 10 audit (docs-only finalize)

- DeepSeek audit signoff=false on Nemotron's stage 10 pivot: three blocking ambiguities (version declaration location, required body keys per block type, `bsl_parser.py` dependency verification). Stages 9a/9b HANDOFF_SCHEMA plan conditionally approved pending `handoff.py` ground-truth verification.

### 2026-06-08 — Stage 7c docs finalize

- README and CHANGELOG updated for the 9-key handoff block schema lock and `BABEL_VERSION` 0.10.3. Anti-timeout cadence held (README + CHANGELOG only). DeepSeek's BISC file-rename concern surfaced as required_change for stage 7b.

### 2026-06-08 — Stage 6 docs finalize (6e+6f)

- README documents handoff query API (`get_latest_handoff`, `list_handoffs`), companion CLI (`init`, `render`, `validate`), frozen handoff schema (6 keys at the time, now superseded by 9-key lock in stage 7a), and seven sub-stage plan. CHANGELOG v0.10.3 section added with planned status.

## v0.10.2 — Handoff Append + BSL Parser + BISC Integrity

Initial BSL parser, handoff append protocol, and BISC integrity spec. Stages 1a–5b shipped as single-file finalize rounds holding the anti-timeout cadence. Carry-over: stages 5a (handoff.py `append_handoff` implementation) and 5b (`test_handoff_append.py`) remain queued in the broader pipeline.

### 2026-06-08 — Stage 4c.2e+4c.2f finalize

- README and CHANGELOG updated with human-readable summaries of stages 1a–4c.2c and planned stage 5a. `agent_id` clarification resolved: prepend `## agent: <id>\n` before SHA256 hash.

### 2026-06-08 — Stage 4c.1

- BISC spec amendment adds `file_error` and `internal_error` to error taxonomy in new section 4.3. Eight codes total (six library + two process). Library/process contract preserved.
