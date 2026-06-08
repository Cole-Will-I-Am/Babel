# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel stack** — deterministic human+AI collaboration protocol: BSL (Babel Spec Language), BISC (Babel Integrity & Style Checks), BCPR (Babel Conflict Prevention Rules).

## Repository Layout

```
MiniMadMax/
  identities/                Agent identity JSON files
  prompts/scaffolds/         Reasoning scaffolds and prompt templates
  orchestrator/              Round configuration and routing rules
  reference/                 Babel spec and reference implementation
    babel/                   Core modules: handoff.py, bsl_parser.py, bsl_validator.py, companion.py
    tests/                   Unit tests for the reference implementation
  autonomy-output/           Working BISC integrity docs and audit notes
  README.md                  This file
  CHANGELOG.md               Change history
```

## Babel Version

`BABEL_VERSION = 0.10.3` (single source of truth: `reference/babel/handoff.py`).

## Handoff Block Schema (v0.10.3, 9 keys)

Every `/blocks/handoff` block body carries the following content dict keys (per stage 7a schema lock):

| Key | Type | Semantics |
|---|---|---|
| `path` | str | Filesystem path of the `.babel` file when the handoff was created |
| `content` | str | Full handoff body including the `## agent: <id>\n` prefix prepended by `append_handoff` |
| `agent_id` | str | Originating agent identifier |
| `next_owner` | str | Downstream agent identifier for model-to-model handoff |
| `signoff` | bool | `True` only when artifacts are internally consistent and commit-ready; encoded as lowercase `true`/`false` in the raw block body |
| `blocking_issues` | list[str] | Items that must be resolved before signoff |
| `required_changes` | list[str] | Follow-up work not included in the current handoff |
| `summary` | str | One-paragraph human-readable summary |
| `memory_note` | str | Short durable note for future sessions |

Frozen by stages 7a + 7b + 7c. The `HANDOFF_SCHEMA` TypedDict is exported from `reference/babel/handoff.py` (stage 9a).

## BSL Validator (v0.10.3, stage 10b)

`reference/babel/bsl_validator.py` exposes:

- `validate_header(header_line: str, line_no: int) -> tuple[str, str]` — returns `(block_type, block_id)`, regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`.
- `validate_body_kv(block_type: str, kv_pairs: list[tuple[str, str]], line_no: int) -> None` — required keys per type (handoff: 9 HANDOFF_SCHEMA keys + `version`; intent: `{purpose, owner, version}`; meta: `{title, version}`). **Rejects extra keys** (deterministic default per stage 10a). Raises `BabelParseError` on duplicate/missing/unknown keys.
- `validate_version(version: str, line_no: int) -> None` — semver string equality against `BABEL_VERSION`; mismatch raises `BabelParseError` with `code='version_mismatch'`.
- `validate_file(path: Path) -> None` — orchestrates all three over the parsed file.
- `validate_block_string(block_type: str, header: str, kv_pairs: list[tuple[str, str]]) -> None` (stage 11a) — direct composition primitive: calls `validate_header(header, line_no=0)` and uses the **returned block_type** for `validate_body_kv` to prevent header-body mismatch. No intermediate block string construction.

## Stage 11a/11a2 — Validator Integration Audit Round 3 (signoff)

**Status:** DeepSeek audit `signoff=true` on Nemotron's refined split-stage 11a/11a2 plan. Both prior blockers fully resolved.

**Prior blockers (now resolved):**

1. ~~Two-file delivery contradiction~~ — Resolved by splitting into sequential single-file stages 11a (`bsl_validator.py`) and 11a2 (`handoff.py`), preserving the anti-timeout single-file cadence.
2. ~~`validate_block_string` design ambiguity~~ — Resolved by direct-call composition: the function invokes `validate_header(header)` and `validate_body_kv(block_type, kv_pairs)` without constructing an intermediate block string.

**Minor consistency refinement (normative, required for stage 11a):**

`validate_block_string` MUST capture the `block_type` returned by `validate_header(header, line_no=0)` and pass it to `validate_body_kv` instead of the function's `block_type` parameter. The parameter is retained for API symmetry, but the body is validated against the actual header type. Implementation sketch:

```python
def validate_block_string(block_type: str, header: str, kv_pairs: list[tuple[str, str]]) -> None:
    header_type, _block_id = validate_header(header, line_no=0)
    validate_body_kv(header_type, kv_pairs, line_no=0)
```

**Approved architecture (non-blocking):**

- Pre-write validation gate in `handoff.py` (calls `validate_block_string` before `write_file`, raises `HandoffIntegrityError` on failure).
- Complete `_encode_handoff_value`/`_decode_handoff_value` contract: `str` (passthrough), `list[str]` (compact JSON via `json.dumps(..., separators=(',', ':'))`), `bool` (lowercase `'true'`/`'false'`).
- `HandoffIntegrityError(Exception)` carrying `BabelParseError` code and line number.
- Scoped single-block validation (whole-file validation remains in `companion.py` lint for CI).

**Five sub-stages queued (single-file finalize rounds holding anti-timeout cadence):**

| Stage | File | Deliverable | Gate |
|---|---|---|---|
| 11a | `reference/babel/bsl_validator.py` | Add `validate_block_string` with direct-call composition using returned `block_type` | none |
| 11a2 | `reference/babel/handoff.py` | Import `validate_block_string`; add `_encode_handoff_value`/`_decode_handoff_value` (str/list/bool); add `HandoffIntegrityError`; add pre-write validation gate | 11a |
| 11b | `reference/babel/companion.py` | Add `lint <path>` subcommand calling `bsl_validator.validate_file` directly | 11a2 |
| 11c | `reference/tests/test_handoff_validation_gate.py` | Cover pre-write rejection, JSON list round-trip, bool round-trip, version mismatch | 11a2 |
| 11d | `reference/babel/bsl_validator.py` | Add grammar manifest comment block (header regex, required keys, encoding conventions) | 11a |

Stages 11b/11c/11d are gated on 11a or 11a2 completion; 11d is gated on 11a because the manifest documents the bool encoding adopted by the direct-call composition.

**Next round:** attempt stage 11a (`bsl_validator.py` `validate_block_string` with the block_type consistency refinement applied).

## Anti-Timeout Cadence

This stage ships exactly the two paired documentation files (README, CHANGELOG) that finalize/remediate rounds always require. The notes tail on `pair_b_finalize` documents 8+ `TimeoutError` failures when multi-file code/spec content was attempted on this exact stage. The single-file-pair pattern holds timeouts at zero across the last 7 successful rounds (4c.2e+4c.2f, 6e+6f, 7c, 10a, 11a round 1, 11a round 2, 11a/11a2 round 3).

## Profiles

- `balanced` — default work
- `precise` — code review, facts, infrastructure
- `fast` — quick checks
- `deep` — planning and broad analysis

## Self-Configuration

- Identities: `identities/minimadmax.json`
- Reasoning scaffold: `prompts/scaffolds/minimadmax_reasoning_scaffold.md`
- Round config: `orchestrator/round_config.json`
