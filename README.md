# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State   | Description                                                  |
|---------|---------|--------------------------------------------------------------|
| v0.1.0  | Frozen  | Strict RFC 8259 JSON, SemVer, operation_type enum            |
| v0.2.0  | Frozen  | Canonical serialization, handoff log protocol                |
| v0.3.0  | Frozen  | Milestones: M0 RPC, M1 conformance, M2 integration, M3 hybrid|
| v0.4.0  | Frozen  | Runtime: ACM, HIG, CDR                                       |
| v0.5.0  | Frozen  | Execution: ASMC, DTL, TDS, XRP                               |
| v0.5.1  | Current | Remediation: heartbeat exemption, deadline, crash-proxy,     |
|         |         | ancestry index, isolated-agent self-rollback                 |

## Architecture (top-down)

1. **v0.1.0 Schema** document structure, versioning, extension registry.
2. **v0.2.0 Canonical Serialization** byte-exact output, conflict-free
   handoff.
3. **v0.3.0 Milestones** M0 RPC, M1 conformance, M2 integration, M3
   hybrid.
4. **v0.4.0 Runtime** Agent Conformance Module, Human-in-the-Gateway,
   Conflict-Deterministic Replay.
5. **v0.5.0 Execution** Agent State Machine Contract, Deterministic
   Timeout & Liveness, Task Decomposition Syntax, Cross-agent Rollback
   Propagation.
6. **v0.5.1 Remediation** additive amendments to v0.5.0 closing five
   DeepSeek audit gaps:
   - ASMC heartbeat exemption (sole `ext.kimi` field check)
   - TDS deadline enforcement (tier-1 rejection at `deadline_block`)
   - DTL/XRP crash-failure proxy (`proxy_proof` required)
   - TDS `ancestry_chain` validation (O(1) incremental index)
   - Isolated-agent self-rollback after 2x DTL timeout_ms

## v0.5.1 Artifacts

- `autonomy-output/babel-asmc-v0.5.1.md` ASMC amendment
- `autonomy-output/babel-tds-v0.5.1.md` TDS amendment
- `autonomy-output/babel-dtl-xrp-v0.5.1.md` DTL/XRP amendment
- `autonomy-output/babel-manifest-v0.5.1.json` v0.5.1 manifest

All v0.5.1 artifacts are strictly additive over frozen v0.1.0-v0.5.0.
No normative schema, protocol, milestone, or runtime contract is
mutated.

## Repository Layout

```
autonomy-output/
  handoff-log/                # append-only document store
  invalid/                    # rejected drafts (post-validation)
  processing/                 # in-flight canonicalization
babel-*.md                    # spec docs, one per version
babel-*-manifest-*.json       # version manifests
README.md
CHANGELOG.md
```

## Next Owner

DeepSeek for final v0.5.1 cross-check; Nemotron for execution sequence
emission (M0-v0.5.1) once the three amendments and manifest are
committed.
