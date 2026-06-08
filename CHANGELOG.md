# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 — Handoff Query + Companion CLI (Unreleased, planned)

Read-side handoff query protocol and human-facing companion CLI. Completes the append-query collaboration loop started in v0.10.2.

### 2026-06-08 — Stage 6e + 6f — README and CHANGELOG Finalize

Updated `README.md` and `CHANGELOG.md` with human-readable summaries of the v0.10.3 cycle. The README now documents:

- The seven sub-stages of stage 6 (6.0 patch, 6a query, 6b companion, 6c query tests, 6d companion tests, 6e README, 6f CHANGELOG).
- The frozen handoff block schema (six keys: id, agent_id, content, blocking_issues, required_changes, next_owner) as the wire format for multi-agent chains.
- The companion CLI surface (`init` / `render` / `validate`) with the zero-dependency boundary preserved by `validate` shelling out to `python -m babel` via `subprocess.run`.
- The handoff append protocol summary (planned, stage 5a) with the `## agent: <id>\n` prefix prepended before SHA256.

Sub-stages 6.0 (handoff.py patch: BABEL_VERSION bump to 0.10.3, `next_owner` stored in body dict), 6a (query methods: `get_latest_handoff`, `list_handoffs` returning frozen schema dicts), 6b (companion CLI implementation), 6c (query tests), and 6d (companion tests) are queued as separate single-file finalize rounds.

Both Nemotron and DeepSeek signed off on the seven-stage decomposition. The anti-timeout cadence is held by shipping only the documentation pair in this round.

## v0.10.2 — Babel Language Surface (Unreleased)

Contract-first bootstrap. Parser core (stages 1a-5b) defines the frozen public API, companion skeleton, BISC error taxonomy, scanner/normalize/writer/CLI logic, and handoff append protocol.

### 2026-06-08 — Stage 4c.2e + 4c.2f — README and CHANGELOG Finalize

Updated `README.md` and `CHANGELOG.md` with human-readable summaries of stages 1a-4c.2c and the planned stage 5a. The `agent_id` clarification from DeepSeek's audit was resolved: `append_handoff` will prepend a structured header line `## agent: <agent_id>\n` to the proposed content before computing the SHA256 idempotency hash.

### 2026-06-08 — Stage 4c.1 — BISC Process-Level Error Codes

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` adding section 4.3 with `file_error` (OSError from CLI) and `internal_error` (unexpected Exception). Eight codes total in the frozen parser error taxonomy (six library + two process). The library/process contract is preserved: the library raises native Python exceptions, the CLI wrapper catches them and translates to BISC stderr JSON.

### 2026-06-07 — Stage 4b.1 — BISC `multiple_intents` Amendment

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` extending the parser error taxonomy (section 4.1) with `multiple_intents` as the sixth code. Detection rule: more than one `#[intent]:<id>@<version>` block in the body raises `BabelParseError(code='multiple_intents', line=second_intent_header_line)`. Ordering note: `duplicate_id` is checked before `multiple_intents`, so two intent blocks with the same id are still reported as `duplicate_id` first.

### 2026-06-07 — Stage 3b — BISC Integrity Spec Sections 4-7

Shipped the BISC integrity spec amendment (`autonomy-output/babel-bisc-integrity-v0.10.2.md`) with sections 4-7: parser error taxonomy (six library codes), structured stderr JSON shape (`{"error","code","line","message"}`), CLI exit code mapping (exit 6 on BabelParseError), and the `companion_path` re-export contract from `companion.py` to `bsl_parser.companion_path`. Resolved both DeepSeek audit blockers: `parse_file` raises (library), CLI wrapper exits 6 (process); `companion_path` is a re-export, not a duplicate implementation.

### 2026-06-07 — Stage 2b — Companion Module Skeleton

Shipped `reference/babel/companion.py` skeleton with zero-import utility design (`pathlib` + `typing` only). `resolve_companion` is a typed stub raising `NotImplementedError`, with the basename-matching contract documented in the docstring only.

### 2026-06-07 — Stage 1c — Contract Bootstrap Appendix

Completed the mapping of `parse_file`, `write_file`, `to_virtual_json`, `companion_path`, `append_handoff`, `resolve_companion` to BWSS lifecycle states and handoff protocol steps in the BISC contract bootstrap appendix.

### 2026-06-07 — Stage 1a — Parser Skeleton

Shipped `reference/babel/bsl_parser.py` skeleton with the frozen public API and `NotImplementedError` stubs. The single-file-per-stage cadence was established here to avoid pair_b_finalize TimeoutErrors.

## v0.10.1 — Prior Cycles

Earlier cycles covered BCPR conflict log format, BISC pre-commit hook design, and the original Babel/BCPR/BISC stack concept. See git history for details.
