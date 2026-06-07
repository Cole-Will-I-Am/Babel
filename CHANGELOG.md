# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.2 — Babel Language Surface (Unreleased)

### Cycle: Stage 4b.1 — BISC `multiple_intents` Amendment

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` extending the parser error taxonomy from five codes to six. The new `multiple_intents` code closes the exactly-one-intent enforcement gap identified in the prior normalizer audit: when a `.babel` file contains two or more `#[intent]:<id>@<version>` blocks in the body with **distinct** `id` values, the parser raises `BabelParseError(code='multiple_intents', line=second_intent_header_line)`. The structured stderr JSON shape in section 4.2 is unchanged; the new code reuses the same wire format. The detection ordering note makes `duplicate_id` the dominant error when two intent blocks share an `id`, and `multiple_intents` the secondary error when ids differ. Stage 4b.2 will implement the detection in `reference/babel/bsl_parser.py` and add test cases to `reference/tests/test_bsl_parser_normalizer.py`; stages 4a (scanner), 4c (writer + CLI wrapper), and 5a (append_handoff) remain queued as separate single-file finalize rounds.

### Cycle: Stage 3b — BISC Parser Error Taxonomy Amendment

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` adding sections 4-7. Resolves the prior audit blockers by clarifying the library/process contract (parse_file raises; the BISC CLI wrapper exits 6) and binding `companion_path` as a re-export of `reference.babel.companion.resolve_companion`. Five frozen error codes introduced: `duplicate_id`, `version_mismatch`, `malformed_header`, `invalid_intent_json`, `missing_intent`. Structured stderr JSON shape and exit-code mapping made normative. Hard prerequisite for stage 4c.

### Cycle: Stage 2b — Companion Resolver Skeleton

Shipped `reference/babel/companion.py` as a single-file skeleton exposing a typed `resolve_companion(babel_path: Path) -> Optional[Path]` stub that raises `NotImplementedError`. Zero parser imports (only `pathlib` and `typing`); companion `.md` resolution contract lives in the docstring only.

### Cycle: Stage 1c — Contract Bootstrap Appendix

Shipped the Contract Bootstrap Appendix appended to `autonomy-output/babel-language-integration-v0.10.2.md`. The appendix maps the six API functions (`parse_file`, `write_file`, `to_virtual_json`, `companion_path`, `append_handoff`, `resolve_companion`) to BWSS lifecycle states and the five-step handoff protocol, distinguishing shipped skeleton (stage 1a) from pending skeleton (stages 2a, 2b).

### Cycle: Stage 1a — Parser API Skeleton

Shipped the contract-first bootstrap for the Babel v0.10.2 reference parser as a single-file deliverable. `reference/babel/bsl_parser.py` exposes the frozen public API (`parse_file`, `write_file`, `to_virtual_json`, `companion_path`) and the `BabelBlock`/`BabelFile` dataclasses. All function bodies raise `NotImplementedError`; implementation deferred to the 4x cycle. Type-enum rank, block-type tuples, error taxonomy constants, and `BABEL_VERSION` are exported as module constants.
