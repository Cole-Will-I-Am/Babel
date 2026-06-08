"""Babel v0.10.3 handoff protocol.

Implements the append-only handoff collaboration record protocol and
read-side query methods for multi-agent continuity.

Exports:
- BABEL_VERSION: str = '0.10.3'
- HANDOFF_SCHEMA: TypedDict with 9 collaboration keys
- append_handoff(path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note) -> tuple[bool, str]
- get_latest_handoff(path) -> dict | None
- list_handoffs(path) -> tuple[dict, ...]
- HandoffIntegrityError: Exception raised on pre-write validation failure

Uses Python 3.12 stdlib only. Reuses orchestrator/canonical.py for serialization.
Reuses bsl_validator.validate_block_string for pre-write gate.
"""

import hashlib
import json
import tempfile
import os
from pathlib import Path
from typing import Any, TypedDict

from orchestrator.canonical import canonical_json
from .bsl_parser import BabelParseError, parse_babel_file
from .bsl_validator import validate_block_string


BABEL_VERSION = '0.10.3'


class HANDOFF_SCHEMA(TypedDict):
    """Frozen schema for handoff block content dict.
    
    All 9 collaboration keys plus version (10 total) are required.
    """
    path: str
    content: str
    agent_id: str
    next_owner: str
    signoff: bool
    blocking_issues: list[str]
    required_changes: list[str]
    summary: str
    memory_note: str


class HandoffIntegrityError(Exception):
    """Exception raised when pre-write validation fails.
    
    Carries the error code and line number from the underlying BabelParseError.
    """
    def __init__(self, message: str, code: str, line_no: int):
        super().__init__(message)
        self.code = code
        self.line_no = line_no


def _encode_handoff_value(key: str, value: Any) -> str:
    """Encode a handoff value to a raw string for BSL body.
    
    Encoding contract:
    - str: passthrough
    - list[str]: compact JSON via json.dumps(separators=(',', ':'))
    - bool: lowercase 'true' or 'false'
    
    Args:
        key: The key name (for type inference)
        value: The value to encode
        
    Returns:
        Raw string suitable for BSL body
    """
    if isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, list):
        return json.dumps(value, separators=(',', ':'))
    else:
        return str(value)


def _decode_handoff_value(key: str, raw: str) -> Any:
    """Decode a raw BSL body string to the appropriate Python type.
    
    Decoding contract (symmetric with _encode_handoff_value):
    - signoff key: 'true' -> True, 'false' -> False
    - list keys (blocking_issues, required_changes): json.loads
    - other keys: passthrough as str
    
    Args:
        key: The key name (for type inference)
        raw: The raw string from BSL body
        
    Returns:
        Decoded Python value
    """
    if key == 'signoff':
        if raw == 'true':
            return True
        elif raw == 'false':
            return False
        else:
            raise ValueError(f"Invalid bool value for signoff: {raw!r}")
    elif key in ('blocking_issues', 'required_changes'):
        return json.loads(raw)
    else:
        return raw


def _compute_handoff_id(content: dict, agent_id: str) -> str:
    """Compute deterministic handoff ID via SHA256.
    
    Prepends agent_id to content before hashing for idempotency.
    Returns 'handoff-{n}' where n is the sequential count.
    
    Args:
        content: The handoff content dict
        agent_id: The agent's identity string
        
    Returns:
        Handoff ID string
    """
    canonical = canonical_json(content)
    prefixed = f"## agent: {agent_id}\n{canonical}"
    hash_hex = hashlib.sha256(prefixed.encode('utf-8')).hexdigest()
    return f"handoff-{hash_hex[:12]}"


def _get_next_handoff_number(path: Path) -> int:
    """Get the next sequential handoff number for a file.
    
    Args:
        path: Path to the .babel file
        
    Returns:
        Next handoff number (1 if no existing handoffs)
    """
    if not path.exists():
        return 1
    
    try:
        blocks = parse_babel_file(str(path))
        handoff_count = sum(1 for b in blocks if b['type'] == 'handoff')
        return handoff_count + 1
    except BabelParseError:
        return 1


def append_handoff(
    path: Path | str,
    content: str,
    agent_id: str,
    next_owner: str,
    signoff: bool,
    blocking_issues: list[str],
    required_changes: list[str],
    summary: str,
    memory_note: str,
) -> tuple[bool, str]:
    """Append a handoff block to a .babel file.
    
    Pre-write validation gate: validates the constructed block before any disk write.
    Raises HandoffIntegrityError if validation fails (no file left behind).
    
    Args:
        path: Path to the .babel file
        content: The handoff content (text)
        agent_id: The agent's identity string
        next_owner: The next agent to take ownership
        signoff: Whether this handoff is signed off
        blocking_issues: List of blocking issue descriptions
        required_changes: List of required change descriptions
        summary: Human-readable summary
        memory_note: Durable note for future sessions
        
    Returns:
        tuple[was_appended, handoff_id] where was_appended is False if duplicate
        
    Raises:
        HandoffIntegrityError: If pre-write validation fails
    """
    path = Path(path)
    
    # Build content dict per HANDOFF_SCHEMA
    handoff_content = {
        'path': str(path),
        'content': content,
        'agent_id': agent_id,
        'next_owner': next_owner,
        'signoff': signoff,
        'blocking_issues': blocking_issues,
        'required_changes': required_changes,
        'summary': summary,
        'memory_note': memory_note,
        'version': BABEL_VERSION,
    }
    
    # Compute handoff ID
    handoff_id = _compute_handoff_id(handoff_content, agent_id)
    
    # Check for idempotency (duplicate content skip)
    if path.exists():
        try:
            blocks = parse_babel_file(str(path))
            for block in blocks:
                if block.get('id') == handoff_id:
                    return (False, handoff_id)
        except BabelParseError:
            pass  # Continue with append if file is unparseable
    
    # Build block string for validation
    header = f"/blocks/handoff:{handoff_id}"
    kv_pairs = [
        (key, _encode_handoff_value(key, value))
        for key, value in handoff_content.items()
    ]
    
    # Pre-write validation gate
    try:
        validate_block_string('handoff', header, kv_pairs)
    except BabelParseError as e:
        raise HandoffIntegrityError(str(e), code=e.code, line_no=e.line_no)
    
    # Construct block text
    block_lines = [header]
    for key, raw_value in kv_pairs:
        block_lines.append(f"{key}: {raw_value}")
    block_lines.append('')  # Empty line terminator
    block_text = '\n'.join(block_lines)
    
    # Atomic write via tempfile + rename
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=parent, prefix='.handoff_', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            if path.exists():
                f.write(path.read_text(encoding='utf-8'))
            f.write(block_text)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    
    return (True, handoff_id)


def get_latest_handoff(path: Path | str) -> dict | None:
    """Get the most recent handoff from a .babel file.
    
    Args:
        path: Path to the .babel file
        
    Returns:
        Handoff content dict with 9 frozen keys, or None if no handoffs
        
    Raises:
        BabelParseError: If file is unparseable
    """
    path = Path(path)
    if not path.exists():
        return None
    
    blocks = parse_babel_file(str(path))
    handoffs = [b for b in blocks if b['type'] == 'handoff']
    if not handoffs:
        return None
    
    latest = handoffs[-1]
    return {
        'path': latest.get('path', ''),
        'content': latest.get('content', ''),
        'agent_id': latest.get('agent_id', ''),
        'next_owner': latest.get('next_owner', ''),
        'signoff': latest.get('signoff', False),
        'blocking_issues': latest.get('blocking_issues', []),
        'required_changes': latest.get('required_changes', []),
        'summary': latest.get('summary', ''),
        'memory_note': latest.get('memory_note', ''),
    }


def list_handoffs(path: Path | str) -> tuple[dict, ...]:
    """List all handoffs from a .babel file in sequential order.
    
    Args:
        path: Path to the .babel file
        
    Returns:
        Tuple of handoff content dicts sorted by handoff ID
        
    Raises:
        BabelParseError: If file is unparseable
    """
    path = Path(path)
    if not path.exists():
        return ()
    
    blocks = parse_babel_file(str(path))
    handoffs = [b for b in blocks if b['type'] == 'handoff']
    
    # Sort by numeric suffix in handoff ID
    def _sort_key(block: dict) -> int:
        block_id = block.get('id', '')
        # Extract numeric part after 'handoff-'
        if block_id.startswith('handoff-'):
            suffix = block_id[8:]
            try:
                return int(suffix)
            except ValueError:
                pass
        return 0
    
    handoffs.sort(key=_sort_key)
    
    return tuple({
        'path': h.get('path', ''),
        'content': h.get('content', ''),
        'agent_id': h.get('agent_id', ''),
        'next_owner': h.get('next_owner', ''),
        'signoff': h.get('signoff', False),
        'blocking_issues': h.get('blocking_issues', []),
        'required_changes': h.get('required_changes', []),
        'summary': h.get('summary', ''),
        'memory_note': h.get('memory_note', ''),
    } for h in handoffs)
