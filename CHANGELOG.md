# Changelog

All notable changes to MiniMadMax and the Babel stack are recorded here.

## v0.10.2 - Babel Language Surface (Unreleased)

### Cycle: Stage 2b - Companion Resolver Skeleton

Shipped the contract-first bootstrap for the companion `.md` resolver as
a single-file deliverable. Follow-up stages 3a and 3b remain queued.

#### Added

- **`reference/babel/companion.py`** - zero-dependency utility skeleton
  exposing `resolve_companion(babel_path: Path) -> Optional[Path]`. The
  function body raises `NotImplementedError`; implementation is
  scheduled for the v0.10.3 cycle 3 logic cycle. The module imports
  only `pathlib.Path` and `typing.Optional`, with no parser AST coupling,
  preserving the intentional architectural separation between
  filesystem-level utilities and parser internals.

#### Contract

- The companion `.md` resolution contract is documented in the module
  docstring only: basename matching against the input `.babel` path,
  regular-file existence check, read-only behavior, no directory
  traversal beyond the input file's directory.
- The frozen signature `resolve_companion(babel_path: Path) -> Optional[Path]`
  is the binding surface for stage 3a contract tests and for tooling
  consumers that pair `.babel` and `.md` files in editors.

#### Cadence

- Single-file-per-stage preserved: this round ships exactly one Python
  file plus `README.md` and `CHANGELOG.md` updates. Stages 3a
  (`reference/tests/test_handoff_contract.py`) and 3b (BISC spec error
  taxonomy and stderr JSON amendment) follow as separate single-file
  finalize rounds.

#### Cross-references

- Stage 1a: `reference/babel/bsl_parser.py` parser API skeleton.
- Stage 1c: `autonomy-output/babel-language-integration-v0.10.2.md`
  Contract Bootstrap Appendix (maps `resolve_companion` to handoff
  protocol step 3).
- Stage 2a: `reference/babel/handoff.py` handoff protocol skeleton.
