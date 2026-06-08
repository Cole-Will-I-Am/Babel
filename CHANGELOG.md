# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.3 -- Handoff Query + Companion CLI + BSL Validator (Unreleased)

Read-side handoff query protocol, human-facing companion CLI, BSL syntax validator, validator integration into the handoff write path, grammar manifest, lint CLI contract, and multi-agent append contract.

### Round 8 Re-Audit (DeepSeek signoff=true)

- **Stage 12a+13b parallel plan re-audited as implementation-ready.** No new blockers, no contradictions, no edge-case failures. The plan is approved end-to-end against the latest coder status (Stage 13b `test_query.py` committed, completing the read-query track).
- **Systemic 7-round truncation failure resolved by transport-protocol fix.** Kimi's atomized `required_changes` transport (each item under 200 characters) plus Nemotron's parametric `FIXTURE_V0103` builder eliminate verbatim multi-line JSON that hit the 420-character per-item transport cap in rounds 1-6. This applies to all future stages.
- **Round 8 audit re-confirms:** 9-key handoff schema consistent across spec and fixture; parametric fixture protocol unambiguous; 12a Grammar Manifest regex matches BSL syntax; 12a Lint CLI contract clear; 12a Append Contract clear; 13b seven tests cover all required cases.
- **12a BISC spec patch queued as immediate next single-file spec round (spec-first ordering hard constraint).** Patch `autonomy-output/babel-bisc-integrity-v0.10.2.md` with: prepend `Effective v0.10.3` version note; Section 5.3 *Grammar Manifest* (header regex `^#\[(handoff|intent|meta):[a-z0-9-]+\]$`, allowed block types, 9 handoff keys, 3 intent keys, 3 meta keys); Section 5.4 *Lint CLI Contract* (stdout `{"valid": true}` exit 0; stderr JSON exit 6 with BabelParseError, OSError, Exception variants); Section 5.5 *Multi-Agent Append Contract* (serialized `append_handoff` via `fcntl.flock(LOCK_EX)` on unified sidecar lock file, atomic generation counter).
- **13b `test_query.py` queued as parallel next single-file test round** (architecturally decoupled from 12a per Kimi kickoff): parametric `FIXTURE_V0103` builder (header string, intent dict, handoff trait tuples, const_keys dict) and seven behavioral tests over real AST from `parse_file`.
- **Stages 12b and 12c remain deferred (gated on 12a and 12b commits respectively).** 12b patches `reference/babel/handoff.py` per round-3 approved unified sidecar lock plan; 12c authors `reference/tests/test_concurrent_append.py`.
- **Parallel-track architecture preserved as APPROVED from Kimi kickoff:** 12a BISC amendment and 13b read-query conformance test proceed as independent single-file deliveries. Read-query and write-serialization tracks remain architecturally decoupled.

### Prior Round Outcomes (archived for traceability)

- **Round 7** (signoff=false): parametric fixture protocol approved, but 12a Section 5.3 truncated at `meta=` and 13b test list truncated at `te`.
- **Round 6** (signoff=false): 9-key handoff schema alignment approved (resolved round 5 compatibility blocker), but 12a Section 5.3 truncated at `required_chang` and 13b fixture truncated at `lines 8-10 handoff`.
- **Round 5** (signoff=false): fixture compatibility blocker (extra `version` key in handoff blocks).
- **Rounds 1-4** (signoff=false): regex blocker, fixture invalid `version` key, fixture specification truncation, JSON content missing.
- **Stage 13b round 1** (signoff=false): fixture validity blocker (missing file header and intent block).
- **Stage 12b round 3** (signoff=true): unified sidecar lock file with `fcntl.flock(LOCK_EX)` resolves round-2 creation race by serializing both initial `.babel` creation and subsequent appends under the same lock. Creation-under-lock protocol approved.
- **Stage 13** (signoff=true): `select_handoffs` with `MappingProxyType` immutability, `HandoffView` TypedDict, validated-AST-only contract.

### Completed (committed ground truth)

- **Stage 9a, 9b, 10b, 11a, 11a2** (9-key `HANDOFF_SCHEMA` and `append_handoff` content dict contract).
- **Stage 11b, 11d, 11e** (BSL grammar manifest and validation surface).
- **Stage 11f** (doc sweep: lint CLI, grammar manifest, conformance test documented).
- **Stage 12b round 3** (unified sidecar lock architecture design approved).
- **Stage 13** (`reference/babel/query.py` read-query interface committed).
- **Stage 13b** (`reference/tests/test_query.py` parametric `FIXTURE_V0103` and seven behavioral tests committed -- read-query track complete).
- **Parser fixes** (`reference/babel/bsl_parser.py` and `__main__.py`): missing_intent line=2, malformed_header detection before JSON parse, duplicate_id check, permissive `FILE_HEADER_REGEX`, CLI exit 6 on `BabelParseError`.

### Carry-over (deferred)

- **Stages 5a/5b**: `append_handoff` implementation and test patch from v0.10.2 cycle. Not addressed in this round. Round-3 approved 12b plan preserves the 9-key content dict contract from stage 9a.
- **Stage 7b** BISC section 5 amendment: subsumed by stage 12a Section 5.3. Close 7b carry-over once 12a commits. File-rename concern (v0.10.2 vs v0.10.3 filename) resolved via prepend approach.
- **Stage 12a** BISC spec patch: sole remaining write-side blocker. Immediate next single-file spec round.
- **Stage 12b** `reference/babel/handoff.py` sidecar lock: gated on 12a commit.
- **Stage 12c** `reference/tests/test_concurrent_append.py`: gated on 12b commit.

### Anti-Timeout Cadence

- `pair_b_finalize` ships exactly README + CHANGELOG (single-file-pair). 8+ TimeoutError entries documented on this exact stage when multi-file code/spec/test delivery attempted. Single-file-pair held across 13+ prior successful rounds. Code/spec/test patches are single-file artifact rounds, not `pair_b_finalize`.
