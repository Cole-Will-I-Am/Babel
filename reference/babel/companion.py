"""
Babel v0.10.3 companion CLI.

Human-facing command-line interface for Babel files.
Zero-dependency: uses only Python stdlib (argparse, subprocess, json, pathlib).

Subcommands:
- init <path.babel>: Scaffold a new .babel file with intent block.
- render <path.babel>: Pretty-print handoffs in sequential order.
- validate <path.babel>: Run parser validation, exit 0 on success, 6 on error.
- lint <path.babel>: Validate BSL syntax using bsl_validator.

BISC contract (Section 4):
- On BabelParseError: emit stderr JSON, exit 6
- On OSError: emit file_error, exit 6
- On other Exception: emit internal_error, exit 6
- On success: silent, exit 0
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.canonical import canonical_json

# Import from bsl_parser (no circular import since resolve_companion is there)
from reference.babel.bsl_parser import (
    BabelParseError,
    BabelFile,
    parse_file,
    resolve_companion,
    write_file,
)

# Import handoff functions for render command
from reference.babel.handoff import list_handoffs


def emit_stderr_json(error: str, code: str, line: Optional[int], message: str) -> None:
    """Emit BISC-compliant stderr JSON (no trailing newline in content, newline after)."""
    obj = {
        'error': error,
        'code': code,
        'line': line,
        'message': message,
    }
    sys.stderr.write(canonical_json(obj).rstrip('\n'))
    sys.stderr.write('\n')


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a new .babel file with minimal intent block."""
    path = Path(args.path)
    
    # Check if file already exists
    if path.exists():
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message=f'File already exists: {path}',
        )
        return 6
    
    # Scaffold minimal .babel content
    content = """#[babel]:0.10.2
#[intent]:main@0.10.2
{"agent_id": "agent"}
"""
    
    try:
        write_file(path, content)
        return 0
    except OSError as e:
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message=f'{path}: {e}',
        )
        return 6


def cmd_render(args: argparse.Namespace) -> int:
    """Pretty-print handoffs from a .babel file."""
    path = Path(args.path)
    
    try:
        handoffs = list_handoffs(path)
        
        if not handoffs:
            print("No handoffs found.")
            return 0
        
        for i, handoff in enumerate(handoffs):
            print(f"--- Handoff {i + 1} ---")
            print(f"ID: {handoff.get('id', 'unknown')}")
            print(f"Agent: {handoff.get('agent_id', 'unknown')}")
            print(f"Summary: {handoff.get('summary', 'no summary')}")
            print()
        
        return 0
    
    except BabelParseError as e:
        sys.stderr.write(e.to_stderr_json())
        sys.stderr.write('\n')
        return 6
    
    except OSError as e:
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message=f'{path}: {e}',
        )
        return 6
    
    except Exception as e:
        exc_class = type(e).__name__
        emit_stderr_json(
            error='InternalError',
            code='internal_error',
            line=None,
            message=f'{exc_class}: {e}',
        )
        return 6


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a .babel file by running parser via subprocess."""
    path = Path(args.path)
    
    # Run parser as subprocess for isolation
    result = subprocess.run(
        [sys.executable, '-m', 'reference.babel', str(path)],
        capture_output=True,
        text=True,
    )
    
    # Forward stderr output
    if result.stderr:
        sys.stderr.write(result.stderr)
    
    return result.returncode


def cmd_lint(args: argparse.Namespace) -> int:
    """Lint a .babel file using bsl_validator."""
    path = Path(args.path)
    
    try:
        # Import here to avoid circular import at module level
        from reference.babel.bsl_validator import validate_file
        
        validate_file(path)
        # Print success JSON to stdout
        print(canonical_json({'valid': True}).rstrip('\n'))
        return 0
    
    except BabelParseError as e:
        # Print error JSON to stderr
        error_obj = {
            'path': str(path),
            'line': e.line,
            'code': e.code,
        }
        sys.stderr.write(canonical_json(error_obj).rstrip('\n'))
        sys.stderr.write('\n')
        return 6
    
    except OSError as e:
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message=f'{path}: {e}',
        )
        return 6
    
    except Exception as e:
        exc_class = type(e).__name__
        emit_stderr_json(
            error='InternalError',
            code='internal_error',
            line=None,
            message=f'{exc_class}: {e}',
        )
        return 6


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='babel-companion',
        description='Babel companion CLI for human-facing operations',
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # init subcommand
    init_parser = subparsers.add_parser('init', help='Scaffold a new .babel file')
    init_parser.add_argument('path', help='Path to new .babel file')
    init_parser.set_defaults(func=cmd_init)
    
    # render subcommand
    render_parser = subparsers.add_parser('render', help='Pretty-print handoffs')
    render_parser.add_argument('path', help='Path to .babel file')
    render_parser.set_defaults(func=cmd_render)
    
    # validate subcommand
    validate_parser = subparsers.add_parser('validate', help='Validate .babel file')
    validate_parser.add_argument('path', help='Path to .babel file')
    validate_parser.set_defaults(func=cmd_validate)
    
    # lint subcommand
    lint_parser = subparsers.add_parser('lint', help='Lint .babel file syntax')
    lint_parser.add_argument('path', help='Path to .babel file')
    lint_parser.set_defaults(func=cmd_lint)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
