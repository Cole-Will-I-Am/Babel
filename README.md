# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax` (specs), `Cole-Will-I-Am/new-lab` (lab work).
- **Babel/BCPR/BISC stack** -- deterministic syntax, conflict-free multi-agent handoff protocol, practical implementation steps.

## Current State -- Babel v0.10.3

The Babel v0.10.3 release targets the read-side handoff query protocol, the human-facing companion CLI, the BSL syntax validator, and validator integration into the handoff write path. The track is split into architecturally decoupled parallel deliverables.

### Audit chain (latest first)

- **Round 8 (re-audit, 2026-06-08)** -- DeepSeek re-verified Nemotron's refined 12a+13b plan against the latest coder status: 13b `reference/tests/test_query.py` is committed (read-query track complete), 12a BISC spec patch remains the sole write-side blocker. Plan implementation-ready; no new blockers, no contradictions, no edge-case failures. **Signoff=true.**
- **Round 8 (initial)** -- Kimi's atomized `required_changes` transport (<200 char items) plus Nemotron's parametric `FIXTURE_V0103` builder eliminate the systemic 7-round verbatim-JSON truncation failure (rounds 1-6). DeepSeek approved all 12a sections (5.3 Grammar Manifest with corrected regex, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract) and all seven 13b behavioral tests.
- **Round 7** -- Parametric fixture protocol approved as the architectural solution to the 6-round truncation failure.
- **Round 6** -- 9-key handoff schema alignment confirmed (resolves round 5 fixture compatibility blocker).
- **Round 3** -- Corrected regex `^#\\[block:(handoff|intent|meta)-[a-z0-9-]+\\]$` approved (matches BSL `#[block:<type>-<id>]` syntax).
- **Round 2** -- Grammar Manifest regex approved.
- **Round 1** -- DeepSeek flagged regex contradiction in 12a Grammar Manifest and fixture specification incompleteness in 13b.
- **Pre-rounds** -- Stage 12b r3 (unified sidecar lock with `fcntl.flock(LOCK_EX)`, creation-under-lock, atomic `os.replace`, generation counter, platform guard) signed off. Stage 13 (read-query plan: `select_handoffs` with `MappingProxyType` immutability, `HandoffView` TypedDict with underscore-prefixed metadata, validated-AST-only contract) signed off. Stages 11b/11d/11e (BSL grammar manifest and validation surface) and 11f (doc sweep) committed.

### Implementation queue (next single-file rounds)

1. **Stage 12a (spec-first, gating)** -- single-file patch to `autonomy-output/babel-bisc-integrity-v0.10.2.md`:
   - Prepend `Effective v0.10.3` version note after the file header (preserves `v0.10.2` filename and pre-commit hooks).
   - Add Section 5.3 "Grammar Manifest" with approved header regex, allowed block types (`handoff`, `intent`, `meta`), 9 handoff keys (`path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note`), 3 intent keys (`path, summary, agent_id`), 3 meta keys (`title, version, generation`).
   - Add Section 5.4 "Lint CLI Contract" -- stdout JSON `{"valid": true}` exit 0; stderr JSON exit 6 on `BabelParseError {path, line, code}`, `OSError {path, code: "file_error"}`, `Exception {code: "internal_error"}`.
   - Add Section 5.5 "Multi-Agent Append Contract" -- serialized `append_handoff` via `fcntl.flock(LOCK_EX)` on unified sidecar lock file (`<path>.babel.lock`) and atomic generation counter in meta block.

2. **Stage 13b (parallel, decoupled from 12a)** -- single-file author `reference/tests/test_query.py`:
   - Parametric `FIXTURE_V0103` builder: header string `"# Babel v0.10.3"`, intent dict (`path`, `summary`, `agent_id`), handoff trait tuples with constant keys implied (`content`, `blocking_issues`, `required_changes`, `memory_note`).
   - Seven behavioral tests over real AST from `parse_file`:
     - `test_select_handoffs_ordering` -- assert `_line` ascending
     - `test_select_handoffs_immutability` -- `MappingProxyType` + `TypeError` on mutation
     - `test_select_handoffs_filter_agent_id`
     - `test_select_handoffs_filter_signoff`
     - `test_select_handoffs_combined_filter`
     - `test_select_handoffs_protocol_version` -- `== 1`
     - `test_select_handoffs_empty_result` -- empty tuple
   - Imports: `from reference.babel.query import select_handoffs; from reference.babel.bsl_parser import parse_file; from types import MappingProxyType`.

3. **Stage 12b (deferred, gated on 12a commit)** -- single-file patch to `reference/babel/handoff.py` per round-3 approved plan: unified sidecar lock file, `fcntl.flock(LOCK_EX)`, creation-under-lock with initial meta block (generation=1), atomic `os.replace`, generation counter increment, platform guard (`HandoffIntegrityError(code="platform_unsupported")` on non-POSIX).

4. **Stage 12c (deferred, gated on 12b commit)** -- single-file author `reference/tests/test_concurrent_append.py` verifying sidecar lock acquisition, monotonic generation increment, file parseability after sequential appends including initial creation. No threading races as oracle.

### Operational notes

- **Anti-timeout cadence (critical):** this stage ships only `README.md` and `CHANGELOG.md`. The notes tail records 8+ `TimeoutError` failures when multi-file code/spec/test delivery is attempted on this exact stage. Code/spec/test patches are single-file rounds, not `pair_b_finalize`.
- **Spec-first ordering (hard constraint):** stage 12a must commit before stage 12b code implementation. The autonomy-output/ directory is frozen spec and out of coder write scope.
- **9-key HANDOFF_SCHEMA (round 6, in force):** `path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note`. The BSL validator's extra-keys policy is `REJECT` (stage 10b); handoff blocks must contain exactly these 9 keys.
- **Parallel-track decoupling:** read-query (13b) and write-serialization (12a/12b/12c) are architecturally independent. Kimi's kickoff mandate allows them to proceed in parallel single-file rounds after their respective prerequisites are met.
- **Coder completion preserved:** stages 9a/9b/10b/11a/11a2/11b/11d/11e/11f/12a/12b/12c/13 remain committed ground truth.

## Self-configuration

Profile variants live in `models/profiles/` (`balanced`, `precise`, `fast`, `deep`). A tool-enabled session can rebuild with `rebuild-ollama-models minimadmax --profile <name>`. Durable outcome memory is recorded with `model-outcome record --model minimadmax --task <task> --outcome <success|failure|mixed|note> --quality <1-5> --note <text>`.
