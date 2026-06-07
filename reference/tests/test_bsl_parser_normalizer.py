"""
Unit tests for Babel v0.10.2 parser normalizer (stage 4b.2).

Tests cover:
- Body sort determinism by (TYPE_ENUM_RANK[type], id)
- Global duplicate (type, id) detection across body+handoffs
- Version consistency across all blocks
- missing_intent error (zero intents)
- multiple_intents error (>1 intents with distinct ids)
- duplicate_id precedence over multiple_intents (same-id intents)
- invalid_intent_json (missing agent_id, non-string agent_id)
- Accurate 1-based line numbers from scanner metadata
"""

import tempfile
import unittest
from pathlib import Path

from reference.babel.bsl_parser import (
    BabelParseError,
    BabelFile,
    parse_file,
    TYPE_ENUM_RANK,
)


class TestBodySortDeterminism(unittest.TestCase):
    """Test that body blocks are sorted by (TYPE_ENUM_RANK[type], id)."""
    
    def test_sort_by_type_rank(self):
        """Blocks sorted by type rank: intent < spec < test < impl."""
        content = """#[babel]:test@0.10.2
#[impl]:main@0.10.2
{}
#[spec]:main@0.10.2
{}
#[intent]:main@0.10.2
{"agent_id": "test"}
#[test]:main@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = parse_file(path)
            # Should be sorted: intent, spec, test, impl
            self.assertEqual(len(result.body), 4)
            self.assertEqual(result.body[0].type, 'intent')
            self.assertEqual(result.body[1].type, 'spec')
            self.assertEqual(result.body[2].type, 'test')
            self.assertEqual(result.body[3].type, 'impl')
        finally:
            path.unlink()
    
    def test_sort_by_id_within_type(self):
        """Blocks of same type sorted by id alphabetically."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[spec]:zebra@0.10.2
{}
#[spec]:alpha@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = parse_file(path)
            # spec blocks should be: alpha, zebra
            spec_blocks = [b for b in result.body if b.type == 'spec']
            self.assertEqual(len(spec_blocks), 2)
            self.assertEqual(spec_blocks[0].id, 'alpha')
            self.assertEqual(spec_blocks[1].id, 'zebra')
        finally:
            path.unlink()
    
    def test_handoffs_excluded_from_sort(self):
        """Handoff blocks remain chronological, not sorted with body."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[handoff]:step2@0.10.2
{}
#[handoff]:step1@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = parse_file(path)
            # Handoffs remain in original order
            self.assertEqual(len(result.handoffs), 2)
            self.assertEqual(result.handoffs[0].id, 'step2')
            self.assertEqual(result.handoffs[1].id, 'step1')
        finally:
            path.unlink()


class TestDuplicateIdDetection(unittest.TestCase):
    """Test global duplicate (type, id) detection across body+handoffs."""
    
    def test_duplicate_in_body(self):
        """Duplicate (type, id) in body raises duplicate_id."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[intent]:main@0.10.2
{"agent_id": "other"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'duplicate_id')
            # Line 4 is the second intent header
            self.assertEqual(ctx.exception.line, 4)
        finally:
            path.unlink()
    
    def test_duplicate_across_body_handoff(self):
        """Duplicate (type, id) across body and handoff raises duplicate_id."""
        content = """#[babel]:test@0.10.2
#[spec]:main@0.10.2
{}
#[handoff]:main@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'duplicate_id')
        finally:
            path.unlink()
    
    def test_duplicate_id_before_multiple_intents(self):
        """Same-id intent pairs reported as duplicate_id, not multiple_intents."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[intent]:main@0.10.2
{"agent_id": "other"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            # duplicate_id takes precedence over multiple_intents
            self.assertEqual(ctx.exception.code, 'duplicate_id')
        finally:
            path.unlink()


class TestVersionConsistency(unittest.TestCase):
    """Test version consistency across all blocks."""
    
    def test_version_mismatch(self):
        """Different @version strings raise version_mismatch."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[spec]:main@0.10.3
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'version_mismatch')
            # Line 4 is the mismatched spec header
            self.assertEqual(ctx.exception.line, 4)
        finally:
            path.unlink()
    
    def test_version_mismatch_handoff(self):
        """Version mismatch in handoff also raises version_mismatch."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[handoff]:step1@0.10.3
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'version_mismatch')
        finally:
            path.unlink()


class TestMissingIntent(unittest.TestCase):
    """Test missing_intent error detection."""
    
    def test_missing_intent_empty_body(self):
        """Empty body raises missing_intent at line 1."""
        content = """#[babel]:test@0.10.2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'missing_intent')
            self.assertEqual(ctx.exception.line, 1)
        finally:
            path.unlink()
    
    def test_missing_intent_nonempty_body(self):
        """Body without intent raises missing_intent at first body block."""
        content = """#[babel]:test@0.10.2
#[spec]:main@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'missing_intent')
            # Line 2 is the spec header (first body block)
            self.assertEqual(ctx.exception.line, 2)
        finally:
            path.unlink()


class TestMultipleIntents(unittest.TestCase):
    """Test multiple_intents error detection."""
    
    def test_multiple_intents_distinct_ids(self):
        """Two intent blocks with distinct ids raise multiple_intents."""
        content = """#[babel]:test@0.10.2
#[intent]:primary@0.10.2
{"agent_id": "test"}
#[intent]:secondary@0.10.2
{"agent_id": "other"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'multiple_intents')
            # Line 4 is the second intent header
            self.assertEqual(ctx.exception.line, 4)
        finally:
            path.unlink()
    
    def test_multiple_intents_three_blocks(self):
        """Three intent blocks raise multiple_intents at second."""
        content = """#[babel]:test@0.10.2
#[intent]:first@0.10.2
{"agent_id": "a"}
#[intent]:second@0.10.2
{"agent_id": "b"}
#[intent]:third@0.10.2
{"agent_id": "c"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'multiple_intents')
            # Line 4 is the second intent header
            self.assertEqual(ctx.exception.line, 4)
        finally:
            path.unlink()


class TestInvalidIntentSchema(unittest.TestCase):
    """Test invalid_intent_json for schema violations."""
    
    def test_missing_agent_id(self):
        """Intent without agent_id raises invalid_intent_json."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"other_field": "value"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'invalid_intent_json')
            self.assertEqual(ctx.exception.line, 2)
            self.assertIn('agent_id', ctx.exception.message)
        finally:
            path.unlink()
    
    def test_non_string_agent_id(self):
        """Intent with non-string agent_id raises invalid_intent_json."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": 123}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'invalid_intent_json')
            self.assertEqual(ctx.exception.line, 2)
            self.assertIn('string', ctx.exception.message)
        finally:
            path.unlink()
    
    def test_intent_not_object(self):
        """Intent content that's not a JSON object raises invalid_intent_json."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
"not an object"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'invalid_intent_json')
            self.assertEqual(ctx.exception.line, 2)
        finally:
            path.unlink()


class TestLineNumberAccuracy(unittest.TestCase):
    """Test that error line numbers are accurate 1-based indices."""
    
    def test_malformed_header_line(self):
        """Malformed header reports correct line number."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[invalid header here
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'malformed_header')
            # Line 4 is the malformed header
            self.assertEqual(ctx.exception.line, 4)
        finally:
            path.unlink()
    
    def test_version_mismatch_line(self):
        """Version mismatch reports line of first mismatched block."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[spec]:main@0.10.2
{}
#[test]:main@0.10.3
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(BabelParseError) as ctx:
                parse_file(path)
            self.assertEqual(ctx.exception.code, 'version_mismatch')
            # Line 6 is the first mismatched block
            self.assertEqual(ctx.exception.line, 6)
        finally:
            path.unlink()


class TestValidFileParsing(unittest.TestCase):
    """Test that valid files parse successfully."""
    
    def test_minimal_valid_file(self):
        """Minimal valid file with just intent parses."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test-agent"}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = parse_file(path)
            self.assertEqual(result.version, '0.10.2')
            self.assertEqual(len(result.body), 1)
            self.assertEqual(result.body[0].type, 'intent')
            self.assertEqual(result.body[0].id, 'main')
            self.assertEqual(result.body[0].content['agent_id'], 'test-agent')
        finally:
            path.unlink()
    
    def test_full_valid_file(self):
        """Full file with all block types parses and sorts correctly."""
        content = """#[babel]:test@0.10.2
#[intent]:main@0.10.2
{"agent_id": "test"}
#[impl]:main@0.10.2
{}
#[spec]:main@0.10.2
{}
#[test]:main@0.10.2
{}
#[handoff]:step1@0.10.2
{}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.babel', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)
        
        try:
            result = parse_file(path)
            self.assertEqual(result.version, '0.10.2')
            self.assertEqual(len(result.body), 4)
            # Check sort order
            self.assertEqual(result.body[0].type, 'intent')
            self.assertEqual(result.body[1].type, 'spec')
            self.assertEqual(result.body[2].type, 'test')
            self.assertEqual(result.body[3].type, 'impl')
            self.assertEqual(len(result.handoffs), 1)
        finally:
            path.unlink()


if __name__ == '__main__':
    unittest.main()
