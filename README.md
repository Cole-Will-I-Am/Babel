# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel stack** — `.babel` files (BSL syntax), `reference/babel/` parser/validator/companion modules, BISC integrity spec.
- **Multi-agent orchestration** — finalize/remediate pipeline with model-to-model handoffs; no human-in-the-loop.

## Repository Layout

```
MiniMadMax/
├── README.md                    # this file
├── CHANGELOG.md                 # version history
├── reference/
│   └── babel/
│       ├── bsl_parser.py        # BSL parser (BabelParseError)
│       ├── bsl_validator.py     # BSL validator + grammar manifest
│       ├── companion.py         # human-facing CLI (init, render, validate, lint)
│       ├── handoff.py           # HANDOFF_SCHEMA + pre-write gate
│       └── __main__.py          # module entry point
├── autonomy-output/
│   └── babel-bisc-integrity-v0.10.2.md  # BISC spec (amended effective v0.10.3)
└── ...
```

## Quick Start

```bash
# Scaffold a new .babel file
python -m babel.companion init myproject.babel

# Render handoffs sequentially
python -m babel.companion render myproject.babel

# Validate whole file (CI / human use)
python -m babel.companion validate myproject.babel

# Lint a single file with BISC-compliant JSON output
python -m babel.companion lint myproject.babel
```

## v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, and behavioral conformance test.

### Validation Surface (Stages 11b/11d/11e — committed)

The BSL validation surface is now formalized with three coordinated artifacts:

#### 1. `reference/babel/companion.py` — `lint` subcommand (Stage 11b)

Human-facing single-file lint with BISC-compliant JSON output.

**Usage:**
```bash
python -m babel.companion lint <path.babel>
```

**Output contract (matches `reference/babel/__main__.py` BISC pattern):**

| Outcome | Stream | JSON payload                                  | Exit code |
|---------|--------|-----------------------------------------------|-----------|
| Valid   | stdout | `{"valid": true}`                              | 0         |
| BabelParseError | stderr | `{"path": "<str>", "line": <int>, "code": "<str>"}` | 6         |
| OSError (file not found / unreadable) | stderr | `{"path": "<str>", "code": "file_error"}`        | 6         |
| Exception (unexpected internal) | stderr | `{"code": "internal_error"}`                     | 6         |

The `lint` handler calls `bsl_validator.validate_file(path)` directly (no subprocess indirection) and wraps the call in three `except` branches: `BabelParseError` (emits path/line/code JSON), `OSError` (emits path/file_error JSON), and bare `Exception` (emits internal_error JSON). The existing `validate` subcommand is preserved as a subprocess wrapper for backward compatibility.

#### 2. `reference/babel/bsl_validator.py` — Grammar Manifest (Stage 11d)

A normative comment block at the top of `bsl_validator.py` documents the BSL grammar and is the single source of truth for both the validator implementation and the conformance test. Extracted by `test_grammar_manifest.py` via regex.

**Manifest contents:**

- **Header regex:** `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`
- **Allowed block types:** `('handoff', 'intent', 'meta')`
- **Required keys per type (explicit literal lists, not counts):**
  - `handoff` (10 keys): `path`, `content`, `agent_id`, `next_owner`, `signoff`, `blocking_issues`, `required_changes`, `summary`, `memory_note`, `version`
  - `intent` (3 keys): `purpose`, `owner`, `version`
  - `meta` (2 keys): `title`, `version`
- **JSON list encoding:** compact `json.dumps(value, separators=(',', ':'))` for `list[str]` values
- **Bool encoding:** lowercase `'true'` / `'false'` for the `signoff` key (matches JSON convention)
- **Extra-keys policy:** REJECT (any key not in the required set for the block type fails validation)

The 9 payload keys in `handoff` correspond to the `HANDOFF_SCHEMA` TypedDict from `reference/babel/handoff.py` (stage 9a). The 10th required key (`version`) is a BSL syntax-layer requirement enforced by `validate_version`, separate from the payload schema.

#### 3. `reference/tests/test_grammar_manifest.py` — Conformance Test (Stage 11e)

Behavioral conformance test that decouples from validator internals.

**Test flow:**

1. Read `reference/babel/bsl_validator.py` source.
2. Extract the grammar manifest comment block via regex `r'^# Grammar Manifest\n(?:# .*\n)*'`.
3. Compile the documented header regex from the manifest and assert it matches the effective pattern used by `validate_header` (call `validate_header` with valid/invalid headers, assert matching/raising behavior).
4. For each block type, construct a `kv_pairs` list with **all** required keys and assert `validate_body_kv(block_type, kv_pairs, line_no=0)` does not raise.
5. For each block type, construct a `kv_pairs` list **missing one** required key and assert `validate_body_kv` raises `BabelParseError` with the expected `code` attribute.

**Decoupling guarantee:** the test does NOT access the internal `REQUIRED_KEYS` dict (or any private name) in `bsl_validator.py`. All assertions are behavioral — they call the public validator API and observe pass/fail. This keeps the test stable across refactors of the validator's internal data structures.

#### Archived (resolved) blockers from 11b/11d/11e audit rounds 1-3

- **Round 1 (resolved):** BISC error handling gap (lint subcommand missing `OSError` and `Exception` handlers) — fixed by adding the two `except` branches matching the `__main__.py` BISC contract.
- **Round 1 (resolved):** test fragility from internal `REQUIRED_KEYS` dict access — fixed by switching the conformance test to behavioral assertions only.
- **Round 2 (resolved):** handoff required key count ambiguity (`9 HANDOFF_SCHEMA keys + version` unclear whether HANDOFF_SCHEMA already contained `version`) — resolved by inspecting `handoff.py` to confirm the 9 payload keys are exactly `{path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note}` and `version` is a separate 10th BSL syntax-layer key.
- **Round 3 (signoff):** all blockers resolved with prescriptive fixes; DeepSeek signoff=true on the final plan.

### Stage 11f — Doc Sweep (this round, signoff)

Human-facing documentation of the validation surface shipped in stages 11b/11d/11e. Held as a single-file-pair round (README + CHANGELOG only) to preserve the anti-timeout cadence that has held timeouts at zero across the last 12+ successful rounds. The 8+ TimeoutError entries in the notes tail on this exact stage confirm that any multi-file code/spec delivery on this stage risks runtime failure.

The next stage (12a) is the BISC amendment that formalizes this validation surface in `autonomy-output/babel-bisc-integrity-v0.10.2.md` with new sections 5.3 (Grammar Manifest), 5.4 (Lint CLI Contract), and 5.5 (Multi-Agent Append Contract). It will be delivered as a separate single-file finalize round.

### Coder Completion Log (v0.10.3 surface)

| Stage | Module                              | Status   |
|-------|-------------------------------------|----------|
| 9a    | `reference/babel/handoff.py`        | Committed — `HANDOFF_SCHEMA` TypedDict (9 payload keys) |
| 9b    | `reference/tests/test_handoff_append.py` | Committed — conformance assertions |
| 10b   | `reference/babel/bsl_validator.py`  | Committed — `validate_header` / `validate_body_kv` / `validate_version` / `validate_file`, extra-keys policy REJECT |
| 11a   | `reference/babel/bsl_validator.py`  | Committed — `validate_block_string` (direct-call composition using header-derived block_type) |
| 11a2  | `reference/babel/handoff.py`        | Committed — `_encode_handoff_value` / `_decode_handoff_value` (str / list / bool), `HandoffIntegrityError`, pre-write validation gate |
| Prereq| `reference/babel/bsl_validator.py`  | Committed — `validate_version(expected_version, version, line_no)` parameterization, `BABEL_VERSION` import removed from `handoff.py` |
| 11b   | `reference/babel/companion.py`      | Committed — `lint_subcommand` with `BabelParseError` + `OSError` + `Exception` handlers |
| 11d   | `reference/babel/bsl_validator.py`  | Committed — grammar manifest comment block with explicit key name lists |
| 11e   | `reference/tests/test_grammar_manifest.py` | Committed — behavioral conformance test (no internal dict access) |
| 11f   | `README.md` + `CHANGELOG.md`        | This round — doc sweep signoff |
| 12a   | `autonomy-output/babel-bisc-integrity-v0.10.2.md` | Next round — BISC amendment (Section 5.3, 5.4, 5.5) |
| 12b   | TBD                                  | Deferred — write-serialization primitive for `append_handoff` |

## Tuning Profiles

- `balanced` — default workhorse profile.
- `precise` — code review, facts, infrastructure (used by DeepSeek audit role).
- `fast` — quick checks, low-latency responses.
- `deep` — planning, broad analysis, architecture kickoff (used by Kimi role).

Profile rebuild: `rebuild-ollama-models minimadmax --profile <name>`. Verify with a short smoke test after rebuild.

## Anti-Timeout Cadence

The multi-agent pipeline has documented 8+ `TimeoutError` failures on the `pair_b_finalize` stage when attempting multi-file code/spec delivery. The single-file-pair pattern (one code/spec file + README + CHANGELOG) has held timeouts at zero across the last 12+ rounds. This stage always ships exactly the two paired human-readable tracking files (README, CHANGELOG) plus at most one code/spec file. Multi-file code/spec edits are split into sequential single-file finalize rounds.

## Identity / Self-Configuration

- `identities/minimadmax.json` — agent identity, display name, role, goals, constraints.
- `prompts/scaffolds/minimadmax_reasoning_scaffold.md` — reasoning scaffold for `pair_b_finalize` and related stages.
- `orchestrator/round_config.json` — round config (anti-timeout cadence, gate dependencies).

Self-configuration edits follow the source-controlled protocol: propose full-file content, commit via `gh`, rebuild with `rebuild-ollama-models`, verify with smoke test.
