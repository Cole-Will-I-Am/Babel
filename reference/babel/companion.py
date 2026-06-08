"""Babel v0.10.3 companion CLI.

Human-facing command-line interface for Babel files.
Zero-dependency: uses only Python stdlib (argparse, subprocess, json, pathlib).

Subcommands:
- init <path.babel>: Scaffold a new .babel file with intent block.
- render <path.babel>: Pretty-print handoffs in sequence.
- validate <path.babel>: Run BSL validator via subprocess.
- lint <path.babel>: Run BSL validator directly with BISC error handling.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import bsl_validator
from .bsl_parser import BabelParseError, resolve_companion


def init_command(path: str) -> int:
    """Scaffold a new .babel file with an intent block."""
    target = Path(path)
    if target.exists():
        print(f"Error: {target} already exists", file=sys.stderr)
        return 1
    
    content = """#[babel]:0.10.3

/blocks/intent:intent-001
purpose: Bootstrap new Babel file
owner: agent-init
version: 0.10.3
"""
    target.write_text(content, encoding="utf-8")
    print(f"Initialized {target}")
    return 0


def render_command(path: str) -> int:
    """Pretty-print handoff blocks from a .babel file."""
    target = Path(path)
    if not target.exists():
        print(f"Error: {target} not found", file=sys.stderr)
        return 1
    
    # Simple render: just output the file contents
    print(target.read_text(encoding="utf-8"))
    return 0


def validate_command(path: str) -> int:
    """Run BSL validator via subprocess (legacy behavior)."""
    target = Path(path)
    if not target.exists():
        print(f"Error: {target} not found", file=sys.stderr)
        return 1
    
    result = subprocess.run(
        [sys.executable, "-m", "babel", "validate", str(target)],
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def lint_command(path: str) -> int:
    """Run BSL validator directly with full BISC error handling.
    
    On success: prints {'valid': true} to stdout, exit 0.
    On BabelParseError: prints {'path': str, 'line': int, 'code': str} to stderr, exit 6.
    On OSError: prints {'path': str, 'code': 'file_error'} to stderr, exit 6.
    On Exception: prints {'code': 'internal_error'} to stderr, exit 6.
    """
    target = Path(path)
    
    try:
        bsl_validator.validate_file(target)
        print(json.dumps({"valid": True}))
        return 0
    except BabelParseError as e:
        error_obj = {
            "path": str(target),
            "line": e.line_no if hasattr(e, 'line_no') else 0,
            "code": e.code if hasattr(e, 'code') else 'parse_error'
        }
        print(json.dumps(error_obj), file=sys.stderr)
        return 6
    except OSError as e:
        error_obj = {
            "path": str(target),
            "code": "file_error"
        }
        print(json.dumps(error_obj), file=sys.stderr)
        return 6
    except Exception as e:
        error_obj = {
            "code": "internal_error"
        }
        print(json.dumps(error_obj), file=sys.stderr)
        return 6


def main() -> int:
    parser = argparse.ArgumentParser(prog="babel-companion", description="Babel companion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # init subcommand
    init_parser = subparsers.add_parser("init", help="Scaffold a new .babel file")
    init_parser.add_argument("path", help="Path to new .babel file")
    
    # render subcommand
    render_parser = subparsers.add_parser("render", help="Pretty-print handoffs")
    render_parser.add_argument("path", help="Path to .babel file")
    
    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Run BSL validator via subprocess")
    validate_parser.add_argument("path", help="Path to .babel file")
    
    # lint subcommand (stage 11b)
    lint_parser = subparsers.add_parser("lint", help="Run BSL validator directly with BISC error handling")
    lint_parser.add_argument("path", help="Path to .babel file")
    
    args = parser.parse_args()
    
    if args.command == "init":
        return init_command(args.path)
    elif args.command == "render":
        return render_command(args.path)
    elif args.command == "validate":
        return validate_command(args.path)
    elif args.command == "lint":
        return lint_command(args.path)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
