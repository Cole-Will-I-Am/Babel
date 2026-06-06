# Babel Extension Prefix Registry v0.1.0

## Reserved Prefixes
| Prefix   | Owner        | Contact       |
|----------|--------------|---------------|
| kimi     | Architect    | kimi          |
| nemotron | Verifier     | nemotron      |
| deepseek | Analyst      | deepseek      |
| minimadmax | Implementer | minimadmax  |

## Governance
- New prefixes require a human-approved PR to this file.
- Each prefix maps to exactly one owner agent or human role.
- Unreserved prefixes encountered at parse time are handled per architecture section 5:
  - Major version mismatch: error.
  - Document minor > parser minor: warning.
  - Document minor == parser minor: silently ignored.
  - Document minor < parser minor: silently ignored.
- Patch version differences never affect extension handling.

## Naming Rules
- Each segment MUST match `^[a-z][a-z0-9_]*$`.
- At least two segments required (e.g. `kimi.feature`).
- Extensions are namespaced under `ext.<prefix>.<feature>` in the document.

## Initial Set Justification
The four prefixes bootstrap the multi-agent workflow described in architecture section 8. Additional agents (e.g. future verifiers) must request prefixes through the governance process.