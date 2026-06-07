"""
Unittest suite for Babel v0.10.3 Spec-Index Bootstrap Reference Implementation.

Tests cover all seven test vectors from spec Section 10:
- TV-BOOT-1: bootstrap from v0.9.0 manifest (success case)
- TV-BOOT-2: missing manifest detection
- TV-BOOT-3: placeholder hash detection
- TV-BOOT-4: basis_ref mismatch detection
- TV-BOOT-5: genesis has basis detection
- TV-BOOT-6: duplicate key detection
- TV-BOOT-7: bad path detection

All tests use temporary directories with synthetic manifest data.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from orchestrator.canonical import canonical_json

# Import bootstrap module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from babel.bootstrap import (
    BOOTSTRAP_BAD_PATH,
    BOOTSTRAP_BASIS_MISMATCH,
    BOOTSTRAP_DUPLICATE_KEY,
    BOOTSTRAP_GENESIS_HAS_BASIS,
    BOOTSTRAP_INVALID_BASIS_REF,
    BOOTSTRAP_MISSING_MANIFEST,
    BOOTSTRAP_PLACEHOLDER_HASH,
    BootstrapError,
    SpecIndexBootstrap,
    _is_placeholder_hash,
    _parse_version,
    _validate_path,
)


class TestVersionParsing(unittest.TestCase):
    """Test semver version parsing per spec Section 2.3."""

    def test_valid_versions(self):
        """Test valid semver version strings."""
        self.assertEqual(_parse_version("v0.1.0"), (0, 1, 0))
        self.assertEqual(_parse_version("v0.8.1"), (0, 8, 1))
        self.assertEqual(_parse_version("v0.9.0"), (0, 9, 0))
        self.assertEqual(_parse_version("v1.0.0"), (1, 0, 0))
        self.assertEqual(_parse_version("v10.20.30"), (10, 20, 30))

    def test_invalid_versions(self):
        """Test invalid version strings raise ValueError."""
        invalid = [
            "0.1.0",  # missing 'v'
            "v0.1",  # missing patch
            "v0.01.0",  # leading zero
            "v0.1.0-beta",  # pre-release tag
            "invalid",
            "",
        ]
        for v in invalid:
            with self.subTest(version=v):
                with self.assertRaises(ValueError):
                    _parse_version(v)


class TestPlaceholderHashDetection(unittest.TestCase):
    """Test placeholder hash detection per spec Section 3."""

    def test_valid_hash(self):
        """Valid sha256:hex64 is not a placeholder."""
        valid_hash = "sha256:" + "a" * 64
        self.assertFalse(_is_placeholder_hash(valid_hash))

    def test_empty_hash(self):
        """Empty string is a placeholder."""
        self.assertTrue(_is_placeholder_hash(""))
        self.assertTrue(_is_placeholder_hash(None))

    def test_pending_hash(self):
        """sha256:PENDING... is a placeholder."""
        self.assertTrue(_is_placeholder_hash("sha256:PENDING_COMPUTE_AT_COMMIT"))
        self.assertTrue(_is_placeholder_hash("sha256:PENDING"))


class TestPathValidation(unittest.TestCase):
    """Test path validation per spec Section 3."""

    def test_valid_paths(self):
        """Valid paths under autonomy-output/ or scripts/."""
        valid = [
            "autonomy-output/babel-manifest-v0.9.0.json",
            "autonomy-output/babel-bwcc-v0.9.0.md",
            "scripts/compute-manifest-sha256.py",
            "autonomy-output/subdir/file.txt",
        ]
        for p in valid:
            with self.subTest(path=p):
                self.assertTrue(_validate_path(p))

    def test_invalid_paths(self):
        """Invalid paths are rejected."""
        invalid = [
            "/absolute/path",  # leading slash
            "back\\slash",  # backslash
            "../escape",  # parent traversal
            "other/file.txt",  # wrong root segment
            "",  # empty
            "autonomy-output/",  # trailing slash no filename
        ]
        for p in invalid:
            with self.subTest(path=p):
                self.assertFalse(_validate_path(p))


class TestBootstrapSuccess(unittest.TestCase):
    """TV-BOOT-1: Successful bootstrap from v0.9.0 manifest."""

    def setUp(self):
        """Create temporary directory with synthetic manifest chain."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 genesis manifest
        self.v010_manifest = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "",
            "artifacts": [
                {
                    "type": "spec",
                    "path": "autonomy-output/babel-bwcc-v0.1.0.md",
                    "canonical_sha256": "sha256:" + "a" * 64,
                }
            ],
        }
        self._write_manifest("v0.1.0", self.v010_manifest)

        # Create v0.2.0 manifest
        self.v020_manifest = {
            "version": "v0.2.0",
            "basis_ref": "",
            "basis_target": "v0.1.0",
            "canonical_sha256": "",
            "artifacts": [
                {
                    "type": "spec",
                    "path": "autonomy-output/babel-bssc-v0.2.0.md",
                    "canonical_sha256": "sha256:" + "b" * 64,
                }
            ],
        }
        self._write_manifest("v0.2.0", self.v020_manifest)
        # Update v0.2.0 basis_ref to actual hash of v0.1.0
        v010_path = self.base_path / "babel-manifest-v0.1.0.json"
        self.v020_manifest["basis_ref"] = "sha256:" + canonical_sha256(v010_path)[7:]
        self._write_manifest("v0.2.0", self.v020_manifest)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def _write_manifest(self, version: str, data: dict):
        """Write manifest to temp directory."""
        path = self.base_path / f"babel-manifest-{version}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True, indent=2)
            f.write("\n")
        # Update canonical_sha256
        data["canonical_sha256"] = "sha256:" + canonical_sha256(path)[7:]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True, indent=2)
            f.write("\n")

    def test_bootstrap_success(self):
        """TV-BOOT-1: Bootstrap from v0.2.0 (simplified chain) succeeds."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        output = bootstrap.run(start_version="v0.2.0")

        data = json.loads(output)
        self.assertEqual(data["bootstrap_version"], "v0.10.3")
        self.assertEqual(data["generated_by"], "babel-spec-index-bootstrap-v0.10.3")
        self.assertIn("frozen_base", data)
        self.assertIn("seed_entries", data)
        self.assertIn("manifest_entries", data)

        # Should have 2 manifest entries (v0.1.0, v0.2.0)
        self.assertEqual(len(data["manifest_entries"]), 2)

        # Should have 2 seed entries (one artifact per manifest)
        self.assertEqual(len(data["seed_entries"]), 2)


class TestBootstrapMissingManifest(unittest.TestCase):
    """TV-BOOT-2: Missing manifest detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 genesis
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

        # Create v0.2.0 referencing non-existent v0.1.5
        v020 = {
            "version": "v0.2.0",
            "basis_ref": "sha256:" + "b" * 64,
            "basis_target": "v0.1.5",  # Does not exist
            "canonical_sha256": "sha256:" + "c" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.2.0.json"
        with open(path, "w") as f:
            json.dump(v020, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_missing_manifest(self):
        """TV-BOOT-2: Missing basis_target raises BOOTSTRAP_MISSING_MANIFEST."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.2.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_MISSING_MANIFEST)
        self.assertEqual(ctx.exception.version, "v0.2.0")


class TestBootstrapPlaceholderHash(unittest.TestCase):
    """TV-BOOT-3: Placeholder hash detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 with placeholder hash in artifact
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [
                {
                    "type": "spec",
                    "path": "autonomy-output/test.md",
                    "canonical_sha256": "sha256:PENDING_COMPUTE_AT_COMMIT",
                }
            ],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_placeholder_hash(self):
        """TV-BOOT-3: Placeholder hash raises BOOTSTRAP_PLACEHOLDER_HASH."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.1.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_PLACEHOLDER_HASH)
        self.assertEqual(ctx.exception.path, "autonomy-output/test.md")


class TestBootstrapBasisMismatch(unittest.TestCase):
    """TV-BOOT-4: Basis ref mismatch detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 genesis
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

        # Create v0.2.0 with tampered basis_ref
        v020 = {
            "version": "v0.2.0",
            "basis_ref": "sha256:" + "x" * 64,  # Wrong hash
            "basis_target": "v0.1.0",
            "canonical_sha256": "sha256:" + "b" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.2.0.json"
        with open(path, "w") as f:
            json.dump(v020, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_basis_mismatch(self):
        """TV-BOOT-4: Tampered basis_ref raises BOOTSTRAP_BASIS_MISMATCH."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.2.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_BASIS_MISMATCH)
        self.assertEqual(ctx.exception.version, "v0.2.0")
        self.assertIsNotNone(ctx.exception.expected)
        self.assertIsNotNone(ctx.exception.actual)


class TestBootstrapGenesisHasBasis(unittest.TestCase):
    """TV-BOOT-5: Genesis with non-null basis_ref detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 with non-null basis_ref (violation)
        v010 = {
            "version": "v0.1.0",
            "basis_ref": "sha256:" + "a" * 64,  # Should be null
            "basis_target": "v0.0.0",
            "canonical_sha256": "sha256:" + "b" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_genesis_has_basis(self):
        """TV-BOOT-5: Genesis with basis raises BOOTSTRAP_GENESIS_HAS_BASIS."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.1.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_GENESIS_HAS_BASIS)
        self.assertEqual(ctx.exception.version, "v0.1.0")


class TestBootstrapDuplicateKey(unittest.TestCase):
    """TV-BOOT-6: Duplicate (version, type) key detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 with duplicate artifact types
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [
                {
                    "type": "spec",
                    "path": "autonomy-output/test1.md",
                    "canonical_sha256": "sha256:" + "b" * 64,
                },
                {
                    "type": "spec",  # Duplicate type
                    "path": "autonomy-output/test2.md",
                    "canonical_sha256": "sha256:" + "c" * 64,
                },
            ],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_duplicate_key(self):
        """TV-BOOT-6: Duplicate (version, type) raises BOOTSTRAP_DUPLICATE_KEY."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.1.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_DUPLICATE_KEY)
        self.assertEqual(ctx.exception.version, "v0.1.0")


class TestBootstrapBadPath(unittest.TestCase):
    """TV-BOOT-7: Invalid path detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 with invalid path
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [
                {
                    "type": "spec",
                    "path": "/absolute/path.md",  # Invalid: leading slash
                    "canonical_sha256": "sha256:" + "b" * 64,
                }
            ],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_bad_path(self):
        """TV-BOOT-7: Invalid path raises BOOTSTRAP_BAD_PATH."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.1.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_BAD_PATH)
        self.assertEqual(ctx.exception.path, "/absolute/path.md")


class TestBootstrapInvalidBasisRef(unittest.TestCase):
    """Additional test: Invalid basis_ref format detection."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)

        # Create v0.1.0 genesis
        v010 = {
            "version": "v0.1.0",
            "basis_ref": None,
            "basis_target": None,
            "canonical_sha256": "sha256:" + "a" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.1.0.json"
        with open(path, "w") as f:
            json.dump(v010, f)

        # Create v0.2.0 with malformed basis_ref
        v020 = {
            "version": "v0.2.0",
            "basis_ref": "invalid-hash-format",  # Not sha256:hex64
            "basis_target": "v0.1.0",
            "canonical_sha256": "sha256:" + "b" * 64,
            "artifacts": [],
        }
        path = self.base_path / "babel-manifest-v0.2.0.json"
        with open(path, "w") as f:
            json.dump(v020, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_invalid_basis_ref(self):
        """Malformed basis_ref raises BOOTSTRAP_INVALID_BASIS_REF."""
        bootstrap = SpecIndexBootstrap(base_path=str(self.base_path))
        with self.assertRaises(BootstrapError) as ctx:
            bootstrap.run(start_version="v0.2.0")

        self.assertEqual(ctx.exception.code, BOOTSTRAP_INVALID_BASIS_REF)
        self.assertEqual(ctx.exception.version, "v0.2.0")


if __name__ == "__main__":
    unittest.main()
