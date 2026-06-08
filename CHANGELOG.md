# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, and grammar manifest formalization.

### Round 8 Audit (2026-06-08) -- Stage 12a+13b Parallel Plan, signoff=true

**Outcome:** DeepSeek signed off Nemotron's refined round 8 plan. All `required_changes` are atomized under 200 chars and complete. No truncation, no guessing required. The plan is implementation-ready.

**Resolved blockers (rounds 1-7):**
- Round 1+2: 12a Grammar Manifest header regex corrected from `^/blocks/(handoff|intent|meta):[a-z0-9-]+$` to `^#\[block:(handoff|intent|meta)-[a-z0-9-]+\]$` (matches BSL `#[block:<type>-<id>]` syntax).
- Round 5: 13b fixture handoff blocks no longer contain a `version` key (would have caused BabelParseError on extra-keys REJECT policy).
- Round 6: 9-key HANDOFF_SCHEMA alignment confirmed across spec and fixture.
- Round 7: Parametric fixture protocol replaces verbatim multi-line JSON in 13b.
- Round 8: All `required_changes` items atomized under 200 chars; no truncation in transport.

**Systemic 7-round truncation failure:** RESOLVED. Kimi's atomized `required_changes` transport (<200 char items per item) plus Nemotron's parametric `FIXTURE_V0103` builder eliminate the verbatim multi-line JSON that hit the 420-char per-item transport cap in rounds 1-6. This is a transport-protocol fix, not a per-round workaround, and applies to all future stages.

**Approved artifacts:**
- 12a BISC spec patch (Sections 5.3-5.5): Grammar Manifest with corrected regex, 9+3+3 key enumerations, Lint CLI Contract (stdout JSON exit 0, stderr JSON exit 6 with error types), Multi-Agent Append Contract (fcntl.flock LOCK_EX on sidecar lock file, atomic temp-file + os.replace, generation counter).
- 13b test_query.py: parametric FIXTURE_V0103 builder (header, intent dict, handoff trait tuples, const_keys) and seven behavioral tests over real AST from `parse_file`.

**Implementation queue:**
1. Stage 12a (next single-file spec round, spec-first).
2. Stage 13b (parallel next single-file test round).
3. Stage 12b (after 12a commits, sidecar lock + atomic append).
4. Stage 12c (after 12b commits, concurrent-append test).

### Round 7 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's parametric fixture protocol (solves 6-round truncation failure) but flagged two specification-completeness blockers: 12a Section 5.3 truncated at `meta=` (missing 3 meta keys: title, version, generation); 13b test list truncated at `te` (missing 7th test: `test_select_handoffs_empty_result`). Resolved in round 8.

### Round 6 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's 9-key handoff schema alignment (resolves round 5 compatibility blocker) but flagged two specification-completeness blockers: 12a Section 5.3 truncated at `required_chang` (missing key enumerations); 13b fixture truncated at `lines 8-10 handoff` (missing handoff-b/c JSON). Resolved in round 8.

### Round 5 Audit (2026-06-08) -- TimeoutError

Model call failure. Continued with fail-safe path; signoff=false.

### Round 4 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's corrected regex (matches BSL syntax) but flagged fixture JSON content missing from 13b `required_changes`. Resolved in round 8.

### Round 3 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's corrected regex but flagged 13b fixture handoff block contains `version` key not in HANDOFF_SCHEMA and 13b fixture specification truncated mid-line. Resolved in round 8.

### Round 2 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's 12a+13b parallel plan but flagged two blockers: 12a Grammar Manifest header regex does not match BSL syntax, 13b fixture specification incomplete. Round 1+2 regex blockers resolved in round 3.

### Round 1 Audit (2026-06-08) -- signoff=false

DeepSeek approved Nemotron's seven-test scope for 13b but flagged fixture validity blocker: missing file header and intent block in `.babel` fixture would cause `parse_file` to raise BabelParseError. Resolved by parametric fixture protocol in round 7.

### Round 0 Audit (2026-06-08) -- Stage 13 Read-Query Plan, signoff=true

DeepSeek signed off Nemotron's implementation-ready stage 13 draft: `select_handoffs(ast, *, agent_id=None, signoff=None)` returning `tuple[MappingProxyType, ...]` ordered by ascending `_line`; `HandoffView` TypedDict with underscore-prefixed metadata; private `_filter_by_agent_id` and `_filter_by_signoff_status` helpers; `MappingProxyType` runtime immutability; validated-AST-only contract. `reference/babel/query.py` committed.

### Round 0 Audit (2026-06-08) -- Stage 12b Sidecar Lock, Round 3, signoff=true

DeepSeek signed off Nemotron's refined plan: unified sidecar lock file (`<path>.babel.lock`) with `fcntl.flock(LOCK_EX)` resolves the round-2 creation race by serializing both initial `.babel` creation and subsequent appends under the same lock. Creation-under-lock protocol approved: acquire sidecar lock, if target absent create with initial meta block (generation=1) via temp-file + `os.replace`, if present read-modify-write under lock with generation counter increment. Deferred until stage 12a BISC patch commits (spec-first ordering).

### Round 0 Audit (2026-06-08) -- Stage 12b Sidecar Lock, Round 2, signoff=false

DeepSeek approved Nemotron's lock-based mechanism (`fcntl.flock` + generation counter + atomic replace) for existing files, but flagged a new blocker: no conflict-free creation protocol for new `.babel` files. Must add O_CREAT|O_EXCL+rename, sidecar lock file, or dedicated init function. Resolved in round 3.

### Round 0 Audit (2026-06-08) -- Stage 12b Sidecar Lock, Round 1, signoff=false

DeepSeek rejected Nemotron's plan: generation counter + atomic replace is optimistic locking, not conflict-free, allows lost updates. Must adopt `fcntl.flock` or accept non-conflict-free semantics. Resolved in round 2.

## v0.10.2 -- BSL Parser, Validator, Append Protocol (Released)

Initial BSL parser, validator, and append protocol. Stages 4c.2e, 4c.2f, 6e, 6f, 7c, 9a, 9b, 10a, 10b, 11a, 11a2, 11b, 11d, 11e, 11f all committed.

## v0.10.1 -- Babel Source Language Spec (Released)

Initial BSL specification, block types, and HANDOFF_SCHEMA draft.

## v0.10.0 -- Babel Stack Initialization (Released)

Initial repository structure, MiniMadMax agent identity, and stage pipeline scaffold.
