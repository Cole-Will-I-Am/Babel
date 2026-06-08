# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel language stack** -- BSL parser, handoff protocol, companion CLI, BISC integrity spec under `autonomy-output/`.

## Operating Context

- HTTPS git operations through `gh auth git-credential` (preferred over SSH).
- Secrets (tokens, passwords, keys) must never be printed, embedded in commits, copied into prompts, or stored in project files.
- Multi-agent pipeline: Kimi (architect) → Nemotron (planner) → DeepSeek (auditor) → minimadmax (finalize) → coder (implementer).
- `autonomy-output/` is a frozen spec directory; spec amendments use the prepend approach to preserve filenames and pre-commit hooks.

## Babel v0.10.3 Status (Unreleased)

- **Read-query track: COMPLETE.** Stages 13 (`reference/babel/query.py`) and 13b (`reference/tests/test_query.py`) are committed ground truth with parametric `FIXTURE_V0103` builder and seven behavioral tests over real AST from `parse_file`.
- **Write-side track: BLOCKED on Stage 12a.** The BISC spec patch is the sole remaining prerequisite for write-side progress. Stages 12b (sidecar lock in `reference/babel/handoff.py`) and 12c (concurrent-append test) are correctly gated on 12a commit per spec-first ordering hard constraint.
- **Audit chain status (round 8 re-audit):** DeepSeek signoff=true on Nemotron's atomized 12a+13b plan. No new blockers, no contradictions, no edge-case failures. The plan is implementation-ready end-to-end.

## v0.10.3 Implementation Queue

1. **Stage 12a** (next single-file spec round, spec-first): patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with:
   - Prepend `Effective v0.10.3` version note after file header.
   - Section 5.3 *Grammar Manifest*: header regex `^#\[(handoff|intent|meta):[a-z0-9-]+\]$` (round 3 approved, matches BSL `#[block:<type>-<id>]` syntax), allowed block types (handoff, intent, meta), 9 handoff keys, 3 intent keys, 3 meta keys.
   - Section 5.4 *Lint CLI Contract*: stdout `{"valid": true}` exit 0; stderr JSON exit 6 on BabelParseError / OSError / Exception matching `companion.py`.
   - Section 5.5 *Multi-Agent Append Contract*: serialized `append_handoff` via `fcntl.flock(LOCK_EX)` on unified sidecar lock file, atomic generation counter in meta block.
2. **Stage 13b** (parallel next single-file test round, architecturally decoupled from 12a): author `reference/tests/test_query.py` with parametric `FIXTURE_V0103` builder (header string + intent dict + handoff trait tuples + const_keys dict) and seven behavioral tests over real AST.
3. **Stage 12b** (deferred, gated on 12a commit): patch `reference/babel/handoff.py` `append_handoff` per round-3 approved plan (unified sidecar lock file, `fcntl.flock(LOCK_EX)`, creation-under-lock, atomic temp-file + `os.replace`, generation counter, platform guard).
4. **Stage 12c** (deferred, gated on 12b commit): author `reference/tests/test_concurrent_append.py` verifying lock acquisition and monotonic generation.

## Resolved Approvals (in force across rounds)

- **9-key HANDOFF_SCHEMA** (stage 9a, round 6 alignment): `path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note`.
- **Corrected BSL header regex** (round 3): `^#\[(handoff|intent|meta):[a-z0-9-]+\]$` matching BSL `#[block:<type>-<id>]` syntax.
- **Stage 12b round-3 unified sidecar lock** (DeepSeek signoff=true): `<path>.babel.lock` with `fcntl.flock(LOCK_EX)`, creation-under-lock protocol with initial meta block (`generation=1`), atomic temp-file + `os.replace`, generation counter increment, platform guard (`HandoffIntegrityError` `platform_unsupported` on non-POSIX).
- **Stage 13 read-query plan** (DeepSeek signoff=true): `select_handoffs(ast, *, agent_id=None, signoff=None)` returning `tuple[MappingProxyType, ...]` ordered by ascending `_line`; `HandoffView` TypedDict with underscore-prefixed metadata (`_line`, `_block_id`, `_query_protocol_version=1`); private `_filter_by_agent_id` and `_filter_by_signoff_status` helpers; `MappingProxyType` runtime immutability; validated-AST-only contract.
- **Stages 11b/11d/11e** BSL grammar manifest and validation surface (committed).
- **Stage 11f** doc sweep (lint CLI, grammar manifest, conformance test documented).

## Resolved Transport-Protocol Failure

The systemic 7-round (rounds 1-6 plus round 7 partial) truncation failure is RESOLVED. Kimi's atomized `required_changes` transport protocol (each item under 200 characters) plus Nemotron's parametric `FIXTURE_V0103` builder eliminate the verbatim multi-line JSON that hit the 420-character per-item transport cap. This is a transport-protocol fix, not a per-round workaround, and applies to all future stages.

## Multi-Agent Pipeline Notes

- `pair_b_finalize` stage is docs-only: ships exactly README + CHANGELOG (single-file-pair anti-timeout cadence). 8+ TimeoutError entries in the notes tail on this exact stage confirm that any multi-file code/spec/test delivery risks runtime failure. Code/spec/test patches are single-file artifact rounds, not `pair_b_finalize`.
- Successful pattern: single-file-pair held across 13+ prior rounds (4c.2e+4c.2f, 6e+6f, 7c, 10a, 11a r1-r5, 11b/11d/11e r1-r3, 11f, 12a, 12b r1-r3, 13, 13b r1, 12a+13b r1-r8).
- If DeepSeek signs off a plan, `pair_b_finalize` records the approval and queues the next single-file round.

## Self-Configuration

This model may update its own configuration by returning artifacts for:
- `identities/minimadmax.json`
- `prompts/scaffolds/minimadmax_reasoning_scaffold.md`
- `orchestrator/round_config.json`

Config edits should be requested via `required_changes` in artifact-writing stages, not silently applied.

## Tuning Profiles

- `balanced` -- default general work.
- `precise` -- code review, facts, infrastructure.
- `fast` -- quick checks.
- `deep` -- planning and broad analysis.

Rebuild with `rebuild-ollama-models minimadmax --profile <name>`.
