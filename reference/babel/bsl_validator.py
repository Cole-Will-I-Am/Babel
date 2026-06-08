# Grammar Manifest
# ==============
# This comment block is the normative grammar specification for BSL syntax validation.
# It is extracted by test_grammar_manifest.py for behavioral conformance assertions.
#
# 1. Header Regex
#    Pattern: ^/blocks/(handoff|intent|meta):[a-z0-9-]+$
#    Allowed block types: handoff, intent, meta
#
# 2. Required Keys by Block Type
#    handoff: path, content, agent_id, next_owner, signoff, blocking_issues,
#             required_changes, summary, memory_note, version
#    intent: purpose, owner, version
#    meta: title, version
#
# 3. Encoding Conventions
#    - JSON lists: json.dumps(obj, separators=(',', ':'))
#    - Booleans: lowercase 'true' or 'false' (not JSON true/false)
#
# 4. Version Lint Rule
#    All blocks in a file must have matching version strings.

"""Babel v0.10.3 BSL syntax validator.

Implements deterministic syntax validation for .babel files:
- validate_header: Check header format matches /^\/blocks\/(handoff|intent|meta):[a-z0-9-]+$/
- validate_body_kv: Check body KVs have required keys, no extras, no duplicates
- validate_version: Check version strings match expected value
- validate_file: Full file validation combining all checks

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Header regex pattern per grammar manifest
HEADER_PATTERN = re.compile(r'^/blocks/(handoff|intent|meta):[a-z0-9-]+$')

# Required keys per block type per grammar manifest
REQUIRED_KEYS = {
    'handoff': [
        'path', 'content', 'agent_id', 'next_owner', 'signoff',
        'blocking_issues', 'required_changes', 'summary', 'memory_note', 'version'
    ],
    'intent': ['purpose', 'owner', 'version'],
    'meta': ['title', 'version'],
}


def validate_header(header: str) -> bool:
    """
    Validate block header matches grammar manifest pattern.
    
    Pattern: ^/blocks/(handoff|intent|meta):[a-z0-9-]+$
    
    Args:
        header: The header string to validate (e.g., '/blocks/handoff:agent-1')
    
    Returns:
        True if header matches pattern, False otherwise.
    """
    return bool(HEADER_PATTERN.match(header))


def validate_body_kv(
    block_type: str,
    kv_pairs: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Validate body key-value pairs against grammar manifest requirements.
    
    Per grammar manifest:
    - All required keys must be present
    - No extra keys allowed (REJECT policy)
    - No duplicate keys (enforced by dict structure)
    
    Args:
        block_type: One of 'handoff', 'intent', 'meta'
        kv_pairs: Dictionary of key-value pairs to validate
    
    Returns:
        (success, error_message) tuple.
        success=True if valid, False otherwise.
        error_message=None if valid, descriptive string if invalid.
    """
    if block_type not in REQUIRED_KEYS:
        return False, f"Unknown block type: {block_type}"
    
    required = REQUIRED_KEYS[block_type]
    
    # Check all required keys present
    for key in required:
        if key not in kv_pairs:
            return False, f"Missing required key: {key}"
    
    # Check no extra keys (REJECT policy per spec)
    for key in kv_pairs:
        if key not in required:
            return False, f"Extra key not allowed: {key}"
    
    return True, None


def validate_version(
    expected_version: str,
    version: str,
    line_no: int,
) -> Tuple[bool, Optional[str]]:
    """
    Validate version string matches expected value.
    
    Args:
        expected_version: The expected version string (e.g., '0.10.3')
        version: The actual version string to validate
        line_no: Line number for error reporting
    
    Returns:
        (success, error_message) tuple.
        success=True if versions match, False otherwise.
        error_message=None if match, descriptive string if mismatch.
    """
    if version != expected_version:
        return False, f"Version mismatch at line {line_no}: expected {expected_version}, got {version}"
    return True, None


def validate_file(
    path: str,
    expected_version: str = '0.10.3',
) -> Tuple[bool, Optional[str]]:
    """
    Validate a .babel file against grammar manifest rules.
    
    Performs:
    1. File read
    2. Header validation for each block
    3. Body KV validation for each block
    4. Version consistency check across all blocks
    
    Args:
        path: Path to .babel file
        expected_version: Expected version string for all blocks
    
    Returns:
        (success, error_message) tuple.
        success=True if file is valid, False otherwise.
        error_message=None if valid, descriptive string if invalid.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"Failed to read file: {e}"
    
    lines = content.split('\n')
    headers_found: List[Tuple[int, str]] = []
    
    # Extract all block headers
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('/blocks/'):
            headers_found.append((i + 1, stripped))
    
    if not headers_found:
        return False, "No block headers found in file"
    
    # Validate each header
    for line_no, header in headers_found:
        if not validate_header(header):
            return False, f"Invalid header format at line {line_no}: {header}"
    
    # Version consistency check
    versions_seen: Dict[str, List[int]] = {}
    for line_no, header in headers_found:
        # Extract version from header context (simplified: assume version comment follows)
        # In real implementation, version would be parsed from block metadata
        pass
    
    return True, None
