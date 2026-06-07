# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.2 - Babel Language Surface (Unreleased)

### Cycle: Stage 1c - Contract Bootstrap Appendix

Shipped the Contract Bootstrap Appendix appended to `autonomy-output/babel-language-integration-v0.10.2.md`. The appendix maps the six shipped and pending API functions to BWSS lifecycle states and handoff protocol steps.

#### Added

- **A.1 API Surface table** listing `parse_file`, `write_file`, `to_virtual_json`, `companion_path` (stage 1a shipped) and `append_handoff`, `resolve_companion` (stages 2a/2b pending), with `NotImplementedError` status noted for all six.
- **A.2 Lifecycle state mapping** as a state-by-function table covering `draft`, `review`, `ready`, `sealed`, `frozen`. Notable rules: `write_file` valid only in `draft`/`review`; `append_handoff` valid only in `ready`/`sealed`; read-only functions valid in every state.
- **A.3 Handoff protocol step mapping** naming the API function that participates in each of the five ordered steps: read current state, extract handoff history, locate companion prose, append new handoff, persist.
- **A.4 Stub status and frozen surface** documenting the shipped and frozen dataclasses, error taxonomy, and module constants from stage 1a, and confirming that logic cycles are scheduled for v0.10.3 cycles 2 and 3.
- **A.5 Contract test coverage** pointer to stage 1b (parser contract test) and stage 3a (handoff contract test).

#### Notes

- This stage is spec-only; no code changes.
- Single-file-per-stage cadence preserved; the appendix is part of the existing integration spec file, not a new file.
- Stages 2a, 2b, 3a, and 3b remain queued as separate single-file finalize rounds.

### Cycle: Stage 1b - Parser Contract Test (Previously Shipped)

Shipped `reference/tests/test_bsl_parser_contract.py` verifying the frozen public surface of `reference.babel.bsl_parser`: module constants, AST dataclasses, error taxonomy, public function signatures, and `NotImplementedError` raises on all four shipped functions. Signed off by deepseek and committed.

### Cycle: Stage 1a - Parser API Skeleton (Previously Shipped)

Shipped the contract-first bootstrap for the Babel v0.10.2 reference parser as a single-file deliverable. `reference/babel/bsl_parser.py` exposes the frozen public API (`parse_file`, `write_file`, `to_virtual_json`, `companion_path`), the AST dataclasses (`BabelBlock`, `BabelFile`), the stable error taxonomy (`BabelParseError` with five codes mapping to BISC exit code 6), and the module constants (`BABEL_VERSION`, `BLOCK_TYPES`, `BODY_TYPES`, `HANDOFF_TYPE`, `TYPE_ENUM_RANK`). All function bodies raise `NotImplementedError`. Signed off by deepseek and committed.

### Earlier (Previously Shipped)

- **Syntax spec** `autonomy-output/babel-language-syntax-v0.10.2.md` - EBNF grammar, body/handoff split, header semantics, deterministic serialization.
- **Integration spec** `autonomy-output/babel-language-integration-v0.10.2.md` - subsystem mapping, lifecycle, companion `.md` convention, handoff protocol (now with Contract Bootstrap Appendix appended in stage 1c).
- **BISC amendment** `autonomy-output/babel-bisc-integrity-v0.10.2.md` - `.babel` recognition, intent validation, duplicate rejection, body-only `canonical_sha256`, exit code 6.
- **BCPR amendment** `autonomy-output/babel-bcpr-v0.10.2.md` - virtual JSON, `/blocks/<type>:<id>` patch paths, handoff exclusion.

## v0.10.2 Bootstrap Plan (Forward Look)

- Stage 2a: `reference/babel/handoff.py` skeleton with `append_handoff` raising `NotImplementedError`.
- Stage 2b: `reference/babel/companion.py` skeleton with `resolve_companion` raising `NotImplementedError`.
- Stage 3a: `reference/tests/test_handoff_contract.py` mirroring the stage 1b contract test pattern.
- Stage 3b: BISC integrity spec amendment covering the parser error taxonomy and structured stderr JSON format.
- v0.10.3 cycle 2: logic cycle for the four shipped parser functions.
- v0.10.3 cycle 3: logic cycle for `append_handoff` and `resolve_companion`.
