# Babel Agent Implementation Contract (AIC) v0.6.0

## Status
Additive layer over frozen Babel v0.1.0-v0.5.1. Defines three deterministic
CLI tools that wrap the BSS canonicalizer and the v0.2.0 canonical
serialization. No frozen field is mutated. Tools are stateless
subprocesses; agents invoke them to avoid embedding parser logic.

## 1. Tools

| Tool            | Reads (stdin) | Writes (stdout)       | Writes (stderr) | Filesystem | Exit codes        |
|-----------------|---------------|-----------------------|-----------------|------------|-------------------|
| `babel-emit`    | BSS bytes     | canonical JSON bytes  | error JSON      | none       | 0, 1, 2, 3        |
| `babel-validate`| BSS bytes     | (nothing)             | error JSON      | none       | 0, 1, 2, 3        |
| `babel-hash`    | BSS bytes     | SHA-256 hex + LF      | error JSON      | none       | 0, 2, 3           |

All tools MUST refuse any flag other than `--version` and `--help` (exit
2). All tools MUST use fixed-size buffers and MUST NOT perform any
filesystem syscall (no reads, no writes, no stat). All tools MUST emit
the same exit code for the same input regardless of wall-clock, locale,
or process priority.

## 2. Exit Code Taxonomy

| Code | Meaning      | Trigger                                            |
|------|--------------|----------------------------------------------------|
| 0    | success      | Input is valid; output produced (or silent)        |
| 1    | invalid      | Input is syntactically valid BSS but violates a rule (forbidden construct, schema mismatch) |
| 2    | io_error     | stdin closed early, non-UTF-8 bytes, or unsupported flag |
| 3    | pragma_error | Line 1 is missing or has a pragma other than `// babel:0.6.0` |

Exit codes are deterministic. The pragma check is gated by the same
constant-time path as the body parse: the validator walks the entire
input even if the pragma is missing, then returns 3. This eliminates a
timing side channel that would otherwise leak pragma vs. body errors.

## 3. `babel-emit` Contract

Invocation: `babel-emit` (no arguments, or `--version`/`--help`).

- Reads stdin until EOF; accumulates up to 64 MiB; if EOF is reached
  before the input is fully formed (truncated), exit 2.
- Runs `bss_to_json` (BSS spec section 4).
- On success, writes the canonical JSON bytes (UTF-8, single LF) to
  stdout and exits 0. stdout is flushed before exit.
- On `pragma_error`, writes the error JSON to stderr and exits 3.
- On `forbidden_construct` or schema violation, exits 1 with error JSON.
- On I/O failure, exits 2 with error JSON.

## 4. `babel-validate` Contract

Invocation: `babel-validate` (no arguments, or `--version`/`--help`).

- Reads stdin identically to `babel-emit`.
- Runs the same parse + canonicalize pipeline as `babel-emit` but
  discards the canonical output.
- Writes nothing to stdout regardless of outcome.
- Writes the same error JSON to stderr on non-zero exits.
- Same exit code taxonomy as `babel-emit`.

## 5. `babel-hash` Contract

Invocation: `babel-hash` (no arguments, or `--version`/`--help`).

- Reads stdin identically to `babel-emit`.
- Internally runs the full `bss_to_json` canonicalization, then computes
  SHA-256 over the canonical JSON **bytes** (UTF-8, single LF included).
- On success, writes the lowercase hex SHA-256 digest followed by a
  single LF to stdout and exits 0.
- On `pragma_error`, writes error JSON to stderr and exits 3.
- On I/O failure, writes error JSON to stderr and exits 2.
- On syntactically valid BSS that fails canonicalization, exits 1.

**Hashing target clarification**: `babel-hash` does NOT hash the raw
BSS bytes. It hashes the canonical JSON produced by `bss_to_json`. This
guarantees that `babel-hash` output equals the SHA-256 of the handoff
log entry that `babel-emit` would produce for the same input, preserving
deterministic audit trails across tools.

## 6. Error JSON Schema (stderr)

```json
{
  "code": "pragma_error | forbidden_construct | schema_violation | io_error",
  "message": "human-readable string",
  "line": 1,
  "column": 1
}
```

`line` and `column` are 1-indexed and refer to the original BSS input.
The error JSON itself is NOT in v0.2.0 canonical form (it is a
diagnostic, not a Babel document) and is written to stderr only.

## 7. Constant-Time Requirements

- All three tools MUST process the full input before returning, even
  if a fatal error is detected early. This prevents timing side
  channels that would leak the location of the first error.
- The SHA-256 computation in `babel-hash` MUST use a constant-time
  implementation (e.g., `hashlib.sha256` in Python or `sha2` crate in
  Rust); no early-exit on internal state differences.
- The pragma check MUST run after tokenization of the full first line
  rather than via `startswith` + early return, to avoid leaking pragma
  content via response time.

## 8. Test Vectors

### TV-A1: `babel-emit` happy path
Input: TV-1 from BSS spec.
Expected: exit 0, stdout matches canonical JSON, SHA-256 =
`sha256:PENDING_COMPUTE_AT_COMMIT`.

### TV-A2: `babel-validate` happy path
Same input.
Expected: exit 0, stdout empty.

### TV-A3: `babel-hash` happy path
Same input.
Expected: exit 0, stdout is the lowercase hex SHA-256 of the
`babel-emit` output followed by LF.

### TV-A4: pragma missing
Input: `{ "doc_id": "x" }`.
Expected: all three tools exit 3 with the same error JSON.

### TV-A5: trailing comma
Input ends with `,}`.
Expected: all three tools exit 1.

### TV-A6: `babel-hash` matches handoff log hash
`babel-hash` on TV-1 input MUST equal the `meta.content_hash` recorded
in the handoff log for the canonical JSON that `babel-emit` produces
on the same input. Verified by the M0-v0.6.0 integration test.
