# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel/BCPR/BISC stack** -- deterministic syntax, conflict-free handoff protocol, and practical implementation runbooks for human+AI collaboration.

## Tuning Profiles

| Profile   | Use                                                |
|-----------|----------------------------------------------------|
| balanced  | Default work.                                      |
| precise   | Code review, facts, infrastructure.               |
| fast      | Quick checks.                                      |
| deep      | Planning, broad analysis.                          |

Rebuild: `rebuild-ollama-models minimadmax --profile <name>`.
Record outcomes: `model-outcome record --model minimadmax --task <task> --outcome <success|failure|mixed|note> --quality <1-5> --note <text>`.

## Secrets Policy

Never print, embed in commits, copy into prompts, or store in project files. Identify where credentials are configured; do not reveal secret material.

## Babel v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. The grammar manifest is normative; the lint CLI contract is stable; the multi-agent append contract requires serialized writes.

### Completed Stages

- **Stage 9a** -- `HANDOFF_SCHEMA` TypedDict in `reference/babel/handoff.py` with 9 payload keys: `path`, `content`, `agent_id`, `next_owner`, `signoff`, `blocking_issues`, `required_changes`, `summary`, `memory_note`.
- **Stage 9b** -- `reference/tests/test_handoff_append.py` conformance assertions for the append path.
- **Stage 10b** -- `reference/babel/bsl_validator.py` with `validate_header`, `validate_body_kv`, `validate_version`, `validate_file` and extra-keys policy `REJECT`.
- **Stage 11a** -- `validate_block_string` in `bsl_validator.py` using direct-call composition with header-derived `block_type`.
- **Stage 11a2** -- `handoff.py` pre-write gate with `_encode_handoff_value` and `_decode_handoff_value` for `bool`, `list`, and `str` body KV encoding.
- **Stage 11b** -- `reference/babel/companion.py` `lint <path>` subcommand with BISC-compliant error handling for `BabelParseError`, `OSError`, and `Exception`.
- **Stage 11d** -- Normative grammar manifest comment block at the top of `reference/babel/bsl_validator.py` documenting the header regex, allowed block types, and required key sets with literal key name lists.
- **Stage 11e** -- `reference/tests/test_grammar_manifest.py` behavioral conformance test that reads `bsl_validator.py`, extracts the manifest via regex, and asserts `validate_header` and `validate_body_kv` match the documented contract.
- **Stage 11f** -- Doc sweep documenting the lint subcommand, grammar manifest, and conformance test for human consumers.
- **Stage 12a (plan approved, patch pending)** -- `autonomy-output/babel-bisc-integrity-v0.10.2.md` amendment with `Effective v0.10.3` version note and Sections 5.3-5.5.
- **Stage 12b (plan approved, impl pending)** -- `reference/babel/handoff.py` `append_handoff` with unified sidecar lock file (`<path>.babel.lock`), `fcntl.flock(LOCK_EX)`, creation-under-lock, generation counter, atomic `os.replace`, and platform guard.
- **Stage 12c (queued)** -- `reference/tests/test_concurrent_append.py` for sidecar lock and generation behavior.
- **Two parser fix rounds** -- Coder-delivered patches resolving 4-fail and 3-fail test rounds on `bsl_parser.py` (strict `FILE_HEADER_REGEX`, `missing_intent` line number, version consistency check, `duplicate_id` ordering, CLI exit 6).

### Stage 13 -- Read-Query Protocol (Plan Approved, Impl Pending)

Deterministic, immutable, versioned read-query interface over validated BSL AST. Decouples read-side progress from the pending 12a/12b write-side gating so autonomous agents can discover handoff blocks without waiting for the write-serialization primitive to land.

**Architecture decisions (signed off by DeepSeek):**

- `select_handoffs(ast, *, agent_id=None, signoff=None) -> tuple[MappingProxyType, ...]` returns immutable handoff views ordered by ascending `_line`. Keyword-only filter arguments prevent positional ambiguity.
- `HandoffView` TypedDict extends `HANDOFF_SCHEMA` (9 payload keys from stage 9a) with underscore-prefixed metadata `_line: int`, `_block_id: str`, `_query_protocol_version: Literal[1]`. Underscore prefix avoids collision with the 9 payload keys.
- Private filter helpers `_filter_by_agent_id(blocks, agent_id)` and `_filter_by_signoff_status(blocks, signoff)` return iterators; `select_handoffs` composes them and collects into an ordered tuple. Underscore prefix keeps them out of the public API until usage patterns stabilize.
- Every returned view is wrapped in `types.MappingProxyType` at construction time. Runtime immutability is enforced by the wrapper, not by convention.
- `query_protocol_version=1` is a `Literal[1]` in `HandoffView`. Future schema evolutions must bump this integer so consumers detect incompatibility without silent behavior changes.
- `query.py` operates exclusively on the AST returned by `bsl_parser.parse_file`. It does not accept raw text, does not reimplement grammar validation, and does not duplicate `bsl_validator` responsibilities.

**Approved (non-blocking) items:**

- Single-file delivery of `reference/babel/query.py` to preserve the anti-timeout cadence.
- `test_query.py` deferred to stage 13b after `query.py` commits.
- Stage 12a BISC amendment remains the parallel write-side prerequisite (architectural decoupling; not gating stage 13).

**Implementation queue:**

1. **Stage 13 (next round, single-file):** Author `reference/babel/query.py` with `select_handoffs`, `HandoffView` TypedDict, and private filter helpers. Import `HANDOFF_SCHEMA` from `handoff.py` and `MappingProxyType` from `types`. Sort results by `_line` ascending.
2. **Stage 13a (deferred):** If `ast` input does not have validated handoff blocks, raise `TypeError` with descriptive message. Document the validated-AST-only contract.
3. **Stage 13b (deferred, single-file, gated on stage 13 commit):** Author `reference/tests/test_query.py` verifying deterministic ordering, `MappingProxyType` immutability (`TypeError` on assignment), correct filtering by `agent_id` and `signoff`, `query_protocol_version=1` presence, empty-input behavior, and combined filter intersection.
4. **Stage 12a (parallel, single-file):** Patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with `Effective v0.10.3` version note and Sections 5.3-5.5. Spec-first ordering hard constraint.
5. **Stage 12b (gated on 12a, single-file):** Patch `reference/babel/handoff.py` `append_handoff` per round-3 approved plan (sidecar lock, `fcntl.flock`, creation-under-lock, generation counter, atomic replace, platform guard).
6. **Stage 12c (gated on 12b, single-file):** Author `reference/tests/test_concurrent_append.py` for sidecar lock and generation behavior.

### Archived (Resolved) Blocker Chains

- **Stage 11a blocker chain (rounds 1-5):** Two-file delivery contradiction, `validate_block_string` design ambiguity, dependency inversion in `bsl_validator.py`, `BabelParseError` import source. Resolved by split-stage direct-call composition with `block_type` returned by `validate_header` and `BabelParseError` sourced from `bsl_parser`.
- **Stage 11a2 prerequisite micro-patch:** `validate_version` parameterization with `expected_version: str, version: str, line_no: int` and removal of `from .handoff import BABEL_VERSION` module-level import. Resolved.
- **Stage 11b/11d/11e blocker chain (rounds 1-3):** Missing `OSError`/`Exception` handling in lint, test fragility from internal `REQUIRED_KEYS` dict access, handoff required key count ambiguity. Resolved by full BISC error handling, behavioral-only test assertions, and explicit literal key name lists in the grammar manifest (handoff: 10 keys = 9 payload + version; intent: 3 keys; meta: 3 keys including generation).
- **Stage 12b blocker chain (rounds 1-3):** Generation counter + atomic replace is optimistic locking, allows lost updates. Creation race for new `.babel` files. Both resolved by unified sidecar lock file (`<path>.babel.lock`) with `fcntl.flock(LOCK_EX)` serializing both initial creation and subsequent appends. Creation-under-lock protocol with initial meta block (`generation=1`) committed atomically via temp-file + `os.replace`. Platform guard raises `HandoffIntegrityError(code='platform_unsupported')` on non-POSIX.
- **Stage 13 blocker chain (no blockers):** Kimi kickoff (rounds 1-2 with timeout) and Nemotron refinement both signed off by DeepSeek. No blockers surfaced. Anti-timeout cadence preserved by single-file delivery constraint.

### Carry-Over

- **Stages 5a/5b from v0.10.2 cycle:** `append_handoff` implementation and test patch. The 11a2 pre-write gate and 11b/11d/11e validation surface assumed `append_handoff` exists with the 9-key content dict structure per stage 9a. The round-3 approved 12b plan preserves that contract.
- **Stage 7b BISC section 5 amendment:** Subsumed by stage 12a Section 5.3 (Grammar Manifest documents the 10 required keys). File-rename concern (v0.10.2 vs v0.10.3 filename) resolved via prepend approach (add explicit version note in file header rather than rename to preserve existing links from BISC pre-commit hooks).

## Anti-Timeout Cadence

The `pair_b_finalize` stage has documented 8+ `TimeoutError` failures when multi-file code/spec delivery was attempted. The safe pattern is single-file-pair (README + CHANGELOG only) held across 13+ successful rounds. Code/spec patches are scheduled as separate single-file finalize rounds.

## Self-Configuration

This model may update its own configuration by returning artifacts with full file content for `identities/minimadmax.json`, `prompts/scaffolds/minimadmax_reasoning_scaffold.md`, and `orchestrator/round_config.json`. Config edits are source-controlled in `Cole-Will-I-Am/MiniMadMax` and require a rebuild via `rebuild-ollama-models minimadmax --profile <name>` plus a smoke test.
