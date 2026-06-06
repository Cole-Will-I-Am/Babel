# Babel Canonical Command & Control (BWCC) v0.9.0

## Status
Additive layer over frozen Babel v0.1.0-v0.8.1. Defines a static
workflow envelope for deterministic multi-agent task coordination.
No frozen field is mutated.

## 1. Purpose
BWCC v0.9.0 introduces a content-addressed, acyclic workflow
definition that the autonomy gateway executes in coordination with
v0.3.0 M0 RPC and v0.6.0 AIC tooling. Workflows emit extensible
result packages (XRPs) per v0.5.x DTL/XRP rules. BWCC is the
foundation for v0.10.x BWSS deterministic workflow syntax.

## 2. Workflow Definition Schema

```json
{
  "workflow_definition": {
    "task_ids":   ["string", "..."],
    "depends_on": { "task_id": ["upstream_task_id", "..."] }
  }
}
```

| Field        | Type                       | Constraint                                                  |
|--------------|----------------------------|-------------------------------------------------------------|
| `task_ids`   | `string[]`                 | Non-empty, unique, regex `^[a-zA-Z0-9_.-]{1,64}$`          |
| `depends_on` | `object<string,string[]>`  | All keys and all values must be members of `task_ids`       |

## 3. Canonicalization and workflow_id

- `workflow_definition` is serialized per v0.2.0 canonical JSON:
  NFC Unicode normalization, sorted keys, deterministic number
  formatting, single LF line endings.
- `workflow_id = "sha256:" + hex(SHA-256(canonical_json(workflow_definition)))`.
- `workflow_id` is the content-addressed primary key for every
  v0.9.0+ document that references this workflow.

## 4. Tier-1 Validation (Mandatory)

Gateways MUST reject a `workflow_definition` at tier-1 if any check
fails. On reject the gateway emits a BSS document with
`operation_type: "validation_failure"`, exit code 2 (validation-fail),
and one of the deterministic error codes below.

1. **Schema check**: `task_ids` non-empty, all entries unique, every
   entry matches the regex. `depends_on` keys are a subset of
   `task_ids`; every value array is a subset of `task_ids`.
   Membership tests use a hash-set of `task_ids` (O(1) per probe,
   O(n+e) total).
2. **Acyclicity (Kahn's algorithm, O(n+e))**: Compute in-degree per
   task, initialize a queue of zero-in-degree tasks, repeatedly
   dequeue and decrement neighbors' in-degrees. If the emitted
   count is less than `n`, the graph contains a cycle. Reject with
   `BWCC_CYCLE`.
3. **No self-loops**: For any task `t`, `t` MUST NOT appear in
   `depends_on[t]`. Reject with `BWCC_BAD_REFERENCE`.

## 5. workflow_amend Operation

A `workflow_amend` document modifies an existing workflow:

```json
{
  "operation_type":       "workflow_amend",
  "previous_workflow_id": "sha256:...",
  "new_workflow_definition": { "task_ids": [...], "depends_on": {...} }
}
```

The new workflow_id is computed from `new_workflow_definition` per
Section 3. The amendment is itself recorded as a v0.1.0 JSON
document with `meta.amend_of = previous_workflow_id`.

### 5.1 Non-Retroactivity (Normative)

A `workflow_amend` defines a NEW workflow. **Tasks already in-flight
under `previous_workflow_id` continue executing under that original
workflow_id with their original dependency bindings and XRP cascade
paths unchanged.** The amendment affects only:

- Tasks that have not yet started dispatch under the amended
  workflow, and
- Future workflow invocations that reference `new_workflow_id`
  directly.

This rule is normative and resolves DeepSeek v0.9.0 clarification 1.
No amendment may retroactively alter task semantics, dependency
bindings, or XRP cascade paths for tasks that have already begun
execution under a prior workflow_id.

### 5.2 Amendment Chain Acyclicity

For any workflow W, the amendment chain is the sequence
W -> amend -> W' -> amend -> W'' -> ... linked by
`previous_workflow_id`. Gateway tier-1 MUST traverse ancestors and
reject if:

- Any duplicate `workflow_id` appears in the chain (amendment cycle).
  Reject with `BWCC_AMEND_CYCLE`.
- The chain length exceeds 256 ancestors. Reject with
  `BWCC_CHAIN_TOO_LONG` (DOS bound).

A hash-set over observed ancestor workflow_ids provides O(1)
membership; total work is bounded by the 256-ancestor cap.

## 6. Workflow-Level XRP Cascade

When a task emits an XRP, the cascade follows `depends_on`:

- A task's XRP is published only after every upstream task listed in
  `depends_on[t]` has either completed (XRP accepted) or failed (XRP
  rejected with `BWCC_UPSTREAM_FAIL`).
- A failed upstream task propagates `BWCC_UPSTREAM_FAIL` to every
  transitive downstream task. Those downstream tasks MUST emit an
  XRP with `status: "cancelled"` and MUST NOT execute their handler.
- A cycle detected at runtime (should not occur given tier-1) yields
  `BWCC_RUNTIME_CYCLE` and halts the affected subgraph.

## 7. Workflow Document Schema

A workflow is recorded as a v0.1.0 JSON document:

```json
{
  "operation_type":     "workflow_register",
  "workflow_definition": { "task_ids": [...], "depends_on": {...} },
  "meta": { "author": "human|agent_id" }
}
```

The gateway computes `workflow_id` from `workflow_definition` and
stores the binding `{workflow_id, workflow_definition,
registered_at, meta}`.

## 8. Cross-References

- **BSSC v0.9.0**: `state_snapshot` tuples MAY include
  `workflow_id` for recovery context. Gateway-recommended but not
  mandatory; absence MUST be justified by the gateway.
- **BHOP v0.9.0**: `human_override.target_workflow_id` references
  any active or pending `workflow_id`.
- **BCRP v0.8.1**: Results paginated by composite key
  `(canonical_sha256, seq)`; workflow documents appear in this sort.

## 9. Conformance

A gateway is BWCC v0.9.0 conformant iff:

1. Tier-1 validation rejects every malformed `workflow_definition`
   input with the specified deterministic error codes.
2. `workflow_id` is computed exactly as in Section 3 and matches
   across all internal references.
3. `workflow_amend` is non-retroactive: in-flight tasks under
   `previous_workflow_id` are unaltered.
4. Am