# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.2 — Babel Language Surface (Unreleased)

### 2026-06-08 — Stage 4c.2e + 4c.2f — README and CHANGELOG Finalize

Updated `README.md` and `CHANGELOG.md` with human-readable summaries of the v0.10.2 contract-first bootstrap, parser logic stages 4a–4c, and the planned handoff append stage 5a. Held the single-file-per-stage anti-timeout cadence that has held since stage 1a.

### 2026-06-08 — Stage 4c.2c — BISC CLI Wrapper

Shipped `reference/babel/__main__.py` CLI wrapper. Catches `BabelParseError` (re-emit as-is), `OSError` (translate to `file_error`), and `Exception` (translate to `internal_error`). Emits BISC-compliant structured stderr JSON. Exits 6 on error, 0 silent on success.

### 2026-06-08 — Stage 4c.2b — Virtual JSON Serializer

Implemented `to_virtual_json` in `reference/babel/bsl_parser.py` with deterministic `/blocks/<type>:<id>` schema, handoff exclusion, and normalized body sort by type rank (intent=0, spec=1, test=2, impl=3).

### 2026-06-08 — Stage 4c.2a — Atomic Writer

Implemented `write_file` in `reference/babel/bsl_parser.py` with atomic tempfile+rename and explicit `tmp_path` cleanup. Target file is never partially written; failed writes leave no tempfile residue.

### 2026-06-08 — Stage 4c.1 — BISC Process-Level Error Codes

Amended `autonomy-output/babel-bisc-integrity-v0.10.2.md` adding section 4.3 with `file_error` (OSError from CLI) and `internal_error` (unexpected Exception) as the seventh and eighth codes. Library/process contract preserved: library raises native Python exceptions, CLI wrapper translates to BISC stderr JSON.

### 2026-06-08 — Stage 4b.1 — BISC multiple_intents Error Code

Amended `autonomy-output/babel-bisc-integrity-v0.10.2.md` extending the parser error taxonomy with `multiple_intents` as the sixth code. Detects >1 intent block in body; line semantics reference the second intent header line. `duplicate_id` is checked before `multiple_intents` so same-id intent pairs report as `duplicate_id` first.

### 2026-06-08 — Stage 4a — Reference Parser Skeleton and Contract Bootstrap

Shipped `reference/babel/bsl_parser.py` as a typed skeleton with frozen public API (`parse_file`, `write_file`, `to_virtual_json`, `companion_path`). `companion_path` re-exports `resolve_companion` from `reference/babel/companion.py` per BISC section 7.

### 2026-06-08 — Stage 3b — BISC Parser Error Taxonomy Amendment

Amended `autonomy-output/babel-bisc-integrity-v0.10.2.md` with sections 4–7: parser error taxonomy (5 codes), structured stderr JSON format, CLI exit code mapping, and companion_path re-export contract. Resolves both deepseek audit blockers: parse_file raises (library) and CLI wrapper exits 6 (process).

### 2026-06-08 — Stage 2b — Companion Resolver Skeleton

Shipped `reference/babel/companion.py` as a zero-dependency utility with `resolve_companion(babel_path: Path) -> Optional[Path]` stub raising NotImplementedError. Basename-matching contract documented in docstring. No parser imports; preserves the machine/human content boundary.

### 2026-06-08 — Stage 1a–1c — Contract Bootstrap

Shipped reference parser skeleton, handoff.py skeleton, and Contract Bootstrap Appendix mapping `parse_file`/`write_file`/`to_virtual_json`/`companion_path`/`append_handoff`/`resolve_companion` to BWSS lifecycle states and handoff protocol steps. Resolved deepseek's blocking issue on lifecycle mapping.

### 2026-06-07 — Stage 0 — Spec Cycle Kickoff

Shipped four normative specs: `babel-syntax-v0.10.2.md`, `babel-integration-v0.10.2.md`, `babel-bisc-integrity-v0.10.2.md`, `babel-bcpr-v0.10.2.md`. All Nemotron + DeepSeek decisions preserved: JSON-only intent, body sorted, handoff appended, version SemVer shared per file, unique (type, id), virtual JSON `/blocks/<type>:<id>`, body-only canonical_sha256, exit 6 on intent violations.

## Prior Cycles

- **v0.10.1** — initial multi-agent runtime scaffolding.
- **v0.10.0** — Ollama runtime + GitHub CLI auth.
