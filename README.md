# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel/BCPR/BISC stack** — deterministic language surface, conflict-free protocol, and integrity spec for human+AI collaboration.

## Babel v0.10.2 — Language Surface

Babel is a deterministic source format designed for conflict-free human+AI collaboration. The v0.10.2 cycle ships the contract-first bootstrap and reference parser implementation.

### File Layout

- `foo.babel` — machine-authored intent, spec, test, and impl blocks. Sorted body, deterministic.
- `foo.md` — companion file, human-authored prose. Same basename, paired via `resolve_companion`.

### Block Types

- `#[intent]:<id>@<version>` — exactly one per file; declares the contract.
- `#[spec]:<id>@<version>` — normative specification.
- `#[test]:<id>@<version>` — executable test surface.
- `#[impl]:<id>@<version>` — implementation reference.
- `#[handoff]:<id>@<version>` — append-only collaboration record.

### Cycle Stages (v0.10.2)

- **Stage 1a–1c** — contract bootstrap: skeleton modules and BWSS lifecycle mapping.
- **Stage 2a–2b** — companion resolver skeleton: `reference/babel/companion.py`.
- **Stage 3a–3b** — BISC integrity spec with parser error taxonomy and CLI exit contract.
- **Stage 4a–4c** — reference parser: scanner, normalizer, writer, and CLI wrapper.
- **Stage 5a–5b** — handoff append protocol with sequential IDs and content-hash idempotency.

### BISC CLI

`python -m reference.babel <file.babel>` validates the file against the BISC integrity spec.

- Exit 0: silent success.
- Exit 6: structured stderr JSON with one of the eight error codes.

### Error Codes (8 total)

**Library (parser):** `duplicate_id`, `version_mismatch`, `malformed_header`, `invalid_intent_json`, `missing_intent`, `multiple_intents`.

**Process (CLI):** `file_error` (OSError), `internal_error` (unexpected Exception).

The library/process contract is preserved: `parse_file` and `write_file` raise native Python exceptions (`BabelParseError`, `OSError`); the BISC CLI wrapper at `reference/babel/__main__.py` catches them and emits the BISC stderr JSON shape with exit code 6.

### Handoff Protocol

Handoff blocks are append-only collaboration records. Each handoff block has a sequential ID `handoff-{n}` (max existing + 1, starting at `handoff-1`). Content-hash idempotency guards against duplicate agent outputs on retry: the SHA256 is computed over the raw content string (prefixed with the agent header line `## agent: <agent_id>\n`).

## Repository Layout

```
reference/
  babel/
    bsl_parser.py    # parse_file, write_file, to_virtual_json, companion_path
    handoff.py       # append_handoff (stage 5a)
    companion.py     # resolve_companion
    __main__.py      # BISC CLI wrapper
  tests/
    test_bsl_parser_*.py
    test_handoff_*.py
autonomy-output/
  babel-*.md         # Syntax, Integration, BISC, BCPR specs
identities/
  minimadmax.json    # identity record
prompts/scaffolds/
  minimadmax_reasoning_scaffold.md
orchestrator/
  round_config.json
```

## Configuration

- **Identity:** `identities/minimadmax.json`
- **Reasoning scaffold:** `prompts/scaffolds/minimadmax_reasoning_scaffold.md`
- **Round config:** `orchestrator/round_config.json`

Rebuild with `rebuild-ollama-models <model>` and verify with a short smoke test after any config change. Tuning profiles live in `models/profiles/` (`balanced`, `precise`, `fast`, `deep`).
