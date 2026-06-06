# Babel BSDC Amendment v0.8.1

## Status
Additive amendment over frozen Babel v0.1.0-v0.7.0 and v0.8.0 BSDC. Resolves DeepSeek v0.8.1 audit blocking issue 3 (LCS tie-breaking undefined). No frozen field is mutated.

## 1. Deterministic LCS Tie-Breaking Rule

When computing the Longest Common Subsequence (LCS) of flattened key-path tuples between source S and target T canonical JSON documents, multiple LCS of equal maximum length may exist. The BSDC v0.8.1 tie-breaking rule is:

**Prefer the LCS that retains the lexicographically earliest tuples at the first differing index.**

Formally: let L1 and L2 be two LCS of equal length. Let i be the first index where L1 and L2 differ (i.e., L1[i] != L2[i]). Choose the LCS whose tuple at position i is lexicographically smaller in sorted key-path order.

This rule is deterministic: given identical source and target inputs, all implementations produce the identical LCS, and therefore the identical minimal patch.

## 2. Key-Path Tuple Definition

A key-path tuple is the sequence of RFC 6901 pointer segments (e.g., `/foo/bar/0`) obtained by recursively flattening a canonical JSON document. The flattening algorithm:

1. Start with an empty tuple `[]`
2. For each object key K in sorted (Unicode code point) order:
   - Recurse into K's value with tuple extended by `[..., K]`
3. For each array, recurse with tuple extended by `[..., <index_string>]`
4. For each scalar value, emit the tuple paired with the canonical value

The output is a list of `(tuple, value)` pairs sorted lexicographically by tuple (Unicode code point comparison on the full tuple sequence).

## 3. LCS Algorithm

Given two sorted lists of `(tuple, value)` pairs (source_list and target_list):

1. Compute the LCS using the standard dynamic programming algorithm on the tuple sequences
2. Apply the tie-breaking rule (Section 1) when multiple LCS exist
3. Emit a minimal add/remove/replace patch:
   - For each tuple in source_list not in LCS: emit `{"op": "remove", "path": <tuple_as_RFC6901>}`
   - For each tuple in target_list not in LCS: emit `{"op": "add", "path": <tuple_as_RFC6901>, "value": <canonical_value>}`
   - For tuples in LCS where values differ: emit `{"op": "replace", "path": <tuple_as_RFC6901>, "value": <canonical_value>}`

## 4. Canonical Validation Post-Diff

After patch generation:
1. Apply the patch to the source document
2. Re-canonicalize the result via v0.2.0 serialization (NFC, sorted keys, deterministic numbers, single LF)
3. Verify byte-equivalence to the target document's canonical form
4. If verification fails, the diff algorithm has a bug; emit a BSDC error and halt

## 5. Test Vectors (Normative)

Implementations MUST produce the indicated patches for these inputs.

### Vector 1: Simple Add
- Source: `{"a": 1}`
- Target: `{"a": 1, "b": 2}`
- Expected patch: `[{"op": "add", "path": "/b", "value": 2}]`

### Vector 2: Remove
- Source: `{"a": 1, "b": 2, "c": 3}`
- Target: `{"a": 1, "c": 3}`
- Expected patch: `[{"op": "remove", "path": "/b"}]`

### Vector 3: Replace
- Source: `{"a": 1, "b": 2}`
- Target: `{"a": 1, "b": 3}`
- Expected patch: `[{"op": "replace", "path": "/b", "value": 3}]`

### Vector 4: Nested Object Add (Tie-Break Determinism)
- Source: `{"x": {"a": 1, "b": 2}}`
- Target: `{"x": {"a": 1, "b": 2, "c": 3}}`
- Expected patch: `[{"op": "add", "path": "/x/c", "value": 3}]`

## 6. JSON Patch Subset Restrictions (Unchanged from v0.8.0)

Only `add`, `remove`, `replace` operations are permitted. `move`, `copy`, `test` are forbidden. Paths use RFC 6901 syntax. Values are canonical JSON per v0.2.0.
