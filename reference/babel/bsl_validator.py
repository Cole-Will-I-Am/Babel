"""Babel v0.10.3 BSL syntax validator.

Implements deterministic syntax validation for .babel files:
- validate_header: Check header format matches /^\/blocks\/(handoff|intent|meta):[a-z0-9-]+$/
- validate_body_kv: Check body KVs have required keys, no extras, no duplicates
- validate_version: Check version string equals BABEL_VERSION
- validate_file: Orchestrate all validations over a parsed file
- validate_block_string: Direct composition primitive for pre-write validation

Extra keys policy: REJECT (deterministic default per stage 10a).
Bool encoding: lowercase 'true'/'false' as opaque raw strings (stage 11a).
List encoding: compact JSON via json.dumps(value, separators=(',', ':')) (stage 11a).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

# Import BabelParseError from bsl_parser with fallback
try:
    from .bsl_parser import BabelParseError
except ImportError:
    class BabelParseError(Exception):
        """Fallback BabelParseError if bsl_parser not available."""
        def __init__(self, message: str, code: str = "unknown", line_no: int | None = None) -> None:
            super().__init__(message)
            self.code = code
            self.line_no = line_no

# Import BABEL_VERSION from handoff with fallback
try:
    from .handoff import BABEL_VERSION
except ImportError:
    BABEL_VERSION = "0.10.3"

if TYPE_CHECKING:
    from .bsl_parser import BabelFile

# Header regex: ^/blocks/(handoff|intent|meta):[a-z0-9-]+$
HEADER_REGEX = re.compile(r"^/blocks/(handoff|intent|meta):[a-z0-9-]+$")

# Required keys per block type
HANDOFF_KEYS = frozenset({
    "path", "content", "agent_id", "next_owner", "signoff",
    "blocking_issues", "required_changes", "summary", "memory_note", "version"
})
INTENT_KEYS = frozenset({"purpose", "owner", "version"})
META_KEYS = frozenset({"title", "version"})

BLOCK_TYPE_KEYS: dict[str, frozenset[str]] = {
    "handoff": HANDOFF_KEYS,
    "intent": INTENT_KEYS,
    "meta": META_KEYS,
}


def validate_header(header_line: str, line_no: int) -> tuple[str, str]:
    """Validate a BSL block header line.

    Args:
        header_line: The header line (e.g., '/blocks/handoff:handoff-1')
        line_no: Line number for error reporting

    Returns:
        Tuple of (block_type, block_id) extracted from the header

    Raises:
        BabelParseError: If header does not match the required format
    """
    match = HEADER_REGEX.match(header_line)
    if not match:
        raise BabelParseError(
            f"Invalid header format: {header_line!r}",
            code="malformed_header",
            line_no=line_no
        )
    block_type = match.group(1)
    block_id = header_line.split(":", 1)[1]
    return block_type, block_id


def validate_body_kv(block_type: str, kv_pairs: list[tuple[str, str]], line_no: int) -> None:
    """Validate body key-value pairs for a block.

    Args:
        block_type: The block type ('handoff', 'intent', or 'meta')
        kv_pairs: List of (key, value) tuples from the block body
        line_no: Line number for error reporting

    Raises:
        BabelParseError: If keys are missing, extra, duplicated, or version mismatches
    """
    if block_type not in BLOCK_TYPE_KEYS:
        raise BabelParseError(
            f"Unknown block type: {block_type!r}",
            code="unknown_block_type",
            line_no=line_no
        )

    required_keys = BLOCK_TYPE_KEYS[block_type]
    seen_keys: set[str] = set()

    for key, _value in kv_pairs:
        # Check for duplicates
        if key in seen_keys:
            raise BabelParseError(
                f"Duplicate key: {key!r}",
                code="duplicate_key",
                line_no=line_no
            )
        seen_keys.add(key)

        # Check for extra keys (reject policy)
        if key not in required_keys:
            raise BabelParseError(
                f"Extra key not allowed: {key!r}",
                code="extra_key",
                line_no=line_no
            )

    # Check for missing keys
    missing = required_keys - seen_keys
    if missing:
        raise BabelParseError(
            f"Missing required keys: {sorted(missing)!r}",
            code="missing_key",
            line_no=line_no
        )

    # Validate version if present
    version_value = None
    for key, value in kv_pairs:
        if key == "version":
            version_value = value
            break

    if version_value is not None:
        validate_version(version_value, line_no)


def validate_version(version: str, line_no: int) -> None:
    """Validate version string equals BABEL_VERSION.

    Args:
        version: The version string from the block body
        line_no: Line number for error reporting

    Raises:
        BabelParseError: If version does not match BABEL_VERSION
    """
    if version != BABEL_VERSION:
        raise BabelParseError(
            f"Version mismatch: expected {BABEL_VERSION!r}, got {version!r}",
            code="version_mismatch",
            line_no=line_no
        )


def validate_block_string(block_type: str, header: str, kv_pairs: list[tuple[str, str]]) -> None:
    """Direct composition primitive for pre-write block validation.

    Validates a block by directly calling validate_header and validate_body_kv
    without constructing an intermediate block string. This eliminates redundant
    parsing and prevents drift between constructed strings and parser output.

    Per the DeepSeek audit refinement (stage 11a), this function captures the
    block_type returned by validate_header and passes it to validate_body_kv,
    rather than using the function's block_type parameter. This guarantees the
    body is validated against the actual header type, preventing inconsistency
    if a caller passes a mismatched block_type.

    Args:
        block_type: Block type for API symmetry (not used for validation)
        header: The header line (e.g., '/blocks/handoff:handoff-1')
        kv_pairs: List of (key, value) tuples from the block body

    Raises:
        BabelParseError: If header or body validation fails
    """
    # Capture the block_type from the header, not the parameter
    header_type, _block_id = validate_header(header, line_no=0)
    # Validate body against the actual header type
    validate_body_kv(header_type, kv_pairs, line_no=0)


def validate_file(path: Path) -> None:
    """Orchestrate all validations over a parsed .babel file.

    Args:
        path: Path to the .babel file to validate

    Raises:
        BabelParseError: If any validation fails
        FileNotFoundError: If the file does not exist
    """
    # Import here to avoid circular dependency
    from .bsl_parser import parse_file

    babel_file = parse_file(path)

    # Validate each block
    for block in babel_file.blocks:
        header_line = f"/blocks/{block.type}:{block.id}"
        validate_header(header_line, block.line_no)

        # Convert block content to kv_pairs
        kv_pairs = [(k, v) for k, v in block.content.items()]
        validate_body_kv(block.type, kv_pairs, block.line_no)


__all__ = [
    "validate_header",
    "validate_body_kv",
    "validate_version",
    "validate_file",
    "validate_block_string",
    "BabelParseError",
    "BABEL_VERSION",
    "HEADER_REGEX",
    "HANDOFF_KEYS",
    "INTENT_KEYS",
    "META_KEYS",
    "BLOCK_TYPE_KEYS",
]
