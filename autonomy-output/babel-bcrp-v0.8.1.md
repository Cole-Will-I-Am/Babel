# Babel BCRP Amendment v0.8.1

## Status
Additive amendment over frozen Babel v0.1.0-v0.7.0 and v0.8.0 BCRP. Resolves DeepSeek v0.8.1 audit blocking issue 1 (result ordering contradiction) and clarification item 1 (cursor validity after log compaction). No frozen field is mutated.

## 1. Composite Cursor Format

The pagination cursor for v0.8.1 is the composite string:

    sha256:<lowercase_hex>:seq:<uint64>

Where:
- `lowercase_hex` is the FIPS 180-4 canonical SHA-256 hex digest (64 lowercase hex chars, 0-9a-f) of the last document returned in the previous page
- `uint64` is the decimal sequence number of that document, assigned monotonically at handoff log append

The cursor uniquely identifies a position in the sorted result set. Two documents with identical canonical SHA-256 are disambiguated by their sequence number.

## 2. Sequence Number Semantics

- Sequence numbers are assigned at handoff log append (atomic rename time)
- Sequence numbers are monotonic, strictly increasing, never reused
- Log compaction and archival preserve original sequence numbers; compaction removes only the file content, not the seq from the persistent log index
- A document's sequence number is recorded as `meta.seq` (uint64) in the canonical JSON

## 3. Result Ordering (Corrected)

Documents matching the BCRP filter are returned sorted lexicographically by the composite key (canonical_sha256, seq) where:
- Primary sort: canonical SHA-256 hex string, lexicographic ascending
- Secondary sort: sequence number, numeric ascending

Pagination resumes from the strict successor of the cursor's composite key in this sort order.

**NOTE: This sort order does NOT match append order.** Append order is preserved by sorting by `meta.seq` only. Implementers MUST NOT assume lex order of SHA-256 corresponds to chronological order. The composite sort provides stable, deterministic pagination independent of insertion timing.

## 4. Scan-Limit Truncation Behavior (Unchanged from v0.8.0)

- Maximum 10,000 documents scanned per BCRP request
- Maximum 100 results returned per page
- If the scan limit is reached without exhausting the result set, the response includes:
  - `incomplete: true`
  - `next_cursor` pointing to the last evaluated document's composite cursor
  - `scanned_count: 10000`

## 5. Cursor Validity After Log Compaction

If a cursor references a sequence number whose file content has been removed by log compaction:
- The BCRP gateway MUST resolve the sequence number to its canonical SHA-256 via the persistent log index (preserved across compaction)
- If both the file and the index entry are gone, the gateway returns an error response:
  - `{"error": "cursor_invalid", "cursor": "<offending_cursor>", "reason": "sequence_number_not_found"}`
  - HTTP status 410 (Gone) or application-level exit code 4
- The client MUST restart pagination from the beginning (cursor=null) upon receiving cursor_invalid

This guarantees forward progress: clients can always restart from scratch if the cursor is invalidated by archival.

## 6. Filter Evaluation Order (Unchanged from v0.8.0)

Filters are evaluated in fixed order: (1) operation_type exact match, (2) meta.author exact match, (3) time bounds range check. Each document is evaluated in append order (`meta.seq` ascending) with early-exit on first filter failure. Query complexity bound: max 10,000 documents scanned, max 100 results per page.

## 7. Test Vectors (Normative)

### Vector 1: Duplicate Hash Disambiguation
- Log contains two documents with identical canonical SHA-256 `abc...000` at seq=5 and seq=12
- Cursor after first occurrence: `sha256:abc...000:seq:5`
- Next page resumes at `sha256:abc...000:seq:12` (composite successor)

### Vector 2: Compaction Invalidation
- Client holds cursor `sha256:def...111:seq:42`
- Log compaction removes seq=42 file content and index entry
- Gateway response: `{"error": "cursor_invalid", "cursor": "sha256:def...111:seq:42", "reason": "sequence_number_not_found"}`
- Client restarts with cursor=null
