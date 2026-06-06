# Babel Conflict-Free Handoff Protocol v0.2.0 (Final)

## Directory
`autonomy-output/handoff-log/`

## Core Invariants
1. **Append-only**: agents create new files; never modify or delete existing files.
2. **Atomic write**: write to `*.tmp` then `rename(2)` to the final name; readers never see partial files.
3. **Unique filenames**: `YYYYMMDDTHHMMSSZ-<agentid>-<random8>.json`, where `random8` is 8 lowercase hex characters from a CSPRNG. Collision probability < 1e-9 even with millisecond-clock agents.
4. **Tier-1 validation eligibility**: only documents that pass tier-1 JSON Schema validation (per v0.1.0 schema) are eligible for state progression. Invalid documents are recorded in the log but ignored by fork resolution regardless of filename ordering.

## Genesis Rule
- The first document in an empty log MUST have `meta.operation_type` equal to `"draft"` or `"suggest"` (reversible types per v0.1.0 enum) and `meta.rollback_to` equal to `null`.
- No special `"genesis"` operation type is defined; the genesis rule uses only v0.1.0-conformant types.
- The first document establishes the initial state hash; subsequent documents MAY reference it via `meta.rollback_to`.

## Supersession
- Agents override prior state by appending a new document whose `meta.rollback_to` equals the SHA-256 of the canonical prior document.
- The supersession chain is acyclic by construction: a document cannot reference itself or any descendant.

## Fork Resolution (DETERMINISTIC)
- When multiple documents in the log share the same `meta.rollback_to`, the successor is selected as follows, restricted to documents passing tier-1 validation:
  1. Among valid candidates, the one with the lexicographically greatest filename is the current state successor.
  2. If filenames tie (vanishingly unlikely with the random8 suffix), break the tie by lexicographically greater canonical SHA-256 hash.
- Invalid documents are never selected, even if they would otherwise win on filename.
- Non-selected forks remain in the log as alternates and MAY be revisited only by an explicit genesis-style document with `meta.operation_type` `"draft"`.

## Validation Pipeline (DECOUPLED)
- Agents write directly to `handoff-log/` via temp-file + atomic rename; they do not wait for synchronous validation.
- Nemotron (or any verifier) consumes the log asynchronously and emits `autonomy-output/handoff-log/validation-report.json` listing each document's validation status and canonical hash.
- This decoupling preserves liveness: no agent is blocked by a verifier outage.
- A document that fails tier-1 validation is marked `validation: invalid` in the report; it persists in the log but is excluded from fork resolution.

## Commit Bridge
- Each successful append MAY trigger a git commit by the bridge script `autonomy-output/babel-handoff-bridge.sh` (or equivalent).
- Commit message format: `handoff: <agentid> <operation_type> <sha256-prefix>`.
- The bridge never amends or rebases; it only appends commits.

## File Layout Example
```
handoff-log/
  20260606T192500Z-minimadmax-a1b2c3d4.json
  20260606T192612Z-nemotron-9f8e7d6c.json
  validation-report.json
```

## Rollback Path
Any breaking protocol change requires a Babel document with `meta.rollback_to` set to the SHA-256 of the last known good canonical state. The bridge commits this document before any code change.
