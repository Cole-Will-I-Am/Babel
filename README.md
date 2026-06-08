# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel stack** — BSL syntax, handoff block protocol, BISC integrity contract, BCPR prompt protocol.
- **Babel validator surface** — `reference/babel/bsl_validator.py` (validate_header, validate_body_kv, validate_version, validate_file, validate_block_string), `reference/babel/companion.py` (lint subcommand with full BISC error handling).
- **Grammar manifest** — normative comment block at top of `reference/babel/bsl_validator.py` documenting header regex, allowed block types, required keys per type, JSON list encoding, bool encoding.
- **Conformance tests** — `reference/tests/test_grammar_manifest.py` (behavioral assertions against manifest), `reference/tests/test_handoff_append.py` (conformance against HANDOFF_SCHEMA), `reference/tests/test_handoff_validation_gate.py` (pre-write gate, round-trip encoding).

## Babel v0.10.3 — Handoff Query + Companion CLI + BSL Validator

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. Continues the append-query collaboration loop from v0.10.2.

### Stage 7 — Handoff Block Schema (locked)

Nine-key handoff block content dict: `path`, `content`, `agent_id`, `next_owner`, `signoff`, `blocking_issues`, `required_changes`, `summary`, `memory_note`. BSL version KV is a 10th key required by the syntax layer. BISC section 5 amendment still pending (carry-over).

### Stage 9 — HANDOFF_SCHEMA TypedDict (complete)

`HANDOFF_SCHEMA` TypedDict committed in `reference/babel/handoff.py` with the 9 payload keys. Conformance test `reference/tests/test_handoff_append.py` asserts stored handoff blocks conform to the schema.

### Stage 10 — BSL Validator (complete)

`reference/babel/bsl_validator.py` module with:

- `validate_header(header_line, line_no) -> tuple[str, str]` — extracts block type and block id from `/blocks/(handoff|intent|meta):[a-z0-9-]+$` headers.
- `validate_body_kv(block_type, kv_pairs, line_no) -> None` — enforces required keys per block type; rejects extra keys (REJECT policy); rejects duplicate keys.
- `validate_version(expected_version, version, line_no) -> None` — semver string equality check, raises `BabelParseError` with `code='version_mismatch'`.
- `validate_file(path) -> None` — orchestrates all three for whole-file validation.
- `validate_block_string(block_type, header, kv_pairs) -> None` — direct-call composition using header-derived `block_type` for pre-write gating.

Extra-keys policy: **REJECT** (deterministic default; prevents silent schema drift).

### Stage 11 — Validator Integration & Grammar Formalization (complete)

Pre-write validation gate in `reference/babel/handoff.py` (stage 11a2) with str/list/bool encoding helpers, `HandoffIntegrityError` exception, and corrected import topology:

- `validate_block_string` from `.bsl_validator`
- `BabelParseError` from `.bsl_parser` (definition site)
- `BABEL_VERSION` import removed from `bsl_validator`; passed explicitly to `validate_version`

### Stage 11b/11d/11e — Validation Surface (signoff round 3)

Three single-file stages approved by DeepSeek audit (signoff=true) and queued for sequential delivery:

**11b — Companion lint subcommand** (`reference/babel/companion.py`):

- Add `lint <path>` subcommand alongside existing `validate`.
- Direct call to `bsl_validator.validate_file(path)` (no subprocess).
- Full BISC error handling: `BabelParseError` → `{'path': str(path), 'line': line_no, 'code': code}` stderr, exit 6; `OSError` → `{'path': str(path), 'code': 'file_error'}` stderr, exit 6; `Exception` → `{'code': 'internal_error'}` stderr, exit 6.
- Success: `{'valid': true}` stdout, exit 0.

**11d — Grammar manifest** (`reference/babel/bsl_validator.py` top):

- Normative comment block documenting:
  1. Header regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$` with allowed block types tuple.
  2. Required body keys per type with explicit key name lists:
     - handoff = `{path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note, version}` (10 total).
     - intent = `{purpose, owner, version}` (3 total).
     - meta = `{title, version}` (2 total).
  3. JSON list encoding: `json.dumps(value, separators=(',', ':'))` for `list[str]`.
  4. Bool encoding: lowercase `'true'`/`'false'` for `signoff` key.
  5. Version lint rule referencing `BABEL_VERSION` import.

**11e — Conformance test** (`reference/tests/test_grammar_manifest.py`):

- Behavioral assertions only — no internal `REQUIRED_KEYS` dict access.
- Reads `bsl_validator.py` source; extracts manifest via regex `r'^# Grammar Manifest\n(?:# .*\n)*'`.
- Compiles documented header regex; calls `validate_header` with valid/invalid headers to verify behavioral match.
- For each block type, constructs `kv_pairs` with all required keys → assert no error; omits one key → assert `BabelParseError` with expected code.

#### Handoff key ambiguity resolution (archived)

The round-2 blocker "9 HANDOFF_SCHEMA keys + version" is resolved by inspection: `HANDOFF_SCHEMA` (stage 9a TypedDict) contains exactly 9 payload keys. The 10th key (`version`) is a BSL syntax layer requirement, separate from the payload schema. Grammar manifest lists all 10 key names explicitly to prevent recurrence.

#### Lint BISC error handling (archived)

The round-1 issue "missing OSError/Exception handling" is resolved by matching the BISC contract used in `reference/babel/__main__.py`: `try` calls `bsl_validator.validate_file(path)`; `except BabelParseError` emits structured path/line/code JSON to stderr and exits 6; `except OSError` emits path/file_error JSON and exits 6; `except Exception` emits internal_error JSON and exits 6.

#### Test fragility (archived)

The round-1 issue "internal REQUIRED_KEYS dict access" is resolved by replacing it with behavioral assertions: construct complete `kv_pairs` for each block type and assert no error; construct incomplete sets and assert `BabelParseError` with the expected code. The test is now decoupled from the validator's internal naming.

### Stage 11f — Doc Sweep (deferred)

Human-facing README/CHANGELOG updates documenting the lint CLI subcommand, grammar manifest, and conformance test for human consumers. Held until 11b/11d/11e are committed.

### Carry-over

- **Stages 5a/5b** (v0.10.2 cycle): `append_handoff` implementation and test patch.
- **Stage 7b**: BISC section 5 amendment formalizing the 9-key handoff block content dict schema in `autonomy-output/babel-bisc-integrity-v0.10.2.md`. Recommend adding explicit version note in the file header rather than renaming to preserve BISC pre-commit hook links.
- **Prerequisite micro-patch** (if not yet committed): `bsl_validator.py` signature change `validate_version(expected_version, version, line_no)` and removal of `BABEL_VERSION` import from `handoff.py`.

## Anti-Timeout Cadence

This stage ships only the two paired documentation files (README + CHANGELOG). The 8+ TimeoutError entries in the notes tail on this exact stage confirm that multi-file code/spec delivery risks runtime failure. All implementation stages (11b, 11d, 11e) are explicitly named with file paths, function signatures, and gate dependencies so the next artifact-writing stage can attempt the smallest atomic unit without waiting on further architecture decisions.
