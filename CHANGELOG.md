# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, behavioral conformance test, doc sweep, BISC amendment, and write-serialization audit. Stages 9a/9b/10b/11a/11a2/11b/11d/11e/11f/12a/12b/12c/13.

### 2026-06-08

#### Stage 12b audit round 3: signoff=true

- **Kimi**: revised 12b kickoff adopting unified sidecar lock file (`<path>.babel.lock`) with `fcntl.flock(LOCK_EX)` to resolve the round-2 creation race by serializing both initial `.babel` creation and subsequent appends under the same lock.
- **Nemotron**: implementation-ready refinement combining sidecar lock + generation counter (int in meta block) + atomic `temp-file + os.replace` + platform guard (`HandoffIntegrityError(code='platform_unsupported')` on non-POSIX) + creation-under-lock protocol (initial meta block with `generation=1`).
- **DeepSeek**: audit signoff=true. No blockers. The architecture resolves all prior round-1 (generation counter insufficient for conflict-free) and round-2 (creation protocol missing) issues. Assumption noted: `fcntl.flock` requires local filesystem with proper lock support; network filesystems may not guarantee mutual exclusion.
- **Implementation queue** (single-file stages, spec-first ordering):
  1. **12a BISC patch** (immediate next, single-file, prerequisite): `autonomy-output/babel-bisc-integrity-v0.10.2.md` prepending `Effective v0.10.3` version note and adding Section 5.3 Grammar Manifest, Section 5.4 Lint CLI Contract, Section 5.5 Multi-Agent Append Contract.
  2. **12b handoff.py** (single-file, gated on 12a): `fcntl.flock` sidecar lock acquisition; creation-under-lock with initial meta block (`generation=1`); read-modify-validate-increment-append-replace for existing files.
  3. **12b bsl_validator.py** (single-file, gated on 12a): add `generation` int to meta block required keys; update grammar manifest comment block.
  4. **12c test_concurrent_append.py** (single-file, gated on 12b): behavioral sequential simulation verifying sidecar lock acquisition and monotonic generation increment.
  5. **13 query.py** (deferred): deterministic read-query protocol over parsed BSL AST with `filter_by_agent_id` and `filter_by_signoff_status` primitives. `query_protocol_version` integer.
- **Coder completion log** preserved: stages 9a/9b/10b/11a/11a2/11b/11d/11e/11f complete. Two parser fix rounds (4-fail and 3-fail) verified.
- **signoff=true**: documentation pair is internally consistent, additive to prior 12b round-2 docs surface, every claim is grounded in the audit chain. Next artifact-writing stage can attempt stage 12a immediately without waiting on further architecture decisions.

#### Stage 12b audit round 2: signoff=false (archived, resolved)

- DeepSeek approved Nemotron's `fcntl.flock` mechanism for existing-file appends but flagged creation race for new `.babel` files as a new blocker. Resolution: unified sidecar lock file (`<path>.babel.lock`) added in round 3.

#### Stage 12b audit round 1: signoff=false (archived, resolved)

- DeepSeek rejected generation counter + atomic replace as optimistic locking that allows lost updates. Resolution: `fcntl.flock` adopted in round 2/3.

#### Stage 12a BISC amendment plan: signoff (archived, plan approved)

- DeepSeek signed off Nemotron's implementation-ready plan for the BISC v0.10.2 -> v0.10.3 amendment. Three normative sections (5.3 Grammar Manifest, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract) align with committed stages 11b/11d/11e. Physical patch queued as the next single-file spec round.

#### Stage 11f doc sweep: signoff (archived, complete)

- README v0.10.3 documents the `companion.py` `lint <path>` subcommand, the grammar manifest in `bsl_validator.py`, and `test_grammar_manifest.py` behavioral conformance coverage for human consumers.

#### Stage 11b/11d/11e audit round 3: signoff (archived, complete)

- DeepSeek signed off Nemotron's refined validation surface plan: handoff key ambiguity resolved (10 keys = 9 `HANDOFF_SCHEMA` payload + 1 BSL syntax-layer `version` key), lint has full BISC error handling (`BabelParseError` + `OSError` + `Exception`), conformance test uses behavioral assertions only, grammar manifest is explicit with literal key name lists. Three single-file stages 11b/11d/11e queued.

#### Stage 11b/11d/11e audit round 2: signoff=false (archived, resolved)

- Handoff key count ambiguity flagged and resolved: `HANDOFF_SCHEMA` (stage 9a TypedDict) contains exactly 9 payload keys; `version` is a 10th BSL syntax-layer key required by stage 10a `validate_version`.

#### Stage 11b/11d/11e audit round 1: signoff=false (archived, resolved)

- Two blockers: missing BISC-compliant `OSError`/`Exception` handling in lint subcommand; test fragility from internal `REQUIRED_KEYS` dict access. Both resolved with prescriptive fixes.

#### Stage 11a2 round-5 audit: signoff=true (archived, complete)

- `BabelParseError` correctly sourced from `bsl_parser`; dependency inversion via `validate_version` parameterization approved; pre-write gate with bool/list/str encoding approved. Prerequisite micro-patch (`bsl_validator.py` single-file) gating step before 11a2.

#### Stage 11a/11a2 split-plan round-3 audit: signoff=true (archived, complete)

- Both prior blockers (two-file contradiction, `validate_block_string` design ambiguity) fully resolved by split-stage direct-call composition. Five sub-stages queued as single-file rounds.

#### Stage 11a round-2 audit: signoff=false (archived, resolved)

- Two-file delivery contradicted anti-timeout cadence; `validate_block_string` constructs redundant block string. Resolved by split into 11a (`bsl_validator.py`) + 11a2 (`handoff.py`) and direct-call composition.

#### Stage 11 audit: signoff=false (archived, resolved)

- Three blockers (post-write gate persistence, missing bool encoding, whole-file scope) required amendment before 11a-11d implementation. Resolved in subsequent rounds.

#### Stage 10a architecture: signoff=true (archived, complete)

- DeepSeek signed off Kimi/Nemotron amended architecture: version in body KV, required keys per block type, parser dependency with fallback. Extra keys policy resolved: reject any key not in required set per block type for deterministic validation. Three single-file stages (9a TypedDict, 9b test, 10b validator) queued.

## v0.10.2 -- BSL Parser + Validator + Handoff Foundation (Released)

- `Babel Source Language (BSL)` parser with file header and `#[/blocks/{type}:{id}]` block headers.
- `HANDOFF_SCHEMA` with 9 payload keys.
- BISC v0.10.2 base specification.
- Stages 1-8 complete.
