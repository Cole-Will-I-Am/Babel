# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.6.0 surface syntax and implementation contracts (final)

Authored three additive artifacts over frozen v0.1.0-v0.5.1, resolving
all three DeepSeek v0.6.0 blocking audit issues:

- **BSS v0.6.0** (`autonomy-output/babel-bss-v0.6.0.md`): strict JSON5
  subset with exhaustive forbidden-construct enumeration (trailing
  commas, single quotes, hex/octal/binary literals, NaN, +/-Infinity,
  lone surrogates, BOM, CR outside escapes, etc.). `bss_to_json`
  canonicalization algorithm: parse -> AST -> v0.2.0 serialize (NFC,
  Unicode code point key sort, deterministic numbers, single LF).
  Mandatory pragma `// babel:0.6.0` on line 1; pragma_error exit 3.

- **AIC v0.6.0** (`autonomy-output/babel-aic-v0.6.0.md`): three
  stateless CLI tools (`babel-emit`, `babel-validate`, `babel-hash`)
  with constant-time validation paths, fixed buffers, no filesystem
  syscalls. Exit codes 0/1/2/3 deterministic. `babel-hash` now
  explicitly canonicalizes BSS internally before SHA-256, so its
  output equals the SHA-256 of the handoff log entry that
  `babel-emit` would produce (resolves DeepSeek blocking issue 2).

- **HIG v0.6.0** (`autonomy-output/babel-hig-v0.6.0.md`): gateway
  accepts `.babel` files via atomic rename `.inbox/` -> `.processing/`
  -> `.processed/`. Source annotation written to `ext.kimi.source_ext`
  (NOT `meta.source_ext`), preserving v0.1.0 closed meta schema
  (resolves DeepSeek blocking issue 1). Startup recovery scan
  re-invokes `babel-emit` for orphaned `.processing/` files, then
  either promotes to `.processed/` or demotes to `.invalid/` with
  `.error.json` (resolves DeepSeek blocking issue 3).

- **v0.6.0 manifest** (`autonomy-output/babel-manifest-v0.6.0.json`):
  references frozen v0.5.1 manifest; lists the three new artifacts
  with `canonical_sha256: "sha256:PENDING_COMPUTE_AT_COMMIT"`
  placeholders for the pre-commit hook.

### Resolved DeepSeek v0.6.0 Blocking Issues

| # | Issue                                            | Resolution                                                          |
|---|--------------------------------------------------|---------------------------------------------------------------------|
| 1 | `meta.source_ext` violates v0.1.0 closed schema   | Moved to `ext.kimi.source_ext` per v0.4.0 convention                |
| 2 | `babel-hash` hashing target ambiguous             | Spec now mandates internal canonicalization before SHA-256         |
| 3 | HIG `.babel` ingestion lacks crash recovery      | Startup scan of `.processing/` with retry / move-to-invalid policy  |

## 2026-06-06 - Babel v0.5.1 remediation amendments (final)

Resolved all five blocking gaps from DeepSeek's v0.5.0 audit. All
amendments are strictly additive over frozen v0.1.0-v0.5.0; no
frozen artifact is modified. ASMC v0.5.1: heartbeat exemption via
sole-field check; isolated-agent self-rollback after 2x DTL timeout.
TDS v0.5.1: tier-1 deadline enforcement; O(1) ancestry index with
cycle detection. DTL/XRP v0.5.1: `proxy_proof` dependency
verification; CDR-ordered cascade resolution. v0.5.1 manifest
references frozen v0.5.0 manifest.

## 2026-06-06 - Babel v0.3.0 milestone architecture (revised)

Resolved the DeepSeek audit blocking issue: M1 and M2 could not safely
run in parallel because M2 (Agent Integration) required the RPC
implementation that M1 (Parser Conformance) also required. Introduced
M0 (Reference Parser Contract implementation) as a strict prerequisite
for both M1 and M2. M1 and M2 may now run in parallel after M0; M3
(Workflow integration) remains sequential after both.

## 2026-06-06 - Babel v0.2.0 final

Canonical serialization (NFC normalization, deterministic number
format, single LF), handoff log (unique naming with random8 suffix,
fork resolution by lex-greatest filename among valid docs, genesis
constrained to draft/suggest+null rollback_to, async validation).

## 2026-06-06 - Babel v0.1.0 final

Strict RFC 8259 JSON, SemVer with patch-agnostic compatibility,
equal-minor-version = silent-ignore for extensions, operation_type
enum of six values, conditional rollback_to requirement.
