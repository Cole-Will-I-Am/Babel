"""Babel v0.10.3 companion CLI.

Human-facing command-line interface for Babel files.
Zero-dependency: uses only Python stdlib (argparse, subprocess, json, pathlib).

Subcommands:
- init <path.babel>: Scaffold a new .babel file with intent block.
- render <path.babel>: Pretty-print handoffs in sequential order.
- validate <path.babel>: Exit 0 if valid, 6 if invalid (BISC stderr JSON).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .handoff import list_handoffs, append_handoff

__all__ = ['main', 'resolve_companion']


def resolve_companion(babel_path: Path) -> Path | None:
    """Resolve the companion .md file for a .babel file.
    
    The companion_path contract: the .md filename must share the basename
    of the .babel file (e.g., module.babel pairs with module.md).
    
    Args:
        babel_path: Path to the .babel file.
    
    Returns:
        Path to the sibling .md file if it exists as a regular file,
        otherwise None.
    """
    if not babel_path.suffix == '.babel':
        return None
    
    md_path = babel_path.with_suffix('.md')
    if md_path.is_file():
        return md_path
    return None


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new .babel file with an intent block."""
    path = args.path
    
    # Check if file already exists
    if path.exists():
        print(f'Error: {path} already exists', file=sys.stderr)
        return 1
    
    # Create minimal .babel content with intent block
    intent_body = json.dumps({
        'id': 'init',
        'version': '0.10.3',
        'agent_id': 'minimadmax',
    }, separators=(',', ':'))
    
    content = f'''#[babel]:v0.10.3
#[intent]:init@0.10.3
{intent_body}
'''
    
    path.write_text(content, encoding='utf-8')
    print(f'Created {path}')
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    """Pretty-print handoffs in sequential order."""
    path = args.path
    
    if not path.exists():
        print(f'Error: {path} does not exist', file=sys.stderr)
        return 1
    
    try:
        handoffs = list_handoffs(path)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1
    
    if not handoffs:
        print('No handoffs found.')
        return 0
    
    for handoff in handoffs:
        hid = handoff['id']
        agent = handoff['agent_id']
        content = handoff['content']
        
        print(f'--- {hid} (agent: {agent}) ---')
        print(content)
        print()
    
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a .babel file via subprocess to python -m babel."""
    path = args.path
    
    if not path.exists():
        print(f'Error: {path} does not exist', file=sys.stderr)
        return 1
    
    # Shell out to python -m babel for zero-dependency boundary
    result = subprocess.run(
        [sys.executable, '-m', 'babel', str(path)],
        capture_output=True,
        text=True,
    )
    
    # Print stderr (BISC JSON on error)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    
    # Map exit codes: 0 = valid, 6 = parse error, other = internal
    if result.returncode == 0:
        return 0
    elif result.returncode == 6:
        return 6
    else:
        # Unexpected non-zero exit
        print(f'Internal error: exit code {result.returncode}', file=sys.stderr)
        return result.returncode


def main(argv: list[str] | None = None) -> int:
    """Main entry point for companion CLI."""
    parser = argparse.ArgumentParser(
        prog='babel-companion',
        description='Babel companion CLI for human-facing operations.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # init subcommand
    init_parser = subparsers.add_parser(
        'init',
        help='Scaffold a new .babel file with intent block.',
    )
    init_parser.add_argument(
        'path',
        type=Path,
        help='Path to the new .babel file.',
    )
    init_parser.set_defaults(func=cmd_init)
    
    # render subcommand
    render_parser = subparsers.add_parser(
        'render',
        help='Pretty-print handoffs in sequential order.',
    )
    render_parser.add_argument(
        'path',
        type=Path,
        help='Path to the .babel file.',
    )
    render_parser.set_defaults(func=cmd_render)
    
    # validate subcommand
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate .babel file (exit 0 valid, 6 invalid).',
    )
    validate_parser.add_argument(
        'path',
        type=Path,
        help='Path to the .babel file.',
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
