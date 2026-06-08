# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, and conformance test coverage. Bridge to v0.10.4 via stage 12 write-serialization primitive.

### 2026-06-08 — Stage 12b audit round 3: signoff

- Kimi revised 12b kickoff with unified sidecar lock file (`<path>.babel.lock`) resolving the round-2 creation race blocker.
- Nemotron implementation-ready refinement combining sidecar lock (`fcntl.flock(LOCK_EX)`) + generation counter + atomic temp-file + `os.replace` + creation-under-lock protocol (initial meta block `generation=1`) + platform guard (`HandoffIntegrityError('platform_unsupported')` on non-POSIX).
- DeepSeek audit signoff=true: no blockers. Unified sidecar lock serializes both initial `.babel` file creation and subsequent `append_handoff` operations, resolving the round-2 creation race. Orphaned sidecar files are harmless.
- 12a BISC file patch remains the gating prerequisite (spec-first ordering hard constraint). Implementation queue: 12a BISC (single-file) → 12b code (single-file) → 12c concurrent test (single-file).

### 2026-06-08 — Stage 12b audit round 2: signoff=false (creation protocol missing)

- Kimi revised 12b kickoff adopting `fcntl.flock(LOCK_EX)` per prior round 1 audit.
- Nemotron implementation-ready refinement with lock + generation + atomic replace.
- DeepSeek audit signoff=true on lock-based mechanism for existing files, signoff=false on plan due to missing creation protocol for new `.babel` files.
- Prescriptive resolution: unified sidecar lock file (`<path>.babel.lock`) for creation+append serialization.

### 2026-06-08 — Stage 12b audit round 1: signoff=false (optimistic locking)

- Kimi stage 12b kickoff after 12a plan approval.
- Nemotron refined plan with generation counter + atomic replace.
- DeepSeek audit signoff=false: generation counter + atomic replace is optimistic locking with TOCTOU race window, allows lost updates under concurrent `append_handoff` calls, contradicts conflict-free requirement.
- Prescriptive resolution: adopt `fcntl.flock` for true mutual exclusion or explicitly accept non-conflict-free semantics.

### 2026-06-08 — Stage 12a BISC amendment plan: signoff

- Kimi architecture kickoff after 11f doc sweep.
- Nemotron implementation-ready refinement with three normative sections (5.3 Grammar Manifest, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract).
- DeepSeek audit signoff=true with no blockers. BISC file patch queued as next single-file spec round.

### 2026-06-08 — Stage 11f doc sweep: signoff

- Kimi 11f doc sweep kickoff after 11b/11d/11e commit.
- Nemotron refined plan: README documents `companion.py lint` subcommand, grammar manifest, and conformance test; CHANGELOG records delivery chain.
- DeepSeek audit signoff=true with no blockers. Coder delivery of stages 11b/11d/11e recorded.

### 2026-06-08 — Stage 11b/11d/11e audit round 3: signoff

- Kimi validation surface architecture kickoff after 11a2 commit.
- Nemotron implementation-ready refinement: `companion.py lint` subcommand with full BISC error handling, grammar manifest in `bsl_validator.py` with explicit literal key names, `test_grammar_manifest.py` behavioral conformance test.
- DeepSeek audit signoff=true: handoff key ambiguity resolved (10 keys = 9 `HANDOFF_SCHEMA` payload + `version`), lint has full BISC error handling, conformance test uses behavioral assertions only. All prior blockers resolved.

### 2026-06-08 — Stage 11b/11d/11e audit round 2: handoff keys

- Nemotron refined plan with round 1 amendments (BISC error handling, behavioral assertions).
- DeepSeek audit signoff=true on amendments, signoff=false on plan: handoff required key count ambiguity (does `HANDOFF_SCHEMA` include `version`?).
- Prescriptive resolution: inspect `handoff.py` `HANDOFF_SCHEMA` to determine exact 9 payload keys; list 10 explicit key names in manifest.

### 2026-06-08 — Stage 11b/11d/11e audit round 1: signoff=false

- Kimi validation surface kickoff after 11a2 commit.
- Nemotron implementation-ready refinement.
- DeepSeek audit signoff=false: two issues (missing `OSError`/`Exception` handling in lint violating BISC contract, test fragility from internal `REQUIRED_KEYS` dict access).
- Prescriptive resolution: wrap `validate_file` in try/except for `BabelParseError` + `OSError` + `Exception`; replace internal dict access with behavioral assertions.

### 2026-06-08 — Stage 11a2 audit round 5: signoff

- Kimi 11a2 round-5 kickoff after round 4 rejection.
- Nemotron corrected plan: `BabelParseError` import source fixed (from `.bsl_parser`, the exception's definition site).
- DeepSeek audit signoff=true: import topology and dependency inversion are sound. Prerequisite micro-patch (`bsl_validator.py` `validate_version` parameterization + `BABEL_VERSION` import removal) remains gating.

### 2026-06-08 — Stage 11a2 audit round 4: signoff=false

- Kimi 11a2 kickoff after 11a commit.
- Nemotron refined plan: pre-write gate with `_encode_handoff_value`/`_decode_handoff_value`.
- DeepSeek audit signoff=false: two blockers (unverified prerequisite dependency inversion, `BabelParseError` import source incorrect).

### 2026-06-08 — Stage 11a/11a2 split-plan round-3 audit: signoff

- Kimi split-stage architecture kickoff after round 2.
- Nemotron refined plan: 11a (`bsl_validator.py`) + 11a2 (`handoff.py`); `validate_block_string` direct-call composition.
- DeepSeek audit signoff=true: both round-2 blockers resolved.

### 2026-06-08 — Stage 11a round-2 audit: signoff=false

- Kimi 11a kickoff after 10b commit.
- Nemotron refined plan.
- DeepSeek audit signoff=false: two blockers (two-file delivery contradicting anti-timeout cadence, `validate_block_string` design ambiguity).
- Resolution: split into 11a + 11a2 single-file rounds; direct-call composition.

### 2026-06-08 — Stage 11 audit: signoff=false

- Kimi 11 kickoff after 10b commit.
- Nemotron refined plan.
- DeepSeek audit signoff=false: three blockers (post-write gate persistence, missing bool encoding, whole-file scope).

### 2026-06-08 — Stage 10a architecture approval: signoff

- Kimi 10a architecture kickoff after 9a/9b ground-truth verification.
- Nemotron amended architecture: version in body KV, required keys per block type, parser dependency with fallback.
- DeepSeek audit signoff=true: extra-keys policy resolved (REJECT any key not in required set per block type for deterministic validation). Implementation queued as three single-file stages (9a, 9b, 10b).

### 2026-06-08 — Stage 9/10 architecture audit: signoff=false

- Kimi 9/10 architecture kickoff.
- Nemotron implementation-ready plan.
- DeepSeek audit signoff=false: three blocking ambiguities (version declaration location, required body keys per block type, `bsl_parser.py` dependency verification).

## v0.10.2 — Prior Cycle

- `append_handoff` carry-over (stages 5a/5b) deferred to v0.10.3 stage 12b.
- BISC section 5 amendment carry-over (stage 7b) deferred to v0.10.3 stage 12a.

## v0.10.1 — Initial Babel Stack

- BISC integrity spec, BCPR protocol, BSL syntax, initial handoff implementation.
