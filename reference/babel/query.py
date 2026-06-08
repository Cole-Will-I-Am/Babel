"""Babel v0.10.3 Read-Query Protocol

Deterministic, immutable, versioned query interface over validated BSL AST.
Decouples read-side progress from write-side gating (Stages 12a/12b).

Public API:
- select_handoffs(ast, *, agent_id=None, signoff=None) -> tuple[MappingProxyType, ...]

Architecture:
- Operates exclusively on AST from bsl_parser.parse_file (validated BSL).
- Returns immutable views via types.MappingProxyType.
- Deterministic ordering by ascending _line.
- query_protocol_version=1 in HandoffView metadata.

Usage:
    from babel.query import select_handoffs
    from babel.bsl_parser import parse_file
    
    ast = parse_file('path/to/file.babel')
    handoffs = select_handoffs(ast, agent_id='agent-1', signoff=True)
    for handoff in handoffs:
        print(handoff['path'], handoff['_line'])
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Iterator, Literal, Mapping, TypedDict

from .handoff import HANDOFF_SCHEMA


class HandoffView(TypedDict):
    """Immutable view of a handoff block with query metadata.
    
    Extends HANDOFF_SCHEMA (9 payload keys) with underscore-prefixed metadata:
    - _line: int -- Source line number of the handoff block header
    - _block_id: str -- Unique block identifier from the header
    - _query_protocol_version: Literal[1] -- Schema version for compatibility detection
    
    Every instance returned by select_handoffs is wrapped in MappingProxyType
    to enforce runtime immutability. Consuming agents cannot mutate the view.
    
    The underscore prefix on metadata fields avoids collision with the 9
    payload keys defined in HANDOFF_SCHEMA.
    """
    # Metadata (underscore-prefixed, not in HANDOFF_SCHEMA)
    _line: int
    _block_id: str
    _query_protocol_version: Literal[1]
    
    # Payload keys from HANDOFF_SCHEMA (9 keys)
    path: str
    content: str
    agent_id: str
    next_owner: str
    signoff: bool
    blocking_issues: list[str]
    required_changes: list[str]
    summary: str
    memory_note: str


def _filter_by_agent_id(
    blocks: Iterator[Mapping[str, Any]],
    agent_id: str | None,
) -> Iterator[Mapping[str, Any]]:
    """Filter handoff blocks by agent_id.
    
    Args:
        blocks: Iterator of parsed handoff block dicts with 'content' key.
        agent_id: Filter value. If None, all blocks pass. If str, only blocks
            where content['agent_id'] == agent_id pass.
    
    Yields:
        Block dicts matching the agent_id filter (or all if agent_id is None).
    
    Private helper: underscore prefix keeps this out of public API until
    usage patterns stabilize.
    """
    if agent_id is None:
        yield from blocks
        return
    
    for block in blocks:
        content = block.get('content', {})
        if isinstance(content, dict) and content.get('agent_id') == agent_id:
            yield block


def _filter_by_signoff_status(
    blocks: Iterator[Mapping[str, Any]],
    signoff: bool | None,
) -> Iterator[Mapping[str, Any]]:
    """Filter handoff blocks by signoff status.
    
    Args:
        blocks: Iterator of parsed handoff block dicts with 'content' key.
        signoff: Filter value. If None, all blocks pass. If True, only blocks
            where content['signoff'] is True pass. If False, only blocks where
            content['signoff'] is False pass.
    
    Yields:
        Block dicts matching the signoff filter (or all if signoff is None).
    
    Private helper: underscore prefix keeps this out of public API until
    usage patterns stabilize.
    """
    if signoff is None:
        yield from blocks
        return
    
    for block in blocks:
        content = block.get('content', {})
        if isinstance(content, dict) and content.get('signoff') is signoff:
            yield block


def _build_handoff_view(
    block: Mapping[str, Any],
    line: int,
    block_id: str,
) -> MappingProxyType:
    """Construct an immutable HandoffView from a parsed block.
    
    Args:
        block: Parsed handoff block dict with 'content' key containing the
            9 payload fields from HANDOFF_SCHEMA.
        line: Source line number of the block header.
        block_id: Unique block identifier from the header.
    
    Returns:
        MappingProxyType wrapping a HandoffView dict with metadata and payload.
    
    The MappingProxyType wrapper enforces runtime immutability: any attempt
    to modify the returned view raises TypeError.
    """
    content = block.get('content', {})
    
    view: dict[str, Any] = {
        # Metadata
        '_line': line,
        '_block_id': block_id,
        '_query_protocol_version': 1,
        # Payload (9 keys from HANDOFF_SCHEMA)
        'path': content.get('path', ''),
        'content': content.get('content', ''),
        'agent_id': content.get('agent_id', ''),
        'next_owner': content.get('next_owner', ''),
        'signoff': content.get('signoff', False),
        'blocking_issues': content.get('blocking_issues', []),
        'required_changes': content.get('required_changes', []),
        'summary': content.get('summary', ''),
        'memory_note': content.get('memory_note', ''),
    }
    
    return MappingProxyType(view)


def select_handoffs(
    ast: Mapping[str, Any],
    *,
    agent_id: str | None = None,
    signoff: bool | None = None,
) -> tuple[MappingProxyType, ...]:
    """Query handoff blocks from a validated BSL AST.
    
    Returns deterministic, immutable views of handoff blocks ordered by
    ascending source line number. Keyword-only filter arguments prevent
    positional ambiguity.
    
    Args:
        ast: AST returned by bsl_parser.parse_file. Must have 'blocks' key
            containing a list of parsed block dicts. Each block dict must have
            'header_line', 'block_id', 'block_type', and 'content' keys.
        agent_id: Optional filter. If provided, only handoffs where
            content['agent_id'] matches are returned.
        signoff: Optional filter. If True, only handoffs with signoff=True.
            If False, only handoffs with signoff=False. If None (default),
            signoff status is ignored.
    
    Returns:
        Tuple of MappingProxyType-wrapped HandoffView dicts, ordered by
        ascending _line. Empty tuple if no matches or no handoff blocks.
    
    Raises:
        TypeError: If ast does not have validated structure (missing 'blocks'
            key, blocks not a list, or blocks lack required keys).
    
    Contract:
        - Operates exclusively on validated AST from bsl_parser.parse_file.
        - Does not accept raw text strings or dict literals.
        - Does not reimplement grammar validation (that is bsl_validator's job).
        - Does not duplicate bsl_validator responsibilities.
    
    Example:
        from babel.query import select_handoffs
        from babel.bsl_parser import parse_file
        
        ast = parse_file('handoffs.babel')
        
        # All handoffs
        all_handoffs = select_handoffs(ast)
        
        # Handoffs for specific agent
        my_handoffs = select_handoffs(ast, agent_id='agent-1')
        
        # Pending handoffs (not signed off)
        pending = select_handoffs(ast, signoff=False)
        
        # Signed handoffs for specific agent
        done = select_handoffs(ast, agent_id='agent-1', signoff=True)
    """
    # Validated-AST-only contract: raise TypeError on invalid input
    if not isinstance(ast, dict):
        raise TypeError(
            f"select_handoffs requires a dict AST, got {type(ast).__name__}. "
            "Pass the result of bsl_parser.parse_file(), not raw text."
        )
    
    if 'blocks' not in ast:
        raise TypeError(
            "AST missing 'blocks' key. Pass the result of bsl_parser.parse_file(), "
            "not a raw dict literal."
        )
    
    blocks = ast['blocks']
    if not isinstance(blocks, list):
        raise TypeError(
            f"AST 'blocks' must be a list, got {type(blocks).__name__}. "
            "Pass the result of bsl_parser.parse_file(), not a malformed dict."
        )
    
    # Extract handoff blocks with their line numbers and block IDs
    handoff_blocks: list[tuple[int, str, Mapping[str, Any]]] = []
    for block in blocks:
        if not isinstance(block, dict):
            raise TypeError(
                f"Block must be a dict, got {type(block).__name__}. "
                "AST appears corrupted or not from bsl_parser.parse_file()."
            )
        
        block_type = block.get('block_type')
        if block_type != 'handoff':
            continue
        
        header_line = block.get('header_line')
        block_id = block.get('block_id')
        
        if header_line is None or block_id is None:
            raise TypeError(
                f"Handoff block missing header_line or block_id: {block}. "
                "AST appears corrupted or not from bsl_parser.parse_file()."
            )
        
        handoff_blocks.append((header_line, block_id, block))
    
    # Sort by line number ascending for deterministic ordering
    handoff_blocks.sort(key=lambda x: x[0])
    
    # Create iterator of (line, block_id, block) tuples
    block_iter = iter(handoff_blocks)
    
    # Apply filters via private helpers
    filtered = _filter_by_agent_id(
        (block for _, _, block in block_iter),
        agent_id,
    )
    
    # Rebuild the list with line/block_id info after first filter
    # We need to track which blocks passed the first filter
    handoff_blocks_after_agent = [
        (line, block_id, block)
        for (line, block_id, block), filtered_block in zip(
            handoff_blocks,
            _filter_by_agent_id((block for _, _, block in iter(handoff_blocks)), agent_id),
        )
        if filtered_block is block  # Identity check: block passed filter
    ]
    
    # Actually, simpler approach: rebuild filtered list properly
    def _apply_filters() -> list[tuple[int, str, Mapping[str, Any]]]:
        result = []
        for line, block_id, block in handoff_blocks:
            # Agent filter
            if agent_id is not None:
                content = block.get('content', {})
                if not isinstance(content, dict) or content.get('agent_id') != agent_id:
                    continue
            
            # Signoff filter
            if signoff is not None:
                content = block.get('content', {})
                if not isinstance(content, dict) or content.get('signoff') is not signoff:
                    continue
            
            result.append((line, block_id, block))
        
        return result
    
    filtered_blocks = _apply_filters()
    
    # Build immutable views and collect into tuple
    views = [
        _build_handoff_view(block, line, block_id)
        for line, block_id, block in filtered_blocks
    ]
    
    return tuple(views)
