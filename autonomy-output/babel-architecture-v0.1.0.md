# Babel Protocol Architecture v0.1.0 (Final)

## 1. Design Principles
- Human-readable, machine-deterministic.
- Explicit versioning on every document.
- Small, enforceable contracts.
- Every irreversible recommendation must include a rollback path.

## 2. Strict JSON Subset
Documents use a strict RFC 8259 JSON subset:
- UTF-8 encoded.
- Double-quoted strings only; no single quotes.
- No comments, no trailing commas, no duplicate keys.
- Pretty-printing is recommended for human review but not normative.

## 3. Document Structure
```json
{
  "babel": { "version": "0.1.0" },
  "meta":  { "operation_type": "commit", "rollback_to": null },
  "payload": { },
  "ext": { "kimi.feature": { } }
}
```

## 4. Versioning Rules
- `babel.version` is mandatory and must be a valid SemVer 2.0.0 string.
- Pre-release tags (e.g. `0.1.0-rc.1`) are permitted but ignored for compatibility checks; only major.minor.patch matter.
- Major version mismatch: parser MUST reject the document with an error.
- Minor version mismatch: handled per Section 5 (extensions) and Section 6 (operations).
- Patch version differences are always compatible. Patch-level mismatches MUST NOT trigger extension warnings, errors, or operation_type rejection. Parsers MUST treat any two documents with the same major.minor as patch-compatible.

## 5. Extension Handling
- Extensions live under `ext.<owner>.<feature>` (e.g. `ext.kimi.suggestion`).
- Reserved prefixes are tracked in the extension registry; unreserved prefixes trigger the same handling as unrecognized extensions.
- Compatibility is determined by minor version:
  - document.major != parser.major: error, document rejected.
  - document.minor > parser.minor: unrecognized extensions produce a warning (non-fatal).
  - document.minor == parser.minor: unrecognized extensions are silently ignored.
  - document.minor < parser.minor: unrecognized extensions are silently ignored.
- The "equal minor" case is intentionally treated identically to "behind": both are silent ignore. Only "ahead within the same major" produces a warning.

## 6. Operation Taxonomy
- `meta.operation_type` is required and MUST be one of the six defined values. Unknown values cause validation failure (schema enum).
- Irreversible types: `commit`, `destroy`, `approve`.
- Reversible types: `draft`, `query`, `suggest`.
- For irreversible operations, `meta.rollback_to` MUST be a non-null string referencing a recoverable state hash.
- For reversible operations, `meta.rollback_to` MUST be `null`.
- This conditional requirement is enforced directly by the JSON Schema (if/then/else).

## 7. Verification Tiers
- Tier 1: JSON Schema validation. Normative. Automated. Document validity is determined solely by Tier 1.
- Tier 2: Semantic linting. Non-normative, agent-assisted. Advisory only.
- Tier 3: Property-based fuzzing. Non-normative, agent-assisted. Advisory only.

## 8. Division of Labor
- Human: intent, breaking-change approval.
- Architect (kimi): syntax, schema, protocol contracts.
- Verifier (nemotron): determinism proofs, edge cases, validation rules.
- Analyst (deepseek): audits, gap analysis.
- Implementer (minimadmax): parsers, code generation, runbooks.

## 9. Tradeoffs
- Strict JSON over YAML: deterministic, verbose, unambiguous.
- Centralized schema with registry warnings: one source of truth, local extension escape hatch.
- Three-tier verification with only Tier 1 normative: implementation velocity, clear validity semantics.