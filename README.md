# MiniMadMax

Autonomous multi-agent engineering runtime for the Babel/BCPR/BISC stack.

## Components

- **Ollama runtime** — hosts `minimadmax:latest` and profile variants (`balanced`, `precise`, `fast`, `deep`).
- **GitHub CLI auth** — local `gh` with HTTPS git-credential helper; target repos: `Cole-Will-I-Am/MiniMadMax`, `Cole-Will-I-Am/new-lab`.
- **Babel spec** — `reference/babel/` (BSL grammar, parser, validator, handoff protocol, companion CLI).
- **BISC contract** — `autonomy-output/babel-bisc-integrity-v0.10.2.md` (Babel/Stable Integrity Convention: taxonomy, CLI wrapper, pre-commit hook).
- **BCPR protocol** — model-to-model handoff schema and conflict-free continuation rules.
- **Reference tests** — `reference/tests/` (handoff conformance, validation gate).

## Babel v0.10.3 — Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, and validator integration into the handoff write path. Completes the append-query collaboration loop started in v0.10.2.

### Stage map (v0.10.3)

- **Stage 6 (shipped 6e+6f)** — handoff query API and companion CLI `init` / `render` / `validate`.
- **Stage 7a+7b+7c (shipped)** — frozen handoff block schema with 9 keys, BISC section 5 amendment, and docs finalize.
- **Stage 9a+9b (shipped per coder)** — `HANDOFF_SCHEMA` TypedDict in `reference/babel/handoff.py` (9 keys: `path:str`, `content:str`, `agent_id:str`, `next_owner:str`, `signoff:bool`, `blocking_issues:list[str]`, `required_changes:list[str]`, `summary:str`, `memory_note:str`); `reference/tests/test_handoff_append.py` patched with conformance assertions.
- **Stage 10b (shipped per coder)** — `reference/babel/bsl_validator.py` with `validate_header`, `validate_body_kv`, `validate_version`, `validate_file`. Extra-keys policy is normative REJECT (rejects any body KV key not in the required set per block type: handoff = 9 HANDOFF_SCHEMA keys + `version`; intent = `{purpose, owner, version}`; meta = `{title, version}`).
- **Stage 10a (architecture approved, docs-only finalize shipped)** — version in body KV, required keys per block type, parser dependency with fallback.
- **Stage 11a (shipped per coder)** — `validate_block_string(block_type, header, kv_pairs)` in `bsl_validator.py` using direct-call composition; `header_type, block_id = validate_header(header, line_no=0); validate_body_kv(header_type, kv_pairs, line_no=0)`. The body validation uses the block_type returned from `validate_header` to prevent header-body mismatch.
- **Stage 11a2 (audit round 5: signoff)** — pre-write validation gate in `handoff.py` with `_encode_handoff_value` / `_decode_handoff_value` for str/list/bool, `HandoffIntegrityError` with `code` and `line_no` from `BabelParseError`. Imports: `validate_block_string` from `.bsl_validator`, `BabelParseError` from `.bsl_parser`. **Gating step: prerequisite micro-patch on `bsl_validator.py` (validate_version parameterization + removal of BABEL_VERSION import from handoff.py) must commit first.**
- **Stage 11b (queued)** — companion.py `lint <path>` subcommand.
- **Stage 11c (queued)** — `reference/tests/test_handoff_validation_gate.py`.
- **Stage 11d (queued)** — grammar manifest comment block in `bsl_validator.py`.

### Stage 11a2 — Handoff Pre-Write Gate Audit (Round 5: signoff)

DeepSeek audited Nemotron's corrected stage 11a2 implementation plan and signed off (`signoff=true`).

**Audit outcome:**
- ✅ **Pre-write validation gate** approved (validates the new block before `write_file`, raises `HandoffIntegrityError` on `BabelParseError`, no invalid block reaches disk).
- ✅ **Complete bool encoding** approved (lowercase `'true'`/`'false'` for the `signoff` key, symmetric decoding).
- ✅ **Scoped single-block validation** approved (gate calls `validate_block_string` on the constructed block; whole-file `validate_file` is reserved for the companion `lint` subcommand).
- ✅ **Dependency inversion** approved (prerequisite micro-patch parameterizes `validate_version(expected_version, version, line_no)` and removes any `BABEL_VERSION` import from `handoff.py` in `bsl_validator.py`).
- ✅ **Import topology** approved: `handoff.py` imports `validate_block_string` from `.bsl_validator` and `BabelParseError` from `.bsl_parser` (the exception's definition site). No circular import risk.

**Blockers (round 4) — all resolved in round 5:**
- ~~Prerequisite dependency inversion unverified~~ → resolved: prescribed as a single-file micro-patch on `bsl_validator.py`, must commit before 11a2.
- ~~BabelParseError import source incorrect~~ → resolved: corrected to `from .bsl_parser import BabelParseError`.

**Implementation queue (two-file prerequisite-then-11a2 sequence + downstream):**
1. **Prerequisite micro-patch (single-file, must commit first):** patch `reference/babel/bsl_validator.py` to parameterize `validate_version(expected_version, version, line_no)` and remove any `from .handoff import BABEL_VERSION` module-level import. Update internal callers to pass `BABEL_VERSION` explicitly.
2. **Stage 11a2 (single-file, gated on prerequisite):** patch `reference/babel/handoff.py` with imports, `_encode_handoff_value` / `_decode_handoff_value`, `HandoffIntegrityError`, and pre-write validation gate.
3. **Stage 11b (single-file):** patch `reference/babel/companion.py` to add `lint <path>` subcommand.
4. **Stage 11c (single-file):** author `reference/tests/test_handoff_validation_gate.py`.
5. **Stage 11d (single-file):** add grammar manifest comment block to `reference/babel/bsl_validator.py`.

**Cross-references:**
- `reference/babel/handoff.py` — `HANDOFF_SCHEMA` TypedDict and the three new helpers to be added in 11a2.
- `reference/babel/bsl_validator.py` — `validate_block_string` (direct-call composition, header-derived block_type).
- `reference/babel/bsl_parser.py` — `BabelParseError` (exception source for 11a2 import).
- `reference/babel/companion.py` — `lint` subcommand (stage 11b).

### Coder completion log (v0.10.3)

Per coder's prior round deliveries:
- Stage 9a — `HANDOFF_SCHEMA` TypedDict in `reference/babel/handoff.py`.
- Stage 9b — `reference/tests/test_handoff_append.py` conformance assertions.
- Stage 10b — `reference/babel/bsl_validator.py` with `validate_header` / `validate_body_kv` / `validate_version` / `validate_file` and extra-keys policy REJECT.
- Stage 11a — `validate_block_string` in `reference/babel/bsl_validator.py` (direct-call composition, header-derived block_type).
- `manifest.py` — `compute_basis_ref` with precedence chain.
- `bootstrap.py` — deterministic init.
- `bsl_parser` / `companion` / `handoff` circular-import triad — resolved.

### Anti-timeout cadence

The single-file-pair (README + CHANGELOG) finalize pattern has held timeouts at zero across stages 4c.2e+4c.2f, 6e+6f, 7c, 10a, 11a r1, 11a r2, 11a/11a2 r3, 11a2 r4, and 11a2 r5. The 8+ `TimeoutError` entries in the notes tail on this exact stage confirm that any multi-file code/spec delivery risks runtime failure. Implementation stages are decomposed into single-file sub-stages (prerequisite → 11a2 → 11b → 11c → 11d) preserving the cadence.

## Babel v0.10.2 — Handoff Append + Agent Identity (Shipped)

Append-side handoff protocol, agent identity convention, and BISC error taxonomy. Stage 4c.1 ships file_error and internal_error as the eighth and ninth codes (six library + two process). Stage 4c.2a-f decompose the 9-key schema definition into single-file sub-stages. Stages 5a/5b carry over into the v0.10.3 cycle.

## See also

- `CHANGELOG.md` — full version history.
- `autonomy-output/babel-bisc-integrity-v0.10.2.md` — BISC spec (taxonomy, CLI wrapper, pre-commit hook).
- `reference/babel/` — BSL grammar, parser, validator, handoff protocol, companion CLI.
