# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** - hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** - local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel reference** - `reference/babel/` (parser, handoff, companion) and `reference/tests/` (contract tests).
- **Babel specs** - `autonomy-output/` (syntax, integration, BISC, BCPR amendments).

## Babel v0.10.2 Contract-First Bootstrap

The Babel v0.10.2 reference implementation is being shipped in a single-file-per-stage cadence to avoid the multi-file stage timeouts that affected earlier pair cycles. Each stage delivers exactly one artifact and is independently revertible.

### Bootstrap Sequencing

| Stage | Artifact                                                             | Status         |
|-------|----------------------------------------------------------------------|----------------|
| 1a    | `reference/babel/bsl_parser.py` (parser API skeleton)                | shipped        |
| 1b    | `reference/tests/test_bsl_parser_contract.py` (parser contract test) | shipped        |
| 1c    | `autonomy-output/babel-language-integration-v0.10.2.md` (Contract Bootstrap Appendix) | shipped        |
| 2a    | `reference/babel/handoff.py` (handoff skeleton)                      | pending        |
| 2b    | `reference/babel/companion.py` (companion skeleton)                  | pending        |
| 3a    | `reference/tests/test_handoff_contract.py` (handoff contract test)  | pending        |
| 3b    | `autonomy-output/babel-bisc-integrity-v0.10.2.md` (BISC error taxonomy amendment) | pending |

Stages 1a and 1b are signed off. Stage 1c (this round) ships the Contract Bootstrap Appendix that maps the shipped and pending API surface to BWSS lifecycle states and handoff protocol steps. Stages 2a, 2b, 3a, and 3b are queued as separate single-file finalize rounds.

### Stage 1c Details

The Contract Bootstrap Appendix appears at the end of `autonomy-output/babel-language-integration-v0.10.2.md` and covers:

- A.1 API surface table for the six shipped and pending functions.
- A.2 Mapping of those functions to BWSS lifecycle states (`draft`, `review`, `ready`, `sealed`, `frozen`).
- A.3 Mapping of those functions to the five handoff protocol steps from section 5 of the integration spec.
- A.4 Stub status (`NotImplementedError` on all six functions) and the frozen surface from stage 1a.
- A.5 Contract test coverage from stage 1b and the planned stage 3a handoff contract test.

All function bodies in shipped and pending modules raise `NotImplementedError` until the corresponding logic cycle ships. The frozen surface (dataclasses, error codes, module constants) is not subject to revision under v0.10.2 bootstrap rules.

## Spec Index

- `autonomy-output/babel-language-syntax-v0.10.2.md` - normative syntax (EBNF, header grammar, body/handoff split, deterministic serialization).
- `autonomy-output/babel-language-integration-v0.10.2.md` - normative integration (subsystem mapping, lifecycle, companion `.md`, handoff protocol, Contract Bootstrap Appendix).
- `autonomy-output/babel-bisc-integrity-v0.10.2.md` - BISC amendment (`.babel` recognition, intent validation, body-only `canonical_sha256`, exit code 6).
- `autonomy-output/babel-bcpr-v0.10.2.md` - BCPR amendment (virtual JSON, `/blocks/<type>:<id>` patch paths, body-only conflict hash, handoff exclusion).

## Changelog

See `CHANGELOG.md` for the full record of shipped stages and follow-up rounds.
