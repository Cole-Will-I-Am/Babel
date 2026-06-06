# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent engineering. Each version is a strictly additive layer on top of the previous frozen spec.

## Status

| Version | State   | Description                                                                                          |
|---------|---------|------------------------------------------------------------------------------------------------------|
| v0.1.0  | frozen  | Strict RFC 8259 JSON, SemVer, operation taxonomy, conditional rollback_to                            |
| v0.2.0  | frozen  | Canonical serialization (NFC, deterministic numbers, single LF), handoff log protocol                |
| v0.3.0  | frozen  | Reference Parser Contract, DTH, AIP, human+AI workflow milestones                                    |
| v0.4.0  | frozen  | Runtime: ASMC, TDS, DTL, HIG gateway, XRP cascade                                                    |
| v0.5.0  | frozen  | Execution layer: ASMC state machine, TDS ancestry, DTL timeout, XRP rollback                         |
| v0.5.1  | frozen  | Additive remediation: heartbeat exemption, deadline enforcement, crash proxy, ancestry index         |
| v0.6.0  | frozen  | Surface syntax (BSS), AIC CLI tools, HIG .babel acceptance                                           |
| v0.7.0  | frozen  | Toolchain (TIC), Workspace (WCP), Integration Test Protocol (ITP)                                    |
| v0.8.0  | frozen  | Context retrieval (BCRP), structural diff (BSDC), review protocol (BRAP)                             |
| v0.8.1  | final   | Additive remediation: composite hash-seq cursors, bounded amend cycle, LCS tie-breaking, scan limits |

## Architecture

Babel is a strictly additive protocol stack. Each version freezes its artifacts and amendments are published as a new version that references the frozen basis in its manifest. No frozen artifact is ever mutated.

The handoff log is an append-only directory of canonical JSON files with unique deterministic names. Agents write via atomic rename; readers never observe partial files. Cross-agent consistency is guaranteed by canonical SHA-256 identity.

## Versioning

Each version is strictly additive. A frozen version is never mutated; amendments are published as new versions that reference the frozen basis in their manifest. See `autonomy-output/babel-manifest-*.json` for the artifact list and canonical SHA-256 hashes of each version.

## Repository Layout

```
autonomy-output/
  babel-<protocol>-v<version>.md       # normative spec documents
  babel-manifest-v<version>.json       # artifact manifest with canonical SHA-256
  handoff-log/                          # append-only handoff log directory
human-src/
  .inbox/                               # human-authored .babel files awaiting ingestion
  .processing/                          # files currently being compiled
  .processed/                           # successfully ingested files
  .invalid/                             # files that failed ingestion (with .error.json)
```

## v0.8.1 Additions

- **BCRP composite cursor**: `sha256:<hex>:seq:<uint64>` resolves duplicate-hash ambiguity; results sort by (sha256, seq) lex order, NOT append order
- **BCRP compaction recovery**: cursor invalidation returns `cursor_invalid` error; client restarts from `cursor=null`
- **BRAP amend bound**: reviewer must approve or reject after author revision; no second amend per cycle
- **BSDC LCS tie-breaking**: deterministic rule preferring earliest sorted tuples; four normative test vectors
- **v0.8.1 manifest**: references frozen v0.8.0 manifest; hash placeholders for pre-commit hook
