# Babel Canonical Serialization v0.2.0 (Final)

## Purpose
Define byte-exact serialization rules so that two independent implementations produce identical output for the same logical document. Required for stable SHA-256 state identity and conflict-free handoff.

## Encoding
- UTF-8, no BOM.
- No CRLF; LF (0x0A) is the only line terminator permitted within and between tokens.
- No trailing whitespace on any line.
- Output ends with exactly one LF character (0x0A); no trailing blank line.

## String Normalization
- All strings (values and keys) must be in Unicode Normalization Form C (NFC) before serialization.
- Non-NFC input must be normalized at parse time; normalization is a required pipeline stage.
- Unpaired UTF-16 surrogates are rejected.

## Object Key Ordering (MANDATORY)
- All object keys MUST be sorted lexicographically by Unicode code point of the NFC-normalized key string.
- Sort range: U+0020..U+10FFFF.
- Ties (equal code-point sequences) are broken by string length (shorter first).
- Sorting is recursive: nested objects apply the same rule.
- This rule is normative and required for SHA-256 stability across platforms.

## Number Formatting (DETERMINISTIC)
- Integers: decimal digits with no leading zeros (except the integer 0 itself); no decimal point; no exponent.
- Fractions: at least one digit after the decimal point; no trailing zeros after the decimal; no exponent.
  - Examples: `1` (integer), `1.0` (fractional), `0.1` (fractional); `1e0`, `.1`, `1.`, `1.00` are forbidden.
- Negative zero `-0` is forbidden; serialize as `0`.
- Numbers outside IEEE 754 double precision are rejected.

## Whitespace and Indentation
- 2-space indentation per nesting level.
- Single space after `:` and `,`.
- No whitespace inside empty `{}` or `[]` (compact form preferred); full spec allows either, but producers MUST pick one and consumers MUST accept both.

## Booleans and Null
- Lowercase only: `true`, `false`, `null`.

## Validation Order
1. Lex (strict RFC 8259).
2. NFC normalize strings.
3. Validate against v0.1.0 schema (tier 1).
4. Sort keys recursively by Unicode code point.
5. Format numbers deterministically.
6. Emit indented UTF-8 with single LF terminator.
7. SHA-256 hash the resulting byte sequence.

## Conformance Test Vector
A canonical vector suite is provided in `autonomy-output/babel-canonical-test-vectors-v0.2.0.json` containing inputs and expected SHA-256 hashes for round-trip verification.
