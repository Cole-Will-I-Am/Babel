# Babel HIG Amendment v0.6.0

## Status
Additive amendment to frozen Babel HIG v0.4.0. Adds `.babel` file
acceptance to the gateway ingestion path. No frozen field is mutated.
The `.json` ingestion path defined in v0.4.0 is unchanged and remains
the canonical path for machine-generated documents.

## 1. Accepted File Extensions

The gateway watches `autonomy-output/handoff-inbox/` (per v0.4.0) and
accepts files with extension:

- `.json` (canonical, v0.4.0 path — unchanged)
- `.babel` (BSS source, this amendment)

All other extensions are ignored and left in place.

## 2. Gateway Pipeline (`.babel`)

1. Atomic-rename detection: a file appears in `.inbox/` via a
   `rename(2)` from the agent's working directory. The gateway does not
   act on files that are still being written (open write handle or
   `.tmp` suffix).
2. On stable appearance, the gateway atomic-renames the file from
   `.inbox/<name>.babel` to `.processing/<name>.babel`.
3. The gateway invokes `babel-emit` as a subprocess, piping the file
   contents to stdin. No filesystem write is performed by `babel-emit`
   itself; the gateway captures stdout into a memory buffer.
4. On exit 0:
   - The gateway appends the canonical JSON to
     `autonomy-output/handoff-log/` using the v0.2.0 naming and
     atomic-write protocol (temp file + `rename(2)`).
   - The appended document includes
     `ext.kimi.source_ext = ".babel"` and
     `ext.kimi.gateway_agent = <gateway_id>`.
   - The gateway atomic-renames the source file from
     `.processing/<name>.babel` to `.processed/<name>.babel`.
5. On exit 1, 2, or 3:
   - The gateway writes a `.error.json` file to
     `autonomy-output/handoff-invalid/<name>.error.json` via temp +
     `rename(2)`. The error file contains the error JSON from stderr,
     the source filename, the source extension, and the original
     `babel-emit` exit code.
   - The gateway atomic-renames the source file from
     `.processing/<name>.babel` to `.invalid/<name>.babel`.

## 3. Schema Compliance: `ext.kimi.source_ext`

Per frozen v0.1.0 schema, the `meta` object is closed to additional
properties. The `.babel` source annotation is therefore placed in
`ext.kimi`, matching the v0.4.0 convention for gateway-emitted
metadata. Specifically, the handoff log entry produced from a `.babel`
file contains:

```json
{
  "ext": {
    "kimi": {
      "source_ext": ".babel",
      "gateway_agent": "<gateway_id>"
    }
  }
}
```

`meta.source_ext` MUST NOT be used; doing so violates the v0.1.0
schema and causes tier-1 validation rejection.

## 4. Atomicity Guarantees

- A single writer (the gateway process) serializes all appends to the
  handoff log via per-file temp + `rename(2)`. No concurrent writers
  exist.
- File moves use `rename(2)` (POSIX atomic) or
  `MoveFileExW(MOVEFILE_REPLACE_EXISTING)` (Windows atomic). A
  partial-move is not possible.
- The gateway never opens a `.babel` file in `.inbox/` for writing; it
  only atomic-renames it.

## 5. Crash Recovery (Startup Scan)

A gateway crash may leave files in `.processing/`. On startup, the
gateway performs the following recovery scan:

1. List all files in `.processing/` matching `*.babel` or `*.json`.
2. For each file:
   a. Attempt to resume: re-invoke `babel-emit` (for `.babel`) or
      re-validate against the v0.1.0 schema (for `.json`).
   b. On success, continue the normal append + atomic-rename to
      `.processed/` (or, for a `.json` file that is already valid
      canonical JSON, append directly).
   c. On failure, atomic-rename the file to
      `.invalid/<name>.<ext>` and write a `.error.json` indicating
      `recovery_failed: true` plus the original error.
3. The recovery scan runs to completion before the gateway begins
   watching `.inbox/`. A second crash during recovery leaves the
   remaining files in `.processing/` for the next startup.

This guarantees that no file is left orphaned in `.processing/`
indefinitely: every file is either promoted to `.processed/`,
demoted to `.invalid/`, or left for the next recovery pass.

## 6. `.error.json` Schema

```json
{
  "code": "string",
  "message": "string",
  "line": 0,
  "column": 0,
  "source_filename": "string",
  "source_ext": ".babel | .json",
  "babel_emit_exit": 0,
  "recovery_failed": false
}
```

The file is written to `.invalid/<name>.error.json` next to the
original source file. The original source file is also moved to
`.invalid/<name>.<ext>` so that the pair can be inspected together.

## 7. Test Vectors

### TV-H1: happy `.babel` ingest
Place `tv1.babel` in `.inbox/`. Within one poll cycle, gateway must
produce a handoff log entry matching TV-1 from the BSS spec, with
`ext.kimi.source_ext = ".babel"` and `ext.kimi.gateway_agent` set.

### TV-H2: forbidden construct
Place `tv2.babel` containing a trailing comma. Gateway must move to
`.invalid/` and write `.error.json` with `code = "forbidden_construct"`.
No handoff log entry is produced.

### TV-H3: crash recovery
Kill the gateway mid-ingest (after step 2 atomic-rename into
`.processing/`, before step 4 append). Restart the gateway. Recovery
scan must complete the append and move the file to `.processed/`.

### TV-H4: recovery failure
Same as TV-H3 but with a syntactically invalid `.babel` file. Recovery
scan must move the file to `.invalid/` and write `.error.json` with
`recovery_failed: true`.
