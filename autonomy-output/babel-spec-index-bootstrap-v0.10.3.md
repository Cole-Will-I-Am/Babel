# Babel Spec-Index Bootstrap Procedure v0.10.3

## Status
Normative. First cycle (1 of 7) of the Babel v0.10.3 deterministic
synthesis sequence. Strictly additive over frozen v0.1.0-v0.8.1
artifacts and the completed v0.9.0 freeze (BWCC, BSSC, BHOP specs and
manifest). Defines the recursive procedure by which the v0.10.3
spec-index aggregates canonical_sha256 values from every prior Babel
manifest, eliminating the v0.10.2 manual-bootstrap gap without
introducing human-input dependencies.

## 1. Purpose
The v0.10.3 spec-index is a content-addressed registry of every Babel
artifact, with a unique canonical_sha256 per (version, type) tuple.
Populating it with v0.1.0-v0.9.0 historical hashes is a precondition
for the v0.10.3 synthesis algorithm and the v0.10.2 procedural
materialization. This spec defines:

  a) The recursive traversal procedure from the v0.9.0 manifest back
     to the v0.1.0 genesis manifest, following basis_ref pointers.
  b) The hash aggregation rule: one (version, type, path,
     canonical_sha256) tuple per artifact entry encountered.
  c) Gap detection: explicit failures for missing manifests or
     placeholder canonical_sha256 values that would silently corrupt
     the spec-index.
  d) The output format that the v0.10.3 spec-index author consumes to
     seed the registry.

## 2. Traversal Procedure

### 2.1 Entry point
The bootstrap procedure's entry point is the frozen v0.9.0 manifest at
the canonical path:

  autonomy-output/babel-manifest-v0.9.0.json

This file MUST exist, MUST parse as JSON, and MUST contain a
non-empty `canonical_sha256` field on itself and a non-empty
`basis_ref` field pointing to a `sha256:hex64` hash.

### 2.2 Recursive step
For a manifest M at version V with basis_ref B and basis_target T
(the predecessor manifest at V_pred):

  1. Verify B is well-formed: matches `^sha256:[0-9a-f]{64}$`.
     FAIL with BOOTSTRAP_INVALID_BASIS_REF.
  2. Verify T exists on disk at
     `autonomy-output/babel-manifest-v{V_pred}.json`.
     FAIL with BOOTSTRAP_MISSING_MANIFEST.
  3. Canonicalize T via the v0.2.0 canonical serialization (NFC
     unicode, LF line endings, sorted keys, deterministic numbers)
     and SHA-256 hash the result.
  4. Verify the computed hash equals B.
     FAIL with BOOTSTRAP_BASIS_MISMATCH on any discrepancy.
  5. Recurse on T with V <- V_pred.
  6. Termination: V_pred is v0.1.0. Verify that T's basis_ref is
     null and T's basis_target is absent.
     FAIL with BOOTSTRAP_GENESIS_HAS_BASIS if v0.1.0 has a basis.

### 2.3 Predecessor resolution
The semver predecessor of V is V_pred such that:

  - V_pred is the highest version < V with the same major version
    (e.g., v0.9.0 -> v0.8.1, v0.8.1 -> v0.8.0, v0.1.0 -> genesis).
  - Pre-release tags are NOT used in Babel versioning; all versions
    match `^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`.
  - Tie-breaking is by semver-point ordering only; v0.8.1 precedes
    v0.9.0 with no special handling.

This rule is stable across the v0.1.0-v0.9.0 chain because the
frozen manifests at autonomy-output/ use semver-point versions only.

## 3. Hash Aggregation

For each manifest M traversed (V0.9.0, V0.8.1, ..., V0.1.0):

  1. For each entry E in M.artifacts:
     a. Verify E.canonical_sha256 matches
        `^sha256:[0-9a-f]{64}$` and is NOT
        `sha256:PENDING_COMPUTE_AT_COMMIT` and is NOT empty.
        FAIL with BOOTSTRAP_PLACEHOLDER_HASH.
     b. Verify E.path is a relative POSIX path: no leading `/`, no
        backslashes, no `..` segments, and the first path segment
        is `autonomy-output/` or `scripts/`.
        FAIL with BOOTSTRAP_BAD_PATH.
     c. Emit a spec-index seed tuple:
        {
          "version": V,
          "type": E.type,
          "path": E.path,
          "canonical_sha256": E.canonical_sha256
        }
  2. Do NOT include M itself in seed_entries; manifests are tracked
     by the separate manifest_entries[] list (see Section 5).
  3. De-duplicate by (version, type) within the running aggregation.
     If a duplicate appears, halt with BOOTSTRAP_DUPLICATE_KEY. The
     v0.1.0-v0.9.0 frozen chain is known to be duplicate-free; this
     gate catches authoring errors.

## 4. Gap Detection

The procedure MUST halt with a deterministic exit code on any of:

  - BOOTSTRAP_MISSING_MANIFEST (exit 1): a referenced basis_target
    does not exist on disk.
  - BOOTSTRAP_PLACEHOLDER_HASH (exit 1): any manifest entry has a
    placeholder or empty canonical_sha256.
  - BOOTSTRAP_INVALID_BASIS_REF (exit 1): basis_ref is not
    `^sha256:[0-9a-f]{64}$`.
  - BOOTSTRAP_BASIS_MISMATCH (exit 1): computed basis hash !=
    stored basis_ref.
  - BOOTSTRAP_GENESIS_HAS_BASIS (exit 1): v0.1.0 manifest has a
    non-null basis_ref.
  - BOOTSTRAP_BAD_PATH (exit 1): any artifact path is not a
    relative POSIX path under autonomy-output/ or scripts/.
  - BOOTSTRAP_DUPLICATE_KEY (exit 1): two entries share an identical
    (version, type) tuple.

Gap detection exits with code 1 and writes a JSON error to stderr:

  {
    "code": "BOOTSTRAP_*",
    "version": V,
    "path": E.path or null,
    "expected": <hash> or null,
    "actual": <hash> or null
  }

## 5. Output Format

The procedure writes a single JSON object to stdout:

  {
    "bootstrap_version": "v0.10.3",
    "generated_by": "babel-spec-index-bootstrap-v0.10.3",
    "frozen_base": {
      "version": "v0.9.0",
      "path": "autonomy-output/babel-manifest-v0.9.0.json",
      "canonical_sha256": "sha256:hex64"
    },
    "seed_entries": [
      { "version": "v0.9.0", "type": "spec",
        "path": "autonomy-output/babel-bwcc-v0.9.0.md",
        "canonical_sha256": "sha256:hex64" },
      ... (one per artifact in v0.1.0 through v0.9.0)
    ],
    "manifest_entries": [
      { "version": "v0.9.0", "type": "manifest",
        "path": "autonomy-output/babel-manifest-v0.9.0.json",
        "canonical_sha256": "sha256:hex64" },
      ... (one per manifest v0.1.0 through v0.9.0)
    ]
  }

The v0.10.3 spec-index author (cycle 6) consumes this output and
extends it with placeholder entries for v0.10.2 and v0.10.3 artifacts.
The spec-index validator enforces the composite unique constraint
with error code SPECINDEX_MANIFEST_DUPLICATE for type=manifest.

## 6. Composite Unique Constraint

The seed_entries[] (and ultimately the full v0.10.3 spec-index) MUST
satisfy:

  For all E, E' in seed_entries:
    E.(version, type) == E'.(version, type) implies E == E'.

In other words, at most one entry per (version, type) tuple. This is
a hard schema constraint enforced at authoring time, not a
tie-breaker. The bootstrap procedure halts with BOOTSTRAP_DUPLICATE_KEY
on any duplicate detected during aggregation. The v0.10.3 spec-index
validator repeats the check with the manifest-specific error code
SPECINDEX_MANIFEST_DUPLICATE.

## 7. Algorithmic Complexity

  - Traversal: O(n) where n = number of historical versions (currently
    9 for v0.1.0-v0.9.0).
  - Per-step basis_ref verification: O(1) hash recomputation + O(1)
    disk read of the predecessor manifest.
  - Total hash aggregation: O(k) where k = total artifact entries
    across all manifests.
  - Memory: O(n + k) for the output JSON.

All operations are deterministic and reproducible across agents.

## 8. Reference Implementation

A reference implementation at `reference/babel/bootstrap.py` is
deferred to a subsequent cycle. The procedure is specified here in
sufficient detail that any conformant implementation must produce
byte-identical output for the same input set, modulo JSON formatting
(an optional `jq -S` post-pass normalizes whitespace).

## 9. Cross-References

  - Babel v0.2.0 canonical JSON serialization: NFC unicode, LF line
    endings, sorted keys, deterministic numbers.
  - Babel v0.9.0 manifest schema: basis_ref, frozen_manifest_ref,
    artifacts[].
  - v0.10.3 template registry (cycle 2): consumes the bootstrap
    output to parameterize procedural artifact synthesis.
  - v0.10.3 spec-index (cycle 6): consumes the bootstrap output to
    seed historical entries; adds placeholders for v0.10.2 and
    v0.10.3 artifacts.
  - validate-spec-index.py (cycle 6): bidirectional completeness
    gate that recomputes canonical_sha256 for every spec-index entry
    and rejects unlisted committed files under autonomy-output/ and
    scripts/.

## 10. Test Vectors (mandatory)

  - TV-BOOT-1: bootstrap from v0.9.0 manifest. Expect 9 manifest
    entries (v0.1.0 through v0.9.0) and k artifact entries where k
    is determined by the frozen v0.1.0-v0.9.0 manifest contents.
  - TV-BOOT-2: bootstrap with one manifest (e.g., v0.5.0) deleted
    from disk. Expect BOOTSTRAP_MISSING_MANIFEST with version=v0.5.0.
  - TV-BOOT-3: bootstrap with a placeholder hash injected into any
    manifest entry. Expect BOOTSTRAP_PLACEHOLDER_HASH with the
    affected path.
  - TV-BOOT-4: bootstrap with a tampered basis_ref (e.g., v0.8.0's
    basis_ref altered to a random hash). Expect
    BOOTSTRAP_BASIS_MISMATCH on the first mismatched step.
  - TV-BOOT-5: bootstrap with v0.1.0 manifest having a non-null
    basis_ref. Expect BOOTSTRAP_GENESIS_HAS_BASIS.
  - TV-BOOT-6: bootstrap with two entries sharing the same
    (version, type) (e.g., a duplicate injected into v0.7.0's
    artifacts). Expect BOOTSTRAP_DUPLICATE_KEY.
  - TV-BOOT-7: bootstrap with a path outside autonomy-output/ or
    scripts/. Expect BOOTSTRAP_BAD_PATH.

## 11. Cycle 7 Synthesis Path Resolution

The v0.10.3 synthesis algorithm (cycle 7) emits the following files
via template registry expansion, in the order listed:

  1. README.md                          (repo root, v0.9.0 format)
  2. CHANGELOG.md                       (repo root, v0.9.0 format)
  3. autonomy-output/babel-manifest-v0.10.2.json
  4. scripts/compute-manifest-sha256.py (v0.10.2 hook)
  5. README.md                          (repo root, v0.10.2 format)
  6. CHANGELOG.md                       (repo root, v0.10.2 format)

Items 1-2 are v0.9.0-format procedural artifacts (the gap that
previously blocked pair_b_finalize signoff due to TimeoutError).
Items 3-6 are v0.10.2-format procedural artifacts. All six are
verified via re-synthesis + SHA-256 match against spec-index entries.
