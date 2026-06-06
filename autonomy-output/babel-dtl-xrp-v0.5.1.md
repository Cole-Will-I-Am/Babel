# Babel DTL/XRP Amendment v0.5.1

## Status
Additive amendment over frozen Babel v0.5.0 DTL and XRP. Implements
remediation for DeepSeek v0.5.0 audit gap 3 (XRP crash-failure
detection). Supports gap 5 (isolated agent liveness) by providing
cascade ordering that interacts deterministically with the ASMC
v0.5.1 self-rollback path. No frozen field is mutated.

## 1. Crash-Failure Proxy Semantics

A peer agent P may emit a DTL rollback draft on behalf of a stalled
agent S if and only if the draft contains:

```json
{
  "ext": {
    "kimi": {
      "stalled_agent_failed": true,
      "proxy_proof": {
        "dependent_agent": "<P.agent_id>",
        "dependent_last_draft_hash": "<sha256 of P's last draft>",
        "referenced_stalled_hash": "<S's last valid state hash>"
      }
    }
  },
  "meta": {
    "rollback_to": "<S's last valid state hash>"
  }
}
```

Nemotron treats the presence of `ext.kimi.stalled_agent_failed = true`
as equivalent to S having emitted `ext.kimi.state = "failed"` for the
purposes of XRP cascade detection.

## 2. Authorized Peer Eligibility

A peer P is eligible to emit a proxy rollback for stalled agent S only
if both conditions hold:

1. `dependent_last_draft_hash` exists in the handoff log.
2. The document at `dependent_last_draft_hash` has
   `meta.rollback_to === referenced_stalled_hash`.

This requires P to have had a prior dependency on S. A malicious peer
that never referenced S cannot fabricate a proxy because it cannot
produce a `dependent_last_draft_hash` whose `meta.rollback_to` matches
`referenced_stalled_hash`. The dependency proof is structural and
cannot be forged without control of an already-committed draft.

### 2.1 Validation Pseudocode

```python
def validate_proxy(draft, log):
    if not draft.ext.kimi.get("stalled_agent_failed"):
        return ACCEPT_NORMAL
    proof = draft.ext.kimi.proxy_proof
    dep_doc = log.get(proof.dependent_last_draft_hash)
    if dep_doc is None:
        return REJECT("dependent_hash_not_in_log")
    if dep_doc.meta.rollback_to != proof.referenced_stalled_hash:
        return REJECT("rollback_to_mismatch")
    return ACCEPT_PROXY
```

## 3. Cascade Ordering

When multiple rollback drafts target the same failed state hash H,
including both XRP rollback drafts and isolated-agent self-rollback
drafts (ASMC v0.5.1), they are ordered by canonical SHA-256 hash
(lexicographic sort). The first processed wins; subsequent drafts
targeting H are rejected because the agent is no longer in `failed`
state after the first rollback transitions it to `idle`.

## 4. DTL Rollback Draft Format (v0.5.1 superset)

A DTL rollback draft D satisfies:

- `D.meta.rollback_to = S's last valid state hash`.
- If S is detected crashed: `D.ext.kimi.stalled_agent_failed = true`
  plus `D.ext.kimi.proxy_proof` per section 1.
- If S is detected as having emitted `failed` state normally: no proxy
  fields required; nemotron observes `ext.kimi.state = "failed"` in
  S's own log entry and triggers XRP per frozen v0.5.0.

## 5. Termination Guarantee

Cascade depth is bounded by the number of distinct agents that ever
referenced the failed state. CDR hash ordering provides total order
over simultaneous rollback drafts. Failed state is terminal; the
`rollback_to` DAG property from v0.5.0 prevents circular rollback
chains. Adding the proxy path does not change the DAG property because
each proxy is itself a single rollback draft referencing a single
prior state hash.

## 6. Determinism Guarantee

Proxy validation is a pure function of the draft content and the
handoff log. The full check is byte-deterministic and O(1) per draft
(two independent hash lookups, no iteration over cascade depth at
validation time).
