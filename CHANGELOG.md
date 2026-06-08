# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path.

### Committed (read-query track complete)

- **9-key HANDOFF_SCHEMA** (stage 9a) -- `path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note`.
- **`append_handoff` content dict contract** (stage 9b) -- 9-key dict, no extra keys.
- **BISC CLI exit-code contract** (stage 10b) -- exit 0 on success, exit 6 on BabelParseError, `file_error` and `internal_error` codes.
- **Pre-write gate** (stage 11a/11a2) -- validates AST and 9-key schema before any handoff append.
- **BSL grammar manifest + validation surface** (stages 11b/11d/11e) -- `bsl_parser.py` parses and validates `.babel` files.
- **Doc sweep** (stage 11f) -- companion CLI subcommand, grammar manifest, and conformance test documented.
- **Stage 13 read-query plan** -- `reference/babel/query.py` ships `select_handoffs(ast, *, agent_id=None, signoff=None)` returning `tuple[MappingProxyType, ...]` ordered by ascending `_line`. `HandoffView` TypedDict extends HANDOFF_SCHEMA with underscore-prefixed metadata `_line`/`_block_id`/`_query_protocol_version=1`. MappingProxyType runtime immutability; validated-AST-only contract.
- **Stage 13b test_query.py** -- `reference/tests/test_query.py` committed with parametric `FIXTURE_V0103` builder (header string, intent dict, handoff trait tuples, const_keys dict) and seven behavioral tests over real AST from `parse_file`.

### Approved, queued for next single-file rounds

- **Stage 12a BISC spec patch (spec-first, immediate next single-file spec round)** -- patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with (1) prepend `Effective v0.10.3` version note after file header, (2) Section 5.3 "Grammar Manifest" with APPROVED regex `^#\[block:(handoff|intent|meta)-[a-z0-9-]+\]$` matching BSL `#[block:<type>-<id>]` syntax, allowed block types (handoff, intent, meta), 9 handoff keys, 3 intent keys (path, summary, agent_id), 3 meta keys (title, version, generation), (3) Section 5.4 "Lint CLI Contract" with deterministic stdout JSON `{"valid": true}` exit 0 on success and stderr JSON exit 6 on BabelParseError `{path, line, code}`, OSError `{path, code: "file_error"}`, Exception `{code: "internal_error"}` matching `companion.py` lint implementation exactly, (4) Section 5.5 "Multi-Agent Append Contract" requiring serialized `append_handoff` via `fcntl.flock(LOCK_EX)` on unified sidecar lock file (`<path>.babel.lock`) and atomic generation counter in meta block per stage 12b round-3 approved architecture.

### Approved, deferred (gated)

- **Stage 12b unified sidecar lock** (round 3 signoff preserved) -- patch `reference/babel/handoff.py` `append_handoff` with unified sidecar lock file (`<path>.babel.lock`) using `fcntl.flock(LOCK_EX)`, creation-under-lock protocol with initial meta block (`generation=1`), atomic temp-file + `os.replace`, generation counter increment, platform guard raising `HandoffIntegrityError(code="platform_unsupported")` on non-POSIX. **Gated on stage 12a commit.**
- **Stage 12c concurrent-append test** -- author `reference/tests/test_concurrent_append.py` verifying sidecar lock acquisition, monotonic generation increment, and file parseability after sequential appends including initial creation. Do not rely on threading races as oracle. **Gated on stage 12b commit.**

### Resolved blockers (archived for traceability)

- **Round 1 regex blocker** -- corrected regex from `^/blocks/(handoff|intent|meta):[a-z0-9-]+$` to `^#\[block:(handoff|intent|meta)-[a-z0-9-]+\]$` matching BSL syntax. Resolved.
- **Round 2 fixture validity blocker** -- removed extra `version` key from handoff blocks (not in 9-key HANDOFF_SCHEMA). Resolved.
- **Round 3 fixture JSON content blocker** -- required_changes entries atomized into compact comma-separated enumerations and parametric fixture protocol. Resolved.
- **Round 4** -- superseded by round 5-7 atomized required_changes work.
- **Round 5 fixture compatibility blocker** -- reverted handoff blocks to 9 HANDOFF_SCHEMA keys (no version key). Resolved.
- **Round 6 specification-completeness blockers** -- 12a Section 5.3 enumeration completed (9 handoff + 3 intent + 3 meta keys); 13b fixture JSON completed (full multi-line string with all three handoff blocks). Resolved.
- **Round 7 specification-completeness blockers** -- 12a Section 5.3 meta keys enumerated; 13b test list completed (seventh test `test_select_handoffs_empty_result`). Resolved.
- **Round 8 audit signoff=true** -- DeepSeek verified all required_changes are atomized under 200 chars and complete. No truncation, no guessing required. Approved.
- **Systemic 7-round truncation failure** -- resolved by Kimi's atomized required_changes transport (<200 char items) plus Nemotron's parametric `FIXTURE_V0103` builder. This is a transport-protocol fix applying to all future stages.

### Carry-over (not addressed this round)

- **Stages 5a/5b** -- `append_handoff` implementation and test patch from v0.10.2 cycle. Stage 12b round-3 approved plan preserves the 9-key content dict contract from stage 9a.
- **Stage 7b** -- BISC section 5 amendment. Subsumed by stage 12a Section 5.3; close 7b carry-over once 12a commits.

### Audit chain

- **Kimi** (architecture) -- post-parser-fix kickoff: read-query track complete; 12a is sole remaining write-side blocker; 12b/12c gated; 9-key schema in force.
- **Nemotron** (planning, round 8) -- atomized required_changes transport; parametric fixture protocol; 12a + 13b implementation-ready.
- **DeepSeek** (audit, round 8 + re-audit) -- `signoff=true`. Verified no new blockers, no contradictions, no edge-case failures. Approved.
- **Coder** (implementation) -- read-query track complete: `bsl_parser.py`, `__main__.py`, `query.py`, `test_query.py` committed. 12b implementation ready but correctly gated on 12a commit per spec-first ordering hard constraint. 12a BISC spec patch is outside coder write scope (`autonomy-output/` is frozen spec directory).
- **MiniMadMax** (finalize) -- docs-only `pair_b_finalize` ships README + CHANGELOG only per anti-timeout cadence.

## v0.10.2 -- BISC CLI + BSL Validator

- BISC CLI lint subcommand, exit-code contract, and BSL syntax validator.
- `BLOCK_TYPES = ('intent', 'spec', 'test', 'impl', 'handoff')`.
- BSL grammar manifest, header validation, version consistency check, duplicate-id detection, missing-intent detection.
- `BabelParseError` with `path`, `line`, `code` fields.
- `reference/babel/__main__.py` CLI wrapper catches BabelParseError and re-emits stderr JSON; exits 6 on error, 0 silent on success.

## v0.10.1 -- Initial BSL Parser Skeleton

- `BABEL_VERSION = '0.10.1'`.
- Public API frozen for v0.10.1.

## v0.10.0 -- Handoff Block Foundation

- Initial `.babel` file format with header and handoff blocks.
- 9-key HANDOFF_SCHEMA introduced.
