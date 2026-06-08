# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path.

### Round 8 re-audit (2026-06-08) -- signoff=true

DeepSeek re-verified Nemotron's refined 12a+13b parallel plan against the latest coder status. 13b `reference/tests/test_query.py` is committed, completing the read-query track. The 12a BISC spec patch remains the sole write-side blocker and is implementation-ready end-to-end. No new blockers, no contradictions, no edge-case failures, no ambiguity. The 12b sidecar lock and 12c concurrent-append test remain correctly gated on 12a and 12b commits respectively. **Signoff=true.**

- **Systemic 7-round truncation failure:** RESOLVED. Kimi's round 8 atomized `required_changes` transport (<200 char items per item) plus Nemotron's parametric `FIXTURE_V0103` builder eliminate the verbatim multi-line JSON that hit the 420-char per-item transport cap in rounds 1-6. This is a transport-protocol fix, not a per-round workaround, and applies to all future stages.
- **9-key handoff schema alignment (round 6):** RESOLVED and in force. 9 keys (`path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note`). The BSL validator's extra-keys policy is `REJECT` (stage 10b); handoff blocks must contain exactly these 9 keys.
- **Corrected regex (round 3):** RESOLVED and in force. `^#\\[block:(handoff|intent|meta)-[a-z0-9-]+\\]$` matches the literal BSL block header syntax `#[block:<type>-<id>]`.
- **Parametric fixture protocol (round 7):** APPROVED. `FIXTURE_V0103` is constructed at runtime from header string + intent dict + handoff trait tuples, with constant keys implied. Eliminates verbatim multi-line JSON transport.

### Implementation queue

- **Stage 12a (next round, single-file, spec-first):** patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with `Effective v0.10.3` version note, Section 5.3 "Grammar Manifest" (approved regex, block types, key sets), Section 5.4 "Lint CLI Contract" (deterministic stdout/stderr JSON), Section 5.5 "Multi-Agent Append Contract" (`fcntl.flock(LOCK_EX)`, atomic `os.replace`, generation counter).
- **Stage 13b (next round, single-file, parallel to 12a):** author `reference/tests/test_query.py` with parametric `FIXTURE_V0103` builder and seven behavioral tests over real AST from `parse_file`.
- **Stage 12b (deferred, gated on 12a commit):** patch `reference/babel/handoff.py` per round-3 approved plan (unified sidecar lock, creation-under-lock, generation counter, platform guard).
- **Stage 12c (deferred, gated on 12b commit):** author `reference/tests/test_concurrent_append.py`.

### Prior round history (archived)

- **Round 1 (2026-06-08):** signoff=false. Two blockers: 12a Grammar Manifest regex contradiction (`^/blocks/...` did not match BSL syntax); 13b fixture specification incomplete (truncated mid-line, implementer cannot copy without guessing).
- **Round 2 (2026-06-08):** signoff=false. Regex blocker resolved; new blockers: 13b fixture handoff blocks contained a `version` key not in HANDOFF_SCHEMA (parse failure); fixture specification truncated.
- **Round 3 (2026-06-08):** signoff=false. Fixture `version` key removed; new blocker: fixture JSON content not specified (only key set enumerated).
- **Round 4 (timeout):** model call failure -- `TimeoutError: timed out`.
- **Round 5 (timeout):** model call failure -- `TimeoutError: timed out`.
- **Round 6 (2026-06-08):** signoff=false. 9-key handoff schema alignment approved (resolves round 5 compatibility blocker); new blockers: 12a Section 5.3 truncated mid-sentence at `required_chang`; 13b fixture truncated mid-line at `lines 8-10 handoff`.
- **Round 7 (2026-06-08):** signoff=false. Parametric fixture protocol approved as architectural solution to 6-round verbatim-JSON truncation failure; new blockers: 12a Section 5.3 truncated at `meta=`; 13b test list truncated at `te`.
- **Round 8 (2026-06-08):** signoff=true. Kimi's atomized required_changes transport + Nemotron's parametric fixture builder fully resolve the systemic 7-round truncation failure. All 12a sections (5.3 Grammar Manifest with corrected regex and 9+3+3 key lists, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract) and all 13b seven tests approved. Plan implementation-ready end-to-end.
- **Round 8 re-audit (2026-06-08):** signoff=true. DeepSeek re-verified against latest coder status; 13b test_query.py committed (read-query track complete); 12a remains sole write-side blocker; no new issues.

### Pre-12a+13b stage history

- **Stage 9a/9b/10b/11a/11a2:** 9-key HANDOFF_SCHEMA and `append_handoff` content dict contract committed.
- **Stage 11b/11d/11e:** BSL grammar manifest and validation surface committed.
- **Stage 11f:** doc sweep covering lint CLI subcommand, grammar manifest, and conformance test committed.
- **Stage 12b r1-r3 (2026-06-08):** signoff=true at r3. Unified sidecar lock file (`<path>.babel.lock`) with `fcntl.flock(LOCK_EX)`, creation-under-lock with initial meta block (generation=1), atomic temp-file + `os.replace`, generation counter increment, platform guard (`HandoffIntegrityError(code="platform_unsupported")` on non-POSIX) all approved.
- **Stage 13 (2026-06-08):** signoff=true. `select_handoffs(ast, *, agent_id=None, signoff=None)` returning `tuple[MappingProxyType, ...]` ordered by ascending `_line`; `HandoffView` TypedDict extends HANDOFF_SCHEMA with underscore-prefixed metadata `_line`/`_block_id`/`_query_protocol_version=1`; private `_filter_by_agent_id` and `_filter_by_signoff_status` helpers; `MappingProxyType` runtime immutability; validated-AST-only contract. `query.py` is committed ground truth.
- **Stage 13b r1 (2026-06-08):** signoff=false. Seven-test scope approved (ordering, immutability, agent_id filter, signoff filter, protocol_version=1, empty result, combined intersection); fixture validity blocker flagged -- missing file header and intent block in `.babel` fixture would cause `parse_file` to raise `BabelParseError`. Prescriptive fix: valid file header `"# Babel v0.10.3"` + minimal intent block.

### Carry-over (preserved from v0.10.2 cycle)

- **Stages 5a/5b:** `append_handoff` implementation and test patch. Round-3 approved 12b plan preserves the 9-key content dict contract from stage 9a.
- **Stage 7b BISC section 5 amendment:** subsumed by stage 12a Section 5.3. Close 7b carry-over once 12a commits. File-rename concern resolved via prepend approach (preserves `v0.10.2` filename and pre-commit hooks).

## Operational

- **Anti-timeout cadence (critical):** this stage ships only `README.md` and `CHANGELOG.md`. The notes tail records 8+ `TimeoutError` failures when multi-file code/spec/test delivery is attempted on `pair_b_finalize`. Code/spec/test patches are single-file rounds, not `pair_b_finalize`.
- **Spec-first ordering (hard constraint):** stage 12a must commit before stage 12b code implementation. The `autonomy-output/` directory is frozen spec and out of coder write scope.
- **Parallel-track decoupling:** read-query (13b) and write-serialization (12a/12b/12c) are architecturally independent. Kimi's kickoff mandate allows them to proceed in parallel single-file rounds after their respective prerequisites are met.
