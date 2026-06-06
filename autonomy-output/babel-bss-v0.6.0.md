# Babel Surface Syntax (BSS) v0.6.0

## Status
Additive layer over frozen Babel v0.1.0-v0.5.1. Defines a human-authorable
surface syntax that compiles deterministically to v0.2.0 canonical JSON. No
frozen field is mutated. The handoff log entries produced by `bss_to_json`
are byte-identical to the canonical JSON specified in
`autonomy-output/babel-canonical-serialization-v0.2.0.md`.

## 1. File Extension and Pragma

- File extension: `.babel`.
- Line 1, before any other content, must be a single-line comment:
  `// babel:0.6.0`
- Lines 2..N contain the document body (or leading comments, which are
  stripped before parse).
- Compilation fails with `pragma_error` (exit code 3) if line 1 is missing,
  has a different version, or uses block-comment syntax for the pragma.

## 2. Grammar (EBNF)

```
document     = pragma , ( comment | value ) ;
pragma       = "// babel:0.6.0" , LF ;
comment      = line-comment | block-comment ;
line-comment = "//" , { not-LF } , LF ;
block-comment= "/*" , { not-star | "*" not-slash } , "*/" ;
value        = object | array | string | number | "true" | "false" | "null" ;
object       = "{" , [ member , { "," , member } ] , "}" ;
member       = key , ":" , value ;
key          = string | ident ;
ident        = ( "$" | "_" | letter ) , { "$" | "_" | letter | digit } ;
string       = "\"" , { char | escape } , "\"" ;
escape       = "\\" , ( "\"" | "\\" | "/" | "b" | "f" | "n" | "r" | "t" | "u" hex4 ) ;
number       = [ "-" ] , ( "0" | digit1-9 { digit } ) , [ "." , digit { digit } ] ;
```

Ident keys are restricted to the JS-identifier subset
`/^[A-Za-z_$][A-Za-z0-9_$]*$/`. Reserved JSON keywords (`true`, `false`,
`null`) are not valid as unquoted ident keys; they must be quoted strings.

## 3. Forbidden Constructs (Exhaustive)

Compilation MUST fail (exit code 1, error code `forbidden_construct`) if
any of the following appear:

| Construct                              | Rationale                          |
|----------------------------------------|------------------------------------|
| Trailing comma in object/array         | JSON5 ambiguity                    |
| Single-quoted strings                  | Encoding ambiguity                 |
| Hex (`0x`), octal (`0o`), binary (`0b`)| Cross-platform parse divergence    |
| Leading `+` on numbers                 | JSON5 ambiguity                    |
| Leading zeros on non-zero integers    | Octal confusion                    |
| `NaN`, `+Infinity`, `-Infinity`        | Not in JSON; not representable     |
| `undefined` literal                    | Not in JSON                        |
| Lone surrogates in strings             | Non-UTF-8 invariant violation      |
| Non-standard escapes (`\x`, `\v`)     | JSON spec violation                |
| Unquoted ident keys containing `-`    | Identifier subset above is strict  |
| Multiple top-level values             | JSON requires single root          |
| BOM anywhere in the file               | Breaks byte-equality invariant     |
| CR (0x0D) outside of allowed CRLF escapes| Line ending ambiguity            |

## 4. Canonicalization Algorithm (`bss_to_json`)

```
function bss_to_json(bss_bytes):
    raw = bss_bytes.decode("utf-8")         // reject if not valid UTF-8
    if raw[0:1] == "\uFEFF": reject "forbidden_construct: BOM"
    lines = raw.split("\n")
    if not lines[0].startswith("// babel:0.6.0"):
        reject "pragma_error: missing or wrong pragma"
    body = "\n".join(lines[1:])
    tokens = lex(body)                       // strips comments first
    ast    = parse(tokens)                   // validates forbidden constructs
    canon  = serialize_v020(ast)             // v0.2.0 canonical JSON
    return canon.encode("utf-8") + b"\n"     // single LF terminator
```

`serialize_v020` is the canonicalization function defined in
`autonomy-output/babel-canonical-serialization-v0.2.0.md`:
NFC normalize all strings, sort object keys lexicographically by Unicode
code point (ties broken by string length), format numbers deterministically
(no leading zeros, single trailing-zero-stripped decimal), end with one LF.

## 5. Test Vectors

### TV-1: Ident keys + comment
Input:
```
// babel:0.6.0
// a meta block
{
  doc_id: "v6-tv1",
  meta: { version: "0.6.0", operation_type: "draft", rollback_to: null },
  body: { value: 42 }
}
```
Expected canonical JSON (bytes):
```
{"body":{"value":42},"doc_id":"v6-tv1","meta":{"operation_type":"draft","rollback_to":null,"version":"0.6.0"}}
```
SHA-256 of expected: `sha256:PENDING_COMPUTE_AT_COMMIT`

### TV-2: Forbidden trailing comma
Input ends with `,\n}` after member list.
Expected: exit 1, stderr `{"code":"forbidden_construct","message":"trailing comma","line":N,"column":M}`.

### TV-3: Pragma missing
Input starts with `{`.
Expected: exit 3, stderr `{"code":"pragma_error","message":"missing or wrong pragma","line":1,"column":1}`.

## 6. Determinism Guarantee

`bss_to_json` is pure: no filesystem access, no clock reads, no
environment-variable reads. Two independent implementations of the
algorithm above MUST produce byte-identical output for any valid input
on Linux, macOS, and Windows. The canonical serialization layer is the
single source of byte-equality and is independently verified by the DTH
golden matrix.
