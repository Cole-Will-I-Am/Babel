# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax` (home for this model's specs) and `Cole-Will-I-Am/new-lab` (lab workspace with admin permissions).
- **Babel reference implementation** -- `reference/babel/` ships the BCPR/BISC spec parser, query interface, and handoff write-path skeleton.
- **Companion CLI** -- BISC-compatible `lint` and `query` subcommands with deterministic stdout/stderr JSON contracts.
- **Tuning profiles** -- `models/profiles/balanced.json`, `precise.json`, `fast.json`, `deep.json` consumed by `rebuild-ollama-models`.
- **Outcome memory** -- `model-outcome record` and `model-outcome list` for durable cross-session task quality tracking.

## Autonomous Multi-Agent Workflow

MiniMadMax runs a five-agent pipeline with model-to-model handoff and zero human-in-the-loop approval:

1. **Kimi** (architecture) -- emits high-level decisions and atomized required_changes (<200 chars per item).
2. **Nemotron** (planning) -- refines architecture into implementation-ready drafts with parametric fixture protocols.
3. **DeepSeek** (audit) -- verifies internal consistency, gates signoff, and surfaces blockers.
4. **Coder** (implementation) -- writes code/spec/test files inside `reference/` and `autonomy-output/`.
5. **MiniMadMax** (finalize) -- ships the docs-only pair (README + CHANGELOG) per the anti-timeout cadence.

Handoffs are encoded as BSL blocks inside `.babel` files per the BISC v0.10.3 spec (Sections 5.3-5.5). The 9-key HANDOFF_SCHEMA and the 3-key intent schema are normative.

## Babel Stack Status (v0.10.3)

| Track | Status | Owner |
|---|---|---|
| 9-key HANDOFF_SCHEMA (stage 9a) | Committed, in force | coder |
| `append_handoff` content dict contract (stage 9b) | Committed | coder |
| BISC CLI exit-code contract (stage 10b) | Committed | coder |
| Pre-write gate (stage 11a/11a2) | Committed | coder |
| BSL grammar manifest + validation surface (11b/11d/11e) | Committed | coder |
| Doc sweep (stage 11f) | Committed | coder |
| Stage 12a BISC spec patch | **Queued, next single-file spec round (spec-first)** | minimadmax/nemotron |
| Stage 12b unified sidecar lock | Approved (r3 signoff), deferred (gated on 12a) | coder |
| Stage 12c concurrent-append test | Approved, deferred (gated on 12b) | coder |
| Stage 13 read-query plan | Committed (`reference/babel/query.py`) | coder |
| Stage 13b test_query.py | Committed (read-query track complete) | coder |

## Anti-Timeout Cadence

The `pair_b_finalize` stage has documented 8+ `TimeoutError` failures in the notes tail whenever it attempted multi-file code/spec/test delivery. The successful pattern is to ship **only** the README + CHANGELOG pair in finalize/remediate rounds. Code/spec/test patches are single-file artifact rounds, never `pair_b_finalize`.

## Secret Handling

Token values, passwords, and private keys must never be printed, embedded in commits, copied into prompts, or stored in project files. Git operations prefer `gh` and HTTPS remotes.

## Tuning and Memory

```bash
# Rebuild model with a profile
rebuild-ollama-models minimadmax --profile balanced

# Record an outcome
model-outcome record --model minimadmax --task <task> --outcome <success|failure|mixed|note> --quality <1-5> --note <text>
```

Profiles: `balanced` (default), `precise` (code review, facts, infra), `fast` (quick checks), `deep` (planning, broad analysis).

## Self-Configuration

Self-config edits to `identities/minimadmax.json`, `prompts/scaffolds/minimadmax_reasoning_scaffold.md`, and `orchestrator/round_config.json` are source-controlled in `Cole-Will-I-Am/MiniMadMax` and applied via the artifact-writing stages. No human approval is required for config edits.
