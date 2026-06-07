"""Babel v0.10.2 companion module skeleton.

Resolves companion .md files for .babel files via basename matching.
Human-authored prose lives in companion .md files (same basename as the
.babel file, e.g., ``module.babel`` pairs with ``module.md``). This
module is a zero-dependency utility: it operates at the filesystem
level only and does not import parser AST types.

Contract (docstring only; implementation deferred to v0.10.3 cycle 3):

* Given a ``.babel`` path, return the sibling ``.md`` path if a regular
  file exists at that sibling location.
* Return ``None`` if the sibling ``.md`` does not exist, if the
  ``.babel`` path has no suffix, or if the sibling is not a regular
  file (e.g., directory, symlink loop, device node).
* The function is read-only; it never writes, never deletes, and never
  resolves paths outside the directory of the input ``.babel`` file.
* Basename matching is the only pairing rule. There is no header
  cross-reference, no manifest lookup, and no recursive search.

This module is the contract-first bootstrap (stage 2b) for the Babel
companion resolver. The public signature is frozen; the function body
raises ``NotImplementedError`` and will be filled in during the v0.10.3
cycle 3 logic schedule. The Integration spec (Appendix A.3) names
``resolve_companion`` as the handoff protocol step 3 surface for
tooling-side editor linking.
"""

from pathlib import Path
from typing import Optional


# Frozen module version constant, matching the parser module.
BABEL_VERSION: str = "0.10.2"


def resolve_companion(babel_path: Path) -> Optional[Path]:
    """Return the companion ``.md`` path for a given ``.babel`` path.

    Contract (implementation deferred to v0.10.3 cycle 3):

    * If ``babel_path`` has suffix ``.babel`` and a regular file exists
      at ``babel_path.with_suffix('.md')`` in the same directory,
      return that resolved ``Path``.
    * Otherwise return ``None``.

    The function does not read the ``.md`` file, does not validate its
    contents, and does not touch the parser. Callers are responsible
    for any further I/O on the returned path.

    :param babel_path: Path to a ``.babel`` source file.
    :returns: The companion ``.md`` path if it exists as a regular file,
              otherwise ``None``.
    :raises NotImplementedError: Stage 2b skeleton; logic ships in
                                  v0.10.3 cycle 3.
    """
    raise NotImplementedError(
        "resolve_companion is a stage 2b skeleton; "
        "implementation is scheduled for the v0.10.3 cycle 3 logic cycle."
    )
