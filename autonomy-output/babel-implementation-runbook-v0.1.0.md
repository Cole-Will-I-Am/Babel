# Babel v0.1.0 Implementation Runbook

## Purpose
Step-by-step guidance for implementers building Babel v0.1.0 parsers and validators. Aligned with architecture v0.1.0 and schema v0.1.0.

## 1. Parse Strict JSON
- Use a strict RFC 8259 parser. Reject: comments, trailing commas, single quotes, duplicate keys, non-UTF-8 input.
- If parsing fails, return a parse error. Do not attempt recovery.

## 2. Validate Against Schema
- Validate the parsed object against `babel-schema-v0.1.0.json` using a JSON Schema draft-07 validator.
- If validation fails, return validation errors keyed by JSON pointer.
- Validation is the sole normative check; pass = valid document.

## 3. Version Compatibility Check
- Parse `babel.version` as SemVer 2.0.0.
- Compare `major`:
  - mismatch: ERROR, reject.
  - match: proceed.
- Compare `minor`:
  - `doc.minor > parser.minor`: set `ext_warn = true`.
  - `doc.minor <= parser.minor`: `ext_warn = false`.
- Compare `patch`: differences are always compatible; ignore.

## 4. Extension Handling
- Enumerate keys under `ext`.
- For each key, take the first segment as the prefix.
- If prefix is in the registry: process as known extension (no warn, no error).
- If prefix is not in the registry:
  - `ext_warn == true`: emit a non-fatal warning.
  - `ext_warn == false`: silently ignore.
- Never fail validation on unrecognized extensions within the same major version.

## 5. Operation Type Handling
- Read `meta.operation_type` (already enum-validated by schema).
- Branch on the value:
  - `commit`, `destroy`, `approve`: irreversible. Confirm `meta.rollback_to` is a non-null string (schema enforces).
  - `draft`, `query`, `suggest`: reversible. Confirm `meta.rollback_to` is null (schema enforces).
- If schema validation passed, this check is a sanity log, not a re-check.

## 6. Reference Implementation Skeleton (pseudocode)
```
function validate(doc, parser_version, registry):
  parse_json_strict(doc) -> err on fail
  validate_schema(doc, SCHEMA_V010) -> err on fail
  d = parse_semver(doc.babel.version)
  p = parse_semver(parser_version)
  if d.major != p.major: return error("major mismatch")
  warn_extensions = d.minor > p.minor
  for key in doc.ext:
    prefix = key.split(".")[1]
    if prefix not in registry:
      if warn_extensions: emit_warning(key)
  return ok(doc)
```

## 7. Testing Checklist
- [ ] Parse rejection: comments, trailing commas, single quotes, duplicate keys.
- [ ] Schema reject: missing `babel.version`.
- [ ] Schema reject: `meta.operation_type` outside enum.
- [ ] Schema reject: `commit` with `rollback_to: null`.
- [ ] Schema accept: `draft` with `rollback_to: null`.
- [ ] Major mismatch: error.
- [ ] Patch mismatch: accepted, no warn.
- [ ] Equal minor + unknown ext: silent ignore.
- [ ] Ahead minor + unknown ext: warning.
- [ ] Behind minor + unknown ext: silent ignore.
- [ ] Round-trip: write and re-read produces equal canonical form.

## 8. Non-Goals (Tier 2/3)
- Semantic linting and fuzzing are non-normative. Do not gate document validity on them. They are agent-assisted QA tools only.