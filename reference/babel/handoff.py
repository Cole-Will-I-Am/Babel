"""Babel v0.10.2 handoff append protocol.

Implements the append-only handoff collaboration record protocol:
- Sequential handoff-{n} IDs (max existing + 1, starting at handoff-1)
- Raw-content SHA256 idempotency guard (agent-prefixed content)
- Atomic rewrite via frozen parser API (parse_file/write_file)

Exports:
- BABEL_VERSION: str = '0.10.2'
- append_handoff: function with signature (path, content, agent_id, next_owner, blocking_issues, required_changes) -> tuple[bool, str]
"""

import hashlib
from pathlib import Path
from typing import List, Tuple

from .bsl_parser import BabelBlock, parse_file, write_file


BABEL_VERSION: str = '0.10.2'

__all__ = ['BABEL_VERSION', 'append_handoff']


def append_handoff(
    path: Path,
    content: str,
    agent_id: str,
    next_owner: str,
    blocking_issues: List[str],
    required_changes: List[str],
) -> Tuple[bool, str]:
    """
    Append a handoff block to a .babel file.
    
    Args:
        path: Path to the .babel file.
        content: Handoff content string.
        agent_id: ID of the agent appending this handoff.
        next_owner: ID of the next agent to receive the handoff.
        blocking_issues: List of blocking issue descriptions.
        required_changes: List of required change descriptions.
    
    Returns:
        Tuple of (appended, handoff_id) where:
        - appended: True if handoff was appended, False if skipped (idempotency).
        - handoff_id: The handoff block ID (e.g., 'handoff-1').
    
    Protocol:
        1. Parse the .babel file using frozen parser API.
        2. Generate sequential handoff-{n} ID (max existing + 1, starting at handoff-1).
        3. Prepend '## agent: <agent_id>\n' to content for attribution.
        4. Compute SHA256 of agent-prefixed content for idempotency check.
        5. If handoffs exist and hash matches most recent, skip append (return False, existing_id).
        6. Otherwise, create handoff block with content dict schema and append.
        7. Write file atomically via frozen parser API.
    
    Errors:
        - BabelParseError: Propagates to CLI wrapper for structured stderr.
        - OSError: Propagates to CLI wrapper for file_error.
    """
    # Parse the file using frozen parser API
    babel_file = parse_file(path)
    
    # Generate sequential handoff ID
    handoff_ids = []
    for block in babel_file.handoffs:
        if block.id.startswith('handoff-'):
            try:
                n = int(block.id.split('-')[1])
                handoff_ids.append(n)
            except (ValueError, IndexError):
                pass
    
    if handoff_ids:
        next_n = max(handoff_ids) + 1
    else:
        next_n = 1
    
    next_id = f'handoff-{next_n}'
    
    # Build handoff content with agent attribution
    agent_header = f'## agent: {agent_id}\n'
    prefixed_content = agent_header + content
    
    # Compute SHA256 for idempotency check
    content_hash = hashlib.sha256(prefixed_content.encode('utf-8')).hexdigest()
    
    # Check idempotency: if handoffs exist and hash matches most recent, skip
    if babel_file.handoffs:
        most_recent = babel_file.handoffs[-1]
        if isinstance(most_recent.content, dict):
            existing_content = most_recent.content.get('content', '')
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
        else:
            existing_content = str(most_recent.content) if most_recent.content else ''
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
        
        if content_hash == existing_hash:
            return (False, most_recent.id)
    
    # Build handoff block content dict per schema
    handoff_content = {
        'path': str(path),
        'content': content,
        'agent_id': agent_id,
        'blocking_issues': blocking_issues,
        'required_changes': required_changes,
    }
    
    # Create handoff block
    handoff_block = BabelBlock(
        type='handoff',
        id=next_id,
        version=babel_file.version,
        header_line=0,
        content=handoff_content,
    )
    
    # Append to handoffs list
    babel_file.handoffs.append(handoff_block)
    
    # Write file atomically via frozen parser API
    # We need to serialize the file back - use the parser's write_file
    # Since write_file expects a string, we need to reconstruct the file content
    # For now, we'll call write_file with a reconstructed content
    # This is a simplification - the full implementation would serialize BabelFile
    
    # Reconstruct file content from parsed structure
    lines = []
    lines.append(f'#[babel]:{babel_file.version}')
    lines.append('')
    
    # Write body blocks (sorted by type rank, id)
    from .bsl_parser import TYPE_ENUM_RANK
    sorted_body = sorted(babel_file.body, key=lambda b: (TYPE_ENUM_RANK.get(b.type, 99), b.id))
    for block in sorted_body:
        lines.append(f'#[{block.type}]:{block.id}@{block.version}')
        if block.content is not None:
            import json
            lines.append(json.dumps(block.content, indent=2, sort_keys=False))
        lines.append('')
    
    # Write handoff blocks (chronological order)
    for block in babel_file.handoffs:
        lines.append(f'#[{block.type}]:{block.id}@{block.version}')
        if block.content is not None:
            import json
            lines.append(json.dumps(block.content, indent=2, sort_keys=False))
        lines.append('')
    
    file_content = '\n'.join(lines)
    write_file(path, file_content)
    
    return (True, next_id)
