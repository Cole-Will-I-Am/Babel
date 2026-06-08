"""Babel v0.10.2 CLI Wrapper (BISC)

Implements the BISC CLI contract from babel-bisc-integrity-v0.10.2.md:
- Catches BabelParseError and re-emits stderr JSON as-is
- Catches OSError and translates to file_error
- Catches Exception and translates to internal_error
- Exits 6 on error, 0 silent on success
"""

import sys
from pathlib import Path

from orchestrator.canonical import canonical_json

from reference.babel.bsl_parser import BabelParseError, parse_file


def emit_stderr_json(error: str, code: str, line: object, message: str) -> None:
    """Emit BISC-compliant stderr JSON (no trailing newline)."""
    obj = {
        'error': error,
        'code': code,
        'line': line,
        'message': message,
    }
    sys.stderr.write(canonical_json(obj).rstrip('\n'))
    sys.stderr.write('\n')


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) != 2:
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message='Usage: python -m reference.babel <path.babel>',
        )
        return 6
    
    input_path = Path(sys.argv[1])
    
    try:
        # Parse the file
        parse_file(input_path)
        return 0
    
    except BabelParseError as e:
        # Re-emit library error as-is (section 4.2)
        # to_stderr_json() already returns JSON without trailing newline
        sys.stderr.write(e.to_stderr_json())
        sys.stderr.write('\n')
        return 6
    
    except OSError as e:
        # Translate to file_error (section 4.3)
        emit_stderr_json(
            error='OSError',
            code='file_error',
            line=None,
            message=f'{input_path}: {e}',
        )
        return 6
    
    except Exception as e:
        # Translate to internal_error (section 4.3)
        exc_class = type(e).__name__
        emit_stderr_json(
            error='InternalError',
            code='internal_error',
            line=None,
            message=f'{exc_class}: {e}',
        )
        return 6


if __name__ == '__main__':
    sys.exit(main())
