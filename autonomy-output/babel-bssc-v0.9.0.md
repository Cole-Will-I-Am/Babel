# Babel Snapshot State Continuity (BSSC) v0.9.0

## Status
Additive layer over frozen Babel v0.1.0-v0.8.1 and shipped BWCC v0.9.0. Defines a deterministic checkpoint protocol for agent state recovery across gateway crashes. No frozen field is mutated.

## 1. Purpose
BSSC v0.9.0 introduces content-addressed state snapshots with bounded hash_chain integrity, enabling deterministic crash recovery for any agent (workflow or non-workflow) without full log replay. Snapshots are emission-bounded by time and rate-limited by seq monotonicity to prevent log bloat and replay.

## 2. State Snapshot Schema
A state_snapshot document is a BSS JSON object:

- `operation_type`: string enum, MUST be `"state_snapshot"`
- `ext.kimi.state_snapshot`: canonical array of tuples
- `ext.kimi.previous_snapshot_sha256`: string|null
- `meta.author`: string (agent_id emitting this snapshot)
- `meta.emitted_at`: RFC 3339 UTC timestamp

Each tuple in `ext.kimi.state_snapshot` is a 4-element array:
- `agent_id`: string matching `^[a-zA-Z0-9_.-]{1,64}$`
- `ext.kimi.state`: object (arbitrary agent state, canonical JSON)
- `last_seen_seq`: uint64 (monotonic per agent)
- `workflow_id`: string|null (optional BWCC v0.9.0 cross-reference)

### 2.1 Canonical Tuple Ordering
Tuples are sorted lexicographically by `agent_id` per v0.2.0 canonical JSON (Unicode code point order). `workflow_id: null` sorts before non-null strings per JSON null ordering. This ordering is deterministic across implementations.

### 2.2 Unique agent_id Constraint
Within a single `ext.kimi.state_snapshot` array, each `agent_id` MUST appear at most once. Duplicate agent_ids are rejected with `BSSC_DUPLICATE_AGENT`. This ensures deterministic ordering and prevents state confusion on replay.

## 3. Hash Chain Pointer
Each snapshot document includes `ext.kimi.previous_snapshot_sha256`:
- Genesis snapshot: `null`
- Subsequent: `"sha256:"` + hex(SHA-256(canonical_json(prior_snapshot_document)))

Tier-1 validation recomputes the prior snapshot's canonical SHA-256 and rejects mismatches with `BSSC_HASH_MISMATCH`.

## 4. Tier-1 Validation
The gateway performs these checks on every state_snapshot submission:

### 4.1 Schema Validation
All required fields present, types correct, agent_id matches regex, last_seen_seq is uint64.

### 4.2 Unique agent_id Check
Reject with `BSSC_DUPLICATE_AGENT` if any agent_id appears twice in the array.

### 4.3 Time-Based Emission Bound (DISTINCT from seq monotonicity)
At most ONE state_snapshot submission per agent per DTL heartbeat interval (e.g., 30s). This is a time-based rate limit enforced via gateway-side per-agent timestamp tracking of the last accepted snapshot emit time. Rejection: `BSSC_EMISSION_RATE_EXCEEDED`. This check is independent of and complementary to the seq monotonicity check below.

### 4.4 Seq Monotonicity Check (Replay Prevention)
For each tuple's `last_seen_seq`, the gateway verifies: `last_seen_seq > last_seq_per_agent[agent_id]` where `last_seq_per_agent` is updated on each accepted snapshot. Reject with `BSSC_SEQ_REGRESSION` on equality or decrease. This prevents replay regardless of timing and is distinct from the emission bound.

### 4.5 Per-Agent Cross-Snapshot Seq Check
When processing a new snapshot, for each agent_id present, compare its `last_seen_seq` against the seq recorded for that same agent_id in the immediate prior snapshot document. This is the cross-snapshot regression check, distinct from the in-array check. Reject with `BSSC_CROSS_SNAPSHOT_REGRESSION` on violation. Catches regression that may be masked if the prior snapshot did not include that agent.

### 4.6 Hash Chain Validation
Recompute prior snapshot's canonical SHA-256; reject with `BSSC_HASH_MISMATCH` on mismatch.

### 4.7 Recovery Bypass
Crash recovery reads historical log via hash_chain traversal; it does not submit new snapshots, so the emission bound (4.3) is not applied during recovery. No deadlock.

## 5. Crash Recovery Fallback
Gateway crash recovery traverses the hash_chain tail-first, capped at **1024 snapshots** backward from the most recent intact snapshot.

### 5.1 Bounded Traversal
Recovery is O(n) with n ≤ 1024. At DTL heartbeat of 30s, this covers ~8.5 hours of history.

### 5.2 Documented Limitation
Hash_chain integrity verification is guaranteed ONLY for the most recent 1024 snapshots. Snapshots older than the 1024-cap are NOT guaranteed intact. Implementations MUST document this trade-off in their user-facing documentation. The cap bounds worst-case recovery time but sacrifices long-tail integrity.

### 5.3 Fallback Semantics
On first broken link (hash mismatch or seq regression):
1. Fall back to the last intact snapshot document found within the cap.
2. If no intact snapshot exists within the cap, replay from genesis (snapshot 0).
3. If genesis itself is broken or missing, reject with `BSSC_CHAIN_BROKEN`.

## 6. Snapshot Validation Algorithm
```
function validate_snapshot(snap, prior_doc, last_seq, last_emit, now):
  if not valid_schema(snap): return BSSC_SCHEMA_INVALID
  ids = [t[0] for t in snap.ext.kimi.state_snapshot]
  if len(ids) != len(set(ids)): return BSSC_DUPLICATE_AGENT
  if now - last_emit[snap.meta.author] < DTL_HEARTBEAT:
    return BSSC_EMISSION_RATE_EXCEEDED
  for t in snap.ext.kimi.state_snapshot:
    agent, state, seq, wf = t
    if seq <= last_seq.get(agent, 0): return BSSC_SEQ_REGRESSION
  for t in snap.ext.kimi.state_snapshot:
    agent, state, seq, wf = t
    if agent in prior_doc and seq <= prior_doc[agent].last_seen_seq:
      return BSSC_CROSS_SNAPSHOT_REGRESSION
  if prior_doc and snap.previous_snapshot_sha256 != compute_sha256(prior_doc):
    return BSSC_HASH_MISMATCH
  return ACCEPT
```

## 7. Cross-References
- **BWCC v0.9.0**: `workflow_id` in snapshot tuples is gateway-recommended for recovery context but optional.
- **BCRP v0.8.1**: snapshot documents appear in BCRP results sorted by (canonical_sha256, seq).
- **DTL v0.5.1**: heartbeat interval defines the emission bound period.
