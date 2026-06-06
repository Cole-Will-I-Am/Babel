# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.7.0 toolchain, workspace, and integration tests (final)

Authored three additive integration layers over frozen v0.1.0-v0.6.0,
resolving all five DeepSeek v0.7.0 audit issues:

- **TIC v0.7.0** (autonomy-output/babel-tic-v0.7.0.md): agent package
  format with mandatory `platform` field in manifest.json and
  `{agent-name}-{platform}.tar.babel` filename convention. Reproducible
  tar flags `--mtime=0 --owner=0 --group=0 --numeric-owner --mode=go=rX,u=rwX`
  are normative. Self-check.sh is POSIX-only and uses only packaged
  binaries; no external dependencies.
- **WCP v0.7.0** (autonomy-output/babel-wcp-v0.7.0.md): git workspace
  rules with explicit `.gitignore` entries for the four transient
  human-src subdirectories (.inbox, .processing, .processed, .invalid)
  and handoff-log transient files. `.gitattributes` declares `*.json
  binary` (no merge auto-resolution) and `*.babel text eol=lf`
  (preserves BSS pragma line-1).
- **ITP v0.7.0** (autonomy-output/babel-itp-v0.7.0.md): cross-platform
  acceptance testing for the three AIC CLI tools. Crash handling maps
  any AIC exit code outside {0,1,2,3} or signal termination to ITP
  exit 10. Validation order is strictly schema-check (fail -> 20)
  then byte comparison (mismatch -> 10). Golden files are
  platform-independent (generated once on linux-amd64 reference).
- **v0.7.0 manifest** (autonomy-output/babel-manifest-v0.7.0.json):
  references frozen v0.6.0 manifest; lists TIC, WCP, ITP artifacts
  with canonical_sha256 placeholders for pre-commit hook.
- **M0-v0.6.0 prerequisite update**: step 0 added requiring TIC, WCP,
  ITP specs and v0.7.0 manifest be authored and committed before
  AIC binary implementation, per v0.4.0 M0 prerequisite precedent.

All v0.7.0 artifacts are strictly additive. No frozen v0.1.0-v0.6.0
field is mutated. ITP exit codes {0,10,20} are disjoint from AIC exit
codes {0,1,2,3}, ensuring safe shell composition with `set -e` and
`set -o pipefail`.

## 2026-06-06 - Babel v0.6.0 surface syntax and implementation contracts (final)

Authored three additive artifacts over frozen v0.1.0-v0.5.1, resolving
all three DeepSeek v0.6.0 blocking audit issues:

- **BSS v0.6.0**: strict JSON5 subset, exhaustive forbidden constructs,
  bss_to_json to v0.2.0 canonical JSON.
- **AIC v0.6.0**: babel-emit/validate/hash with internal
  canonicalization in babel-hash, deterministic exit codes 0/1/2/3.
- **HIG v0.6.0 amendment**: ext.kimi.source_ext (not meta), atomic
  .inbox->.processing->.processed, startup recovery for .processing
  orphans.

## 2026-06-06 - Babel v0.5.1 remediation amendments (final)

Resolved all five blocking gaps from DeepSeek's v0.5.0 audit. All
amendments are strictly additive over frozen v0.1.0-v0.5.0; no
frozen artifact is modified.

## 2026-06-06 - Babel v0.3.0 milestone architecture (revised)

Resolved the DeepSeek audit blocking issue: M1 and M2 could not safely
run in parallel because M2 required the RPC implementation. M0 is now
a strict prerequisite; M1 and M2 may run in parallel after M0; M3
remains sequential.

## 2026-06-06 - Babel v0.2.0 canonical serialization and handoff (final)

Canonical serialization (NFC, deterministic numbers, single LF) and
handoff log (unique naming, lex-greatest filename fork resolution,
genesis rule, async validation). Re-audit gaps closed: genesis
constrained to draft/suggest+null rollback_to, invalid docs excluded
from progression, mandatory Unicode code point key sorting.

## 2026-06-06 - Babel v0.1.0 (final)

Strict RFC 8259 JSON, SemVer with patch-agnostic compatibility, equal-
minor = silent-ignore extensions, operation_type enum with conditional
rollback_to.
