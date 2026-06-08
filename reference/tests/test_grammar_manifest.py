"""Unit tests for Babel v0.10.3 grammar manifest conformance (stage 11e).

Behavioral assertions only - no internal REQUIRED_KEYS dict access.
Reads bsl_validator.py source, extracts manifest via regex, compiles
documented header regex, and asserts validate_header/validate_body_kv
match the documented grammar.
"""

import re
import unittest
from pathlib import Path

# Import validator functions for behavioral testing
from babel.bsl_validator import (
    validate_header,
    validate_body_kv,
    BabelParseError
)


class TestGrammarManifestExtraction(unittest.TestCase):
    """Test that the grammar manifest can be extracted from bsl_validator.py source."""
    
    def test_manifest_extraction(self):
        """Extract grammar manifest comment block via regex."""
        validator_path = Path(__file__).parent.parent / "babel" / "bsl_validator.py"
        source = validator_path.read_text(encoding="utf-8")
        
        # Extract manifest via regex per spec
        manifest_pattern = re.compile(r'^# Grammar Manifest\n(?:# .*\n)*', re.MULTILINE)
        match = manifest_pattern.search(source)
        
        self.assertIsNotNone(match, "Grammar manifest comment block not found")
        manifest = match.group(0)
        
        # Verify manifest contains expected sections
        self.assertIn("Header Regex", manifest)
        self.assertIn("Required Body Keys Per Block Type", manifest)
        self.assertIn("handoff:", manifest)
        self.assertIn("intent:", manifest)
        self.assertIn("meta:", manifest)


class TestHeaderRegexBehavior(unittest.TestCase):
    """Test that validate_header matches the documented header regex."""
    
    def test_valid_handoff_header(self):
        """Valid handoff header should parse successfully."""
        block_type, block_id = validate_header("/blocks/handoff:handoff-001", line_no=1)
        self.assertEqual(block_type, "handoff")
        self.assertEqual(block_id, "handoff-001")
    
    def test_valid_intent_header(self):
        """Valid intent header should parse successfully."""
        block_type, block_id = validate_header("/blocks/intent:intent-abc", line_no=1)
        self.assertEqual(block_type, "intent")
        self.assertEqual(block_id, "intent-abc")
    
    def test_valid_meta_header(self):
        """Valid meta header should parse successfully."""
        block_type, block_id = validate_header("/blocks/meta:meta-123", line_no=1)
        self.assertEqual(block_type, "meta")
        self.assertEqual(block_id, "meta-123")
    
    def test_invalid_header_type(self):
        """Invalid block type should raise BabelParseError."""
        with self.assertRaises(BabelParseError) as ctx:
            validate_header("/blocks/invalid:test-001", line_no=1)
        self.assertEqual(ctx.exception.code, 'malformed_header')
    
    def test_invalid_header_format(self):
        """Invalid header format should raise BabelParseError."""
        with self.assertRaises(BabelParseError) as ctx:
            validate_header("/blocks/handoff/invalid", line_no=1)
        self.assertEqual(ctx.exception.code, 'malformed_header')
    
    def test_invalid_header_id_uppercase(self):
        """Uppercase block ID should raise BabelParseError (regex requires lowercase)."""
        with self.assertRaises(BabelParseError) as ctx:
            validate_header("/blocks/handoff:HANDOFF-001", line_no=1)
        self.assertEqual(ctx.exception.code, 'malformed_header')


class TestRequiredKeysBehavior(unittest.TestCase):
    """Test that validate_body_kv enforces documented required key sets."""
    
    def test_handoff_all_required_keys(self):
        """Handoff block with all 10 required keys should pass."""
        kv_pairs = [
            ("path", "test.py"),
            ("content", "print('hello')"),
            ("agent_id", "agent-001"),
            ("next_owner", "agent-002"),
            ("signoff", "true"),
            ("blocking_issues", "[]"),
            ("required_changes", "[]"),
            ("summary", "Test handoff"),
            ("memory_note", "Test note"),
            ("version", "0.10.3"),
        ]
        # Should not raise
        validate_body_kv("handoff", kv_pairs, line_no=1)
    
    def test_handoff_missing_version(self):
        """Handoff block missing version should raise BabelParseError."""
        kv_pairs = [
            ("path", "test.py"),
            ("content", "print('hello')"),
            ("agent_id", "agent-001"),
            ("next_owner", "agent-002"),
            ("signoff", "true"),
            ("blocking_issues", "[]"),
            ("required_changes", "[]"),
            ("summary", "Test handoff"),
            ("memory_note", "Test note"),
            # version missing
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("handoff", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_handoff_missing_path(self):
        """Handoff block missing path should raise BabelParseError."""
        kv_pairs = [
            # path missing
            ("content", "print('hello')"),
            ("agent_id", "agent-001"),
            ("next_owner", "agent-002"),
            ("signoff", "true"),
            ("blocking_issues", "[]"),
            ("required_changes", "[]"),
            ("summary", "Test handoff"),
            ("memory_note", "Test note"),
            ("version", "0.10.3"),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("handoff", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_intent_all_required_keys(self):
        """Intent block with all 3 required keys should pass."""
        kv_pairs = [
            ("purpose", "Test intent"),
            ("owner", "agent-001"),
            ("version", "0.10.3"),
        ]
        # Should not raise
        validate_body_kv("intent", kv_pairs, line_no=1)
    
    def test_intent_missing_owner(self):
        """Intent block missing owner should raise BabelParseError."""
        kv_pairs = [
            ("purpose", "Test intent"),
            # owner missing
            ("version", "0.10.3"),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("intent", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_meta_all_required_keys(self):
        """Meta block with all 2 required keys should pass."""
        kv_pairs = [
            ("title", "Test meta"),
            ("version", "0.10.3"),
        ]
        # Should not raise
        validate_body_kv("meta", kv_pairs, line_no=1)
    
    def test_meta_missing_title(self):
        """Meta block missing title should raise BabelParseError."""
        kv_pairs = [
            # title missing
            ("version", "0.10.3"),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("meta", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'missing_key')
    
    def test_handoff_extra_key_rejected(self):
        """Handoff block with extra key should raise BabelParseError (REJECT policy)."""
        kv_pairs = [
            ("path", "test.py"),
            ("content", "print('hello')"),
            ("agent_id", "agent-001"),
            ("next_owner", "agent-002"),
            ("signoff", "true"),
            ("blocking_issues", "[]"),
            ("required_changes", "[]"),
            ("summary", "Test handoff"),
            ("memory_note", "Test note"),
            ("version", "0.10.3"),
            ("extra_key", "should_be_rejected"),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("handoff", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'extra_key')
    
    def test_handoff_duplicate_key_rejected(self):
        """Handoff block with duplicate key should raise BabelParseError."""
        kv_pairs = [
            ("path", "test.py"),
            ("content", "print('hello')"),
            ("agent_id", "agent-001"),
            ("next_owner", "agent-002"),
            ("signoff", "true"),
            ("blocking_issues", "[]"),
            ("required_changes", "[]"),
            ("summary", "Test handoff"),
            ("memory_note", "Test note"),
            ("version", "0.10.3"),
            ("path", "duplicate.py"),
        ]
        with self.assertRaises(BabelParseError) as ctx:
            validate_body_kv("handoff", kv_pairs, line_no=1)
        self.assertEqual(ctx.exception.code, 'duplicate_key')


if __name__ == "__main__":
    unittest.main()
