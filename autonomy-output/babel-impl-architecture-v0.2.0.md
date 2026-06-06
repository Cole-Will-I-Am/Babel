# Babel Implementation Architecture v0.2.0 (Final)

## Basis
Builds on frozen Babel v0.1.0 spec (DeepSeek signoff). All v0.1.0 contracts (strict RFC 8259, SemVer, extension registry, operation taxonomy, conditional rollback_to) are inherited unchanged. No normative schema changes in v0.2.0.

## Pipeline (Canonical Order)
1. **Lexer**: strict RFC 8259. Rejects comments, trailing commas, single quotes, duplicate keys, NaN/Infinity.
2. **Normalizer**: apply Unicode Normalization Form C (NFC) to every string value and key. Reject unpaired surrogates.
3. **Schema Validator (Tier 1)**: validate against `autonomy-output/babel-schema-v0.1.0.json`. Enforces operation_type enum and conditional rollback_to rule. Documents failing this stage are flagged invalid; they remain in the log but are ineligible for state progression.
4. **AST Builder**: produce canonical AST with keys already in NFC form.
5. **Key Sorter**: recursively sort all object keys lexicographically by Unicode code point (U+0020..U+10FFFF); ties broken by string length.
6. **Number Formatter**: integers as decimal digits with no leading zeros (except 0); fractional numbers with at least one digit after decimal, no trailing zeros, no exponential notation.
7. **Serializer**: emit 2-space indented JSON, UTF-8 without BOM, terminated by exactly one LF (0x0A). No trailing whitespace.
8. **Hasher**: SHA-256 of the canonical byte sequence is the document identity.

## Canonical Output
- 2-space indentation.
- Keys sorted lexicographically by Unicode code point.
- LF line endings, single terminator LF.
- UTF-8 without BOM.
- NFC-normalized strings.
- Deterministic number formatting.

## Handoff Integration
The handoff log manager invokes stages 1-8 on every document before append. Validation is decoupled from append: invalid documents are appended with a `validation: invalid` marker in the manifest but never selected by fork resolution.

## Compatibility
- v0.2.0 documents are valid v0.1.0 documents at the schema level.
- v0.1.0 parsers reading v0.2.0 documents must ignore unknown top-level fields per v0.1.0 extension rules.
- Patch-version differences in document versions are declared compatible.

## Milestones
- M1: Lexer, normalizer, key sorter, serializer, hasher.
- M2: Tier-1 schema validator and extension namespace checker.
- M3: Handoff log manager with atomic rename and git bridge.
- M4: Agent adapter templates and integration tests.

## Rollback
Any breaking pipeline change requires a Babel document with non-null `meta.rollback_to` referencing the SHA-256 of the last known good canonical state.
