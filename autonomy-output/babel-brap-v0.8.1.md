# Babel BRAP Amendment v0.8.1

## Status
Additive amendment over frozen Babel v0.1.0-v0.7.0 and v0.8.0 BRAP. Resolves DeepSeek v0.8.1 audit blocking issue 2 (amend cycle unbounded). No frozen field is mutated.

## 1. Amend Decision Lifecycle (Bounded)

A review document with `decision: "amend"` creates a binding review cycle with the following termination guarantees.

### 1.1 Single Amend Bound

For any reviewed document D with canonical hash H, the amend cycle is bounded as follows:
- After the original author emits a revised document D' (with new canonical hash H' and `meta.amend_of` referencing the amend review), the original reviewer MUST issue `approve` or `reject` for D'
- The reviewer MUST NOT issue a second `amend` decision for D'
- This bound applies per review per document; a new review of D' is a fresh review cycle with its own single-amend budget

### 1.2 Three Termination Paths

The amend cycle terminates exclusively via one of:

(a) **Author Revision Path**: Original author emits revised document D' with:
    - `meta.amend_of`: canonical SHA-256 of the amend review document
    - New canonical hash H'
    - Operation continues normal flow; reviewer observes D' and issues approve or reject (no second amend)

(b) **Timeout Failure Proxy**: After 2x DTL timeout_ms elapses without author revision, any peer may emit a failure proxy:
    ```json
    {
      "operation_type": "task_draft",
      "meta": {
        "author": "<peer_agent_id>",
        "rollback_to": "<original_amend_review_hash>"
      },
      "ext": {
        "kimi": {
          "amend_timeout": true,
          "proxy_proof": {
            "dependent_agent": "<original_author_id>",
            "dependent_last_draft_hash": "<last_draft_by_author>",
            "referenced_amend_hash": "<amend_review_hash>"
          }
        }
      }
    }
    ```
    The proxy transitions the task to `failed` state per XRP v0.5.1.

(c) **Reviewer Reject Conversion**: Reviewer converts the amend to a reject by emitting a `spec_rejection` document referencing the amend review. This terminates the amend cycle without requiring author revision.

### 1.3 Concurrent Termination Resolution

If multiple termination attempts target the same amend cycle, CDR hash ordering (lexicographic sort of canonical SHA-256 of the termination documents) determines the winner. The first hash wins; subsequent attempts are rejected by ASMC valid_transition.

## 2. Scoped Reject-to-XRP Mapping (Unchanged from v0.8.1)

Reject decisions trigger XRP cascade ONLY for documents with `operation_type` in {task_delegation, task_draft, task_commit}. Tier-1 validation enforces:
- Task documents require `task_id`, `assignee`, `deadline_block` fields
- Spec artifacts require `spec_version`, `manifest_id` fields
- Mislabeling rejected at validation (exit 1)

Spec artifacts (reject on spec_draft) trigger a spec-revision workflow, not XRP cascade. The reviewer appends a `spec_rejection` document; the original author must append a new `spec_draft` with incremented version.

## 3. Review Document Schema (Unchanged from v0.8.0)

```json
{
  "operation_type": "review",
  "meta": {
    "author": "human" | "kimi" | "<agent_id>",
    "reviewed_hash": "<canonical_sha256_of_reviewed_doc>",
    "decision": "approve" | "reject" | "amend",
    "rationale": "<non-empty string, max 4096 chars>"
  },
  "ext": {
    "human": { "review": true },
    "kimi": { "review": true }
  }
}
```

## 4. Circular Dependency Resolution (Unchanged)

Agents observe reviews in CDR hash order (lexicographic sort of review document canonical SHA-256). First review in order wins for any given `reviewed_hash`. This prevents A-approves-B-approves-A deadlocks.

## 5. Test Vector: Amend Cycle Bound

- Reviewer issues amend for D (hash H) at time T0
- Author emits D' with `meta.amend_of = amend_review_hash` at T1
- Reviewer attempts to issue a second amend for D' at T2
- Tier-1 validation rejects the second amend (exit 1, reason `amend_cycle_exhausted`)
- Reviewer must issue approve or reject for D' to close the cycle
