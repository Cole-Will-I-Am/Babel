"""Unit tests for Babel v0.10.3 handoff query methods (stage 6a/6c).

Tests cover:
- Deterministic ordering across handoff-1/handoff-2/handoff-3
- Empty file handling (None from get_latest_handoff, () from list_handoffs)
- Parser error propagation (BabelParseError bubbles unchanged)
- Schema compliance (all 6 frozen keys present in every returned dict)
"""

import unittest
import tempfile
import os
from pathlib import Path

from babel.handoff import get_latest_handoff, list_handoffs
from babel.bsl_parser import parse_file, BabelParseError, write_file


class TestHandoffQueryOrdering(unittest.TestCase):
    """Test deterministic ordering of handoffs by numeric suffix."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'test.babel'
        
        # Create a .babel file with 3 handoffs
        content = '''#[babel]:v0.10.3
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
#[handoff]:handoff-1@0.10.3
{"path":"test.babel","content":"## agent: alice\\nFirst handoff","agent_id":"alice","next_owner":"bob","blocking_issues":[],"required_changes":[]}
#[handoff]:handoff-2@0.10.3
{"path":"test.babel","content":"## agent: bob\\nSecond handoff","agent_id":"bob","next_owner":"carol","blocking_issues":[],"required_changes":[]}  
#[handoff]:handoff-3@0.10.3
{"path":"test.babel","content":"## agent: carol\\nThird handoff","agent_id":"carol","next_owner":null,"blocking_issues":[],"required_changes":[]}
'''
        self.babel_path.write_text(content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_list_handoffs_returns_three(self):
        """list_handoffs returns all 3 handoffs."""
        handoffs = list_handoffs(self.babel_path)
        self.assertEqual(len(handoffs), 3)
    
    def test_list_handoffs_sorted_by_id(self):
        """list_handoffs returns handoffs sorted by numeric suffix."""
        handoffs = list_handoffs(self.babel_path)
        ids = [h['id'] for h in handoffs]
        self.assertEqual(ids, ['handoff-1', 'handoff-2', 'handoff-3'])
    
    def test_get_latest_returns_handoff_3(self):
        """get_latest_handoff returns the most recent handoff."""
        latest = get_latest_handoff(self.babel_path)
        self.assertEqual(latest['id'], 'handoff-3')
        self.assertEqual(latest['agent_id'], 'carol')


class TestHandoffQueryEmptyFile(unittest.TestCase):
    """Test handling of .babel files with no handoffs."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'empty.babel'
        
        # Create a .babel file with only intent, no handoffs
        content = '''#[babel]:v0.10.3
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
'''
        self.babel_path.write_text(content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_get_latest_returns_none(self):
        """get_latest_handoff returns None when no handoffs exist."""
        result = get_latest_handoff(self.babel_path)
        self.assertIsNone(result)
    
    def test_list_handoffs_returns_empty_tuple(self):
        """list_handoffs returns empty tuple when no handoffs exist."""
        result = list_handoffs(self.babel_path)
        self.assertEqual(result, ())
        self.assertIsInstance(result, tuple)


class TestHandoffQueryErrorPropagation(unittest.TestCase):
    """Test that parser errors propagate unchanged."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'invalid.babel'
        
        # Create an invalid .babel file (malformed header)
        content = '''#[invalid-header]
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
'''
        self.babel_path.write_text(content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_get_latest_propagates_parse_error(self):
        """get_latest_handoff propagates BabelParseError."""
        with self.assertRaises(BabelParseError) as ctx:
            get_latest_handoff(self.babel_path)
        self.assertEqual(ctx.exception.code, 'malformed_header')
    
    def test_list_handoffs_propagates_parse_error(self):
        """list_handoffs propagates BabelParseError."""
        with self.assertRaises(BabelParseError) as ctx:
            list_handoffs(self.babel_path)
        self.assertEqual(ctx.exception.code, 'malformed_header')


class TestHandoffQuerySchemaCompliance(unittest.TestCase):
    """Test that returned dicts have all 6 frozen schema keys."""
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.babel_path = Path(self.tmpdir) / 'schema.babel'
        
        # Create a .babel file with one handoff
        content = '''#[babel]:v0.10.3
#[intent]:init@0.10.3
{"id":"init","version":"0.10.3","agent_id":"test"}
#[handoff]:handoff-1@0.10.3
{"path":"schema.babel","content":"## agent: tester\\nTest","agent_id":"tester","next_owner":"reviewer","blocking_issues":["issue1"],"required_changes":["fix1"]}
'''
        self.babel_path.write_text(content, encoding='utf-8')
    
    def tearDown(self):
        os.unlink(self.babel_path)
        os.rmdir(self.tmpdir)
    
    def test_get_latest_has_all_six_keys(self):
        """get_latest_handoff returns dict with all 6 frozen keys."""
        result = get_latest_handoff(self.babel_path)
        self.assertIsNotNone(result)
        expected_keys = {'id', 'agent_id', 'content', 'blocking_issues', 'required_changes', 'next_owner'}
        self.assertEqual(set(result.keys()), expected_keys)
    
    def test_list_handoffs_all_have_six_keys(self):
        """list_handoffs returns dicts all with 6 frozen keys."""
        results = list_handoffs(self.babel_path)
        self.assertEqual(len(results), 1)
        expected_keys = {'id', 'agent_id', 'content', 'blocking_issues', 'required_changes', 'next_owner'}
        for handoff in results:
            self.assertEqual(set(handoff.keys()), expected_keys)
    
    def test_next_owner_is_present(self):
        """next_owner key is present and has correct value."""
        result = get_latest_handoff(self.babel_path)
        self.assertIn('next_owner', result)
        self.assertEqual(result['next_owner'], 'reviewer')
    
    def test_blocking_issues_is_list(self):
        """blocking_issues is a list."""
        result = get_latest_handoff(self.babel_path)
        self.assertIsInstance(result['blocking_issues'], list)
        self.assertEqual(result['blocking_issues'], ['issue1'])
    
    def test_required_changes_is_list(self):
        """required_changes is a list."""
        result = get_latest_handoff(self.babel_path)
        self.assertIsInstance(result['required_changes'], list)
        self.assertEqual(result['required_changes'], ['fix1'])


if __name__ == '__main__':
    unittest.main()
