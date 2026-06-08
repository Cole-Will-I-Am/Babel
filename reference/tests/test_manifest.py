"""Unit tests for Babel v0.10.3 manifest basis_ref computation.

Tests cover:
- compute_basis_ref returns correct hash for valid chain
- MANIFEST_INVALID_BASIS_REF for malformed basis_ref
- MANIFEST_MISSING_PREDECESSOR for missing predecessor
- MANIFEST_BASIS_MISMATCH for hash mismatch
"""

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.canonical import canonical_json

from reference.babel.manifest import (
    ManifestError,
    compute_basis_ref,
    MANIFEST_BASIS_MISMATCH,
    MANIFEST_INVALID_BASIS_REF,
    MANIFEST_MISSING_PREDECESSOR,
)


class TestComputeBasisRefValid(unittest.TestCase):
    """Test compute_basis_ref with valid manifest chain."""

    def test_genesis_no_basis_ref(self):
        """Genesis manifest (v0.1.0) has null basis_ref and returns empty string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            genesis = {
                "version": "v0.1.0",
                "basis_ref": None,
                "basis_target": None,
                "canonical_sha256": "sha256:" + "a" * 64,
            }
            genesis_path = tmpdir / "babel-manifest-v0.1.0.json"
            genesis_path.write_text(canonical_json(genesis))

            result = compute_basis_ref(genesis_path)
            self.assertEqual(result, "")

    def test_predecessor_hash_computed(self):
        """Non-genesis manifest computes predecessor hash correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create genesis
            genesis = {
                "version": "v0.1.0",
                "basis_ref": None,
                "basis_target": None,
                "canonical_sha256": "sha256:" + "a" * 64,
            }
            genesis_path = tmpdir / "babel-manifest-v0.1.0.json"
            genesis_path.write_text(canonical_json(genesis))

            # Compute genesis hash
            from orchestrator.canonical import canonical_sha256
            genesis_hash = canonical_sha256(genesis_path)

            # Create v0.2.0 with correct basis_ref
            v020 = {
                "version": "v0.2.0",
                "basis_ref": genesis_hash,
                "basis_target": "v0.1.0",
                "canonical_sha256": "sha256:" + "b" * 64,
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            # Compute basis_ref for v0.2.0
            result = compute_basis_ref(v020_path)
            self.assertEqual(result, genesis_hash)


class TestInvalidBasisRef(unittest.TestCase):
    """Test compute_basis_ref with invalid basis_ref format."""

    def test_malformed_basis_ref(self):
        """Malformed basis_ref raises MANIFEST_INVALID_BASIS_REF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create genesis
            genesis = {
                "version": "v0.1.0",
                "basis_ref": None,
                "basis_target": None,
            }
            genesis_path = tmpdir / "babel-manifest-v0.1.0.json"
            genesis_path.write_text(canonical_json(genesis))

            # Create v0.2.0 with malformed basis_ref
            v020 = {
                "version": "v0.2.0",
                "basis_ref": "invalid-hash-format",
                "basis_target": "v0.1.0",
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            with self.assertRaises(ManifestError) as ctx:
                compute_basis_ref(v020_path)

            self.assertEqual(ctx.exception.code, MANIFEST_INVALID_BASIS_REF)
            self.assertEqual(ctx.exception.version, "v0.2.0")

    def test_non_genesis_null_basis_ref(self):
        """Non-genesis manifest with null basis_ref raises MANIFEST_INVALID_BASIS_REF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create genesis
            genesis = {
                "version": "v0.1.0",
                "basis_ref": None,
                "basis_target": None,
            }
            genesis_path = tmpdir / "babel-manifest-v0.1.0.json"
            genesis_path.write_text(canonical_json(genesis))

            # Create v0.2.0 with null basis_ref
            v020 = {
                "version": "v0.2.0",
                "basis_ref": None,
                "basis_target": "v0.1.0",
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            with self.assertRaises(ManifestError) as ctx:
                compute_basis_ref(v020_path)

            self.assertEqual(ctx.exception.code, MANIFEST_INVALID_BASIS_REF)


class TestMissingPredecessor(unittest.TestCase):
    """Test compute_basis_ref with missing predecessor manifest."""

    def test_missing_predecessor(self):
        """Missing predecessor manifest raises MANIFEST_MISSING_PREDECESSOR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create v0.2.0 referencing non-existent v0.1.0
            v020 = {
                "version": "v0.2.0",
                "basis_ref": "sha256:" + "a" * 64,
                "basis_target": "v0.1.0",
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            with self.assertRaises(ManifestError) as ctx:
                compute_basis_ref(v020_path)

            self.assertEqual(ctx.exception.code, MANIFEST_MISSING_PREDECESSOR)

    def test_null_basis_target(self):
        """Null basis_target raises MANIFEST_MISSING_PREDECESSOR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create v0.2.0 with null basis_target
            v020 = {
                "version": "v0.2.0",
                "basis_ref": "sha256:" + "a" * 64,
                "basis_target": None,
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            with self.assertRaises(ManifestError) as ctx:
                compute_basis_ref(v020_path)

            self.assertEqual(ctx.exception.code, MANIFEST_MISSING_PREDECESSOR)


class TestBasisMismatch(unittest.TestCase):
    """Test compute_basis_ref with hash mismatch."""

    def test_hash_mismatch(self):
        """Hash mismatch raises MANIFEST_BASIS_MISMATCH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create genesis
            genesis = {
                "version": "v0.1.0",
                "basis_ref": None,
                "basis_target": None,
            }
            genesis_path = tmpdir / "babel-manifest-v0.1.0.json"
            genesis_path.write_text(canonical_json(genesis))

            # Compute actual genesis hash
            from orchestrator.canonical import canonical_sha256
            actual_hash = canonical_sha256(genesis_path)

            # Create v0.2.0 with WRONG basis_ref
            wrong_hash = "sha256:" + "f" * 64
            v020 = {
                "version": "v0.2.0",
                "basis_ref": wrong_hash,
                "basis_target": "v0.1.0",
            }
            v020_path = tmpdir / "babel-manifest-v0.2.0.json"
            v020_path.write_text(canonical_json(v020))

            with self.assertRaises(ManifestError) as ctx:
                compute_basis_ref(v020_path)

            self.assertEqual(ctx.exception.code, MANIFEST_BASIS_MISMATCH)
            self.assertEqual(ctx.exception.expected, wrong_hash)
            self.assertEqual(ctx.exception.actual, actual_hash)


if __name__ == "__main__":
    unittest.main()
