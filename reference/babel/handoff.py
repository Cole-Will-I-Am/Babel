"""Babel v0.10.2 handoff protocol.

Implements the append-only handoff collaboration record protocol and
read-side query methods for multi-agent continuity.

Exports:
- BABEL_VERSION: str = '0.10.2'
- append_handoff(path, content, agent_id, next_owner, signoff, blocking_issues, required_changes, summary, memory_note) -> tuple[bool, str]
- get_latest_handoff(path) -> dict | None
- list_handoffs(path) -> tuple[dict, ...]

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional, Tuple

from reference.babel.bsl_parser import BabelFile, BabelParseError, parse_file, write_file

BABEL_VERSION = '0.10.2'

__all__ = ['BABEL_VERSION', 'append_handoff', 'get_latest_handoff', 'list_handoffs']

# Handoff ID pattern: handoff-{n}
HANDOFF_ID_PATTERN = re.compile(r'^handoff-(\d+)$')


def _compute_content_sha256(content: str) -> str:
    """Compute SHA256 of raw content string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _extract_handoff_id_number(handoff_id: str) -> int:
    """Extract numeric suffix from handoff-{n} ID."""
    match = HANDOFF_ID_PATTERN.match(handoff_id)
    if not match:
        return 0
    return int(match.group(1))


def append_handoff(
    path: Path,
    content: str,
    agent_id: str,
    next_owner: str,
    signoff: bool,
    blocking_issues: list[str],
    required_changes: list[str],
    summary: str,
    memory_note: str,
) -> Tuple[bool, str]:
    """
    Append a handoff block to a .babel file.
    
    Per v0.10.2 spec:
    - Prepends '## agent: <agent_id>\\n' to content before SHA256
    - Sequential handoff-{n} IDs (max existing + 1, starting at handoff-1)
    - Idempotency: if SHA256 matches most recent handoff, skip append
    - Atomic rewrite via parse_file/write_file
    
    Args:
        path: Path to .babel file
        content: Proposed handoff content (raw text)
        agent_id: Agent identifier for attribution
        next_owner: Next agent to receive this handoff
        signoff: Whether this handoff is signed off
        blocking_issues: List of blocking issue descriptions
        required_changes: List of required change descriptions
        summary: Concise summary of this handoff
        memory_note: Durable note for future sessions
    
    Returns:
        (True, handoff_id) on successful append
        (False, existing_id) on idempotency skip
    
    Raises:
        BabelParseError: If .babel file is invalid
        OSError: If file read/write fails
    """
    # Parse existing file
    babel_file = parse_file(path)
    
    # Build handoff content dict with full schema
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
    }
    
    # Compute SHA256 of agent-prefixed content for idempotency
    agent_prefixed = f'## agent: {agent_id}\n{content}'
    content_sha256 = _compute_content_sha256(agent_prefixed)
    
    # Check idempotency: if handoffs exist and SHA256 matches most recent, skip
    if babel_file.handoffs:
        most_recent = babel_file.handoffs[-1]
        existing_sha256 = _compute_content_sha256(most_recent.content)
        if existing_sha256 == content_sha256:
            return (False, most_recent.id)
    
    # Generate sequential handoff ID
    max_n = 0
    for handoff in babel_file.handoffs:
        n = _extract_handoff_id_number(handoff.id)
        if n > max_n:
            max_n = n
    next_id = f'handoff-{max_n + 1}'
    
    # Build handoff block content as JSON string (raw content for block)
    import json
    block_content = json.dumps(handoff_content, sort_keys=True, indent=2)
    
    # Create new handoff block
    from reference.babel.bsl_parser import BabelBlock
    new_handoff = BabelBlock(
        type='handoff',
        id=next_id,
        version=babel_file.version,
        header_line=0,  # Will be set when written
        content=handoff_content,
    )
    
    # Append to handoffs list
    babel_file.handoffs.append(new_handoff)
    
    # Rebuild file content
    file_lines = [f'#[babel]:v{babel_file.version}']
    
    # Add body blocks
    for block in babel_file.body:
        file_lines.append('')
        file_lines.append(f'#[{block.type}]:{block.id}@{block.version}')
        if block.content is not None:
            block_json = json.dumps(block.content, sort_keys=True, indent=2)
            file_lines.append(block_json)
    
    # Add handoff blocks
    for block in babel_file.handoffs:
        file_lines.append('')
        file_lines.append(f'#[{block.type}]:{block.id}@{block.version}')
        if block.content is not None:
            block_json = json.dumps(block.content, sort_keys=True, indent=2)
            file_lines.append(block_json)
    
    file_content = '\n'.join(file_lines) + '\n'
    
    # Atomic write
    write_file(path, file_content)
    
    return (True, next_id)


def get_latest_handoff(path: Path) -> Optional[dict]:
    """
    Get the most recent handoff from a .babel file.
    
    Args:
        path: Path to .babel file
    
    Returns:
        dict with keys: id, agent_id, content, blocking_issues, required_changes, next_owner, signoff, summary, memory_note
        None if no handoffs exist
    
    Raises:
        BabelParseError: If .babel file is invalid
        OSError: If file read fails
    """
    babel_file = parse_file(path)
    
    if not babel_file.handoffs:
        return None
    
    latest = babel_file.handoffs[-1]
    
    # Extract handoff content (already a dict from parser)
    handoff_data = latest.content
    
    # Build result dict with frozen schema
    return {
        'id': latest.id,
        'agent_id': handoff_data.get('agent_id', ''),
        'content': handoff_data.get('content', ''),
        'blocking_issues': handoff_data.get('blocking_issues', []),
        'required_changes': handoff_data.get('required_changes', []),
        'next_owner': handoff_data.get('next_owner', ''),
        'signoff': handoff_data.get('signoff', False),
        'summary': handoff_data.get('summary', ''),
        'memory_note': handoff_data.get('memory_note', ''),
    }


def list_handoffs(path: Path) -> Tuple[dict, ...]:
    """
    List all handoffs from a .babel file in sequential order.
    
    Args:
        path: Path to .babel file
    
    Returns:
        Tuple of dicts, each with keys: id, agent_id, content, blocking_issues, required_changes, next_owner, signoff, summary, memory_note
        Empty tuple if no handoffs exist
    
    Raises:
        BabelParseError: If .babel file is invalid
        OSError: If file read fails
    """
    babel_file = parse_file(path)
    
    if not babel_file.handoffs:
        return ()
    
    # Sort by numeric handoff ID suffix
    sorted_handoffs = sorted(
        babel_file.handoffs,
        key=lambda h: _extract_handoff_id_number(h.id)
    )
    
    result = []
    for handoff in sorted_handoffs:
        handoff_data = handoff.content
        result.append({
            'id': handoff.id,
            'agent_id': handoff_data.get('agent_id', ''),
            'content': handoff_data.get('content', ''),
            'blocking_issues': handoff_data.get('blocking_issues', []),
            'required_changes': handoff_data.get('required_changes', []),
            'next_owner': handoff_data.get('next_owner', ''),
            'signoff': handoff_data.get('signoff', False),
            'summary': handoff_data.get('summary', ''),
            'memory_note': handoff_data.get('memory_note', ''),
        })
    
    return tuple(result)
