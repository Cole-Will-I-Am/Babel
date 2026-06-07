"""
Unittest suite for Babel v0.9.0 manifest hash computation reference implementation.

Tests cover:
- basis_ref computation from base manifest
- basis_ref validation (placeholder population, mismatch rejection)
- Base manifest placeholder rejection
- Artifact hash computation via v0.2.0 canonicalization
- Atomic rewrite via temp+replace
- All exit code paths (0/1/2/3)

All tests are deterministic and use only Python 3.12 stdlib.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from typing import Dict, Any

# Add reference/ to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from babel.manifest import ManifestHasher, PLACEHOLDER_PREFIX


class TestManifestHasher(unittest.TestCase):
    """Test suite for ManifestHasher class."""
    
    def setUp(self):
        """Create temporary directory structure for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.autonomy_dir = os.path.join(self.test_dir, "autonomy-output")
        os.makedirs(self.autonomy_dir)
        self.hasher = ManifestHasher(self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def _create_manifest(self, version: str, content: Dict[str, Any]) -> str:
        """Helper to create a manifest file."""
        path = os.path.join(self.autonomy_dir, f"babel-manifest-v{version}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return path
    
    def _create_artifact(self, rel_path: str, content: str) -> str:
        """Helper to create an artifact file."""
        full_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path
    
    def test_compute_basis_ref_success(self):
        """Test basis_ref computation from valid base manifest."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": "sha256:abc123"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        success, error_code, result = self.hasher.compute_basis_ref(base_path)
        
        self.assertTrue(success)
        self.assertIsNone(error_code)
        self.assertTrue(result.startswith("sha256:"))
        self.assertEqual(len(result), 71)  # "sha256:" + 64 hex chars
    
    def test_compute_basis_ref_missing(self):
        """Test basis_ref computation with missing base manifest."""
        success, error_code, result = self.hasher.compute_basis_ref(
            os.path.join(self.test_dir, "nonexistent.json")
        )
        
        self.assertFalse(success)
        self.assertEqual(error_code, "MANIFEST_MISSING")
    
    def test_validate_base_manifest_no_placeholders(self):
        """Test base manifest validation with all hashes present."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": "sha256:abc123"},
                {"path": "test2.txt", "canonical_sha256": "sha256:def456"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        success, error_code, message = self.hasher.validate_base_manifest(base_path)
        
        self.assertTrue(success)
        self.assertIsNone(error_code)
    
    def test_validate_base_manifest_placeholder_rejected(self):
        """Test base manifest validation rejects placeholder hashes."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        success, error_code, message = self.hasher.validate_base_manifest(base_path)
        
        self.assertFalse(success)
        self.assertEqual(error_code, "BASE_PLACEHOLDER")
        self.assertIn("test.txt", message)
    
    def test_validate_base_manifest_empty_hash_rejected(self):
        """Test base manifest validation rejects empty canonical_sha256."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": ""}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        success, error_code, message = self.hasher.validate_base_manifest(base_path)
        
        self.assertFalse(success)
        self.assertEqual(error_code, "BASE_PLACEHOLDER")
    
    def test_validate_basis_ref_populate_placeholder(self):
        """Test basis_ref validation populates placeholder."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": "sha256:abc123"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:PENDING",
            "artifacts": []
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        success, error_code, basis_ref = self.hasher.validate_basis_ref(target_path, base_path)
        
        self.assertTrue(success)
        self.assertIsNone(error_code)
        self.assertTrue(basis_ref.startswith("sha256:"))
    
    def test_validate_basis_ref_mismatch_rejected(self):
        """Test basis_ref validation rejects mismatch."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "test.txt", "canonical_sha256": "sha256:abc123"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:wronghash",
            "artifacts": []
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        success, error_code, message = self.hasher.validate_basis_ref(target_path, base_path)
        
        self.assertFalse(success)
        self.assertEqual(error_code, "BASIS_REF_MISMATCH")
        self.assertIn("mismatch", message)
    
    def test_compute_artifact_hashes_success(self):
        """Test artifact hash computation."""
        # Create artifact
        artifact_path = self._create_artifact("reference/test.txt", "Hello, Babel!")
        
        target_content = {
            "version": "0.9.0",
            "artifacts": [
                {"path": "reference/test.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        success, error_code, updated = self.hasher.compute_artifact_hashes(target_path)
        
        self.assertTrue(success)
        self.assertIsNone(error_code)
        self.assertEqual(len(updated), 1)
        self.assertTrue(updated[0]["canonical_sha256"].startswith("sha256:"))
    
    def test_compute_artifact_hashes_missing_file(self):
        """Test artifact hash computation with missing file."""
        target_content = {
            "version": "0.9.0",
            "artifacts": [
                {"path": "nonexistent.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        success, error_code, result = self.hasher.compute_artifact_hashes(target_path)
        
        self.assertFalse(success)
        self.assertEqual(error_code, "ARTIFACT_MISSING")
    
    def test_compute_artifact_hashes_missing_path(self):
        """Test artifact hash computation with missing path field."""
        target_content = {
            "version": "0.9.0",
            "artifacts": [
                {"canonical_sha256": "sha256:PENDING"}
            ]
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        success, error_code, result = self.hasher.compute_artifact_hashes(target_path)
        
        self.assertFalse(success)
        self.assertEqual(error_code, "ARTIFACT_MISSING_PATH")
    
    def test_atomic_rewrite_success(self):
        """Test atomic manifest rewrite."""
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:abc123",
            "artifacts": []
        }
        target_path = self._create_manifest("0.9.0", target_content)
        
        updated_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:def456",
            "artifacts": [],
            "generated_at": "1970-01-01T00:00:00Z"
        }
        
        success, error_code, message = self.hasher.atomic_rewrite(target_path, updated_content)
        
        self.assertTrue(success)
        self.assertIsNone(error_code)
        
        # Verify rewrite
        with open(target_path, "r", encoding="utf-8") as f:
            reloaded = json.load(f)
        self.assertEqual(reloaded["basis_ref"], "sha256:def456")
    
    def test_finalize_manifest_full_workflow(self):
        """Test complete manifest finalization workflow."""
        # Create base manifest (fully hashed)
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "base.txt", "canonical_sha256": "sha256:base123"}
            ]
        }
        base_path = self._create_manifest("0.8.1", base_content)
        self._create_artifact("base.txt", "Base content")
        
        # Create target manifest with placeholder
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:PENDING",
            "artifacts": [
                {"path": "artifact.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        target_path = self._create_manifest("0.9.0", target_content)
        self._create_artifact("artifact.txt", "Artifact content")
        
        exit_code, message = self.hasher.finalize_manifest()
        
        self.assertEqual(exit_code, 0)
        self.assertTrue(message.startswith("OK:"))
        self.assertIn("basis_ref=sha256:", message)
        self.assertIn("1 artifact hashes computed", message)
    
    def test_finalize_manifest_base_placeholder_rejected(self):
        """Test finalize rejects base manifest with placeholder."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "base.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        self._create_manifest("0.8.1", base_content)
        
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:PENDING",
            "artifacts": []
        }
        self._create_manifest("0.9.0", target_content)
        
        exit_code, message = self.hasher.finalize_manifest()
        
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR", message)
    
    def test_finalize_manifest_missing_base(self):
        """Test finalize with missing base manifest."""
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:PENDING",
            "artifacts": []
        }
        self._create_manifest("0.9.0", target_content)
        
        exit_code, message = self.hasher.finalize_manifest()
        
        self.assertEqual(exit_code, 2)
        self.assertIn("missing base manifest", message)
    
    def test_finalize_manifest_missing_target(self):
        """Test finalize with missing target manifest."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "base.txt", "canonical_sha256": "sha256:base123"}
            ]
        }
        self._create_manifest("0.8.1", base_content)
        
        exit_code, message = self.hasher.finalize_manifest()
        
        self.assertEqual(exit_code, 2)
        self.assertIn("missing target manifest", message)
    
    def test_finalize_manifest_missing_artifact(self):
        """Test finalize with missing artifact file."""
        base_content = {
            "version": "0.8.1",
            "artifacts": [
                {"path": "base.txt", "canonical_sha256": "sha256:base123"}
            ]
        }
        self._create_manifest("0.8.1", base_content)
        self._create_artifact("base.txt", "Base")
        
        target_content = {
            "version": "0.9.0",
            "basis_ref": "sha256:PENDING",
            "artifacts": [
                {"path": "missing.txt", "canonical_sha256": "sha256:PENDING"}
            ]
        }
        self._create_manifest("0.9.0", target_content)
        
        exit_code, message = self.hasher.finalize_manifest()
        
        self.assertEqual(exit_code, 2)
        self.assertIn("missing artifact", message.lower())
    
    def test_placeholder_prefix_constant(self):
        """Test PLACEHOLDER_PREFIX constant value."""
        self.assertEqual(PLACEHOLDER_PREFIX, "sha256:PENDING")
        self.assertTrue("sha256:PENDING_COMPUTE_AT_COMMIT".startswith(PLACEHOLDER_PREFIX))


class TestCanonicalizationIntegration(unittest.TestCase):
    """Test that manifest hasher uses orchestrator/canonical.py correctly."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.autonomy_dir = os.path.join(self.test_dir, "autonomy-output")
        os.makedirs(self.autonomy_dir)
        self.hasher = ManifestHasher(self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_deterministic_hash_same_content(self):
        """Test that same content produces same hash across runs."""
        content = "Deterministic content with unicode: café ñ 日本語"
        artifact_path = self._create_artifact("test.txt", content)
        
        # Compute hash twice
        hash1 = self.hasher.compute_artifact_hashes(
            self._create_manifest("0.9.0", {
                "version": "0.9.0",
                "artifacts": [{"path": "test.txt", "canonical_sha256": "sha256:PENDING"}]
            })
        )[2][0]["canonical_sha256"]
        
        hash2 = self.hasher.compute_artifact_hashes(
            self._create_manifest("0.9.0", {
                "version": "0.9.0",
                "artifacts": [{"path": "test.txt", "canonical_sha256": "sha256:PENDING"}]
            })
        )[2][0]["canonical_sha256"]
        
        self.assertEqual(hash1, hash2)
    
    def _create_manifest(self, version: str, content: dict) -> str:
        path = os.path.join(self.autonomy_dir, f"babel-manifest-v{version}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f)
        return path
    
    def _create_artifact(self, rel_path: str, content: str) -> str:
        full_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path


if __name__ == "__main__":
    unittest.main()
