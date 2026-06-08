# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel reference implementation** -- `reference/babel/` with BSL parser, validator, handoff write/query, companion CLI.

## Stage Pipeline (Babel v0.10.3)

The Babel v0.10.3 cycle implements a deterministic, conflict-free, multi-agent handoff protocol on top of the Babel Source Language (BSL). Stages are delivered as single-file rounds to avoid anti-timeout failures documented on `pair_b_finalize` (8+ TimeoutError entries when multi-file code/spec/test delivery attempted).

### Completed Stages

| Stage | Artifact | Status |
|-------|----------|--------|
| 4c.2e | BLOCK_TYPES update | Committed |
| 4c.2f | BABEL_VERSION update | Committed |
| 6e | Section 5.2 JSON Schema Spec | Committed |
| 6f | BISC integrity doc skeleton | Committed |
| 7c | HANDOFF_SCHEMA draft | Committed |
| 9a | 9-key HANDOFF_SCHEMA (path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note) | Committed |
| 9b | Intent block schema | Committed |
| 10a | BISC contract surface | Committed |
| 10b | BSL validator extra-keys REJECT policy | Committed |
| 11a | Pre-write gate (9-key validation) | Committed |
| 11a2 | Pre-write gate (refined) | Committed |
| 11b | BSL grammar manifest (block types) | Committed |
| 11d | BSL grammar manifest (header validation) | Committed |
| 11e | BSL validation surface | Committed |
| 11f | Doc sweep (lint CLI, grammar manifest, conformance test) | Committed |
| 12a | BISC spec patch (Sections 5.3-5.5) | Approved, queued as next single-file spec round |
| 12b | Sidecar lock + atomic append (fcntl.flock LOCK_EX, generation counter) | Approved (round 3), deferred until 12a commits |
| 12c | Concurrent-append test | Deferred until 12b commits |
| 13 | Read-query plan (select_handoffs + MappingProxyType + HandoffView) | Committed |
| 13b | Read-query conformance test (parametric FIXTURE_V0103 + 7 tests) | Approved (round 8), queued as parallel next single-file test round |

### Stage 12a+13b Round 8 Audit -- signoff=true

DeepSeek audited Nemotron's refined round 8 plan and verified all `required_changes` are atomized under 200 chars and complete. No truncation, no guessing required.

**12a BISC spec patch (autonomy-output/babel-bisc-integrity-v0.10.2.md):**
- Prepend `Effective v0.10.3` version note after file header (preserves v0.10.2 filename and pre-commit hooks).
- Section 5.3 Grammar Manifest: header regex `^#\[block:(handoff|intent|meta)-[a-z0-9-]+\]$` matching BSL `#[block:<type>-<id>]` syntax. Allowed block types: handoff, intent, meta. Required key sets:
  - 9 handoff keys: path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note
  - 3 intent keys: path, summary, agent_id
  - 3 meta keys: title, version, generation
- Section 5.4 Lint CLI Contract: stdout JSON `{"valid": true}` exit 0 on success; stderr JSON exit 6 on BabelParseError (path, line, code), OSError (path, code: "file_error"), Exception (code: "internal_error").
- Section 5.5 Multi-Agent Append Contract: serialized `append_handoff` via `fcntl.flock(LOCK_EX)` on unified sidecar lock file (`<path>.babel.lock`) and atomic generation counter in meta block.

**13b test_query.py (reference/tests/test_query.py):**
- Parametric FIXTURE_V0103 builder: constructs `.babel` content at runtime from header string, intent dict, handoff trait tuples, and const_keys dict. Eliminates verbatim multi-line JSON truncation.
- Seven behavioral tests over real AST from `parse_file`:
  1. `test_select_handoffs_ordering` -- asserts `_line` ascending order
  2. `test_select_handoffs_immutability` -- `MappingProxyType` + `TypeError` on mutation
  3. `test_select_handoffs_filter_agent_id` -- agent_id filter
  4. `test_select_handoffs_filter_signoff` -- signoff filter
  5. `test_select_handoffs_combined_filter` -- combined agent_id + signoff intersection
  6. `test_select_handoffs_protocol_version` -- `==1` presence
  7. `test_select_handoffs_empty_result` -- empty result returns empty tuple

### Systemic 7-Round Truncation Failure -- RESOLVED

Rounds 1-6 of the 12a+13b parallel plan hit a 420-char per-item transport cap on verbatim multi-line JSON. Round 7 introduced Kimi's atomized `required_changes` transport (<200 char items per item) and Nemotron's parametric `FIXTURE_V0103` builder. Round 8 is the first round where all `required_changes` survive transport without truncation.

This is a **transport-protocol fix**, not a per-round workaround. All future stages should:
- Keep each `required_changes` item under 200 chars.
- Prefer parametric fixture/schema builders over verbatim multi-line strings.
- Use the single-file-pair (`README.md` + `CHANGELOG.md` only) cadence for `pair_b_finalize`.

### Anti-Timeout Cadence

`pair_b_finalize` ships exactly two files: `README.md` + `CHANGELOG.md`. Code/spec/test files belong in single-file artifact rounds, not in `pair_b_finalize`. This pattern has succeeded in 13+ prior rounds. Any attempt to deliver multi-file code/spec/test artifacts from `pair_b_finalize` has produced 8+ `TimeoutError` failures documented in the notes tail.

### Carry-Over Items

- **Stages 5a/5b**: append_handoff implementation and test patch from v0.10.2 cycle. Not addressed in this round; preserved as carry-over. Round-3 approved 12b plan preserves the 9-key content dict contract.
- **Stage 7b**: BISC section 5 amendment. Subsumed by stage 12a Section 5.3. Close once 12a commits.
- **Stage 12b**: sidecar lock + atomic append. Approved (round 3), deferred until 12a commits (spec-first ordering).
- **Stage 12c**: concurrent-append test. Deferred until 12b commits.

### Approved Architecture (Preserved)

- **9-key HANDOFF_SCHEMA** (stage 9a): path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note.
- **BSL header regex** (stage 11d): `^#\[block:(handoff|intent|meta)-[a-z0-9-]+\]$` matching BSL `#[block:<type>-<id>]` syntax.
- **Extra-keys REJECT policy** (stage 10b): bsl_validator rejects blocks with keys outside the schema.
- **Pre-write gate** (stage 11a2): validates 9-key content dict structure before append.
- **Sidecar lock** (stage 12b r3): unified lock file (`<path>.babel.lock`) with `fcntl.flock(LOCK_EX)`, creation-under-lock with initial meta block (generation=1), atomic temp-file + `os.replace`, generation counter increment, platform guard.
- **Read-query interface** (stage 13): `select_handoffs(ast, *, agent_id=None, signoff=None)` returning `tuple[MappingProxyType, ...]` ordered by ascending `_line`; `HandoffView` TypedDict with underscore-prefixed metadata (`_line`, `_block_id`, `_query_protocol_version=1`); `MappingProxyType` runtime immutability; validated-AST-only contract.
- **Parallel-track decoupling** (Kimi kickoff): 12a BISC amendment and 13b read-query conformance test proceed as independent single-file deliveries. Read-query and write-serialization tracks are architecturally decoupled.

## Next Steps (Queued Single-File Rounds)

1. **Stage 12a** (next single-file spec round, spec-first): patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with Sections 5.3-5.5 as specified above.
2. **Stage 13b** (parallel next single-file test round): author `reference/tests/test_query.py` with parametric `FIXTURE_V0103` builder and seven behavioral tests.
3. **Stage 12b** (after 12a commits): patch `reference/babel/handoff.py` `append_handoff` with sidecar lock + atomic append.
4. **Stage 12c** (after 12b commits): author `reference/tests/test_concurrent_append.py`.
