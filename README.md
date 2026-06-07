# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel/BCPR/BISC pipeline** — the autonomous engineering stack that this agent advances through staged pair-b finalize rounds.

## Stack Status

| Subsystem | Spec | Parser skeleton | Logic | Tests |
|-----------|------|-----------------|-------|-------|
| Syntax (`babel-language-syntax-v0.10.2.md`) | Shipped | n/a | n/a | n/a |
| Integration (`babel-language-integration-v0.10.2.md`) | Shipped (+ Contract Bootstrap Appendix, stage 1c) | n/a | n/a | n/a |
| BISC (`babel-bisc-integrity-v0.10.2.md`) | Shipped + stage 4b.1 amendment (multiple_intents) | n/a | n/a | n/a |
| BCPR (`babel-bcpr-protocol-v0.10.2.md`) | Shipped | n/a | n/a | n/a |
| Parser (`reference/babel/bsl_parser.py`) | API frozen | Shipped (stage 1a) | Stages 4a/4b.2/4c | Stage 4b.2 |
| Handoff (`reference/babel/handoff.py`) | Docstring contract | Pending (stage 2a) | Stage 5a | Stage 3a |
| Companion (`reference/babel/companion.py`) | Docstring contract | Shipped (stage 2b) | Future cycle | Future cycle |

## Bootstrap Sequencing

Stages 1a → 1c → 2b → 3b are shipped. The current cycle is stage 4b.1 (BISC spec amendment for `multiple_intents`). The decomposed 4b cadence continues with 4b.2 (normalize logic + tests), 4c (writer + CLI), 4a (scanner), and 5a (append_handoff).

Every finalize/remediate round updates this README and `CHANGELOG.md`.

## Self-Configuration

This agent may update its own configuration by returning artifacts with full file content for:
- `identities/minimadmax.json`
- `prompts/scaffolds/minimadmax_reasoning_scaffold.md`
- `orchestrator/round_config.json`

Config edits are source-controlled in `Cole-Will-I-Am/MiniMadMax` and applied by the next artifact-writing stage.
