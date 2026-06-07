"""
Babel v0.10.2 Handoff Module

Implements the handoff protocol from Babel Language Integration v0.10.2,
Section 5. Agents append #[handoff] blocks in chronological order. The
active handoff is the last #[handoff] block in the file.

Required JSON fields for handoff blocks:
- next_owner (string, kebab-case agent id)
- signoff (boolean)
- blocking_issues (array of strings)
- required_changes (array of strings)
- summary (string)
- memory_note (string)

Ordinal IDs (handoff-1, handoff-2, ...) are assigned by this module at
append time, not by the authoring agent. The parser extracts the active
handoff by selecting the last #[handoff] block in source order.

Handoff blocks are excluded from canonical_sha256 and from the BCPR
virtual JSON representation. BISC validates handoff blocks are well-formed
JSON but does not enforce field semantics.

This is a contract-first bootstrap skeleton (stage 2a). All function
bodies raise NotImplementedError until the v0.10.3 cycle 3 logic ships.
"""

from pathlib import Path
from typing import Optional

from .bsl_parser import BabelFile, BabelBlock


__all__ = [
    'append_handoff',
]


def append_handoff(
    path: Path,
    next_owner: str,
    signoff: bool,
    blocking_issues: list[str],
    required_changes: list[str],
    summary: str,
    memory_note: str,
) -> None:
    """
    Append a new #[handoff] block to a .babel file.

    This function assigns the next ordinal handoff-{n}, guards idempotency
    by content hash, and persists via atomic tempfile + rename so a partial
    write cannot leave the file in a torn state.

    Args:
        path: Path to the .babel file to amend.
        next_owner: Kebab-case agent id for the next owner.
        signoff: Boolean indicating whether this handoff includes signoff.
        blocking_issues: List of blocking issue strings.
        required_changes: List of required change strings.
        summary: Summary string for this handoff.
        memory_note: Memory note string for this handoff.

    Raises:
        NotImplementedError: This stub is scheduled for logic implementation
            in v0.10.3 cycle 3.

    Lifecycle validity:
        - draft: NOT valid (file is still being authored)
        - review: NOT valid (file is still being authored)
        - ready: VALID (ready for human sign via BHOP override)
        - sealed: VALID (human override recorded, CDR entry exists)
        - frozen: NOT valid (must enter amendment chain instead)

    See also:
        Babel Language Integration v0.10.2, Section 5 (Handoff Protocol)
        Contract Bootstrap Appendix A.3 (Handoff Protocol Step Mapping)
    """
    raise NotImplementedError(
        "append_handoff logic scheduled for v0.10.3 cycle 3. "
        "This stub validates the API surface for stage 2a contract tests."
    )
