# Babel Language Integration v0.10.2

**Status:** Normative
**Companion to:** `babel-language-syntax-v0.10.2.md`
**Subsystems:** BISC, BCPR, BWSS, BHOP

## 1. Purpose

This spec maps Babel v0.10.2 block types to the autonomous stack subsystems and defines the `.babel` file lifecycle, the companion `.md` convention, and the handoff protocol. It is the integration point between the language surface (Syntax spec) and the runtime subsystems (BISC integrity, BCPR patch negotiation, BWSS workspace, BHOP override).

## 2. Subsystem Mapping

| Block type  | Subsystem          | Trigger                                    |
|-------------|--------------------|--------------------------------------------|
| `#[intent]` | BISC integrity     | pre-commit hook, CDR admission             |
| `#[spec]`   | BWSS workspace     | workspace validation, review              |
| `#[test]`   | BWSS workspace     | workspace validation, review              |
| `#[impl]`   | BWSS workspace     | build, deploy, human sign                 |
| `#[handoff]`| BCPR session log   | agent-to-agent transition                 |

The mapping is exclusive: each block type maps to exactly one subsystem. `#[spec]`, `#[test]`, and `#[impl]` all live under BWSS because BWSS is the unit of human review and seal; the block-type distinction is preserved inside the workspace for tooling.

## 3. File Lifecycle

```
draft   -- add spec/test/impl --> review
review  -- add impl, human seal --> ready
ready   -- human sign, CDR lock  --> sealed
sealed  -- version bump          --> frozen
frozen  -- amend chain           --> sealed (new version)
```

- **draft**: only `#[intent]` present; intent is validated by BISC against the intent schema.
- **review**: at least one `#[spec]` and one `#[test]` present; BWSS workspace validates structure.
- **ready**: at least one `#[impl]` present; ready for human sign via BHOP override.
- **sealed**: human override recorded; BISC CDR entry created with `canonical_sha256` of the body section.
- **frozen**: CDR entry locked; amendments create a new sealed version with a new `#[intent]` block.

The lifecycle is monotonic in the forward direction. Backward transitions require a new file or an amendment chain; they are not permitted in place.

## 4. Companion `.md` Convention

Each `.babel` file may have a sibling `.md` file with the same basename:

```
foo.babel
foo.md
```

The `.md` file is human-authored prose; the parser does not read or validate it. Tooling pairs files by basename for editor linking, PR descriptions, and review context. The companion is not part of `canonical_sha256` and is not represented in BCPR virtual JSON.

This convention externalizes human prose from `.babel` machine-format files, so a `#[spec]` block can stay terse and canonical while the `.md` companion carries rationale, tradeoffs, and diagrams.

## 5. Handoff Protocol

Agents append `#[handoff]` blocks in chronological order. The active handoff is the last `#[handoff]` block in the file. Required JSON fields:

- `next_owner` (string, kebab-case agent id)
- `signoff` (boolean)
- `blocking_issues` (array of strings)
- `required_changes` (array of strings)
- `summary` (string)
- `memory_note` (string)

Handoff blocks are excluded from `canonical_sha256` and from the BCPR virtual JSON representation. BISC validates handoff blocks are well-formed JSON but does not enforce field semantics; BCPR does not see handoff blocks at all.

Ordinal IDs (`handoff-1`, `handoff-2`, ...) are assigned by the handoff module at append time, not by the authoring agent. The parser extracts the active handoff by selecting the last `#[handoff]` block in source order; rewriting the file in any other order is a contract violation.

## Contract Bootstrap Appendix

This appendix maps the contract-first bootstrap API surface (v0.10.2 stage 1a shipped, stages 2a/2b pending) to BWSS lifecycle states and handoff protocol steps. All function bodies in shipped and pending modules raise `NotImplementedError` until the corresponding logic cycle ships. The appendix is normative for stage sequencing and audit; it is not a substitute for parser implementation.

### A.1 API Surface

| Function                                                                                  | Module                       | Stage      | Body status            |
|-------------------------------------------------------------------------------------------|------------------------------|------------|------------------------|
| `parse_file(path) -> BabelFile`                                                           | `reference.babel.bsl_parser` | 1a shipped | raises NotImplementedError |
| `write_file(babel_file, path) -> None`                                                    | `reference.babel.bsl_parser` | 1a shipped | raises NotImplementedError |
| `to_virtual_json(babel_file) -> dict`                                                     | `reference.babel.bsl_parser` | 1a shipped | raises NotImplementedError |
| `companion_path(babel_path) -> Optional[Path]`                                            | `reference.babel.bsl_parser` | 1a shipped | raises NotImplementedError |
| `append_handoff(path, next_owner, signoff, blocking_issues, required_changes, summary, memory_note) -> None` | `reference.babel.handoff`    | 2a pending | raises NotImplementedError |
| `resolve_companion(babel_path) -> Optional[Path]`                                         | `reference.babel.companion`  | 2b pending | raises NotImplementedError |

Stages 1a/1b are signed off. Stages 2a/2b are scheduled as separate single-file finalize rounds. Stage 3a is the handoff contract test mirroring the 1b pattern. Stage 3b is the BISC integrity amendment covering the parser error taxonomy.

### A.2 Mapping to BWSS Lifecycle States

| Lifecycle state | `parse_file` | `write_file` | `to_virtual_json` | `companion_path` | `append_handoff`        | `resolve_companion` |
|-----------------|--------------|--------------|-------------------|------------------|-------------------------|---------------------|
| `draft`         | not yet      | yes          | no                | yes              | no                      | yes                 |
| `review`        | yes          | yes          | yes               | yes              | no                      | yes                 |
| `ready`         | yes          | no           | yes               | yes              | yes                     | yes                 |
| `sealed`        | yes          | no           | yes               | yes              | yes                     | yes                 |
| `frozen`        | yes          | no           | yes               | yes              | no (amend path required) | yes                 |

Notes:

- `write_file` is only valid in `draft` and `review`. Later states are append-only (`sealed`, `frozen`) or immutable in place; the only path to a new write after `review` is the amendment chain that opens a new version.
- `append_handoff` is only valid in `ready` and `sealed`. In `draft` and `review` the file is still being authored and the BWSS workspace absorbs handoff intent directly. In `frozen` the file is CDR-locked and any new handoff must enter the amendment chain.
- `companion_path` and `resolve_companion` are read-only and valid in every state. They locate the `.md` sibling for editor linking and do not mutate the file.
- `parse_file` is valid in every state once the file exists; BISC CDR admission requires it before any further subsystem runs.
- `to_virtual_json` is required once the file is in `review`. BCPR patch negotiation is post-spec/test, so `draft` files do not have a virtual representation.

### A.3 Mapping to Handoff Protocol Steps

The handoff protocol in section 5 is implemented by these five ordered steps. Each step names the API functions that participate.

1. **Read current state.** `parse_file(path)` loads the file from disk. The last `#[handoff]` block in the returned `BabelFile.handoffs` list is the active handoff. This step is required at every transition.
2. **Extract handoff history.** `to_virtual_json(babel_file)` produces the BCPR virtual representation. Handoff blocks are excluded by design, so this step yields the body view used for conflict detection; the handoff list is read directly from `BabelFile.handoffs`.
3. **Locate companion prose.** `companion_path(babel_path)` and `resolve_companion(babel_path)` find the `.md` sibling. Both must agree on the resolved path; disagreement is a contract violation surfaced as `BabelParseError(malformed_header)` in the shipped skeleton, with the error code to be refined in the companion module's logic cycle.
4. **Append new handoff.** `append_handoff(path, next_owner, signoff, blocking_issues, required_changes, summary, memory_note)` writes a new `#[handoff]` block. The function assigns the next ordinal `handoff-{n}`, guards idempotency by content hash, and persists via atomic `tempfile` + `rename` so a partial write cannot leave the file in a torn state.
5. **Persist.** `write_file(babel_file, path)` is called only when the file is in `draft` or `review`. In `ready` and `sealed` the handoff append is the persistence step; `write_file` is not invoked. In `frozen` neither `write_file` nor `append_handoff` is called directly; persistence goes through the BISC amendment chain.

### A.4 Stub Status and Frozen Surface

All six functions listed in A.1 raise `NotImplementedError` on call. The following surface is shipped and frozen as of stage 1a and is not subject to revision under v0.10.2 bootstrap rules:

- Dataclasses: `BabelBlock` (frozen; fields `type`, `id`, `version`, `content`, `line_number`) and `BabelFile` (fields `version`, `body`, `handoffs`, `source_path`).
- Error taxonomy: `BabelParseError` with stable string codes `duplicate_id`, `version_mismatch`, `malformed_header`, `invalid_intent_json`, `missing_intent`. Codes map to BISC exit code 6.
- Module constants: `BABEL_VERSION = '0.10.2'`, `BLOCK_TYPES`, `BODY_TYPES`, `HANDOFF_TYPE`, `TYPE_ENUM_RANK`.

Logic cycles for `parse_file`, `write_file`, `to_virtual_json`, `companion_path` are scheduled for v0.10.3 cycle 2. Logic cycles for `append_handoff` and `resolve_companion` are scheduled for v0.10.3 cycle 3. No logic cycle may revise the frozen surface; revisions require a v0.10.3 version bump.

### A.5 Contract Test Coverage

Stage 1b ships `reference/tests/test_bsl_parser_contract.py`, verifying the four shipped parser functions (module constants, dataclass shape, error codes, function signatures, and `NotImplementedError` raises on call). Stage 3a will ship `reference/tests/test_handoff_contract.py` mirroring this pattern for `append_handoff`. Stage 1c is spec-only and ships no test file.

Behavioral tests (parsing golden fixtures, handoff ordinal increment, idempotency guard, atomic write crash safety, BCPR conflict detection) are deferred to a post-logic cycle after v0.10.3 cycle 2 and 3 land. The contract tests at stages 1b and 3a are sufficient to lock the API surface during bootstrap and prevent regressions while logic cycles are in flight.
