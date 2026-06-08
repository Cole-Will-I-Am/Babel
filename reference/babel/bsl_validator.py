# Grammar Manifest
# ==============
# This comment block is the normative grammar specification for BSL syntax validation.
# It is extracted by test_grammar_manifest.py for behavioral conformance assertions.
#
# 1. Header Regex
#    Pattern: ^/blocks/(handoff|intent|meta):[a-z0-9-]+$
#    Allowed block types: handoff, intent, meta
#
# 2. Required Body Keys per Block Type
#    handoff (10 keys): path, content, agent_id, next_owner, signoff,
#                       blocking_issues, required_changes, summary,
#                       memory_note, version
#    intent (3 keys): purpose, owner, version
#    meta (2 keys): title, version
#
# 3. JSON List Encoding
#    Lists are encoded via json.dumps with separators=(',',':')
#    to ensure deterministic, compact serialization.
#
# 4. Boolean Encoding
#    Booleans are encoded as lowercase strings: 'true' or 'false'
#
# 5. Version Lint Rule
#    All blocks must include a 'version' key matching BABEL_VERSION.
#    Checked via validate_version(expected_version, version, line_no).

"""Babel v0.10.3 BSL syntax validator.

Implements deterministic syntax validation for .babel files:
- validate_header: Check header format matches BSL grammar
- validate_body_kv: Check body KVs have required keys, no extras, no duplicates
- validate_version: Check version matches expected BABEL_VERSION
- validate_block_string: Compose validate_header + validate_body_kv
- validate_file: Full file validation entry point

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.canonical import canonical_json

from .bsl_parser import BabelParseError, BABEL_VERSION

# Header regex per grammar manifest section 1
HEADER_REGEX = re.compile(r'^/blocks/(handoff|intent|meta):([a-z0-9-]+)$')

# Required keys per block type per grammar manifest section 2
REQUIRED_KEYS = {
    'handoff': [
        'path', 'content', 'agent_id', 'next_owner', 'signoff',
        'blocking_issues', 'required_changes', 'summary', 'memory_note',
        'version'
    ],
    'intent': ['purpose', 'owner', 'version'],
    'meta': ['title', 'version'],
}


def validate_header(header: str, line_no: int) -> Tuple[str, str]:
    """
    Validate block header format.
    
    Args:
        header: Header string (e.g., '/blocks/handoff:agent-1')
        line_no: 1-based line number for error reporting
    
    Returns:
        (block_type, block_id) tuple
    
    Raises:
        BabelParseError with code 'malformed_header' on invalid format
    """
    match = HEADER_REGEX.match(header)
    if not match:
        raise BabelParseError(
            code='malformed_header',
            line=line_no,
            message=f'Invalid header format: {header}',
        )
    return match.group(1), match.group(2)


def validate_body_kv(
    block_type: str,
    kv_pairs: List[Tuple[str, str]],
    line_no: int,
) -> None:
    """
    Validate body key-value pairs.
    
    Args:
        block_type: Block type from header (handoff/intent/meta)
        kv_pairs: List of (key, value) tuples from body
        line_no: 1-based line number for error reporting
    
    Raises:
        BabelParseError with code:
        - 'missing_required_key' if required key absent
        - 'duplicate_key' if key appears twice
        - 'extra_key' if unknown key present
    """
    required = REQUIRED_KEYS.get(block_type, [])
    seen_keys: Dict[str, int] = {}
    
    for key, _ in kv_pairs:
        # Check for duplicate
        if key in seen_keys:
            raise BabelParseError(
                code='duplicate_key',
                line=line_no,
                message=f'Duplicate key: {key}',
            )
        seen_keys[key] = 1
    
    # Check required keys
    for req_key in required:
        if req_key not in seen_keys:
            raise BabelParseError(
                code='missing_required_key',
                line=line_no,
                message=f'Missing required key: {req_key}',
            )
    
    # Check for extra keys (REJECT policy)
    for key in seen_keys:
        if key not in required:
            raise BabelParseError(
                code='extra_key',
                line=line_no,
                message=f'Extra key not allowed: {key}',
            )


def validate_version(
    expected_version: str,
    version: str,
    line_no: int,
) -> None:
    """
    Validate version matches expected BABEL_VERSION.
    
    Args:
        expected_version: Expected version string (e.g., BABEL_VERSION)
        version: Actual version from block
        line_no: 1-based line number for error reporting
    
    Raises:
        BabelParseError with code 'version_mismatch' if versions differ
    """
    if version != expected_version:
        raise BabelParseError(
            code='version_mismatch',
            line=line_no,
            message=f'Version mismatch: expected {expected_version}, got {version}',
        )


def validate_block_string(
    block_type: str,
    header: str,
    kv_pairs: List[Tuple[str, str]],
) -> None:
    """
    Validate a block string via direct composition.
    
    Composes validate_header and validate_body_kv without constructing
    an intermediate block string. Uses header-derived block_type for
    body validation to prevent header-body mismatch.
    
    Args:
        block_type: Block type parameter (retained for API symmetry)
        header: Header string (e.g., '/blocks/handoff:agent-1')
        kv_pairs: List of (key, value) tuples from body
    
    Raises:
        BabelParseError on any validation failure
    """
    # Validate header and get actual block_type from header
    header_type, _block_id = validate_header(header, line_no=0)
    
    # Validate body using header-derived type (not parameter)
    validate_body_kv(header_type, kv_pairs, line_no=0)


def validate_file(path: Path) -> None:
    """
    Validate a .babel file.
    
    Entry point for full file validation. Reads file, parses blocks,
    and validates each block via validate_block_string.
    
    Args:
        path: Path to .babel file
    
    Raises:
        BabelParseError on any validation failure
        OSError on file read failure
    """
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    current_header: Optional[str] = None
    current_block_type: Optional[str] = None
    kv_pairs: List[Tuple[str, str]] = []
    header_line_no: int = 0
    
    for i, line in enumerate(lines):
        line_no = i + 1  # 1-based
        
        # Skip blank lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # Check if this is a header line
        if stripped.startswith('/blocks/'):
            # Validate previous block if exists
            if current_header is not None:
                validate_block_string(
                    current_block_type or 'handoff',
                    current_header,
                    kv_pairs,
                )
            
            # Start new block
            current_header = stripped
            current_block_type = None  # Will be derived from header
            kv_pairs = []
            header_line_no = line_no
        else:
            # Parse as key-value pair
            if ':' in stripped:
                key, _, value = stripped.partition(':')
                kv_pairs.append((key.strip(), value.strip()))
    
    # Validate final block
    if current_header is not None:
        validate_block_string(
            current_block_type or 'handoff',
            current_header,
            kv_pairs,
        )
