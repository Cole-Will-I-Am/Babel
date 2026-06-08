# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. The grammar manifest is normative; the lint CLI contract is stable; the multi-agent append contract requires serialized writes.

### 2026-06-08 -- Stage 13 read-query plan: signoff

- **Kimi** kicked off stage 13 read-query architecture after the 12b round-3 signoff, decoupled from pending 12a/12b write-side gating.
- **Nemotron** refined the kickoff into an implementation-ready draft for single-file `reference/babel/query.py`: deterministic, immutable, versioned query interface over validated BSL AST.
- **DeepSeek** audited the plan and signed off: no blockers. The architecture is sound, the API is clear, and the implementation can proceed independently of 12a/12b.
- **Stage 13 finalize (this round, docs-only):** README and CHANGELOG record the audit approval and queue the implementation as the next single-file code round. Held the anti-timeout cadence that succeeded in 13+ prior rounds.
- **Stage 13 queued (next round, single-file):** Author `reference/babel/query.py` with `select_handoffs(ast, *, agent_id=None, signoff=None) -> tuple[MappingProxyType, ...]`, `HandoffView` TypedDict extending `HANDOFF_SCHEMA` with `_line: int`, `_block_id: str`, `_query_protocol_version: Literal[1]`, and private helpers `_filter_by_agent_id` and `_filter_by_signoff_status`. Import `HANDOFF_SCHEMA` from `handoff.py` and `MappingProxyType` from `types`. Sort results by `_line` ascending.
- **Stage 13a (deferred):** Document and enforce the validated-AST-only contract (raise `TypeError` on raw text or non-AST input).
- **Stage 13b (deferred, single-file, gated on stage 13 commit):** Author `reference/tests/test_query.py` with behavioral assertions for deterministic ordering, `MappingProxyType` immutability, agent/signoff filtering, `query_protocol_version=1` presence, empty-input behavior, and combined filter intersection.
- **Stage 12a (parallel, single-file):** BISC amendment patch queued as write-side prerequisite for 12b/12c, not gating stage 13.
- **Stage 12b/12c (gated on 12a):** Sidecar lock-based `append_handoff` and concurrent-append test as approved in round 3.
- **signoff=true** because the documentation pair is internally consistent, additive to the prior 12b round-3 docs surface, every claim is grounded in the audit chain, and the next artifact-writing stage can attempt stage 13 (query.py single-file) immediately.

### 2026-06-08 -- Stage 12b audit round 3: signoff=true

- **Kimi** revised 12b kickoff with unified sidecar lock file (`<path>.babel.lock`) resolving the round-2 creation race.
- **Nemotron** refined into an implementation-ready plan combining sidecar lock + `fcntl.flock(LOCK_EX)` + generation counter + atomic `os.replace` + platform guard.
- **DeepSeek** audited and signed off: no blockers. Unified sidecar lock serializes both initial `.babel` creation and subsequent appends under the same lock. Creation-under-lock protocol with initial meta block (`generation=1`) written atomically.
- **Archived (resolved) blockers from rounds 1-2:** generation counter + atomic replace is optimistic locking (round 1); creation race for new `.babel` files (round 2).
- **Implementation queue:** 12a BISC patch first (spec-first), then 12b handoff.py patch, then 12c concurrent test.

### 2026-06-08 -- Stage 12b audit round 2: signoff=false

- **Kimi** revised 12b kickoff adopting `fcntl.flock` per prior round 1 audit.
- **Nemotron** refined into an implementation-ready plan with lock + generation + atomic replace.
- **DeepSeek** audited: signoff=true on lock-based mechanism for existing files; signoff=false on plan due to missing creation protocol.
- **New blocker:** Creation race for new `.babel` files (flock only works on existing files).
- **Prescriptive fix:** Use sidecar lock file or O_CREAT|O_EXCL with atomic rename.

### 2026-06-08 -- Stage 12b audit round 1: signoff=false

- **Kimi** kicked off stage 12b after 12a plan approval.
- **Nemotron** refined into an implementation-ready plan with generation counter + atomic replace.
- **DeepSeek** audited: signoff=false. Generation counter + atomic replace is optimistic locking, allows lost updates, contradicts conflict-free requirement.
- **Prescriptive fix:** Use `fcntl.flock` for true mutual exclusion or accept non-conflict-free semantics.

### 2026-06-08 -- Stage 12a BISC amendment plan: signoff

- **Kimi** kicked off stage 12a BISC amendment after 11f doc sweep.
- **Nemotron** refined into an implementation-ready draft with three normative sections (5.3 Grammar Manifest, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract) aligning with committed stages 11b/11d/11e.
- **DeepSeek** audited and signed off: no blockers. The BISC file patch is queued as the next single-file spec round.

### 2026-06-08 -- Stage 11f doc sweep: signoff

- **Kimi** kicked off stage 11f doc sweep after 11b/11d/11e delivery.
- **Nemotron** refined the doc sweep plan covering README updates for lint subcommand, grammar manifest, and conformance test.
- **DeepSeek** audited and signed off: no blockers. Documentation is accurate and additive.
- **Delivered in this round:** README documents the companion.py `lint <path>` subcommand (BISC error handling), the grammar manifest location and structure in bsl_validator.py (header regex, block types, explicit literal key names, list/bool encoding), and the test_grammar_manifest.py behavioral conformance coverage.
- **signoff=true.**

### 2026-06-08 -- Stage 11b/11d/11e audit round 3: signoff

- **DeepSeek** signed off Nemotron's refined validation surface plan.
- **All prior blockers resolved:** handoff key count ambiguity (10 keys = 9 payload + version), lint BISC error handling (`BabelParseError` + `OSError` + `Exception`), test fragility (behavioral assertions only).
- **Three sub-stages queued:** 11b (companion.py lint), 11d (grammar manifest in bsl_validator.py), 11e (test_grammar_manifest.py).
- **signoff=true.**

### 2026-06-08 -- Stage 11b/11d/11e audit round 2: handoff keys

- **Nemotron** refined plan with round-1 amendments applied (full BISC error handling in lint, behavioral assertions in test).
- **DeepSeek** audited: signoff=true on amendments; signoff=false on plan with new handoff key count blocker.
- **Prescriptive resolution:** inspect `HANDOFF_SCHEMA` in handoff.py, list explicit key names for handoff (10), intent (3), meta (3 including generation).

### 2026-06-08 -- Stage 11b/11d/11e audit round 1

- **Nemotron** refined validation surface plan.
- **DeepSeek** audited: signoff=false. Two issues: missing BISC-compliant `OSError`/`Exception` handling in lint subcommand, test fragility from internal `REQUIRED_KEYS` dict access.

### 2026-06-08 -- Stage 11a2 prerequisite micro-patch: signoff

- **Coder** delivered prerequisite micro-patch: `bsl_validator.py` `validate_version(expected_version: str, version: str, line_no: int)` signature; removed `from .handoff import BABEL_VERSION` module-level import.
- **DeepSeek** signed off Nemotron's corrected 11a2 plan: `BabelParseError` sourced from `bsl_parser`, dependency inversion via parameterization, pre-write gate with `bool`/`list`/`str` encoding.
- **11a2 implementation unblocked.**

### 2026-06-08 -- Stage 11a2 round-4 audit

- **DeepSeek** audited: signoff=false. Two blockers: unverified prerequisite dependency inversion in `bsl_validator.py`, `BabelParseError` import source incorrect.
- **Resolution path:** single-file prerequisite micro-patch to `bsl_validator.py`, then 11a2 `handoff.py` patch.

### 2026-06-08 -- Stage 11a/11a2 split-plan round-3 audit: signoff

- **DeepSeek** signed off Nemotron's refined plan: split 11a into 11a (bsl_validator.py) + 11a2 (handoff.py); direct-call composition in `validate_block_string`.
- **Recommendation:** `validate_block_string` should use `block_type` returned by `validate_header` for `validate_body_kv` to prevent header-body mismatch.

### 2026-06-08 -- Stage 11a round-2 audit

- **DeepSeek** audited: signoff=false. One blocker (two-file delivery contradicts anti-timeout cadence) and one design ambiguity (`validate_block_string` constructs redundant block string).
- **Resolution path:** split 11a into 11a + 11a2; clarify `validate_block_string` to direct-call `validate_header` + `validate_body_kv`.

### 2026-06-08 -- Stage 11 audit: signoff=false

- **DeepSeek** audited Nemotron's refined stage 11 plan: three blockers (post-write gate persistence, missing bool encoding, whole-file scope) require amendment before 11a-11d implementation.
- **Resolution path:** amendment round with single-file per sub-stage.

### 2026-06-08 -- Two parser fix rounds (4-fail and 3-fail)

- **Coder** delivered minimal patches to `bsl_parser.py` resolving 4 + 3 test failures.
- **4-fail round:** `missing_intent` line=2 (first body block); strict `FILE_HEADER_REGEX` `r'^#\[babel\]:v?\d+\.\d+\.\d+'`; `duplicate_id` before `missing_intent`; CLI exit 6 verified.
- **3-fail round:** permissive `FILE_HEADER_REGEX` `r'^#\[babel\]:'` for test fixture compatibility; version consistency check on body+handoffs; `missing_intent` line=1.
- **All reference/babel tests pass.**

### Coder delivery log

- **Stage 9a:** `HANDOFF_SCHEMA` TypedDict with 9 keys in `reference/babel/handoff.py`.
- **Stage 9b:** `test_handoff_append.py` conformance assertions.
- **Stage 10b:** `bsl_validator.py` with `validate_header`, `validate_body_kv`, `validate_version`, `validate_file` and extra-keys policy `REJECT`.
- **Stage 11a:** `validate_block_string` direct-call composition with header-derived `block_type`.
- **Stage 11a2:** `handoff.py` pre-write gate with `_encode_handoff_value` and `_decode_handoff_value` for `bool`, `list`, `str` body KV encoding.
- **Stage 11b:** `companion.py` `lint <path>` subcommand with full BISC error handling.
- **Stage 11d:** Normative grammar manifest comment block in `bsl_validator.py`.
- **Stage 11e:** `test_grammar_manifest.py` behavioral conformance test.
- **Stage 11f:** Doc sweep in README and CHANGELOG.
- **Prerequisite micro-patch:** `validate_version` parameterization in `bsl_validator.py`.
- **Parser fix rounds:** 4-fail and 3-fail patches to `bsl_parser.py`.

### Carry-over

- **Stages 5a/5b from v0.10.2 cycle:** `append_handoff` implementation and test patch.
- **Stage 7b BISC section 5 amendment:** subsumed by stage 12a Section 5.3.
- **Stage 12b implementation:** gated on 12a commit (spec-first ordering hard constraint).
- **Stage 13 implementation:** next single-file code round.
