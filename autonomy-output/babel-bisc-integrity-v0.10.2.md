# BISC Integrity Spec — Babel v0.10.2 Amendment

**Status:** Normative amendment to `babel-bisc-integrity-v0.10.2.md`
**Scope:** `.babel` file recognition, intent block validation, body-only canonical_sha256, parser error taxonomy (six codes after stage 4b.1), structured stderr JSON format, CLI exit code mapping, companion path re-export.

## 1. `.babel` File Recognition

A `.babel` file MUST begin with a `#[babel]:<id>@<version>` header at line 1. The file extension is `.babel`. Files matching this recognition rule are routed to the Babel reference parser; all other files pass through unchanged. The BISC pre-commit hook recognizes `.babel` files and dispatches them to `reference/babel/__main__.py`.

## 2. Intent Block Validation

Every `.babel` file MUST contain exactly one `#[intent]:<id>@<version>` block in the body. The intent block's content is a single inline JSON object (no multi-line JSON, no `//` line comments) and MUST contain a string `agent_id` field per the BCPR v0.10.2 cycle 5 minimum schema. Violations cause the BISC pre-commit hook to reject the file and exit with code 6.

## 3. Body-Only canonical_sha256

The `canonical_sha256` field in BCPR conflict log entries is computed over the **body** of a `.babel` file only — header line and handoff blocks are excluded. The body is sorted by `(TYPE_ENUM_RANK[type], id)` before hashing. Handoff blocks are not part of the body and are not hashed.

## 4. Parser Error Taxonomy

The Babel v0.10.2 reference parser raises `BabelParseError` with a stable string `code` attribute. The taxonomy is frozen at six codes and is consumed by BISC pre-commit hooks and the BCPR conflict log.

### 4.1 Stable Error Codes

| Code | Detection site | Line semantics |
|------|----------------|----------------|
| `duplicate_id` | Same `(type, id)` pair appears in more than one block header (body + handoffs) | First offending block header line |
| `version_mismatch` | Block header `@version` strings are not all identical across the file | First block header whose `@version` differs from the established common value |
| `malformed_header` | Block header syntax does not match the grammar in section 1 | First character of the malformed header line |
| `invalid_intent_json` | Intent block body is not valid JSON, or fails the inline minimal schema (agent_id required, string) | Intent block header line |
| `missing_intent` | No intent block in the body | 1 if body is empty, else first line of the first body block |
| `multiple_intents` | More than one intent block in the body | Header line of the second intent block (the first intent block is treated as the canonical one) |

The `multiple_intents` code is normative as of stage 4b.1 and closes the exactly-one-intent enforcement gap. Detection fires **after** the duplicate-id check, so two intent blocks with the same `id` are still reported as `duplicate_id` first; `multiple_intents` fires only when the two intent blocks have **distinct** `id` values. This ordering is safe because duplicate detection is global across body and handoffs and because `duplicate_id` is the more specific diagnosis when ids collide.

### 4.2 Structured Stderr JSON

Each `BabelParseError` carries `code`, `line`, and `message`. The BISC CLI wrapper at `reference/babel/__main__.py` catches `BabelParseError` and emits compact canonical JSON to stderr on a single line with no trailing newline:

```
{"error": "BabelParseError", "code": "<code>", "line": <int>, "message": "<str>"}
```

The `line` field references the first line of the offending block in the source file, using 1-based line numbers from the scanner attached as `BabelBlock.header_line` during the 4a scan phase. The `message` field is a human-readable explanation. The shape is normative: BISC pre-commit hooks and BCPR conflict log readers MUST accept this exact key set and reject extras. The new `multiple_intents` code reuses the same shape with `code` set to `"multiple_intents"`.

## 5. CLI Exit Code Mapping

The BISC CLI wrapper at `reference/babel/__main__.py` exits with code 6 on any `BabelParseError` and 0 on success. Non-BabelParseError exceptions exit with code 1. The mapping is frozen; downstream tooling depends on exit code 6 to mean "Babel parse failure" specifically.

## 6. Library vs. Process Contract

`parse_file` and `write_file` in `reference/babel/bsl_parser.py` are pure library functions. They raise `BabelParseError` on invalid input and never call `sys.exit()`. Process-level concerns (stderr, exit code 6) belong to the BISC CLI wrapper, not the library. This separation lets the library be reused in non-CLI contexts (BCPR virtual JSON, BWSS editor) without process semantics leaking.

## 7. companion_path Re-export Contract

`bsl_parser.py.companion_path` is a re-export of `reference.babel.companion.resolve_companion`. The frozen `bsl_parser.py` public API is fulfilled by importing `resolve_companion` from the companion module and re-exporting it under the alias `companion_path`. `companion.py` remains a zero-parser-import utility module that operates only on `pathlib.Path`; the re-export is a thin alias with no behavioral change.
