"""Babel v0.10.2 companion module.

Resolves companion .md files for .babel files via basename matching.
Human-authored prose lives in companion .md files (same basename as the
.babel file, e.g., ``module.babel`` pairs with ``module.md``). This
module is a zero-dependency utility: it operates at the filesystem
level only and does not import parser AST types.

Contract:

* Given a ``.babel`` path, return the sibling ``.md`` path if a regular
  file exists at that sibling location.
* Return ``None`` if the sibling ``.md`` does not exist, if the
  ``.babel`` path has no suffix, or if the sibling is not a regular
  file (e.g., directory, symlink loop, device node).
* The function is read-only; it never writes, never deletes, and never
  resolves paths outside the directory of the input ``.babel`` file.
* Basename matching is the only pairing rule. There is no header
  cross-reference, no manifest lookup, and no recursive search.
"""

from pathlib import Path
from typing import Optional


# Frozen module version constant, matching the parser module.
BABEL_VERSION: str = "0.10.2"


def resolve_companion(babel_path: Path) -> Optional[Path]:
    """Return the companion ``.md`` path for a given ``.babel`` path.

    Contract:

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
    """
    # Check if path has .babel suffix
    if babel_path.suffix != '.babel':
        return None
    
    # Construct companion path in same directory
    companion_path = babel_path.with_suffix('.md')
    
    # Return only if it exists as a regular file (not dir, symlink, etc.)
    if companion_path.is_file():
        return companion_path
    
    return None
