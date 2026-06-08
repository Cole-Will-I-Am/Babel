"""Babel v0.10.3 companion CLI.

Human-facing command-line interface for Babel files.
Zero-dependency: uses only Python stdlib (argparse, subprocess, json, pathlib).

Subcommands:
- init <path.babel>: Scaffold a new .babel file with intent block.
- render <path.babel>: Pretty-print handoffs in sequence.
- validate <path.babel>: Validate whole file (CI/human use).
- lint <path.babel>: Single-file lint with BISC-compliant JSON output.

Usage:
    python -m babel.companion init myproject.babel
    python -m babel.companion render myproject.babel
    python -m babel.companion validate myproject.babel
    python -m babel.companion lint myproject.babel
"""

import argparse
import json
import sys
from pathlib import Path

from . import bsl_parser
from . import bsl_validator


def init_subcommand(path: str) -> int:
    """Scaffold a new .babel file with intent block."""
    babel_path = Path(path)
    if not babel_path.suffix == '.babel':
        babel_path = babel_path.with_suffix('.babel')
    
    if babel_path.exists():
        print(f"Error: {babel_path} already exists", file=sys.stderr)
        return 1
    
    content = """#[babel]:v0.10.3

/blocks/intent:initial-scaffold
purpose: Initialize project structure
owner: minimadmax
version: 0.10.3
"""
    
    babel_path.write_text(content, encoding='utf-8')
    print(f"Created {babel_path}")
    return 0


def render_subcommand(path: str) -> int:
    """Pretty-print handoffs in sequence."""
    babel_path = Path(path)
    
    try:
        blocks = bsl_parser.parse_file(babel_path)
    except bsl_parser.BabelParseError as e:
        print(e.to_stderr_json(), file=sys.stderr, end='')
        return 6
    except OSError as e:
        print(json.dumps({"path": str(babel_path), "code": "file_error"}), file=sys.stderr)
        return 6
    
    handoffs = [b for b in blocks if b['type'] == 'handoff']
    
    if not handoffs:
        print("No handoffs found.")
        return 0
    
    for i, handoff in enumerate(handoffs, 1):
        print(f"\n=== Handoff {i} ===")
        for key, value in handoff['kvs'].items():
            print(f"  {key}: {value}")
    
    return 0


def validate_subcommand(path: str) -> int:
    """Validate whole file (CI/human use) - subprocess wrapper for backward compatibility."""
    import subprocess
    
    babel_path = Path(path)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'babel.companion', 'lint', str(babel_path)],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, file=sys.stderr, end='')
        return result.returncode
    except Exception as e:
        print(json.dumps({"code": "internal_error"}), file=sys.stderr)
        return 6


def lint_subcommand(path: str) -> int:
    """Single-file lint with BISC-compliant JSON output.
    
    Calls bsl_validator.validate_file(path) directly (no subprocess indirection).
    Wraps the call in three except branches:
    - BabelParseError: emits path/line/code JSON to stderr, exit 6
    - OSError: emits path/file_error JSON to stderr, exit 6  
    - Exception: emits internal_error JSON to stderr, exit 6
    
    On success: prints {"valid": true} to stdout, exit 0
    """
    babel_path = Path(path)
    
    try:
        bsl_validator.validate_file(babel_path)
        print(json.dumps({"valid": True}))
        return 0
    except bsl_parser.BabelParseError as e:
        error_json = json.dumps({
            "path": str(babel_path),
            "line": e.line_no if hasattr(e, 'line_no') else 0,
            "code": e.code if hasattr(e, 'code') else "parse_error"
        })
        print(error_json, file=sys.stderr)
        return 6
    except OSError as e:
        error_json = json.dumps({
            "path": str(babel_path),
            "code": "file_error"
        })
        print(error_json, file=sys.stderr)
        return 6
    except Exception as e:
        error_json = json.dumps({"code": "internal_error"})
        print(error_json, file=sys.stderr)
        return 6


def main(argv=None):
    """Main entry point for babel.companion CLI."""
    parser = argparse.ArgumentParser(
        prog='babel.companion',
        description='Babel companion CLI for human-facing operations'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # init subcommand
    init_parser = subparsers.add_parser('init', help='Scaffold a new .babel file')
    init_parser.add_argument('path', help='Path to new .babel file')
    
    # render subcommand
    render_parser = subparsers.add_parser('render', help='Pretty-print handoffs')
    render_parser.add_argument('path', help='Path to .babel file')
    
    # validate subcommand
    validate_parser = subparsers.add_parser('validate', help='Validate whole file')
    validate_parser.add_argument('path', help='Path to .babel file')
    
    # lint subcommand
    lint_parser = subparsers.add_parser('lint', help='Single-file lint with BISC JSON output')
    lint_parser.add_argument('path', help='Path to .babel file')
    
    args = parser.parse_args(argv)
    
    if args.command == 'init':
        return init_subcommand(args.path)
    elif args.command == 'render':
        return render_subcommand(args.path)
    elif args.command == 'validate':
        return validate_subcommand(args.path)
    elif args.command == 'lint':
        return lint_subcommand(args.path)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
