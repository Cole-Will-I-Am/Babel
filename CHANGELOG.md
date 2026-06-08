# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.2 — Babel Language Surface (Unreleased)

### Cycle: Stage 4c.1 — BISC Process-Level Error Codes

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` adding section 4.3 with the two process-level error codes emitted exclusively by the BISC CLI wrapper:

- `file_error` — `OSError` caught during CLI filesystem operations (read input, write output, access companion `.md` file). Emits `{"error":"OSError","code":"file_error","line":null,"message":"<path>: <oserror str>"}` and exits 6.
- `internal_error` — unexpected `Exception` (not `BabelParseError`, not `OSError`) caught by the CLI catch-all handler. Emits `{"error":"InternalError","code":"internal_error","line":null,"message":"<ExceptionClass>: <str>"}` and exits 6.

The library/process contract is preserved: `parse_file` and `write_file` raise native Python exceptions (`BabelParseError`, `OSError`) directly; the CLI wrapper translates process-level exceptions into the BISC stderr JSON shape. Library consumers that import `parse_file` directly see idiomatic Python errors and are not required to parse the BISC JSON shape.

Sections 1-3, 4.1 (six library codes: `duplicate_id`, `version_mismatch`, `malformed_header`, `invalid_intent_json`, `missing_intent`, `multiple_intents`), 4.2 (stderr JSON format for library codes), 5 (duplicate rejection and exit 6), 6 (CLI exit code mapping extended to all eight codes), and 7 (companion_path re-export from `reference/babel/companion.py`) are preserved verbatim from the stage 4b.1 amendment.

This amendment is the hard prerequisite for stage 4c.2c (`reference/babel/__main__.py` CLI wrapper implementation), which must catch `BabelParseError`, `OSError`, and `Exception` and translate them to the eight BISC stderr codes.

### Cycle: Stage 4b.1 — BISC `multiple_intents` Amendment

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` extending the parser error taxonomy in section 4.1 with the sixth code `multiple_intents`:

- Detection rule: more than one `#[intent]:<id>@<version>` block in the body.
- Line semantics: the second intent block's header line (1-based, from scanner metadata).
- Stderr JSON shape: `{"error":"BabelParseError","code":"multiple_intents","line":<int>,"message":<str>}` per section 4.2.
- Ordering note: `duplicate_id` is checked before `multiple_intents`, so two intent blocks with the same id are still reported as `duplicate_id` first. `multiple_intents` only fires when the two intent blocks have distinct id values.

Sections 1-3, 4.2, 5, 6, and 7 preserved verbatim from the stage 3b amendment.

### Cycle: Stage 3b — BISC Parser Error Taxonomy Amendment

Shipped a normative amendment to `autonomy-output/babel-bisc-integrity-v0.10.2.md` adding sections 4-7:

- Section 4: parser error taxonomy (five library codes initially, six after 4b.1, eight after 4c.1).
- Section 5: duplicate rejection with exit code 6.
- Section 6: CLI exit code mapping (0 success, 6 BabelParseError).
- Section 7: companion_path re-export contract binding `reference/babel/bsl_parser.py` to `reference/babel/companion.py`.

Library/process contract clarified: `parse_file` raises `BabelParseError` (library), and the BISC CLI wrapper (not the library) emits the structured stderr JSON and exits 6 (process).

### Cycle: Stage 2b — Companion Resolver Skeleton

Shipped the contract-first bootstrap for the companion `.md` resolver as a single-file deliverable. Follow-up stages (3a test, 4c CLI wrapper) consume this skeleton.

### Cycle: Stage 1c — Contract Bootstrap Appendix

Shipped the Contract Bootstrap Appendix appended to `autonomy-output/babel-language-integration-v0.10.2.md`. The appendix maps all six parser/companion/handoff API functions to BWSS lifecycle states and the five-step handoff protocol.

### Cycle: Stage 1a — Parser Public API Skeleton

Shipped `reference/babel/bsl_parser.py` with the frozen public API surface: `parse_file`, `write_file`, `to_virtual_json`, `companion_path`, plus `BabelParseError`, `BabelBlock`, `BlockType`, `HandoffBlock`, `Document` dataclasses. All function bodies raise `NotImplementedError` pending stages 4a-4c implementation.
