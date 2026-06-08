# BISC Integrity Spec — Babel v0.10.2 Amendment

**Status:** Normative amendment to `babel-bisc-integrity-v0.10.2.md`
**Scope:** `.babel` file recognition, intent block validation, body-only canonical_sha256, parser error taxonomy (eight codes after stage 4c.1), structured stderr JSON format, CLI exit code mapping, companion path resolution contract
**Applies to:** `babel-language-syntax-v0.10.2.md`, `babel-language-integration-v0.10.2.md`

## 1. `.babel` File Recognition

A file is recognized as a Babel v0.10.2 source file if and only if it satisfies all of the following:

1. Filename suffix is `.babel` (case-sensitive).
2. The first non-blank line begins with the literal token `#[babel]:v0.10.2` (the file header).
3. The file is parseable as UTF-8 text without errors.

If any condition fails, the file is not a Babel v0.10.2 source file and BISC MUST NOT apply any canonical_sha256, intent validation, or block extraction logic to it.

## 2. Intent Block Validation

A Babel v0.10.2 file MUST contain exactly one intent block in its body. The intent block is the first block in the body whose header matches the regex `^#\[intent\]:[A-Za-z0-9_.-]+@\d+\.\d+\.\d+$`.

The intent block body MUST be valid JSON containing exactly the following top-level keys:

- `goal` (string, required)
- `non_goals` (array of strings, required, may be empty)
- `agent_id` (string, required, must be a non-empty string)
- `inputs` (object, required, may be empty `{}`)
- `outputs` (object, required, may be empty `{}`)

If validation fails, BISC exits with code 6 and emits a structured stderr JSON object identifying the violation (see section 4).

## 3. Body-Only `canonical_sha256`

The `canonical_sha256` of a `.babel` file is computed over the body only, where the body is defined as the file content with the following transformations applied in order:

1. Strip the file header line (`#[babel]:v0.10.2`) and the blank line that follows it, if present.
2. Strip all handoff blocks. A handoff block is any block whose header matches the regex `^#\[handoff\]:\d+$`.
3. Strip leading and trailing blank lines from the remaining content.
4. Join lines with `\n` (LF) and ensure the result ends with a single `\n` (no trailing blank line).

The result is UTF-8 encoded and hashed with SHA-256. The hex digest (lowercase, 64 characters) is the canonical_sha256.

This computation is deterministic across operating systems, line ending conventions, and handoff appends: appending a handoff block does not change the canonical_sha256 of a file.

## 4. Parser Error Taxonomy

The parser error taxonomy is a frozen set of stable string identifiers raised by the Babel v0.10.2 parser library and emitted by the BISC CLI wrapper. Each code has a deterministic detection site and a deterministic structured-stderr JSON shape (section 4.2).

### 4.1 Library-Level Codes (raised by `parse_file`)

| Code                  | Detection site                                                            | Line semantics                          |
|-----------------------|---------------------------------------------------------------------------|-----------------------------------------|
| `duplicate_id`        | Global (body + handoffs): two or more blocks with the same `(type, id)`    | First duplicate block's header line     |
| `version_mismatch`    | Two or more blocks in the same file declare different `@<version>` suffixes | First version-collision block's line  |
| `malformed_header`    | A block header does not match the expected `#[<type>]:<id>@<version>` form | The malformed header line              |
| `invalid_intent_json` | Intent block body is not valid JSON, or missing a required top-level key   | The intent block header line            |
| `missing_intent`      | No intent block found in the body                                        | The file header line (line 1)           |
| `multiple_intents`    | More than one `#[intent]:<id>@<version>` block in the body                | The second intent block's header line    |

Ordering note: `duplicate_id` is checked before `multiple_intents`, so two intent blocks with the same id are still reported as `duplicate_id` first. `multiple_intents` only fires when the two intent blocks have distinct id values.

### 4.2 Structured Stderr JSON Format (Library-Level)

All library-level errors emit the following shape on stderr, one JSON object per error, single line, no trailing newline:

```json
{"error":"BabelParseError","code":"<code>","line":<int>,"message":"<str>"}
```

- `error`: always the literal string `"BabelParseError"`.
- `code`: one of the strings in section 4.1.
- `line`: 1-based line number of the offending block header in the source file. Computed during the scan phase from 0-indexed line offsets stored on `BabelBlock.header_line`.
- `message`: human-readable description of the violation, suitable for logs and developer review.

The BISC CLI wrapper writes this JSON to stderr and exits with code 6. A library consumer that imports `parse_file` directly receives a native `BabelParseError` exception and is not required to parse this JSON shape.

### 4.3 Process-Level Codes (emitted by BISC CLI wrapper only)

The BISC CLI wrapper (`reference/babel/__main__.py` or equivalent process entry point) is responsible for translating native Python exceptions raised during process-level operations into the BISC stderr JSON shape. The parser library itself does not raise these codes; it raises the underlying Python exception directly so library consumers see idiomatic Python errors.

| Code             | Detection site (CLI wrapper)                                                                 | `error` field      | `line` | CLI exit |
|------------------|----------------------------------------------------------------------------------------------|--------------------|--------|----------|
| `file_error`     | CLI caught `OSError` reading input, writing output, or performing any filesystem operation on a `.babel` file or its companion `.md` file | `"OSError"`        | `null` | 6        |
| `internal_error` | CLI caught an unexpected `Exception` that is not `BabelParseError` and not `OSError`         | `"InternalError"`  | `null` | 6        |

Structured stderr JSON shape for process-level codes:

```json
{"error":"OSError","code":"file_error","line":null,"message":"<path>: <oserror str>"}
{"error":"InternalError","code":"internal_error","line":null,"message":"<ExceptionClass>: <str>"}
```

- `error`: the string `"OSError"` or `"InternalError"` identifying the underlying exception class.
- `code`: the string `"file_error"` or `"internal_error"` from the table above.
- `line`: always `null` because process-level errors are not anchored to a source line.
- `message`: human-readable description. For `file_error`, includes the affected path. For `internal_error`, includes the exception class name and stringified arguments.

Detection ordering in the CLI wrapper:

1. `BabelParseError` — re-emit the existing stderr JSON shape from section 4.2 unchanged, exit 6.
2. `OSError` — translate to `file_error` per this section, exit 6.
3. `Exception` (catch-all) — translate to `internal_error` per this section, exit 6.

On success, the CLI writes no output to stdout and exits 0 silently.

## 5. Duplicate Rejection and CLI Exit Code

If `parse_file` raises `BabelParseError` for any reason (any of the eight codes in section 4), the BISC CLI wrapper emits the corresponding structured stderr JSON object and exits with code 6. Pre-commit hooks, BCPR conflict log readers, and downstream tooling MUST treat exit code 6 as a hard failure and MUST parse the stderr JSON to determine the specific violation.

## 6. CLI Exit Code Mapping Summary

| Exit code | Meaning                                                                                       |
|-----------|-----------------------------------------------------------------------------------------------|
| 0         | Success; stdout is silent (no output).                                                        |
| 6         | BabelParseError (any of the eight codes in section 4.1 or 4.3); stderr has the JSON object.   |

All eight error codes (six library-level from 4.1, two process-level from 4.3) map uniformly to exit code 6. The exit code alone is not a sufficient signal; downstream tooling MUST also read the stderr JSON to identify the specific code.

## 7. Companion Path Resolution Contract

`reference/babel/bsl_parser.py` exposes a public attribute `companion_path` that is a re-export of `resolve_companion` from `reference/babel/companion.py`. The bsl_parser module imports the resolver and re-exports it under the alias `companion_path` so the frozen bsl_parser.py public API is fulfilled without duplicating filesystem utility logic.

`reference/babel/companion.py` remains a zero-parser-import utility module: it depends only on `pathlib` and `typing`. The companion resolver contract is:

- Given a `.babel` file path, return the path to the companion `.md` file with the same basename (e.g., `module.babel` pairs with `module.md`) if the `.md` file exists as a regular file alongside the `.babel` file.
- Return `None` if the `.md` file does not exist or is not a regular file (directory, symlink loop, broken symlink, etc.).
- Never write to the filesystem; the resolver is read-only.

This separation keeps the machine/human content boundary clean: the parser governs `.babel`, the companion resolver governs `.md` by basename, and they meet only at editor/tooling pairing time (BWSS handoff protocol step 3).
