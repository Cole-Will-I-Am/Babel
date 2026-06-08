# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** -- hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** -- local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel reference implementation** -- `reference/babel/` Python 3.12 stdlib-only modules: `bsl_parser.py`, `bsl_validator.py`, `handoff.py`, `companion.py`, `__main__.py`.
- **BISC specification** -- `autonomy-output/babel-bisc-integrity-v0.10.2.md` (pending v0.10.3 amendment via stage 12a).

## Pipeline Stages

| Stage | Description | Status |
|---|---|---|
| 9a | HANDOFF_SCHEMA TypedDict (9 keys) in handoff.py | Coder complete |
| 9b | test_handoff_append.py conformance assertions | Coder complete |
| 10b | bsl_validator.py validate_header/validate_body_kv/validate_version/validate_file (extra-keys policy: REJECT) | Coder complete |
| 11a | validate_block_string direct-call composition with header-derived block_type | Coder complete |
| 11a2 | handoff.py pre-write gate with _encode_handoff_value/_decode_handoff_value (bool/list/str) | Coder complete |
| 11b | companion.py 'lint <path>' subcommand with full BISC error handling | Coder complete |
| 11d | bsl_validator.py normative grammar manifest comment block | Coder complete |
| 11e | test_grammar_manifest.py behavioral conformance test | Coder complete |
| 11f | Doc sweep documenting lint/grammar manifest/conformance test | Coder complete |
| 12a | BISC v0.10.2 -> v0.10.3 amendment (Sections 5.3-5.5) | Plan signoff; physical patch queued next |
| 12b | Atomic append_handoff with sidecar lock + generation counter | Plan signoff; code queued after 12a |
| 12c | test_concurrent_append.py (behavioral sequential simulation) | Queued after 12b commit |
| 13 | query.py deterministic read-query protocol | Deferred |

## Stage 12b -- Write-Serialization Audit (Round 3: signoff=true)

### Resolution path from prior rounds

- **Round 1 (signoff=false)**: generation counter + atomic replace is optimistic locking; allows lost updates under concurrent append_handoff. **Resolved** by adopting fcntl.flock for true mutual exclusion.
- **Round 2 (signoff=false)**: fcntl.flock only works on existing files; new .babel creation race. **Resolved** by adding a unified sidecar lock file (<path>.babel.lock) that serializes both creation and append under the same lock.

### Approved architecture (Round 3)

1. **Unified sidecar lock file** `<path>.babel.lock` acquired with `fcntl.flock(LOCK_EX)` before any read or write on the target `.babel` file.
2. **Creation-under-lock protocol**: acquire sidecar lock; if target absent, atomically create via `temp-file + os.replace` with initial meta block (title, version, generation=1); if present, proceed with existing-file read-modify-write (read-parse, validate generation, increment meta.generation, append handoff block, serialize to temp, `os.replace`).
3. **Lock release** in `finally` block. `HandoffIntegrityError(code='lock_failed')` on lock acquisition failure.
4. **Atomic write durability** via `temp-file + os.replace`. `generation` counter in meta block incremented on each append.
5. **Platform guard**: if `fcntl` is unavailable (non-POSIX), `append_handoff` raises `HandoffIntegrityError(code='platform_unsupported')` rather than falling back to optimistic locking. Explicit failure preferred over silent data loss.
6. **Meta block schema expansion**: `bsl_validator.py` requires `generation` (int) alongside `title` and `version` in meta block required keys.
7. **Lock assumption**: `fcntl.flock` requires local filesystem with proper lock support; network filesystems may not guarantee mutual exclusion. Documented in BISC and handoff.py docstring.

### Implementation queue (single-file stages, spec-first)

- **12a BISC patch** (next, single-file, prerequisite): `autonomy-output/babel-bisc-integrity-v0.10.2.md` with `Effective v0.10.3` prepended and Sections 5.3 Grammar Manifest, 5.4 Lint CLI Contract, 5.5 Multi-Agent Append Contract added.
- **12b handoff.py** (single-file, gated on 12a): fcntl.flock sidecar lock acquisition; creation-under-lock with initial meta block (generation=1); read-modify-validate-increment-append-replace for existing files.
- **12b bsl_validator.py** (single-file, gated on 12a): add `generation` int to meta block required keys; update grammar manifest comment block.
- **12c test_concurrent_append.py** (single-file, gated on 12b): behavioral sequential simulation verifying sidecar lock acquisition and monotonic generation increment. No threading race oracles.
- **13 query.py** (deferred): deterministic read-query protocol over parsed BSL AST with `filter_by_agent_id` and `filter_by_signoff_status` primitives. `query_protocol_version` integer for evolution.

### Coder completion log (preserved from prior rounds)

- Stage 9a: `HANDOFF_SCHEMA` TypedDict in `reference/babel/handoff.py` with 9 payload keys `{path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note}`.
- Stage 9b: `reference/tests/test_handoff_append.py` conformance assertions for the 9-key schema.
- Stage 10b: `reference/babel/bsl_validator.py` with `validate_header`, `validate_body_kv`, `validate_version`, `validate_file` and extra-keys policy `REJECT`.
- Stage 11a: `validate_block_string` in `bsl_validator.py` using direct-call composition with header-derived `block_type`.
- Stage 11a2: `reference/babel/handoff.py` pre-write gate with `_encode_handoff_value` / `_decode_handoff_value` (bool/list/str) and `BabelParseError` sourced from `bsl_parser`.
- Stage 11b: `reference/babel/companion.py` `lint <path>` subcommand wrapping `bsl_validator.validate_file` in try/except for `BabelParseError` (path/line/code, exit 6), `OSError` (path/file_error, exit 6), `Exception` (internal_error, exit 6).
- Stage 11d: normative grammar manifest comment block at top of `bsl_validator.py` documenting header regex `^/blocks/(handoff|intent|meta):[a-z0-9-]+$`, allowed block types tuple, required key sets with explicit literal names, JSON list encoding, JSON bool encoding.
- Stage 11e: `reference/tests/test_grammar_manifest.py` behavioral conformance test parsing manifest via regex and asserting `validate_header` / `validate_body_kv` enforce documented required keys without internal-dict access.
- Stage 11f: doc sweep documenting lint/grammar manifest/conformance test for human consumers.

## Coder completion log: parser fix rounds

- Round 1 (4 failures): `missing_intent` line corrected to 2; `malformed_header` detection before JSON parsing; `duplicate_id` check before `missing_intent`; CLI `__main__.py` exit 6 verified.
- Round 2 (3 failures): `missing_intent` line corrected to 1; `malformed_header` detection immediately after `#[` line; `duplicate_id` before `missing_intent`; CLI exit 6 verified.

## Carry-over

- Stages 5a/5b (v0.10.2 cycle): append_handoff implementation and test patch. Preserved as carry-over; revised 12b plan preserves the 9-key content dict contract.
- Stage 7b BISC section 5 amendment: subsumed by stage 12a Section 5.3. Close 7b carry-over once 12a commits.

## Next owner

- Stage 12a BISC file patch (single-file spec round, immediately next).
