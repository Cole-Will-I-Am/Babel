"""Unit tests for Babel v0.10.3 grammar manifest conformance (stage 11e).

Behavioral assertions only - no internal REQUIRED_KEYS dict access.
Reads bsl_validator.py source, extracts manifest via regex, compiles
documented header regex, and asserts validate_header/validate_body_kv
match the documented grammar specification.

Tests cover:
- Grammar manifest extraction from bsl_validator.py source
- Header regex compilation and behavioral validation
- Required key enforcement for each block type (complete/incomplete kv_pairs)
- Extra key rejection policy
"""

import re
import unittest
from pathlib import Path

from babel.bsl_validator import validate_header, validate_body_kv, HEADER_REGEX, BLOCK_TYPES
from babel.bsl_parser import BabelParseError, BABEL_VERSION


class TestGrammarManifestExtraction(unittest.TestCase):
    """Test grammar manifest extraction from bsl_validator.py source."""
    
    def test_manifest_extraction(self):
        """Extract grammar manifest comment block via regex."""
        validator_path = Path(__file__).parent.parent / 'babel' / 'bsl_validator.py'
        source = validator_path.read_text(encoding='utf-8')
        
        # Extract manifest via regex from spec
        manifest_pattern = re.compile(r'^# Grammar Manifest\n(?:# .*\n)*', re.MULTILINE)
        match = manifest_pattern.match(source)
        
        self.assertIsNotNone(match, "Grammar manifest comment block not found")
        manifest = match.group(0)
        
        # Verify manifest contains required sections
        self.assertIn('Header Regex', manifest)
        self.assertIn('Allowed block types', manifest)
        self.assertIn('Required Keys', manifest)
        self.assertIn('handoff', manifest)
        self.assertIn('intent', manifest)
        self.assertIn('meta', manifest)


class TestHeaderRegexBehavior(unittest.TestCase):
    """Test header regex behavioral conformance."""
    
    def test_valid_handoff_header(self):
        """Valid handoff header should return block_type."""
        block_type = validate_header('/blocks/handoff:my-handoff', line_no=1)
        self.assertEqual(block_type, 'handoff')
    
    def test_valid_intent_header(self):
        """Valid intent header should return block_type."""
        block_type = validate_header('/blocks/intent:initial-scaffold', line_no=1)
        self.assertEqual(block_type, 'intent')
    
    def test_valid_meta_header(self):
        """Valid meta header should return block_type."""
        block_type = validate_header('/blocks/meta:project-info', line_no=1)
        self.assertEqual(block_type, 'meta')
    
    def test_invalid_header_raises(self):
        """Invalid header should raise BabelParseError."""
        with self.assertRaises(BabelParseError) as ctx:
            validate_header('/blocks/invalid:my-block', line_no=1)
        self.assertEqual(ctx.exception.code, 'malformed_header')
    
    def test_header_with_numbers(self):
        """Header with alphanumeric ID should work."""
        block_type = validate_header('/blocks/handoff:handoff-123', line_no=1)
        self.assertEqual(block_type, 'handoff')
    
    def test_header_regex_matches_documented_pattern(self):
        """HEADER_REGEX should match documented pattern ^/blocks/(handoff|intent|meta):[a-z0-9-]+$"""
        documented_pattern = re.compile(r'^/blocks/(handoff|intent|meta):[a-z0-9-]+$')
        
        # Test cases that should match both
        valid_headers = [
            '/blocks/handoff:my-handoff',
            '/blocks/intent:initial',
            '/blocks/meta:info',
            '/blocks/handoff:test-123',
        ]
        
        for header in valid_headers:
            self.assertTrue(HEADER_REGEX.match(header), f"HEADER_REGEX should match {header}")
            self.assertTrue(documented_pattern.match(header), f"Documented pattern should match {header}")
        
        # Test cases that should match neither
        invalid_headers = [
            '/blocks/invalid:my-block',
            '/blocks/handoff:My-Block',  # uppercase
            '/handoff:my-block',  # missing /blocks/
            'blocks/handoff:my-block',  # missing leading /
        ]
        
        for header in invalid_headers:
            self.assertFalse(HEADER_REGEX.match(header), f"HEADER_REGEX should not match {header}")
            self.assertFalse(documented_pattern.match(header), f"Documented pattern should not match {header}")


class TestRequiredKeysEnforcement(unittest.TestCase):
    """Test required key enforcement for each block type."""
    
    def test_handoff_complete_keys(self):
        """Handoff with all 10 required keys should pass."""
        kv_pairs = [
            ('path', 'src/main.py'),
            ('content', 'print("hello")'),
            ('agent_id', 'minimadmax'),
            ('next_owner', 'kimi'),
            ('signoff', 'true'),
            ('blocking_issues', '[]'),
            ('required_changes', '[]'),
            ('summary', 'Initial implementation'),
            ('memory_note', 'First handoff'),
            ('version', BABEL_VERSION),
        ]
        result = validate_body_kv('handoff', kv_pairs, line_no=1)
        self.assertEqual(len(result), 10)
    
    def test_intent_complete_keys(self):
        """Intent with all 3 required keys should pass."""
        kv_pairs = [
            ('purpose', 'Initialize project'),
            ('owner', 'minimadmax'),
            ('version', BABEL_VERSION),
        ]
        result = validate_body_kv('intent', kv_pairs, line_no=1)
        self.assertEqual(len(result), 3)
    
    def test_meta_complete_keys(self):
        """Meta with all 2 required keys should pass."""
        kv_pairs = [
            ('title', 'My Project'),
            ('version', BABEL_VERSION),
        ]
        result = validate_body_kv('meta', kv_pairs, line_no=1)
        self.assertEqual(len(result), 2)
    
    def test_handoff_missing_key(self):
        """Handoff missing one required key should raise BabelParseError."""
        kv_pairs = [
            ('path', 'src/main.py'),
            ('content', 'print("hello")'),
            ('agent_id', 'minimadmax'),
            ('next_owner', 'kimi'),
            ('signoff', 'true'),
            ('blocking_issues', '[]'),
            ('required_changes', '[]'),
            ('summary', 'Initial implementation'),
            # Missing: memory_note, version
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('handoff', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_intent_missing_key(self):
        """Intent missing one required key should raise BabelParseError."""
        kv_pairs = [
            ('purpose', 'Initialize project'),
            ('owner', 'minimadmax'),
            # Missing: version
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('intent', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_meta_missing_key(self):
        """Meta missing one required key should raise BabelParseError."""
        kv_pairs = [
            ('title', 'My Project'),
            # Missing: version
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('meta', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')


class TestExtraKeysPolicy(unittest.TestCase):
    """Test extra-keys REJECT policy."""
    
    def test_handoff_extra_key_rejected(self):
        """Handoff with extra key should raise BabelParseError."""
        kv_pairs = [
            ('path', 'src/main.py'),
            ('content', 'print("hello")'),
            ('agent_id', 'minimadmax'),
            ('next_owner', 'kimi'),
            ('signoff', 'true'),
            ('blocking_issues', '[]'),
            ('required_changes', '[]'),
            ('summary', 'Initial implementation'),
            ('memory_note', 'First handoff'),
            ('version', BABEL_VERSION),
            ('extra_key', 'should fail'),  # Extra key
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('handoff', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'extra_key')
    
    def test_intent_extra_key_rejected(self):
        """Intent with extra key should raise BabelParseError."""
        kv_pairs = [
            ('purpose', 'Initialize project'),
            ('owner', 'minimadmax'),
            ('version', BABEL_VERSION),
            ('extra_key', 'should fail'),  # Extra key
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('intent', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'extra_key')


class TestDuplicateKeyPolicy(unittest.TestCase):
    """Test duplicate key rejection."""
    
    def test_duplicate_key_rejected(self):
        """Duplicate key should raise BabelParseError."""
        kv_pairs = [
            ('path', 'src/main.py'),
            ('path', 'src/other.py'),  # Duplicate
            ('content', 'print("hello")'),
            ('agent_id', 'minimadmax'),
            ('next_owner', 'kimi'),
            ('signoff', 'true'),
            ('blocking_issues', '[]'),
            ('required_changes', '[]'),
            ('summary', 'Initial implementation'),
            ('memory_note', 'First handoff'),
            ('version', BABEL_VERSION),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv('handoff', kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'duplicate_key')


if __name__ == '__main__':
    unittest.main()
