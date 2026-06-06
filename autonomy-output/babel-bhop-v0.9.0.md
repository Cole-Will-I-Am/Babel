# Babel Human Override Protocol (BHOP) v0.9.0

## Status
Additive layer over frozen Babel v0.1.0-v0.8.1 and shipped BWCC v0.9.0
and BSSC v0.9.0. Defines a deterministic runtime human intervention
protocol for active workflow control. No frozen field is mutated.

## 1. Purpose
BHOP v0.9.0 introduces a first-class `operation_type: "human_override"`
document for runtime workflow control via pause, resume, and cancel
actions. Tier-1 dual-authenticity gating ensures only authorized human
overrides are accepted, and pause is enforced at both gateway and
agent layers to prevent bypass.

## 2. human_override Schema

Canonical JSON per v0.2.0. Required fields:

```
operation_type: "human_override"           (literal)
meta.author: "human"                       (exact, case-sensitive)
meta.created_at: ISO 8601 timestamp string
ext.human.override_action: enum {pause, resume, cancel}
ext.human.target_workflow_id: string matching ^sha256:[0-9a-f]{64}$
ext.kimi.gateway_agent: string              (must be in authorized_hig_gateway)
ext.kimi.previous_override_sha256: string | null   (hash chain, null for genesis)
```

Example:

```json
{
  "operation_type": "human_override",
  "meta": {"author": "human", "created_at": "2026-06-06T22:00:00Z"},
  "ext": {
    "human": {
      "override_action": "pause",
      "target_workflow_id": "sha256:abc123..."
    },
    "kimi": {
      "gateway_agent": "hig-gateway-prod-01",
      "previous_override_sha256": null
    }
  }
}
```

## 3. Tier-1 Dual-Authenticity Validation

Gateway tier-1 MUST reject human_override drafts where:
- `meta.author != "human"` (exact match) → `BHOP_AUTH_FAILURE`
- `ext.kimi.gateway_agent` not in `authorized_hig_gateway` list → `BHOP_AUTH_FAILURE`
- `target_workflow_id` does not match `^sha256:[0-9a-f]{64}$` → `BHOP_INVALID_WORKFLOW`
- `target_workflow_id` well-formed but not present in active/paused set → `BHOP_UNKNOWN_WORKFLOW`
- `override_action` not in enum → `BHOP_INVALID_ACTION`
- `previous_override_sha256` mismatch with latest accepted override for the same workflow_id → `BHOP_CHAIN_BROKEN`

The `authorized_hig_gateway` list is **genesis-configured and IMMUTABLE**
for the v0.9.0 session. No revocation mechanism exists within v0.9.0.
Gateway compromise requires genesis restart. This is a documented trust
assumption; a revocation mechanism is out of v0.9.0 scope and deferred
to a future version.

## 4. Action State Machine

Workflow states: `active`, `paused`, `terminated`.

### 4.1 Pause
- Transition: `active` → `paused`
- Gateway tier-1 **rejects** all new `task_delegation` drafts where
  `target_workflow_id` is in `paused` state → `BHOP_WORKFLOW_PAUSED`
- Agents **MUST** also re-check pause state **immediately before**
  accepting any `task_delegation` (not just at BCRP scan time) to
  prevent in-flight race conditions → reject with `BHOP_WORKFLOW_PAUSED`
- In-flight tasks continue unchanged; only new delegations are blocked
- Pause persists until explicit `resume` override is accepted

### 4.2 Resume
- Transition: `paused` → `active`
- Clears pause state; new `task_delegation` drafts accepted
- Does not affect in-flight tasks
- Resume itself MUST be delivered as a new `human_override` document
  (no implicit timeout-based resume)

### 4.3 Cancel
- Transition: `active | paused` → `terminated`
- Gateway tier-1 **rejects** all new `task_delegation` drafts for
  `terminated` workflows → `BHOP_WORKFLOW_TERMINATED`
- Triggers XRP v0.5.1 rollback cascade scoped to **active non-committed**
  tasks belonging to `target_workflow_id` per BWCC v0.9.0 active-task
  scoping
- Committed tasks remain immutable per BWCC v0.9.0
- Cascade terminates via per-agent active-task scan with commit-state
  re-check (verified by Nemotron in v0.9.0 BHOP verification)
- **Post-cancel state is `terminated`**: the workflow accepts no further
  task delegations. Reactivation requires either (a) a new
  `human_override` with `override_action: "resume"` (allowed since
  `terminated → active` is a valid reactivation), or (b) genesis restart.
  `terminated` workflows do NOT silently re-accept tasks.

## 5. Override Hash Chain

Each accepted `human_override` document carries
`ext.kimi.previous_override_sha256` referencing the canonical SHA-256
of the most recent accepted `human_override` for the same
`target_workflow_id`. The genesis override for a workflow uses `null`.
Tier-1 recomputes the previous hash and rejects `BHOP_CHAIN_BROKEN`
on mismatch. The chain is per-workflow, independent of the BSSC
hash chain (which is per-snapshot).

## 6. HIG Ingestion Path

`human_override` documents enter the handoff log via the HIG v0.4.0
gateway compilation pipeline (`bss_to_json` per v0.6.0 BSS), gaining
deterministic CDR v0.4.0 ordering and canonical SHA-256 like all other
`operation_type` documents. Tier-1 validation occurs before CDR
ordering; rejected documents are not appended to the log.

## 7. Agent Observation

Agents poll for `human_override` documents affecting their assigned
workflow_ids via BCRP v0.8.1 scan with composite cursor
(`canonical_sha256`, `seq`). Apply **most-recent-wins** per
`workflow_id` in log sequence order. BCRP returns results sorted
lexicographically by `(sha256, seq)`; agents track the highest-seen
`seq` per workflow to advance their cursors.

## 8. Agent State Durability

Agents embed an override-observation record within their BSSC v0.9.0
state_snapshot `ext.kimi.state` blob:

```json
{
  "human_override_observation": {
    "last_override_sha256": "sha256:...",
    "last_override_action": "pause",
    "last_override_seq": 42
  }
}
```

This ensures override durability across BSSC snapshots without
mutating the frozen BSSC tuple schema (the `ext.kimi.state` field is
an opaque blob per BSSC v0.9.0). On crash recovery, the agent
re-reads the BCRP scan, diffs against the observed hash+seq, and
applies any newer overrides in seq order.

## 9. Error Codes (Deterministic)

| Code | Meaning |
|------|---------|
| `BHOP_AUTH_FAILURE` | meta.author != "