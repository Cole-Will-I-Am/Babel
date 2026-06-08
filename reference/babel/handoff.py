"""Babel v0.10.2 handoff protocol.

Implements the append-only handoff collaboration record protocol and
read-side query methods for multi-agent continuity.

Exports:
- BABEL_VERSION: str = '0.10.2'
- HANDOFF_SCHEMA: TypedDict with 9 collaboration keys
- append_handoff(path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note) -> tuple[bool, str]
- get_latest_handoff(path) -> dict | None
- list_handoffs(path) -> tuple[dict, ...]
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from orchestrator.canonical import canonical_json

# Import only the exception class to avoid circular import
from reference.babel.bsl_parser import BabelParseError, parse_file, write_file


BABEL_VERSION = '0.10.2'


class HANDOFF_SCHEMA(TypedDict, total=False):
    """Schema for handoff block content per Babel v0.10.2 spec."""
    path: str
    content: str
    agent_id: str
    next_owner: str
    signoff: bool
    blocking_issues: List[str]
    required_changes: List[str]
    summary: str
    memory_note: str


def _compute_handoff_id(content: str, agent_id: str) -> str:
    """
    Compute deterministic handoff ID from content and agent.
    
    Format: agent_id + ':' + sha256(content)[:16]
    This provides idempotency: same content from same agent = same ID.
    """
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    return f'{agent_id}:{content_hash}'


def _get_next_sequential_id(existing_handoffs: List[Dict[str, Any]]) -> str:
    """
    Compute next sequential handoff ID.
    
    Format: handoff-{n} where n = max(existing) + 1, or handoff-1 if none exist.
    """
    if not existing_handoffs:
        return 'handoff-1'
    
    # Extract numeric suffixes from existing handoff IDs
    max_num = 0
    for handoff in existing_handoffs:
        handoff_id = handoff.get('id', '')
        match = re.match(r'handoff-(\d+)', handoff_id)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    return f'handoff-{max_num + 1}'


def append_handoff(
    path: Path,
    content: str,
    agent_id: str,
    next_owner: str,
    signoff: bool,
    blocking_issues: List[str],
    required_changes: List[str],
    summary: str,
    memory_note: str,
) -> Tuple[bool, str]:
    """
    Append a handoff block to a .babel file.
    
    Args:
        path: Path to .babel file.
        content: Raw content string being handed off.
        agent_id: ID of the agent performing the handoff.
        next_owner: ID of the next agent to receive the handoff.
        signoff: Whether this handoff represents a signoff.
        blocking_issues: List of blocking issue descriptions.
        required_changes: List of required change descriptions.
        summary: Human-readable summary of the handoff.
        memory_note: Durable note for future sessions.
    
    Returns:
        Tuple of (success, handoff_id). If handoff already exists (idempotent),
        returns (False, existing_id). On success, returns (True, new_id).
    
    Raises:
        BabelParseError: If file parsing fails.
        OSError: If file I/O fails.
    """
    # Parse existing file
    babel_file = parse_file(path)
    
    # Build handoff content dict per schema
    handoff_content: Dict[str, Any] = {
        'path': str(path),
        'content': content,
        'agent_id': agent_id,
        'next_owner': next_owner,
        'signoff': signoff,
        'blocking_issues': blocking_issues,
        'required_changes': required_changes,
        'summary': summary,
        'memory_note': memory_note,
    }
    
    # Compute deterministic handoff ID for idempotency check
    content_for_id = canonical_json(handoff_content)
    proposed_id = _compute_handoff_id(content_for_id, agent_id)
    
    # Check for existing handoff with same ID (idempotency)
    for existing in babel_file.handoffs:
        existing_content = existing.content
        if isinstance(existing_content, dict):
            existing_id = existing_content.get('id', '')
            if existing_id == proposed_id:
                return (False, existing_id)
    
    # Compute next sequential ID
    handoff_id = _get_next_sequential_id(babel_file.handoffs)
    handoff_content['id'] = handoff_id
    
    # Build handoff block header and content
    handoff_header = f'#[handoff]:{handoff_id}@{BABEL_VERSION}'
    handoff_block_content = json.dumps(handoff_content, indent=2, sort_keys=True)
    
    # Read original file content
    original_content = path.read_text(encoding='utf-8')
    
    # Append handoff block
    new_content = original_content.rstrip() + '\n\n' + handoff_header + '\n' + handoff_block_content + '\n'
    
    # Write atomically
    write_file(path, new_content)
    
    return (True, handoff_id)


def get_latest_handoff(path: Path) -> Optional[Dict[str, Any]]:
    """
    Get the most recent handoff from a .babel file.
    
    Args:
        path: Path to .babel file.
    
    Returns:
        Dict with frozen schema keys if handoffs exist, None otherwise.
    
    Raises:
        BabelParseError: If file parsing fails.
        OSError: If file I/O fails.
    """
    babel_file = parse_file(path)
    
    if not babel_file.handoffs:
        return None
    
    # Return last handoff with frozen schema
    last_handoff = babel_file.handoffs[-1]
    content = last_handoff.content
    
    if isinstance(content, dict):
        return dict(content)  # Return a copy
    
    return None


def list_handoffs(path: Path) -> Tuple[Dict[str, Any], ...]:
    """
    List all handoffs from a .babel file in sequential order.
    
    Args:
        path: Path to .babel file.
    
    Returns:
        Tuple of dicts with frozen schema keys, sorted by handoff ID.
    
    Raises:
        BabelParseError: If file parsing fails.
        OSError: If file I/O fails.
    """
    babel_file = parse_file(path)
    
    if not babel_file.handoffs:
        return ()
    
    # Sort by numeric suffix in handoff ID
    def sort_key(h: Any) -> int:
        content = h.content if hasattr(h, 'content') else h
        if isinstance(content, dict):
            handoff_id = content.get('id', '')
            match = re.match(r'handoff-(\d+)', handoff_id)
            if match:
                return int(match.group(1))
        return 0
    
    sorted_handoffs = sorted(babel_file.handoffs, key=sort_key)
    
    # Return tuple of dicts with frozen schema
    result = []
    for handoff in sorted_handoffs:
        content = handoff.content
        if isinstance(content, dict):
            result.append(dict(content))
    
    return tuple(result)
