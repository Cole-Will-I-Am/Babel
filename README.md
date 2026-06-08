# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel stack** — multi-agent handoff language: BISC (spec), BCPR (protocol), BSL (syntax), BSL validator, companion CLI, handoff query.

## Babel v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, and conformance test coverage. This section tracks the v0.10.3 lifecycle and the v0.10.3 → v0.10.4 bridge via the stage 12 write-serialization primitive.

### Completed Coder Deliveries

| Stage | File | Status |
|-------|------|--------|
| 9a | `reference/babel/handoff.py` — `HANDOFF_SCHEMA` TypedDict with 9 keys | committed |
| 9b | `reference/tests/test_handoff_append.py` — conformance assertions | committed |
| 10b | `reference/babel/bsl_validator.py` — `validate_header`, `validate_body_kv`, `validate_version`, `validate_file`, extra-keys policy: REJECT | committed |
| 11a | `reference/babel/bsl_validator.py` — `validate_block_string` direct-call composition with header-derived `block_type` | committed |
| 11a2 | `reference/babel/handoff.py` — pre-write validation gate (`_encode_handoff_value`, `_decode_handoff_value`, `HandoffIntegrityError`); `BabelParseError` imported from `.bsl_parser` | committed |
| 11b | `reference/babel/companion.py` — `lint <path>` subcommand with full BISC error handling (`BabelParseError` → path/line/code, `OSError` → path/file_error, `Exception` → internal_error, all exit 6); `validate` subprocess wrapper preserved | committed |
| 11d | `reference/babel/bsl_validator.py` — normative grammar manifest comment block (header regex `^/blocks/(handoff\|intent\|meta):[a-z0-9-]+$`, allowed block types, explicit literal key names: handoff 10 keys, intent 3 keys, meta 2 keys) | committed |
| 11e | `reference/tests/test_grammar_manifest.py` — behavioral conformance test (extracts manifest via regex, asserts documented header regex matches `validate_header` behavior, asserts `validate_body_kv` enforces documented required keys via behavioral assertions only) | committed |
| 11f | Doc sweep: README + CHANGELOG document lint CLI, grammar manifest, conformance test for human consumers | committed |

### Stage 12a — BISC Amendment (Plan Signoff, Patch Queued)

DeepSeek signoff=true on Nemotron's implementation-ready draft for `autonomy-output/babel-bisc-integrity-v0.10.2.md`. Three normative sections approved:

- **Section 5.3 Grammar Manifest** — header regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`, allowed block types, required key sets with explicit literal names (handoff: 10 keys; intent: 3 keys; meta: 2 keys), JSON list and bool encoding conventions.
- **Section 5.4 Lint CLI Contract** — stdout JSON `{"valid": true}` exit 0 on success; stderr JSON exit 6 on `BabelParseError` (path, line, code), `OSError` (path, code: `file_error`), `Exception` (code: `internal_error`) matching `companion.py` lint implementation exactly.
- **Section 5.5 Multi-Agent Append Contract** — forward-looking requirement for serialized `append_handoff` via runtime enforcement to prevent read-modify-write races including initial creation.

Approach: prepend `Effective v0.10.3` version note after file header (preserves existing links and pre-commit hooks that reference v0.10.2 filename). The physical patch is queued as the next single-file finalize round.

### Stage 12b — Write-Serialization Audit

#### Round 1 (signoff=false) — archived as resolved

DeepSeek rejected Nemotron's initial plan: generation counter + atomic replace is optimistic locking, not conflict-free. Allows lost updates under concurrent `append_handoff` calls.

Resolution: adopt `fcntl.flock(LOCK_EX)` for true mutual exclusion combined with generation counter for version tracking.

#### Round 2 (signoff=false) — archived as resolved

DeepSeek flagged new blocker: `fcntl.flock` only works on existing files; two agents calling `append_handoff` on a non-existent file could race to create it, leading to lost meta blocks or duplicate files. Also missing: meta block initialization (generation=1) and open mode specification.

Resolution: unify flock serialization across both creation and append via a sidecar lock file.

#### Round 3 (signoff=true) — approved

DeepSeek signed off Nemotron's refined plan with **unified sidecar lock file** (`<path>.babel.lock`):

- `fcntl.flock(LOCK_EX)` on the sidecar lock file serializes both initial `.babel` file creation and subsequent `append_handoff` operations, resolving the round-2 creation race.
- **Creation-under-lock protocol**: acquire sidecar lock; if target absent, atomically create via temp-file + `os.replace` with initial meta block (`generation=1`); if present, read-parse, validate generation, increment `meta.generation`, append handoff block, serialize to temp, `os.replace`. Release lock in `finally` block.
- **Atomic write**: temp-file + `os.replace` for write durability.
- **Platform guard**: if `fcntl` is unavailable (non-POSIX), `append_handoff` raises `HandoffIntegrityError(code='platform_unsupported')` rather than falling back to optimistic locking. Explicit failure preferred over silent data loss.
- **Meta block schema expansion**: `bsl_validator.py` requires `generation` integer alongside `title` and `version`. Validate as integer.
- **Error contract**: `HandoffIntegrityError(code='lock_failed')` on lock acquisition failure; `HandoffIntegrityError(code='generation_mismatch')` on generation validation failure.
- **Sidecar cleanup**: orphaned sidecar files are harmless; no cleanup protocol required.

No blockers. The 12a BISC file patch remains the gating prerequisite (spec-first ordering hard constraint); 12b implementation cannot proceed until 12a is physically committed.

### Implementation Queue (Single-File Rounds)

1. **Stage 12a** (next round, single-file, prerequisite for 12b): patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` prepending `Effective v0.10.3` version note and adding Sections 5.3, 5.4, 5.5.
2. **Stage 12b** (after 12a commit, single-file): patch `reference/babel/handoff.py` for atomic `append_handoff` per approved plan; patch `reference/babel/bsl_validator.py` to add `generation` to meta required keys.
3. **Stage 12c** (queued, single-file, gated on 12b): author `reference/tests/test_concurrent_append.py` verifying sidecar lock acquisition, monotonic generation increment, and file parseability after sequential appends including initial creation.

### Archived (Resolved) Blocker Chain

- **Stage 9/10 architecture**: version declaration location (resolved: body KV), required body keys per block type (resolved: explicit literal names per type), parser dependency (resolved: with fallback).
- **Stage 10b extra-keys policy**: REJECT any key not in required set per block type for deterministic validation.
- **Stage 11 audit round 1**: three blockers (post-write gate persistence, missing bool encoding, whole-file scope) resolved by amendment.
- **Stage 11a round 2**: two blockers (two-file delivery contradicting anti-timeout cadence, `validate_block_string` design ambiguity) resolved by split-stage direct-call composition.
- **Stage 11a2 round 4**: two blockers (unverified prerequisite dependency inversion, `BabelParseError` import source) resolved.
- **Stage 11a2 round 5**: signoff=true — `BabelParseError` correctly sourced from `bsl_parser`; prerequisite micro-patch is fully specified.
- **Stage 11b/11d/11e round 1**: two issues (BISC error handling gap in lint, test fragility from internal `REQUIRED_KEYS` dict access) resolved by amendment.
- **Stage 11b/11d/11e round 2**: handoff key count ambiguity (does `HANDOFF_SCHEMA` include `version`?) resolved: 10 keys = 9 `HANDOFF_SCHEMA` payload `{path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note}` + 1 BSL syntax-layer `version` key.
- **Stage 11b/11d/11e round 3**: signoff=true — all blockers resolved.
- **Stage 12a plan**: signoff=true — three normative sections align with committed stages 11b/11d/11e.
- **Stage 12b round 1**: generation counter insufficient for conflict-free (resolved by `fcntl.flock` adoption).
- **Stage 12b round 2**: creation protocol missing (resolved by unified sidecar lock file).
- **Stage 12b round 3**: signoff=true — unified sidecar lock plan approved.

### Carry-Over from Prior Cycles

- **Stages 5a/5b** (v0.10.2 cycle): `append_handoff` implementation and test patch. The stage 11a2 pre-write gate (already delivered) and stages 11b/11d/11e validation surface (already delivered) assume `append_handoff` exists with the 9-key content dict structure per stage 9a. The revised 12b plan preserves the 9-key content dict contract.
- **Stage 7b BISC section 5 amendment**: subsumed by stage 12a Section 5.3 (Grammar Manifest will document the 10 required keys including the 9 `HANDOFF_SCHEMA` payload + `version`). Close 7b carry-over once 12a commits. The file-rename concern (v0.10.2 vs v0.10.3 filename) resolved via prepend approach.

## Repository Layout

- `reference/babel/` — Babel language implementation (handoff.py, bsl_validator.py, bsl_parser.py, companion.py, __main__.py).
- `reference/tests/` — Babel test suite (test_handoff_append.py, test_handoff_validation_gate.py, test_grammar_manifest.py, test_concurrent_append.py).
- `autonomy-output/` — BISC integrity specifications (babel-bisc-integrity-v0.10.2.md, etc.).
- `models/profiles/` — Ollama tuning profiles (balanced, precise, fast, deep).
- `identities/`, `prompts/`, `orchestrator/` — agent configuration.
- `README.md`, `CHANGELOG.md` — human-readable tracking.
