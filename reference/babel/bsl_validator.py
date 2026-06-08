"""Babel v0.10.3 BSL syntax validator.

Implements deterministic syntax validation for .babel files:
- validate_header: Check header format matches /^\/blocks\/(handoff|intent|meta):[a-z0-9-]+$/
- validate_body_kv: Check body KVs have required keys, no extras, no duplicates
- validate_version: Check version equals BABEL_VERSION
- validate_file: Orchestrate full-file validation
- validate_block_string: Direct-call composition primitive for single-block validation

Exports:
- validate_header(header: str, line_no: int) -> tuple[str, str]
- validate_body_kv(block_type: str, kv_pairs: list[tuple[str,str]], line_no: int) -> None
- validate_version(expected_version: str, version: str, line_no: int) -> None
- validate_file(content: str) -> None
- validate_block_string(block_type: str, header: str, kv_pairs: list[tuple[str,str]]) -> None

Uses Python 3.12 stdlib only. Reuses BabelParseError from bsl_parser.
"""

import re
from typing import list, tuple

# Import BabelParseError from bsl_parser with fallback
try:
    from .bsl_parser import BabelParseError
except ImportError:
    class BabelParseError(Exception):
        def __init__(self, message: str, code: str = "syntax_error", line_no: int = 0):
            super().__init__(message)
            self.code = code
            self.line_no = line_no

# Import BABEL_VERSION from handoff for validator's own use
from .handoff import BABEL_VERSION

# Header regex: /^\/blocks\/(handoff|intent|meta):[a-z0-9-]+$/
HEADER_REGEX = re.compile(r'^/blocks/(handoff|intent|meta):([a-z0-9-]+)$')

# Required keys per block type
HANDOFF_KEYS = frozenset({
    'path', 'content', 'agent_id', 'next_owner', 'signoff',
    'blocking_issues', 'required_changes', 'summary', 'memory_note', 'version'
})
INTENT_KEYS = frozenset({'purpose', 'owner', 'version'})
META_KEYS = frozenset({'title', 'version'})

BLOCK_TYPE_KEYS = {
    'handoff': HANDOFF_KEYS,
    'intent': INTENT_KEYS,
    'meta': META_KEYS,
}


def validate_header(header: str, line_no: int) -> tuple[str, str]:
    """Validate header format and return (block_type, block_id).
    
    Args:
        header: The header line (without leading/trailing whitespace)
        line_no: Line number for error reporting
        
    Returns:
        tuple[block_type, block_id] where block_type is 'handoff'|'intent'|'meta'
        
    Raises:
        BabelParseError: If header format is invalid
    """
    header = header.strip()
    match = HEADER_REGEX.match(header)
    if not match:
        raise BabelParseError(
            f"Invalid header format: {header!r}",
            code="invalid_header",
            line_no=line_no
        )
    block_type = match.group(1)
    block_id = match.group(2)
    return block_type, block_id


def validate_body_kv(block_type: str, kv_pairs: list[tuple[str, str]], line_no: int) -> None:
    """Validate body key-value pairs for a block.
    
    Args:
        block_type: The block type ('handoff', 'intent', or 'meta')
        kv_pairs: List of (key, value) tuples from the body
        line_no: Line number for error reporting
        
    Raises:
        BabelParseError: If keys are missing, extra, or duplicated
    """
    required_keys = BLOCK_TYPE_KEYS.get(block_type)
    if required_keys is None:
        raise BabelParseError(
            f"Unknown block type: {block_type!r}",
            code="unknown_block_type",
            line_no=line_no
        )
    
    seen_keys = set()
    for key, _ in kv_pairs:
        if key in seen_keys:
            raise BabelParseError(
                f"Duplicate key in {block_type} block: {key!r}",
                code="duplicate_key",
                line_no=line_no
            )
        seen_keys.add(key)
        if key not in required_keys:
            raise BabelParseError(
                f"Extra key in {block_type} block: {key!r}",
                code="extra_key",
                line_no=line_no
            )
    
    missing_keys = required_keys - seen_keys
    if missing_keys:
        raise BabelParseError(
            f"Missing required keys in {block_type} block: {sorted(missing_keys)!r}",
            code="missing_key",
            line_no=line_no
        )


def validate_version(expected_version: str, version: str, line_no: int) -> None:
    """Validate version string equals expected version.
    
    Args:
        expected_version: The expected BABEL_VERSION string
        version: The version value from the block
        line_no: Line number for error reporting
        
    Raises:
        BabelParseError: If version does not match expected
    """
    if version != expected_version:
        raise BabelParseError(
            f"Version mismatch: expected {expected_version!r}, got {version!r}",
            code="version_mismatch",
            line_no=line_no
        )


def validate_block_string(block_type: str, header: str, kv_pairs: list[tuple[str, str]]) -> None:
    """Validate a single block via direct-call composition.
    
    This is a primitive for pre-write validation that composes validate_header
    and validate_body_kv without constructing an intermediate block string.
    
    Args:
        block_type: Expected block type (for API symmetry)
        header: The header line
        kv_pairs: List of (key, value) tuples from the body
        
    Raises:
        BabelParseError: If header or body validation fails
    """
    # Use header-derived block_type to prevent header-body mismatch
    header_type, _block_id = validate_header(header, line_no=0)
    validate_body_kv(header_type, kv_pairs, line_no=0)


def validate_file(content: str) -> None:
    """Validate a complete .babel file.
    
    Args:
        content: The full file content as a string
        
    Raises:
        BabelParseError: If any block fails validation
    """
    lines = content.split('\n')
    line_no = 0
    
    while line_no < len(lines):
        line = lines[line_no].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            line_no += 1
            continue
        
        # Parse header
        header = line
        line_no += 1
        
        # Parse body KVs
        kv_pairs = []
        while line_no < len(lines):
            body_line = lines[line_no]
            if not body_line.strip():
                line_no += 1
                continue
            if body_line.startswith('##'):
                break
            # Parse key: value
            if ':' in body_line:
                key, _, value = body_line.partition(':')
                kv_pairs.append((key.strip(), value.strip()))
            line_no += 1
        
        # Validate this block
        block_type, _block_id = validate_header(header, line_no=line_no)
        validate_body_kv(block_type, kv_pairs, line_no=line_no)
        
        # Check version for handoff blocks
        if block_type == 'handoff':
            version_value = None
            for key, value in kv_pairs:
                if key == 'version':
                    version_value = value
                    break
            if version_value is not None:
                validate_version(BABEL_VERSION, version_value, line_no=line_no)
