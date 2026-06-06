# Changelog

All notable changes to the Babel protocol artifacts are recorded here.

## 2026-06-06 - Babel v0.8.1 remediation amendments (final)

Authored three additive amendment artifacts over frozen v0.1.0-v0.7.0 and v0.8.0, resolving all three DeepSeek v0.8.1 audit blocking issues plus the log-compaction clarification:

- **BCRP v0.8.1**: Corrected result ordering to (canonical SHA-256 hex, sequence number) lexicographic sort. Explicitly documented that this does NOT match append order; pagination cursor resumes from the strict successor in the composite sort. Defined cursor invalidation behavior after log compaction: gateway returns `cursor_invalid` error if both file and persistent log index entry are gone; client MUST restart from `cursor=null` to guarantee forward progress.

- **BSDC v0.8.1**: Specified deterministic LCS tie-breaking rule: when multiple LCS of equal maximum length exist, prefer the one retaining the lexicographically earliest tuples at the first differing index. Added four normative test vectors covering simple add, remove, replace, and nested object add. Post-application re-canonicalization (v0.2.0 NFC + sorted keys + deterministic numbers + single LF) verified against target.

- **BRAP v0.8.1**: Bounded the amend cycle: after original author submits revised document D' (with `meta.amend_of` referencing the amend review), the reviewer MUST issue `approve` or `reject`; no second amend is permitted. The three termination paths (author revision, timeout failure proxy, reviewer reject conversion) remain unchanged. Concurrent termination attempts resolve via CDR hash ordering (first canonical SHA-256 wins).

- **v0.8.1 manifest**: Lists BCRP, BSDC, BRAP v0.8.1 amendments with `canonical_sha256` placeholders for pre-commit hook computation. References frozen v0.8.0 manifest via `frozen_manifest_ref`.

All v0.8.1 artifacts are strictly additive; no frozen field is mutated. Cross-references to v0.8.0 BCRP/BSDC/BRAP remain valid as the base layer.

## 2026-06-06 - Babel v0.7.0 toolchain, workspace, and integration tests (final)

Authored three additive integration layers over frozen v0.1.0-v0.6.0, resolving all five DeepSeek v0.7.0 audit issues:

- **TIC v0.7.0**: platform field in manifest.json, filename triplet (linux-amd64, darwin-arm64, windows-amd64), reproducible tar flags, POSIX-only self-check.sh using packaged binaries only
- **WCP v0.7.0**: explicit .gitignore entries for .inbox/.processing/.processed/.invalid and handoff-log tmp/lock files; .gitattributes for binary JSON and LF-normalized BSS
- **ITP v0.7.0**: crash handling via signal/exit-code mapping to ITP exit 10, schema-first validation (exit 20) then byte comparison, platform-independent golden files

## 2026-06-06 - Babel v0.6.0 surface syntax and implementation contracts (final)

Authored three additive artifacts over frozen v0.1.0-v0.5.1:

- **BSS v0.6.0**: strict JSON5 subset with exhaustive forbidden constructs, bss_to_json canonicalization to v0.2.0
- **AIC v0.6.0**: babel-emit, babel-validate, babel-hash CLI tools with deterministic exit codes 0/1/2/3; babel-hash canonicalizes BSS internally before SHA-256
- **HIG v0.6.0**: .babel ingestion via ext.kimi.source_ext, atomic .inbox->.processing->.processed flow, startup recovery for orphaned .processing files

## 2026-06-06 - Babel v0.5.1 remediation amendments (final)

Resolved all five blocking gaps from DeepSeek's v0.5.0 audit. All amendments strictly additive over frozen v0.1.0-v0.5.0.

## 2026-06-06 - Babel v0.3.0 milestone architecture (revised)

Resolved the DeepSeek audit blocking issue: M1 and M2 could not safely run in parallel. Introduced M0 (Reference Parser Contract implementation) as a strict prerequisite for both M1 and M2. M1 and M2 may run in parallel after M0; M3 remains sequential.

## 2026-06-06 - Babel v0.2.0 final

Canonical serialization (NFC, deterministic numbers, single LF), handoff log (unique naming, fork resolution, genesis rule, async validation). All v0.1.0 contracts inherited unchanged.

## 2026-06-06 - Babel v0.1.0 frozen

Strict RFC 8259 JSON, SemVer with patch-agnostic compatibility, equal-minor silent-ignore extensions, operation_type enum with conditional rollback_to.
