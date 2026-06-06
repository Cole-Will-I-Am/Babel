# Babel TDS Amendment v0.5.1

## Status
Additive amendment over frozen Babel v0.5.0 TDS. Implements remediation
for DeepSeek v0.5.0 audit gap 2 (deadline enforcement undefined) and
gap 4 (ancestry_chain can be forged). No frozen field is mutated.

## 1. Deadline Enforcement

Nemotron tier-1 validation rejects any draft emitted by assignee A
for task T if and only if the handoff log's current block sequence
number `current_block > T.deadline_block`. The rejection is recorded
as a tier-1 failure entry in the log, which transitions A to `failed`
state per ASMC `valid_transition`.

### 1.1 Algorithm

```
on draft d from agent A:
  for each open task_delegation T where T.assignee == A:
    if current_block > T.deadline_block:
      record_tier1_failure(d, reason="deadline_exceeded", task_id=T.task_id)
      transition(A, failed)
      reject(d)
      return
```

### 1.2 Thundering-Herd Bound

All deadline-exceeded rejections enter the nemotron tier-1 validation
queue and are processed in CDR hash order (lexicographic sort of
canonical SHA-256 of the rejected draft). Peak queue load equals the
number of tasks sharing the same `deadline_block`. No additional grace
window is required; operators tune `timeout_ms` via
`ext.kimi.capabilities.max_validation_cycle_ms`.

## 2. Ancestry Chain Validation (O(1) via incremental index)

Nemotron maintains an in-memory map:

    task_index: dict[task_id, {assignee, parent_task_ids: list}]

### 2.1 Startup Build

Scan the handoff log once, O(n) in log length. For each
`task_delegation` draft, insert `(task_id, parent_task_ids)`. For each
acceptance draft with `meta.rollback_to == task_id`, set
`assignee = author`.

### 2.2 Incremental Update

On each appended draft, update the index in O(1) amortized. No
backward scanning is required during steady-state operation.

### 2.3 Validation Rule

For any `task_delegation` draft D with `ext.kimi.task_delegation.ancestry_chain`
field AC:

```
expected = task_index[task_id_of_D].parent_task_ids
if AC != expected:
  reject(D, reason="ancestry_chain_mismatch")
```

A draft whose submitted chain diverges from the log-reconstructed
chain including omissions, additions, or reordered entries is rejected.

### 2.4 Cycle Detection

If a submitted `ancestry_chain` contains `T.task_id` itself, nemotron
rejects the draft with `reason="delegation_cycle"` before any state
change occurs. Longer cycles are detected by the index lookup because
any cycle implies the submitted chain contains a repeated `task_id`
that the index lookup would also surface.

## 3. Acceptance Handshake (reaffirmed from v0.5.0)

A child agent accepts task T by emitting a draft with
`meta.rollback_to = T.task_id`. Nemotron sets
`task_index[T.task_id].assignee = author` on append.

## 4. task_delegation Schema (v0.5.1, mandatory ancestry_chain)

```json
{
  "ext": {
    "kimi": {
      "task_delegation": {
        "task_id": "<sha256>",
        "assignee": "<agent_id>",
        "deadline_block": <uint64>,
        "input_rollback_to": "<sha256 or null>",
        "ancestry_chain": ["<sha256>", "<sha256>", ...]
      }
    }
  }
}
```

`ancestry_chain` MUST be present and non-empty for any `task_delegation`
draft submitted after v0.5.1 is in effect. Drafts missing the field
are rejected with `reason="missing_ancestry_chain"`.

## 5. Determinism Guarantee

Index lookup is O(1) per draft. The combined cost of deadline check
(O(1) per open task) and ancestry validation (O(1) per draft) is
bounded and proportional to log size, not to draft history depth.
