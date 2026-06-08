"""
Babel v0.10.2 Reference Parser

Implements the Babel Source Language (BSL) parser for .babel files.
Public API is frozen for v0.10.2; logic implementation proceeds in stages 4a-4c.

Exports:
- BABEL_VERSION: str = '0.10.2'
- BLOCK_TYPES: tuple[str, ...] = ('intent', 'spec', 'test', 'impl', 'handoff')
- BabelParseError: exception class with code, line, message attributes
- BabelBlock: dataclass for parsed blocks
- BabelFile: dataclass for parsed files
- parse_file: main parser entry point
- write_file: atomic file writer
- to_virtual_json: handoff-excluded virtual JSON export
- companion_path: re-export from reference.babel.companion
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.canonical import canonical_json

# Re-export companion resolver per BISC amendment section 7
from reference.babel.companion import resolve_companion as companion_path

BABEL_VERSION = '0.10.2'
BLOCK_TYPES = ('intent', 'spec', 'test', 'impl', 'handoff')
BODY_TYPES = ('intent', 'spec', 'test', 'impl')
HANDOFF_TYPE = 'handoff'

# Deterministic type ordering for body sort and virtual JSON
TYPE_ENUM_RANK = {
    'intent': 0,
    'spec': 1,
    'test': 2,
    'impl': 3,
    'handoff': 99,  # handoffs excluded from body sort but have high rank
}

# Header regex: #[type]:id@version
HEADER_REGEX = re.compile(r'^#\[(\w+)\]:([^@]+)@([^\s]+)$')

# File header regex: #[babel]:v*.*.* (relaxed: optional 'v' prefix)
FILE_HEADER_REGEX = re.compile(r'^#\[babel\]:v?\d+\.\d+\.\d+$')


@dataclass
class BabelParseError(Exception):
    """Parser error with BISC-compliant error code, line number, and message."""
    code: str
    line: int
    message: str

    def to_stderr_json(self) -> str:
        """Return BISC-compliant stderr JSON (no trailing newline)."""
        obj = {
            'error': 'BabelParseError',
            'code': self.code,
            'line': self.line,
            'message': self.message,
        }
        return canonical_json(obj).rstrip('\n')


@dataclass
class BabelBlock:
    """A parsed block from a .babel file."""
    type: str
    id: str
    version: str
    header_line: int  # 1-based line number of header
    content: Any  # parsed JSON content


@dataclass
class BabelFile:
    """A parsed .babel file."""
    version: str
    body: List[BabelBlock]
    handoffs: List[BabelBlock]
    source_path: Optional[Path] = None


def _scan_file(content: str) -> Tuple[List[BabelBlock], List[BabelBlock]]:
    """
    Scan file content and extract blocks.
    
    Returns (body_blocks, handoff_blocks) where body_blocks contains
    intent/spec/test/impl blocks and handoff_blocks contains handoff blocks.
    
    Raises BabelParseError on malformed_header or invalid_intent_json.
    """
    lines = content.split('\n')
    body_blocks: List[BabelBlock] = []
    handoff_blocks: List[BabelBlock] = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip blank lines and non-header lines
        if not line.strip() or not line.startswith('#['):
            i += 1
            continue
        
        # Try to match header
        match = HEADER_REGEX.match(line)
        if not match:
            raise BabelParseError(
                code='malformed_header',
                line=i + 1,  # 1-based
                message=f'Malformed block header: {line}',
            )
        
        block_type = match.group(1)
        block_id = match.group(2)
        block_version = match.group(3)
        header_line = i + 1  # 1-based
        
        # Validate block type
        if block_type not in BLOCK_TYPES:
            raise BabelParseError(
                code='malformed_header',
                line=header_line,
                message=f'Unknown block type "{block_type}" - must be one of: {", ".join(BLOCK_TYPES)}',
            )
        
        # Extract content (lines after header until next header or EOF)
        content_lines: List[str] = []
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if next_line.strip().startswith('#['):
                break
            content_lines.append(next_line)
            j += 1
        
        # Parse content as JSON
        content_text = '\n'.join(content_lines)
        try:
            if content_text.strip():
                block_content = json.loads(content_text)
            else:
                block_content = None
        except json.JSONDecodeError as e:
            raise BabelParseError(
                code='invalid_intent_json',
                line=header_line,
                message=f'Invalid JSON in block content: {e}',
            )
        
        block = BabelBlock(
            type=block_type,
            id=block_id,
            version=block_version,
            header_line=header_line,
            content=block_content,
        )
        
        if block_type == HANDOFF_TYPE:
            handoff_blocks.append(block)
        else:
            body_blocks.append(block)
        
        i = j
    
    return body_blocks, handoff_blocks


def _normalize(
    body: List[BabelBlock],
    handoffs: List[BabelBlock],
) -> List[BabelBlock]:
    """
    Normalize and validate blocks.
    
    - Sort body by (TYPE_ENUM_RANK[type], id)
    - Detect duplicate (type, id) across body+handoffs
    - Detect version mismatch across all blocks
    - Validate exactly one intent block with minimal schema
    
    Returns sorted body list.
    Raises BabelParseError on validation failure.
    """
    all_blocks = body + handoffs
    
    # 1. Check for duplicate (type, id) across all blocks
    seen: Dict[Tuple[str, str], BabelBlock] = {}
    for block in all_blocks:
        key = (block.type, block.id)
        if key in seen:
            raise BabelParseError(
                code='duplicate_id',
                line=block.header_line,
                message=f'Duplicate block: {block.type}:{block.id} (first at line {seen[key].header_line})',
            )
        seen[key] = block
    
    # 2. Check version consistency across all blocks
    versions: Dict[str, List[BabelBlock]] = {}
    for block in all_blocks:
        if block.version not in versions:
            versions[block.version] = []
        versions[block.version].append(block)
    
    if len(versions) > 1:
        # Find the first block with a different version
        first_version = next(iter(versions))
        for block in all_blocks:
            if block.version != first_version:
                raise BabelParseError(
                    code='version_mismatch',
                    line=block.header_line,
                    message=f'Version mismatch: {block.version} (expected {first_version})',
                )
    
    # 3. Validate intent blocks
    intent_blocks = [b for b in body if b.type == 'intent']
    
    if len(intent_blocks) == 0:
        raise BabelParseError(
            code='missing_intent',
            line=1,  # file header line
            message='No intent block found in body',
        )
    
    if len(intent_blocks) > 1:
        # multiple_intents only fires for distinct ids (duplicate_id checked first)
        second_intent = intent_blocks[1]
        raise BabelParseError(
            code='multiple_intents',
            line=second_intent.header_line,
            message=f'Multiple intent blocks found (second at line {second_intent.header_line})',
        )
    
    # 4. Validate intent schema (minimal: agent_id required, string)
    intent = intent_blocks[0]
    if not isinstance(intent.content, dict):
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent.header_line,
            message='Intent block content must be a JSON object',
        )
    
    if 'agent_id' not in intent.content:
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent.header_line,
            message='Intent block missing required key: agent_id',
        )
    
    if not isinstance(intent.content['agent_id'], str):
        raise BabelParseError(
            code='invalid_intent_json',
            line=intent.header_line,
            message='Intent block agent_id must be a string',
        )
    
    # 5. Sort body by (TYPE_ENUM_RANK[type], id)
    sorted_body = sorted(body, key=lambda b: (TYPE_ENUM_RANK.get(b.type, 99), b.id))
    
    return sorted_body


def parse_file(path: Path) -> BabelFile:
    """
    Parse a .babel file and return a BabelFile AST.
    
    Raises BabelParseError on validation failure.
    Raises OSError on file read failure.
    """
    # Read file
    content = path.read_text(encoding='utf-8')
    
    # Validate file header (relaxed: any #[babel]:v*.*.* format)
    lines = content.split('\n')
    header_found = False
    for line in lines:
        if line.strip():
            # Strip whitespace before matching
            stripped = line.strip()
            if FILE_HEADER_REGEX.match(stripped):
                header_found = True
            break
    
    if not header_found:
        raise BabelParseError(
            code='malformed_header',
            line=1,
            message='Missing or invalid file header: expected #[babel]:v*.*.*',
        )
    
    # Scan and normalize
    body, handoffs = _scan_file(content)
    sorted_body = _normalize(body, handoffs)
    
    return BabelFile(
        version=BABEL_VERSION,
        body=sorted_body,
        handoffs=handoffs,
        source_path=path,
    )


def write_file(path: Path, content: str) -> None:
    """
    Write content to a .babel file atomically.
    
    Uses tempfile + os.replace for atomic write.
    Cleans up tempfile on failure using explicit tmp_path tracking.
    
    Raises OSError on write failure.
    """
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=path.parent,
            delete=False,
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(content)
        
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def to_virtual_json(babel_file: BabelFile) -> str:
    """
    Export a BabelFile to virtual JSON format.
    
    Schema: /blocks/<type>:<id> -> {type, id, version, header_line, content}
    Excludes handoff blocks.
    Orders by normalized body sort (TYPE_ENUM_RANK[type], id).
    
    Returns JSON string with trailing LF. Keys are ordered by type rank,
    not alphabetically, to match spec requirements.
    """
    # Sort body blocks by (TYPE_ENUM_RANK[type], id) to ensure deterministic key order
    sorted_blocks = sorted(babel_file.body, key=lambda b: (TYPE_ENUM_RANK.get(b.type, 99), b.id))
    
    # Build JSON manually to preserve key order (canonical_json sorts alphabetically)
    block_strs = []
    for block in sorted_blocks:
        key = f'/blocks/{block.type}:{block.id}'
        block_obj = {
            'type': block.type,
            'id': block.id,
            'version': block.version,
            'header_line': block.header_line,
            'content': block.content,
        }
        # Use json.dumps with sort_keys=False to preserve insertion order within block
        block_json = json.dumps(block_obj, sort_keys=False, ensure_ascii=False)
        block_strs.append(f'"{key}":{block_json}')
    
    result = '{' + ','.join(block_strs) + '}\n'
    return result
