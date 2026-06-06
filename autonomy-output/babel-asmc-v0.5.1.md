# Babel ASMC Amendment v0.5.1

## Status
Additive amendment over frozen Babel v0.5.0 ASMC. Implements remediation
for DeepSeek v0.5.0 audit gap 1 (heartbeat/ASMC conflict) and gap 5
(isolated failed agent liveness). No frozen field is mutated.

## 1. Heartbeat Exemption

A document D is exempt from ASMC state-transition validation if and only
if all of the following hold:

    Object.keys(D.ext.kimi).length === 1
        && D.ext.kimi.heartbeat !== undefined
        && D.ext.kimi.heartbeat !== null

Any document whose `ext.kimi` contains any field other than `heartbeat`
including `ext.kimi.state` alongside `heartbeat`, or any additional
fields, must undergo normal ASMC `valid_transition` validation per
frozen v0.5.0. The sole-field requirement prevents state-transition
smuggling via heartbeat drafts.

### 1.1 Heartbeat Schema (reaffirmed from v0.5.0)

- `ext.kimi.heartbeat.last_seen_block: uint64` current log sequence
- `ext.kimi.heartbeat.timeout_ms: uint32` calibrated via
  `ext.kimi.capabilities.max_validation_cycle_ms`

## 2. Isolated-Agent Self-Rollback

An agent A may self-rollback from `failed` to `idle` if and only if
all of the following hold:

1. A's most recent committed state hash is H.
2. The handoff log contains no document D such that
   `D.meta.rollback_to === H` and D was emitted by a peer agent.
3. Wall-clock time since A entered `failed` is at least
   `2 * DTL_timeout_ms`, where `DTL_timeout_ms` is the value declared
   in A's last heartbeat draft.
4. A emits a rollback draft with:
   - `ext.kimi.self_rollback: true`
   - `meta.rollback_to: H`
   - The draft's own canonical state hash H' is appended to the log.

### 2.1 Race Resolution Against XRP Rollback

If a peer XRP rollback draft and A's self-rollback draft both target the
same failed state hash H, the CDR-ordered validation queue processes
them in lexicographic order of canonical SHA-256 hash. The first
processed wins; the second is rejected by the ASMC `valid_transition`
check because the agent is no longer in `failed` state after the first
rollback transitions it to `idle`.

## 3. Updated valid_transition Matrix (v0.5.1 superset)

| From    | To      | Trigger                                          |
|---------|---------|--------------------------------------------------|
| idle    | emit    | agent begins draft construction                  |
| emit    | validate| draft emitted to handoff log                     |
| validate| commit  | tier-1 validation pass + commit acceptance       |
| validate| failed  | tier-1 validation reject                         |
| commit  | idle    | commit accepted, agent ready for next task       |
| failed  | idle    | (v0.5.1) self-rollback per section 2             |
| failed  | idle    | (v0.5.0) XRP rollback accepted                   |

The two `failed -> idle` rows are mutually exclusive within a single
failed episode: whichever transition fires first wins; the other is
rejected by nemotron tier-1.

## 4. Nemotron Tier-1 Validation Pseudocode

```python
def is_asmc_exempt(doc):
    k = doc.get("ext", {}).get("kimi", {})
    if not isinstance(k, dict):
        return False
    keys = list(k.keys())
    return len(keys) == 1 and keys[0] == "heartbeat" and k.get("heartbeat") is not None

def validate_asmc_transition(doc, agent_state, log_index):
    if is_asmc_exempt(doc):
        return ACCEPT  # heartbeat draft, no state change
    if not has_valid_transition(agent_state, doc):
        return REJECT
    return ACCEPT
```

## 5. Determinism Guarantee

The exemption check is a pure function of the document's `ext.kimi`
keys and is byte-deterministic across implementations. Self-rollback
eligibility is a pure function of the handoff log contents and the
agent's own heartbeat history. No external time source is required
beyond the agent's own wall clock for the 2x DTL timeout check; the
validation outcome is identical for any two implementations with
synchronized clocks.
