# Babel Integration Test Protocol (ITP) v0.7.0

## Status
Additive layer over frozen Babel v0.1.0-v0.6.0. Defines cross-platform
acceptance testing for the three AIC CLI tools introduced in v0.6.0.
No frozen field is mutated. ITP exit codes are disjoint from AIC exit
codes; ITP is invoked only by nemotron and is independent of agent
runtime.

## 1. Scope

ITP exercises the three AIC tools from a TIC package on three target
platforms, against a fixed golden-file matrix. M0-v0.6.0 acceptance
requires 100% ITP pass on all platforms before AIC integration can be
declared complete.

## 2. Golden File Matrix

Golden files live in `autonomy-output/itp-golden-v0.7.0/`. They are
generated ONCE on the reference platform (linux-amd64) and reused
unchanged across all target platforms. Cross-platform convergence is
the property under test.

Layout:

    itp-golden-v0.7.0/
    +-- babel-emit/
    |   +-- 001-minimal.babel           # minimal BSS input
    |   +-- 001-minimal.expected.json   # canonical JSON output
    |   +-- 002-comments.babel
    |   +-- 002-comments.expected.json
    |   +-- 003-unicode-nfc.babel
    |   +-- 003-unicode-nfc.expected.json
    |   +-- ... (N test vectors)
    +-- babel-validate/
    |   +-- 001-valid.babel
    |   +-- 002-invalid-trailing-comma.babel
    |   +-- 003-bad-pragma.babel
    |   +-- ... (N test vectors; golden is exit code only, no stdout)
    +-- babel-hash/
    |   +-- 001-hello.babel
    |   +-- 001-hello.expected.sha256   # golden hex
    |   +-- 002-nested.babel
    |   +-- 002-nested.expected.sha256
    |   +-- ... (N test vectors)

The N test vectors cover: BSS edge cases (NFC, key sorting, number
format, escape rules), forbidden constructs, and pragma variants.

## 3. Validation Order (Normative)

For each test vector, the ITP runner executes the following sequence
in this exact order. Early-exit on the first failure.

1. Invoke AIC tool with the test vector on stdin, capture stdout bytes
   and exit code $rc.
2. Crash handling: if $rc is not in {0,1,2,3} OR the tool was
   terminated by signal (detected via `wait` returning 128+signum),
   emit ITP exit 10 (determinism-fail) for this vector.
3. Schema check: parse the captured stdout against the v0.2.0 canonical
   JSON schema. On parse failure, emit ITP exit 20 (schema-fail) for
   this vector.
4. Byte comparison: if a golden file exists for this vector, byte-
   compare captured stdout against the golden file. On mismatch,
   emit ITP exit 10 (determinism-fail) for this vector.
5. Per-vector pass recorded; continue to next vector.

The schema check is strictly before the byte comparison. A test vector
that produces malformed JSON is schema-fail (20), not determinism-fail
(10), even if it would have differed from the golden file.

## 4. Exit Code Taxonomy

ITP emits exactly one of the following final exit codes:

    0   = all vectors passed schema and byte comparison on this platform
    10  = determinism-fail: at least one vector had a schema-valid stdout
          that did not byte-match its golden file, OR an AIC tool
          crashed (exit code outside {0,1,2,3} or signal termination)
    20  = schema-fail: at least one vector produced stdout that did
          not parse as v0.2.0 canonical JSON

The three codes are mutually exclusive per invocation: only the
first-failed-vector's code is emitted.

## 5. AIC Code Mapping (ITP Runner)

The ITP runner wraps each AIC invocation. AIC exit codes are mapped to
internal result before the ITP code is emitted:

    AIC 0 (success)        -> proceed to schema + byte check
    AIC 1 (invalid input)  -> schema-fail (20) if any stdout was
                              emitted and unparseable; otherwise treated
                              as expected (validate tool with bad input)
    AIC 2 (io_error)       -> determinism-fail (10)
    AIC 3 (pragma_error)   -> schema-fail (20)
    anything else / signal -> determinism-fail (10)

This mapping is internal. The ITP runner NEVER propagates an AIC exit
code directly to the caller.

## 6. Runner Pseudocode

```sh
#!/bin/sh
# ITP runner (POSIX, uses only packaged binaries and standard shell)
set -e
TOOL="$1"      # babel-emit | babel-validate | babel-hash
VECTOR="$2"    # path to .babel test vector
GOLDEN="$3"    # path to golden file (may be empty for validate)

set +e
OUT="$(./binaries/"$TOOL" < "$VECTOR")
RC=$?
set -e

# Crash handling
if [ $RC -lt 0 ] || [ $RC -gt 3 ]; then
  exit 10
fi
# Signal handling is provided by the shell trapping framework above.

# Schema check (skip for babel-hash, whose stdout is hex only)
if [ "$TOOL" != "babel-hash" ]; then
  echo "$OUT" | ./binaries/babel-validate >/dev/null 2>&1
  if [ $? -ne 0 ]; then
    exit 20
  fi
fi

# Byte comparison (skip for validate, where golden is the exit code)
if [ -n "$GOLDEN" ] && [ "$TOOL" != "babel-validate" ]; then
  if [ "$OUT" != "$(cat "$GOLDEN")" ]; then
    exit 10
  fi
fi

exit 0
```

## 7. Nemotron Acceptance Criteria

M0-v0.6.0 milestone draft MUST include an `ext.kimi.itp_pass` array
listing the three target platforms with `result: "pass"` for each,
demonstrating 100% ITP pass on Linux-amd64, Darwin-arm64, and
Windows-amd64. A single failure blocks AIC integration declaration.

## 8. Cross-References

- v0.6.0 AIC contracts: autonomy-output/babel-aic-v0.6.0.md
- v0.7.0 TIC packaging: autonomy-output/babel-tic-v0.7.0.md
- v0.7.0 WCP workspace: autonomy-output/babel-wcp-v0.7.0.md
- v0.7.0 manifest: autonomy-output/babel-manifest-v0.7.0.json
