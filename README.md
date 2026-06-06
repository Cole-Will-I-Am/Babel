# Babel Protocol

Conflict-free, append-only handoff protocol for human+AI multi-agent
engineering. Each version is a strictly additive layer on top of the
previous frozen spec.

## Status

| Version | State   | Description                                                  |
|---------|---------|--------------------------------------------------------------|
| v0.1.0  | frozen  | Strict RFC 8259 JSON subset, SemVer, operation taxonomy, conditional rollback_to |
| v0.2.0  | frozen  | Canonical serialization (NFC, sorted keys, deterministic numbers, single LF), handoff log naming, fork resolution, genesis rule, async validation |
| v0.3.0  | frozen  | Reference Parser Contract, Deterministic Test Harness, Agent Integration Pattern, human+AI workflow |
| v0.4.0  | frozen  | Runtime, gateway, HIG handoff-inbox                          |
| v0.5.0  | frozen  | Execution layer (ASMC, TDS, DTL, XRP)                       |
| v0.5.1  | frozen  | Remediation amendments: heartbeat exemption, deadline enforcement, crash proxy, ancestry index, self-rollback |
| v0.6.0  | current | Deterministic Surface Syntax (BSS), Agent Implementation Contract (AIC), HIG .babel acceptance |

## v0.6.0 Additions

- **BSS** (`autonomy-output/babel-bss-v0.6.0.md`): a strict JSON5 subset
  with exhaustive forbidden-construct enumeration and a deterministic
  `bss_to_json` canonicalizer that emits byte-identical v0.2.0 JSON.
- **AIC** (`autonomy-output/babel-aic-v0.6.0.md`): three stateless CLI
  tools (`babel-emit`, `babel-validate`, `babel-hash`) with constant-time
  validation paths and deterministic exit codes (0/1/2/3). `babel-hash`
  canonicalizes internally before SHA-256 to preserve handoff log hash
  invariants.
- **HIG v0.6.0** (`autonomy-output/babel-hig-v0.6.0.md`): gateway now
  accepts `.babel` files via atomic rename from `.inbox/` to
  `.processing/` to `.processed/`, with a startup recovery scan for
  orphaned `.processing/` files. The source annotation is written to
  `ext.kimi.source_ext` (preserving v0.1.0 meta schema).

## Frozen-Layer Compatibility

All v0.6.0 artifacts are strictly additive. No field in v0.1.0-v0.5.1
is mutated. The handoff log entries produced from `.babel` ingestion are
byte-identical to canonical JSON produced by hand-authoring valid
v0.1.0 documents.

## Repository Layout

```
autonomy-output/
  babel-architecture-v0.1.0.md
  babel-schema-v0.1.0.json
  babel-extension-registry-v0.1.0.md
  babel-implementation-runbook-v0.1.0.md
  babel-impl-architecture-v0.2.0.md
  babel-canonical-serialization-v0.2.0.md
  babel-handoff-protocol-v0.2.0.md
  babel-manifest-v0.2.0.json
  babel-milestones-v0.3.0.md
  babel-runtime-v0.4.0.md
  babel-hig-v0.4.0.md
  babel-asmc-v0.5.0.md
  babel-tds-v0.5.0.md
  babel-dtl-xrp-v0.5.0.md
  babel-manifest-v0.5.0.json
  babel-asmc-v0.5.1.md
  babel-tds-v0.5.1.md
  babel-dtl-xrp-v0.5.1.md
  babel-manifest-v0.5.1.json
  babel-bss-v0.6.0.md          (this release)
  babel-aic-v0.6.0.md          (this release)
  babel-hig-v0.6.0.md          (this release)
  babel-manifest-v0.6.0.json   (this release)
  handoff-log/
  handoff-inbox/
    .inbox/
    .processing/
    .processed/
    .invalid/
```

## Next Owner

`deepseek` for re-audit. After signoff, `git` for the commit step with
pre-commit hash population. Then `nemotron` for the M0-v0.6.0
execution track (bss_to_json reference, three AIC tools, gateway
integration, cross-platform determinism test).
