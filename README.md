# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** - hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** - local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax` and `Cole-Will-I-Am/new-lab`.
- **Babel language surface** - `.babel` source files, canonical JSON v0.2.0 body blocks, deterministic sort, virtual JSON for patch negotiation, handoff protocol, companion `.md` convention.
- **BISC integrity** - canonical document registry, body-only `canonical_sha256`, exit code 6 on intent/dup/header violations.
- **BCPR patch negotiation** - virtual JSON representation, `/blocks/<type>:<id>` patch paths, handoff exclusion, deterministic conflict hash.
- **BWSS workspace** - lifecycle states (`draft -> review -> ready -> sealed -> frozen`) for `.babel` files, handoff block audit trail.

## Current cycle: Babel v0.10.2 contract-first bootstrap

Bootstrapping the Babel v0.10.2 language surface in single-file finalize
rounds to avoid pair_b timeouts. Each stage ships one Python file or
spec document plus `README.md` and `CHANGELOG.md` updates.

| Stage | Artifact | Status |
|-------|----------|--------|
| 1a | `reference/babel/bsl_parser.py` (parser API skeleton) | shipped |
| 1b | `reference/tests/test_bsl_parser_contract.py` | queued |
| 1c | Integration spec Contract Bootstrap Appendix | shipped |
| 2a | `reference/babel/handoff.py` (handoff skeleton) | shipped |
| 2b | `reference/babel/companion.py` (companion skeleton) | **shipped** |
| 3a | `reference/tests/test_handoff_contract.py` | queued |
| 3b | BISC spec error taxonomy and stderr JSON format | queued |

Follow-up: logic implementations land in the v0.10.3 cycle 3 logic
schedule. Stages 1b, 3a, and 3b remain queued as separate single-file
finalize rounds.

## Repos

- `Cole-Will-I-Am/MiniMadMax` - model specs, prompts, identities, orchestrator config.
- `Cole-Will-I-Am/new-lab` - Babel reference implementation, specs, tests.
