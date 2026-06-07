"""
Babel v0.10.2 Reference Parser

Implements the Babel Source Language (BSL) parser for .babel files.
Public API is frozen for v0.10.2; logic implementation proceeds in stages 4a-4c.

Exports:
- BABEL_VERSION: str = '0.10.2'
- BLOCK_TYPES: tuple[str, ...] = ('intent', 'spec', 'test', 'impl', 'handoff')
- BODY_TYPES: tuple[str, ...] = ('intent', 'spec', 'test', 'impl')
- HANDOFF_TYPE: str = 'handoff'
- TYPE_ENUM_RANK: dict[str, int] - ordering for body sort
- BabelBlock: dataclass with type, id, version, content, header_line
- BabelFile: dataclass with version, body, handoffs, source_path
- BabelParseError: exception with code, line, message attributes
- parse_file(path: Path) -> BabelFile
- write_file(path: Path, babel_file: BabelFile) -> None
- to_virtual_json(babel_file: BabelFile) -> dict
- companion_path(babel_path: Path) -> Optional[Path] - re-export from companion
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Re-export companion resolver per BISC amendment section 7
from reference.babel.companion import resolve_companion as companion_path

BABEL_VERSION = '0.10.2'
BLOCK_TYPES = ('intent', 'spec', 'test', 'impl', 'handoff')
BODY_TYPES = ('intent', 'spec', 'test', 'impl')
HANDOFF_TYPE = 'handoff'
TYPE_ENUM_RANK = {'intent': 0, 'spec': 1, 'test': 2, 'impl': 3, 'handoff': 99}

# Header regex: #[type]:id@version
HEADER_REGEX = re.compile(r'^#\[(\w+)\]:([^@]+)@([^\s]+)$')


class BabelParseError(Exception):
    """Parser error with stable code attribute for BISC error taxonomy."""
    
    def __init__(self, code: str, line: int, message: str):
        self.code = code
        self.line = line
        self.message = message
        super().__init__(message)


@dataclass
class BabelBlock:
    """A single block in a .babel file."""
    type: str
    id: str
    version: str
    content: dict
    header_line: int  # 1-based line number of header


@dataclass
class BabelFile:
    """Parsed .babel file AST."""
    version: str
    body: list[BabelBlock] = field(default_factory=list)
    handoffs: list[BabelBlock] = field(default_factory=list)
    source_path: Optional[Path] = None


def _scan_file(content: str) -> tuple[str, list[BabelBlock], list[BabelBlock]]:
    """
    Scan phase: parse headers and extract blocks.
    
    Returns:
        (version, body_blocks, handoff_blocks)
    
    Raises:
        BabelParseError: on malformed headers or invalid JSON
    """
    lines = content.split('\n')
    
    # Normalize: strip trailing whitespace from each line
    lines = [line.rstrip() for line in lines]
    
    # Check for babel header at line 1
    if not lines or not lines[0].startswith('#[babel]:'):
        raise BabelParseError(
            code='malformed_header',
            line=1,
            message='File must begin with #[babel]:<id>@<version> header'
        )
    
    # Parse babel header to get version
    babel_header_match = HEADER_REGEX.match(lines[0])
    if not babel_header_match:
        raise BabelParseError(
            code='malformed_header',
            line=1,
            message='Invalid #[babel] header syntax'
        )
    
    file_version = babel_header_match.group(3)
    
    body_blocks: list[BabelBlock] = []
    handoff_blocks: list[BabelBlock] = []
    
    i = 1
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines between blocks
        if not line:
            i += 1
            continue
        
        # Check for block header
        if line.startswith('#['):
            header_line = i + 1  # 1-based
            match = HEADER_REGEX.match(line)
            
            if not match:
                raise BabelParseError(
                    code='malformed_header',
                    line=header_line,
                    message=f'Invalid block header syntax: {line}'
                )
            
            block_type = match.group(1)
            block_id = match.group(2)
            block_version = match.group(3)
            
            if block_type not in BLOCK_TYPES:
                raise BabelParseError(
                    code='malformed_header',
                    line=header_line,
                    message=f'Unknown block type "{block_type}" - must be one of: intent, spec, test, impl, handoff'
                )
            
            # Extract content (lines until next header or EOF)
            content_lines: list[str] = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith('#['):
                    break
                content_lines.append(next_line)
                i += 1
            
            # Parse content as JSON
            content_text = '\n'.join(content_lines).strip()
            if not content_text:
                content_json = {}
            else:
                try:
                    content_json = json.loads(content_text)
                except json.JSONDecodeError as e:
                    raise BabelParseError(
                        code='invalid_intent_json',
                        line=header_line,
                        message=f'Invalid JSON in block content: {e}'
                    )
            
            block = BabelBlock(
                type=block_type,
                id=block_id,
                version=block_version,
                content=content_json,
                header_line=header_line
            )
            
            if block_type in BODY_TYPES:
                body_blocks.append(block)
            else:
                handoff_blocks.append(block)
        else:
            # Non-empty line that's not a header - skip (could be whitespace)
            i += 1
    
    return file_version, body_blocks, handoff_blocks


def _normalize(
    version: str,
    body: list[BabelBlock],
    handoffs: list[BabelBlock]
) -> tuple[list[BabelBlock], list[BabelBlock]]:
    """
    Normalize phase: validate and sort blocks.
    
    Enforces:
    - Body sort by (TYPE_ENUM_RANK[type], id)
    - Global duplicate (type, id) detection across body+handoff
    - Version consistency across all blocks
    - Exactly-one intent block in body
    - Minimal intent schema (agent_id required, string)
    
    Returns:
        (sorted_body, handoffs) - handoffs remain chronological
    
    Raises:
        BabelParseError: on validation failures
    """
    all_blocks = body + handoffs
    
    # 1. Check version consistency first
    if all_blocks:
        expected_version = all_blocks[0].version
        for block in all_blocks[1:]:
            if block.version != expected_version:
                raise BabelParseError(
                    code='version_mismatch',
                    line=block.header_line,
                    message=f"Block version '{block.version}' does not match file version '{expected_version}'"
                )
    
    # 2. Check for duplicate (type, id) pairs - MUST run before intent checks
    # This ensures duplicate_id is raised before missing_intent/multiple_intents
    seen_keys: set[tuple[str, str]] = set()
    for block in all_blocks:
        key = (block.type, block.id)
        if key in seen_keys:
            raise BabelParseError(
                code='duplicate_id',
                line=block.header_line,
                message=f"Duplicate block: #[{block.type}]:{block.id}@{block.version}"
            )
        seen_keys.add(key)
    
    # 3. Validate intent blocks (exactly one required in body)
    intent_blocks = [b for b in body if b.type == 'intent']
    
    if len(intent_blocks) == 0:
        # missing_intent: no intent block in body
        if not body:
            raise BabelParseError(
                code='missing_intent',
                line=1,
                message='No intent block in body'
            )
        else:
            raise BabelParseError(
                code='missing_intent',
                line=body[0].header_line,
                message='No intent block in body'
            )
    
    if len(intent_blocks) > 1:
        # Check if any have same id (duplicate_id takes precedence - already caught above)
        # If we reach here, ids are distinct - multiple_intents
        second_intent = intent_blocks[1]
        raise BabelParseError(
            code='multiple_intents',
            line=second_intent.header_line,
            message='Multiple intent blocks found; exactly one required'
        )
    
    # 4. Validate intent schema (agent_id required, string)
    intent_block = intent_blocks[0]
    intent_content = intent_block.content
    
    if not isinstance(intent_content, dict):
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent_block.header_line,
            message='Intent block content must be a JSON object'
        )
    
    if 'agent_id' not in intent_content:
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent_block.header_line,
            message='Intent block missing required field: agent_id'
        )
    
    if not isinstance(intent_content['agent_id'], str):
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent_block.header_line,
            message='Intent block agent_id must be a string'
        )
    
    # 5. Sort body by (TYPE_ENUM_RANK[type], id)
    sorted_body = sorted(body, key=lambda b: (TYPE_ENUM_RANK[b.type], b.id))
    
    return sorted_body, handoffs


def parse_file(path: Path) -> BabelFile:
    """
    Parse a .babel file into a BabelFile AST.
    
    Args:
        path: Path to the .babel file
        
    Returns:
        BabelFile with parsed blocks
        
    Raises:
        BabelParseError: on parse or validation failures
        FileNotFoundError: if file doesn't exist
    """
    content = path.read_text(encoding='utf-8')
    
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Scan phase
    version, body, handoffs = _scan_file(content)
    
    # Normalize phase
    sorted_body, handoffs = _normalize(version, body, handoffs)
    
    return BabelFile(
        version=version,
        body=sorted_body,
        handoffs=handoffs,
        source_path=path
    )


def write_file(path: Path, babel_file: BabelFile) -> None:
    """
    Write a BabelFile to disk.
    
    Args:
        path: Destination path for .babel file
        babel_file: BabelFile to write
        
    Raises:
        NotImplementedError: stub for stage 4c
    """
    raise NotImplementedError('write_file: implement in stage 4c (atomic tempfile+rename)')


def to_virtual_json(babel_file: BabelFile) -> dict:
    """
    Convert BabelFile to virtual JSON representation.
    
    Handoff blocks are excluded. Body blocks are represented as
    /blocks/<type>:<id> paths.
    
    Args:
        babel_file: BabelFile to convert
        
    Returns:
        dict with virtual JSON structure
        
    Raises:
        NotImplementedError: stub for stage 4c
    """
    raise NotImplementedError('to_virtual_json: implement in stage 4c (handoff-excluded paths)')
