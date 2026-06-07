"""Contract tests for Babel v0.10.2 handoff API skeleton.

These tests verify the frozen public surface of reference.babel.handoff:
- Module imports successfully
- BABEL_VERSION constant
- append_handoff function signature (7 parameters + None return)
- NotImplementedError raise on append_handoff call
- __all__ exports
- Path import from pathlib for type hints

This is stage 3a of the Babel v0.10.2 contract-first bootstrap.
"""

import unittest
import typing
import inspect
from pathlib import Path


class TestModuleImports(unittest.TestCase):
    """Verify handoff module imports successfully."""

    def test_import_handoff_module(self):
        """handoff module imports without error."""
        from reference.babel import handoff
        self.assertIsNotNone(handoff)

    def test_babel_version_constant(self):
        """BABEL_VERSION constant is exposed and matches v0.10.2."""
        from reference.babel import handoff
        self.assertTrue(hasattr(handoff, 'BABEL_VERSION'))
        self.assertEqual(handoff.BABEL_VERSION, "0.10.2")


class TestAppendHandoffSignature(unittest.TestCase):
    """Verify append_handoff function signature."""

    def test_append_handoff_exists(self):
        """append_handoff function is exposed."""
        from reference.babel import handoff
        self.assertTrue(hasattr(handoff, 'append_handoff'))
        self.assertTrue(callable(handoff.append_handoff))

    def test_append_handoff_parameter_count(self):
        """append_handoff has exactly 7 parameters."""
        from reference.babel import handoff
        sig = inspect.signature(handoff.append_handoff)
        params = list(sig.parameters.keys())
        self.assertEqual(len(params), 7)

    def test_append_handoff_parameter_names(self):
        """append_handoff has correct parameter names."""
        from reference.babel import handoff
        sig = inspect.signature(handoff.append_handoff)
        params = list(sig.parameters.keys())
        expected = ['path', 'next_owner', 'signoff', 'blocking_issues',
                    'required_changes', 'summary', 'memory_note']
        self.assertEqual(params, expected)

    def test_append_handoff_type_hints(self):
        """append_handoff has correct type hints via get_type_hints."""
        from reference.babel import handoff
        hints = typing.get_type_hints(handoff.append_handoff)

        # Verify parameter types
        self.assertEqual(hints.get('path'), Path)
        self.assertEqual(hints.get('next_owner'), str)
        self.assertEqual(hints.get('signoff'), bool)
        self.assertEqual(hints.get('blocking_issues'), list[str])
        self.assertEqual(hints.get('required_changes'), list[str])
        self.assertEqual(hints.get('summary'), str)
        self.assertEqual(hints.get('memory_note'), str)

        # Verify return type is None
        self.assertEqual(hints.get('return'), None)


class TestNotImplementedError(unittest.TestCase):
    """Verify append_handoff raises NotImplementedError."""

    def test_append_handoff_raises_not_implemented(self):
        """append_handoff raises NotImplementedError when called."""
        from reference.babel import handoff
        test_path = Path("/tmp/test.babel")
        with self.assertRaises(NotImplementedError):
            handoff.append_handoff(
                path=test_path,
                next_owner="test_agent",
                signoff=True,
                blocking_issues=[],
                required_changes=[],
                summary="test summary",
                memory_note="test note"
            )

    def test_not_implemented_message_mentions_cycle(self):
        """NotImplementedError message references v0.10.3 cycle 3."""
        from reference.babel import handoff
        test_path = Path("/tmp/test.babel")
        try:
            handoff.append_handoff(
                path=test_path,
                next_owner="test_agent",
                signoff=True,
                blocking_issues=[],
                required_changes=[],
                summary="test summary",
                memory_note="test note"
            )
            self.fail("Expected NotImplementedError")
        except NotImplementedError as e:
            error_message = str(e)
            self.assertIn("v0.10.3", error_message)
            self.assertIn("cycle 3", error_message)


class TestModuleExports(unittest.TestCase):
    """Verify handoff module __all__ exports."""

    def test_all_contains_append_handoff(self):
        """__all__ contains append_handoff."""
        from reference.babel import handoff
        self.assertTrue(hasattr(handoff, '__all__'))
        self.assertIn('append_handoff', handoff.__all__)

    def test_all_is_tuple_or_list(self):
        """__all__ is a tuple or list."""
        from reference.babel import handoff
        self.assertIsInstance(handoff.__all__, (tuple, list))


class TestPathImport(unittest.TestCase):
    """Verify handoff module imports Path from pathlib."""

    def test_path_is_used_in_signature(self):
        """Path type is used in append_handoff signature."""
        from reference.babel import handoff
        hints = typing.get_type_hints(handoff.append_handoff)
        self.assertEqual(hints.get('path'), Path)


class TestTypeAnnotations(unittest.TestCase):
    """Verify list[str] annotations for list parameters."""

    def test_blocking_issues_is_list_str(self):
        """blocking_issues parameter has list[str] type."""
        from reference.babel import handoff
        hints = typing.get_type_hints(handoff.append_handoff)
        self.assertEqual(hints.get('blocking_issues'), list[str])

    def test_required_changes_is_list_str(self):
        """required_changes parameter has list[str] type."""
        from reference.babel import handoff
        hints = typing.get_type_hints(handoff.append_handoff)
        self.assertEqual(hints.get('required_changes'), list[str])


if __name__ == '__main__':
    unittest.main()
