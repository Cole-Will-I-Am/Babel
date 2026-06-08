"""Unit tests for Babel v0.10.3 companion CLI (stage 6b/6d).

Tests cover:
- init creates a valid .babel file with intent block parseable by bsl_parser
- render outputs formatted handoffs in sequential order to stdout
- validate exits 0 on valid .babel, exits 6 on invalid with BISC stderr JSON
"""

import unittest
import tempfile
import os
import sys
import io
import json
import subprocess
from pathlib import Path

from babel.companion import main, resolve_companion
from babel.bsl_parser import parse_file, BabelParseError


class TestCompanionInit(unittest.TestCase):
    """Test companion init subcommand."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'new.babel'
    
    def tearDown(self):
        if self.babel_path.exists():
            os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_init_creates_file(self):
        """init creates a .babel file."""
        exit_code = main(['init', str(self.babel_path)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.babel_path.exists())
    
    def test_init_creates_parseable_intent(self):
        """init creates a .babel file parseable by bsl_parser.parse_file."""
        exit_code = main(['init', str(self.babel_path)])
        self.assertEqual(exit_code, 0)
        
        # Should parse without error
        babel_file = parse_file(self.babel_path)
        self.assertEqual(babel_file.version, '0.10.3')
        self.assertEqual(len(babel_file.body), 1)
        self.assertEqual(babel_file.body[0].type, 'intent')
    
    def test_init_refuses_existing_file(self):
        """init returns non-zero if file already exists."""
        self.babel_path.write_text('existing', encoding='utf-8')
        exit_code = main(['init', str(self.babel_path)])
        self.assertNotEqual(exit_code, 0)


class TestCompanionRender(unittest.TestCase):
    """Test companion render subcommand."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'render.babel'
        
        # Create a .babel file with 2 handoffs
        content = '''#[babel]:v0.10.3
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
#[handoff]:handoff-1@0.10.3
{"path":"render.babel","content":"## agent: alice\\nFirst","agent_id":"alice","next_owner":"bob","blocking_issues":[],"required_changes":[]}
#[handoff]:handoff-2@0.10.3
{"path":"render.babel","content":"## agent: bob\\nSecond","agent_id":"bob","next_owner":null,"blocking_issues":[],"required_changes":[]}
'''
        self.babel_path.write_text(content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_render_outputs_handoffs(self):
        """render outputs handoffs in sequential order to stdout."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            exit_code = main(['render', str(self.babel_path)])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        self.assertEqual(exit_code, 0)
        # Check handoff-1 appears before handoff-2
        pos1 = output.find('handoff-1')
        pos2 = output.find('handoff-2')
        self.assertGreater(pos2, pos1)
        self.assertIn('agent: alice', output)
        self.assertIn('agent: bob', output)
    
    def test_render_nonexistent_file(self):
        """render returns non-zero for nonexistent file."""
        nonexistent = Path(self.tmpdir) / 'nonexistent.babel'
        exit_code = main(['render', str(nonexistent)])
        self.assertNotEqual(exit_code, 0)


class TestCompanionValidate(unittest.TestCase):
    """Test companion validate subcommand."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.valid_path = Path(self.tmpdir) / 'valid.babel'
        self.invalid_path = Path(self.tmpdir) / 'invalid.babel'
        
        # Valid .babel file
        valid_content = '''#[babel]:v0.10.3
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
'''
        self.valid_path.write_text(valid_content, encoding='utf-8')
        
        # Invalid .babel file (malformed header)
        invalid_content = '''#[invalid]
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
'''
        self.invalid_path.write_text(invalid_content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.valid_path)
        os.unlink(self.invalid_path)
        os.rmdir(self.tmpdir)
    
    def test_validate_valid_file_exits_zero(self):
        """validate exits 0 on valid .babel file."""
        exit_code = main(['validate', str(self.valid_path)])
        self.assertEqual(exit_code, 0)
    
    def test_validate_invalid_file_exits_six(self):
        """validate exits 6 on invalid .babel file."""
        exit_code = main(['validate', str(self.invalid_path)])
        self.assertEqual(exit_code, 6)
    
    def test_validate_invalid_emits_bisc_json(self):
        """validate emits BISC-compliant stderr JSON on invalid file."""
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            main(['validate', str(self.invalid_path)])
            stderr_output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        
        # Parse the JSON
        self.assertTrue(stderr_output.strip())
        error_json = json.loads(stderr_output.strip())
        
        # Check BISC schema
        self.assertIn('error', error_json)
        self.assertIn('code', error_json)
        self.assertIn('line', error_json)
        self.assertIn('message', error_json)
        self.assertEqual(error_json['code'], 'malformed_header')


class TestResolveCompanion(unittest.TestCase):
    """Test resolve_companion utility."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'module.babel'
        self.md_path = Path(self.tmpdir) / 'module.md'
        self.babel_path.write_text('#[babel]:v0.10.3\n', encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        if self.md_path.exists():
            os.unlink(self.md_path)
        os.rmdir(self.tmpdir)
    
    def test_resolve_returns_md_when_exists(self):
        """resolve_companion returns .md path when file exists."""
        self.md_path.write_text('# Module', encoding='utf-8')
        result = resolve_companion(self.babel_path)
        self.assertEqual(result, self.md_path)
    
    def test_resolve_returns_none_when_missing(self):
        """resolve_companion returns None when .md does not exist."""
        result = resolve_companion(self.babel_path)
        self.assertIsNone(result)
    
    def test_resolve_rejects_non_babel(self):
        """resolve_companion returns None for non-.babel path."""
        txt_path = Path(self.tmpdir) / 'module.txt'
        txt_path.write_text('text', encoding='utf-8')
        result = resolve_companion(txt_path)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
