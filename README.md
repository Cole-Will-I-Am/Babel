# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State              | Description                                                          |
|---------|--------------------|----------------------------------------------------------------------|
| v0.1.0  | Frozen             | Normative schema, operation taxonomy, extension registry             |
| v0.2.0  | Frozen             | Canonical serialization, handoff protocol, fork resolution           |
| v0.3.0  | Architecture done  | RPC, DTH, AIP, human+AI bridge. Awaiting M0 RPC implementation.      |

## Releases

### v0.1.0 (frozen)
Strict RFC 8259 JSON, SemVer with patch-agnostic compatibility, equal-minor
silent-ignore for unknown extensions, `operation_type` enum with conditional
`rollback_to`. Artifacts:
- `autonomy-output/babel-architecture-v0.1.0.md`
- `autonomy-output/babel-schema-v0.1.0.json`
- `autonomy-output/babel-extension-registry-v0.1.0.md`
- `autonomy-output/babel-implementation-runbook-v0.1.0.md`

### v0.2.0 (frozen)
NFC canonical serialization, deterministic number format, single LF line
ending, Unicode code point key sorting, append-only handoff log with
deterministic file naming, fork resolution by lex-greatest filename, genesis
restricted to reversible types, async tier-1 validation. Artifacts:
- `autonomy-output/babel-impl-architecture-v0.2.0.md`
- `autonomy-output/babel-canonical-serialization-v0.3.0.md`
- `autonomy-output/babel-handoff-protocol-v0.2.0.md`
- `autonomy-output/babel-v0.2.0-changelog.md`

### v0.3.0 (architecture approved)
Reference Parser Contract (RPC), Deterministic Test Harness (DTH), Agent
Integration Pattern (AIP), human+AI collaboration bridge via
`ext.human.intent`. Milestone execution: M0 RPC implementation, then M1
parser conformance and M2 agent integration in parallel, then M3 human+AI
workflow. Artifacts:
- `autonomy-output/babel-milestones-v0.3.0.md`
- `autonomy-output/babel-v0.3.0-changelog.md`

## Next Steps
- Author the DTH golden file matrix in `autonomy-output/dth-golden-v0.3.0/`.
- Generate `autonomy-output/babel-manifest-v0.2.0.json` with canonical
  SHA-256 hashes of the four v0.2.0 artifacts.
- Begin M0: implement the RPC in reference language (Python 3.11+).
- Update the extension registry with a v0.3.0 milestone usage example.
