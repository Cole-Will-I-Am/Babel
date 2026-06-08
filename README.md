# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax` (self-config) and `Cole-Will-I-Am/new-lab` (Babel/BCPR/BISC stack).
- **Babel reference parser** — `reference/babel/bsl_parser.py` (frozen public API, parser core).
- **Handoff protocol** — `reference/babel/handoff.py` (append + query, multi-agent continuity).
- **Companion CLI** — `reference/babel/companion.py` (stdlib-only human interface).
- **BISC pre-commit hooks** — enforce `.babel` file integrity and the BISC error taxonomy (eight codes).
- **BCPR conflict log** — human-readable chain-of-handoff reader, consumes the BISC stderr JSON shape.

## Babel Project Layout

A Babel project consists of two companion files in a single directory:

- `*.babel` — the deterministic, machine-readable source of truth (intent, spec, test, impl, handoff blocks).
- `*.md` — the human-readable companion rendered from the `.babel` body (handoffs excluded from body sort, remain chronological).

The `*.md` filename must share the basename of the `*.babel` file; this is the **companion_path contract** enforced by `companion.resolve_companion` and re-exported as `bsl_parser.companion_path`.

## Block Types

- `#[intent]:<id>@<version>` — exactly one per body; carries `agent_id`.
- `#[spec]:<id>@<version>` — normative spec block.
- `#[test]:<id>@<version>` — test block.
- `#[impl]:<id>@<version>` — implementation block.
- `#[handoff]:handoff-{n}` — chronological handoff block; n starts at 1 and increments.

## Babel Cycles (Releases)

### v0.10.2 — Babel Language Surface (Unreleased)

Parser contract-first bootstrap. Sub-stages 1a-5b define the frozen public API, companion skeleton, BISC error taxonomy, scanner/normalize/writer/CLI logic, and handoff append protocol.

### v0.10.3 — Handoff Query + Companion CLI (Unreleased, planned)

Read-side handoff query protocol and human-facing companion CLI. Sub-stages:

- **6.0 (patch)** — Bump `BABEL_VERSION` to `0.10.3` in `reference/babel/handoff.py`. Patch `append_handoff` to store `next_owner` in the handoff block body dict (keys: `path`, `content`, `agent_id`, `next_owner`, `blocking_issues`, `required_changes`). No signature change; `next_owner` is already a parameter per v0.10.2 stage 5a fixes.
- **6a (query)** — Implement `get_latest_handoff(path) -> dict|None` and `list_handoffs(path) -> tuple[dict,...]` in `handoff.py` using `parse_file`. Return deserialized dicts with the **frozen handoff schema** (id, agent_id, content, blocking_issues, required_changes, next_owner). Sort by sequential handoff ID numeric suffix. Empty file returns `None` / `()`. Parser errors propagate as `BabelParseError`.
- **6b (companion)** — Implement `reference/babel/companion.py` as a stdlib-only CLI with three subcommands: `init`, `render`, `validate`. Uses only `argparse`, `subprocess`, `json`, `pathlib`. Imports `handoff.py` query methods for `init`/`render`; `validate` shells out to `python -m babel <path>` via `subprocess.run` to preserve the zero-dependency boundary.
- **6c (query tests)** — Author `reference/tests/test_handoff_query.py` covering deterministic ordering, empty file handling, parser error propagation, and schema compliance (all six frozen keys present, including `next_owner`).
- **6d (companion tests)** — Author `reference/tests/test_companion_cli.py` covering `init` scaffolding, `render` formatted output, and `validate` exit codes (0 on valid, 6 on invalid) with BISC stderr JSON shape.
- **6e (README)** — This document, human-readable summary of the v0.10.3 cycle. ✅ Shipped 2026-06-08.
- **6f (CHANGELOG)** — ISO-dated entries for stages 4a-6d in `CHANGELOG.md`. ✅ Shipped 2026-06-08.

## Handoff Block Schema (frozen, v0.10.3)

Every handoff block in a `.babel` file deserializes to a dict with exactly six keys:

| Key | Type | Description |
|-----|------|-------------|
| `id` | `str` | `handoff-{n}` where n is the sequential numeric suffix (1, 2, 3, ...). |
| `agent_id` | `str` | Identifier of the agent writing the handoff. Also prepended to content as `## agent: <agent_id>\n` by `append_handoff`. |
| `content` | `str` | Raw text of the handoff body, including the `## agent: <id>\n` prefix. |
| `blocking_issues` | `list[str]` | Issues the writer could not resolve. Empty list when signoff=true. |
| `required_changes` | `list[str]` | Follow-up work the next owner must perform. |
| `next_owner` | `str \| None` | The agent that should pick up this handoff. Stored in body dict (stage 6.0) and returned by query methods (stage 6a). |

This schema is the wire format for multi-agent handoff chains. Any reader (companion, BCPR conflict log, future tooling) must consume all six keys.

## Companion CLI

```
python -m babel.companion init   <path.babel>     # scaffold a new .babel with intent block
python -m babel.companion render <path.babel>     # pretty-print handoffs in sequential order
python -m babel.companion validate <path.babel>   # exit 0 valid, 6 invalid, BISC stderr JSON
```

- `init` — writes a minimal `.babel` file with an `#[intent]` block parseable by `bsl_parser.parse_file`.
- `render` — calls `list_handoffs(path)` and prints each handoff as `--- handoff-{n} (agent: <id>) ---` followed by content.
- `validate` — invokes `subprocess.run(['python', '-m', 'babel', path])`. Exits 0 on success, 6 on `BabelParseError` (reads stderr JSON), non-zero on subprocess failure.

The CLI depends only on the Python stdlib and the `handoff` module. It does **not** import `bsl_parser` directly; the `validate` boundary is the `python -m babel` subprocess, which is the single integration surface for any `.babel` file (including those checked by BISC pre-commit hooks).

## BISC CLI Exit Code Contract

| Exit | Meaning |
|------|---------|
| 0 | Silent success |
| 6 | BabelParseError — see BISC stderr JSON shape |

The eight frozen error codes (see BISC integrity spec section 4):

- **Library** (raised by `parse_file`): `duplicate_id`, `version_mismatch`, `malformed_header`, `invalid_intent_json`, `missing_intent`, `multiple_intents`.
- **Process** (emitted by CLI wrapper): `file_error` (OSError), `internal_error` (unexpected Exception).

The CLI wrapper catches native Python exceptions and translates to BISC stderr JSON:

```json
{"error": "<ExceptionClass>", "code": "<code>", "line": <int|null>, "message": "<str>"}
```

Compact canonical JSON v0.2.0, single line, no trailing newline.

## Handoff Append Protocol

`append_handoff(babel_path, content, agent_id) -> tuple[bool, str]` (planned, stage 5a):

1. Read current `.babel` file via `parse_file`.
2. Compute `max_n` from existing `handoff-{n}` IDs; next id is `handoff-{max_n + 1}` (or `handoff-1` if none).
3. Prepend `## agent: <agent_id>\n` to the proposed content (human-visible attribution).
4. Compute SHA256 of the prefixed content for the idempotency guard.
5. If the most recent handoff has the same SHA256, return `(False, "handoff-{n}")` (idempotent skip).
6. Otherwise, write the new handoff block atomically via `write_file` (tempfile + rename).
7. Return `(True, "handoff-{n}")` on success.

Errors propagate: `BabelParseError` on invalid input, `OSError` on filesystem failure (translated to `file_error` by the CLI wrapper).
