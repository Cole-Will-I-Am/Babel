"""Unit tests for Babel v0.10.2 handoff append protocol (stage 5a/5b).

Tests cover:
- Sequential handoff-{n} ID determinism starting at handoff-1
- Idempotency skip returning (False, existing_id) on duplicate content
- Atomic integrity on write failure (no partial handoff, no tempfile residue)
- Error propagation of BabelParseError on invalid .babel files

Uses Python 3.12 stdlib only (unittest, pathlib, tempfile, os, hashlib).
"""

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from reference.babel.handoff import append_handoff
from reference.babel.bsl_parser import parse_file, BabelParseError


def _create_valid_babel_file(tmp_path: Path, version: str = '0.10.2') -> Path:
    """Create a minimal valid .babel file for testing.
    
    Args:
        tmp_path: Temporary directory path.
        version: Babel version string for file header.
    
    Returns:
        Path to created .babel file.
    """
    babel_path = tmp_path / 'test.babel'
    content = f'''#[babel]:v{version}
#[intent]:main@{version}
{{"agent_id": "test-agent"}}
#[spec]:main@{version}
{{"description": "test spec"}}
'''
    babel_path.write_text(content, encoding='utf-8')
    return babel_path


def _compute_sha256(content: str) -> str:
    """Compute SHA256 hex digest of content string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class TestHandoffSequentialId(unittest.TestCase):
    """Test sequential handoff-{n} ID generation starting at handoff-1."""
    
    def test_first_handoff_starts_at_handoff_1(self):
        """First handoff appended to file with no handoffs gets handoff-1."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            appended, handoff_id = append_handoff(
                babel_path,
                'Test handoff content',
                'agent-alpha',
            )
            
            self.assertTrue(appended)
            self.assertEqual(handoff_id, 'handoff-1')
            
            # Verify file was updated
            babel_file = parse_file(babel_path)
            self.assertEqual(len(babel_file.handoffs), 1)
            self.assertEqual(babel_file.handoffs[0].id, 'handoff-1')
    
    def test_second_handoff_gets_handoff_2(self):
        """Second handoff appended gets handoff-2."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            # First handoff
            append_handoff(babel_path, 'First content', 'agent-alpha')
            
            # Second handoff
            appended, handoff_id = append_handoff(
                babel_path,
                'Second content',
                'agent-beta',
            )
            
            self.assertTrue(appended)
            self.assertEqual(handoff_id, 'handoff-2')
            
            # Verify both handoffs present
            babel_file = parse_file(babel_path)
            self.assertEqual(len(babel_file.handoffs), 2)
            self.assertEqual(babel_file.handoffs[0].id, 'handoff-1')
            self.assertEqual(babel_file.handoffs[1].id, 'handoff-2')
    
    def test_handoff_ids_increment_deterministically(self):
        """Multiple handoffs increment IDs deterministically."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            expected_ids = []
            for i in range(1, 6):
                appended, handoff_id = append_handoff(
                    babel_path,
                    f'Handoff {i} content',
                    f'agent-{i}',
                )
                self.assertTrue(appended)
                expected_id = f'handoff-{i}'
                self.assertEqual(handoff_id, expected_id)
                expected_ids.append(expected_id)
            
            # Verify all handoffs present in order
            babel_file = parse_file(babel_path)
            self.assertEqual(len(babel_file.handoffs), 5)
            actual_ids = [b.id for b in babel_file.handoffs]
            self.assertEqual(actual_ids, expected_ids)


class TestHandoffIdempotency(unittest.TestCase):
    """Test raw-content SHA256 idempotency guard."""
    
    def test_duplicate_content_skipped(self):
        """Identical content from same agent is skipped (idempotency)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            content = 'Duplicate test content'
            agent_id = 'agent-alpha'
            
            # First append
            appended1, id1 = append_handoff(babel_path, content, agent_id)
            self.assertTrue(appended1)
            self.assertEqual(id1, 'handoff-1')
            
            # Second append with same content and agent
            appended2, id2 = append_handoff(babel_path, content, agent_id)
            self.assertFalse(appended2)
            self.assertEqual(id2, 'handoff-1')  # Returns existing ID
            
            # Verify only one handoff in file
            babel_file = parse_file(babel_path)
            self.assertEqual(len(babel_file.handoffs), 1)
    
    def test_different_agent_produces_different_hash(self):
        """Same content from different agent produces different hash (not skipped)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            content = 'Same content'
            
            # First agent
            appended1, id1 = append_handoff(babel_path, content, 'agent-alpha')
            self.assertTrue(appended1)
            self.assertEqual(id1, 'handoff-1')
            
            # Second agent with same content
            appended2, id2 = append_handoff(babel_path, content, 'agent-beta')
            self.assertTrue(appended2)  # Different agent = different hash = appended
            self.assertEqual(id2, 'handoff-2')
            
            # Verify both handoffs present
            babel_file = parse_file(babel_path)
            self.assertEqual(len(babel_file.handoffs), 2)
    
    def test_idempotency_checks_most_recent_only(self):
        """Idempotency only checks against most recent handoff."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            content1 = 'First content'
            content2 = 'Second content'
            agent = 'agent-alpha'
            
            # Append first
            append_handoff(babel_path, content1, agent)
            
            # Append second
            append_handoff(babel_path, content2, agent)
            
            # Retry first content (should NOT be skipped, different from most recent)
            appended, handoff_id = append_handoff(babel_path, content1, agent)
            self.assertTrue(appended)
            self.assertEqual(handoff_id, 'handoff-3')
            
            # Retry second content (should be skipped, matches most recent)
            appended2, handoff_id2 = append_handoff(babel_path, content2, agent)
            self.assertFalse(appended2)
            self.assertEqual(handoff_id2, 'handoff-3')  # Most recent is now handoff-3


class TestHandoffAtomicIntegrity(unittest.TestCase):
    """Test atomic integrity on write failure."""
    
    def test_no_tempfile_residue_on_failure(self):
        """Failed write leaves no tempfile residue."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = _create_valid_babel_file(tmp_path)
            
            # Make parent directory read-only to simulate write failure
            # (This test may be skipped on some systems where chmod doesn't affect root)
            original_mode = tmp_path.stat().st_mode
            try:
                tmp_path.chmod(0o555)  # Read-only
                
                # Attempt append (should fail)
                with self.assertRaises(OSError):
                    append_handoff(babel_path, 'Test content', 'agent-alpha')
                
                # Verify no tempfile residue in directory
                files = list(tmp_path.iterdir())
                # Should only have test.babel, no tmp* files
                for f in files:
                    self.assertFalse(f.name.startswith('tmp'), 
                                   f'Found tempfile residue: {f.name}')
            finally:
                tmp_path.chmod(original_mode)  # Restore permissions
    
    def test_file_unchanged_on_parse_error(self):
        """Invalid .babel file raises BabelParseError without modification."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = tmp_path / 'invalid.babel'
            
            # Create invalid .babel file (missing intent)
            babel_path.write_text('''#[babel]:v0.10.2
#[spec]:test@0.10.2
{"description": "no intent block"}
''', encoding='utf-8')
            
            original_content = babel_path.read_text(encoding='utf-8')
            
            # Attempt append (should raise BabelParseError)
            with self.assertRaises(BabelParseError):
                append_handoff(babel_path, 'Test content', 'agent-alpha')
            
            # Verify file unchanged
            new_content = babel_path.read_text(encoding='utf-8')
            self.assertEqual(new_content, original_content)


class TestHandoffErrorPropagation(unittest.TestCase):
    """Test error propagation to CLI wrapper."""
    
    def test_babel_parse_error_propagates(self):
        """BabelParseError from parse_file propagates unchanged."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = tmp_path / 'invalid.babel'
            
            # Create file with duplicate intent IDs
            babel_path.write_text('''#[babel]:v0.10.2
#[intent]:main@0.10.2
{"agent_id": "agent1"}
#[intent]:main@0.10.2
{"agent_id": "agent2"}
''', encoding='utf-8')
            
            # Should raise BabelParseError with code='duplicate_id'
            with self.assertRaises(BabelParseError) as ctx:
                append_handoff(babel_path, 'Test content', 'agent-alpha')
            
            self.assertEqual(ctx.exception.code, 'duplicate_id')
    
    def test_file_not_found_raises_oserror(self):
        """Non-existent file raises OSError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            babel_path = tmp_path / 'nonexistent.babel'
            
            with self.assertRaises(OSError):
                append_handoff(babel_path, 'Test content', 'agent-alpha')


if __name__ == '__main__':
    unittest.main()
