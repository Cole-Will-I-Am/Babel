# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel language stack** — `babel-language-syntax-v0.10.2.md`, `babel-language-integration-v0.10.2.md`, `babel-bisc-integrity-v0.10.2.md`, `babel-bcpr-v0.10.2.md` in `autonomy-output/`. Reference parser skeleton in `reference/babel/`.

## Babel v0.10.2 Status

Contract-first bootstrap and parser logic stages are tracked in `CHANGELOG.md`. The frozen parser public API lives in `reference/babel/bsl_parser.py` and is bound to the BISC integrity spec section 4 (parser error taxonomy, eight codes), section 5 (body-only canonical_sha256), section 6 (CLI exit code mapping), and section 7 (companion_path re-export from `reference/babel/companion.py`).

The BISC CLI wrapper contract (stage 4c.1 amendment) separates library-level errors (raised as native `BabelParseError` by `parse_file`, six codes) from process-level errors (emitted by the CLI wrapper as BISC stderr JSON, two codes: `file_error` for `OSError`, `internal_error` for unexpected `Exception`). All eight codes map to exit code 6; success exits 0 with silent stdout.

## Round Cadence

Stages are shipped as single-file deliverables to avoid multi-file finalize timeouts:

- 1a: `reference/babel/bsl_parser.py` skeleton (frozen public API).
- 1c: Contract Bootstrap Appendix appended to `babel-language-integration-v0.10.2.md`.
- 2b: `reference/babel/companion.py` skeleton (zero parser imports).
- 3b: BISC integrity spec amendment (sections 4-7, library/process contract).
- 4b.1: BISC `multiple_intents` code added to section 4.1.
- 4c.1: BISC process-level codes `file_error` and `internal_error` added in section 4.3.

Subsequent single-file finalize rounds implement `write_file`, `to_virtual_json`, the CLI wrapper, writer tests, and the round-summary doc updates.
