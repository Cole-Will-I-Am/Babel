"""
Babel v0.9.0 Manifest Hash Computation Reference Implementation

Implements the manifest finalization logic from scripts/compute-manifest-sha256.py
but uses orchestrator/canonical.py for v0.2.0 canonical serialization.

Exit codes (aligned with v0.6.0 AIC convention):
  0 = success, manifest rewritten with computed hashes
  1 = validation failure (placeholder base, basis_ref mismatch, malformed)
  2 = missing manifest or artifact file
  3 = IO error during rewrite
"""
import os
import sys
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any

from orchestrator.canonical import canonical_json, canonical_sha256


PLACEHOLDER_PREFIX = "sha256:PENDING"


class ManifestHasher:
    """
    Computes and validates manifest hashes for Babel v0.9.0 freeze.
    
    Uses orchestrator/canonical.py for v0.2.0 canonical serialization:
    - NFC unicode normalization
    - LF line endings (no CR)
    - Sorted keys in JSON
    - Deterministic number serialization
    - Single LF terminator
    """
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
    
    def compute_basis_ref(self, base_manifest_path: str) -> Tuple[bool, Optional[str], str]:
        """
        Compute basis_ref from frozen base manifest.
        
        Returns:
            (success, error_code, result_or_message)
            On success: (True, None, "sha256:hex64")
            On failure: (False, error_code, error_message)
        """
        if not os.path.exists(base_manifest_path):
            return (False, "MANIFEST_MISSING", f"Base manifest not found: {base_manifest_path}")
        
        try:
            hash_result = canonical_sha256(base_manifest_path)
            return (True, None, hash_result)
        except OSError as exc:
            return (False, "MANIFEST_IO_ERROR", f"Failed to read base manifest: {exc}")
        except ValueError as exc:
            return (False, "MANIFEST_INVALID", f"Invalid base manifest: {exc}")
    
    def validate_base_manifest(self, base_manifest_path: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate that base manifest has no placeholder hashes.
        
        A frozen base must be fully hashed; we never derive a basis_ref
        from a placeholder base.
        
        Returns:
            (success, error_code, message)
        """
        if not os.path.exists(base_manifest_path):
            return (False, "MANIFEST_MISSING", f"Base manifest not found: {base_manifest_path}")
        
        try:
            with open(base_manifest_path, "rb") as f:
                raw = f.read()
            obj = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            return (False, "MANIFEST_IO_ERROR", f"Failed to read base manifest: {exc}")
        
        artifacts = obj.get("artifacts", [])
        for entry in artifacts:
            cs = entry.get("canonical_sha256", "")
            if not cs or cs.startswith(PLACEHOLDER_PREFIX):
                path = entry.get("path", "<unknown>")
                return (False, "BASE_PLACEHOLDER", 
                        f"Base manifest has placeholder canonical_sha256 for {path}")
        
        return (True, None, "Base manifest validated")
    
    def validate_basis_ref(self, target_manifest_path: str, base_manifest_path: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate or populate basis_ref in target manifest.
        
        Returns:
            (success, error_code, basis_ref_or_error_message)
        """
        # Compute expected basis_ref from base
        success, error_code, computed_basis = self.compute_basis_ref(base_manifest_path)
        if not success:
            return (False, error_code, computed_basis)
        
        # Load target manifest
        if not os.path.exists(target_manifest_path):
            return (False, "MANIFEST_MISSING", f"Target manifest not found: {target_manifest_path}")
        
        try:
            with open(target_manifest_path, "rb") as f:
                raw = f.read()
            obj = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            return (False, "MANIFEST_IO_ERROR", f"Failed to read target manifest: {exc}")
        
        stated_basis = obj.get("basis_ref", "")
        
        # If placeholder or empty, populate with computed
        if not stated_basis or stated_basis.startswith(PLACEHOLDER_PREFIX):
            return (True, None, computed_basis)
        
        # If stated, must match computed
        if stated_basis != computed_basis:
            return (False, "BASIS_REF_MISMATCH",
                    f"basis_ref mismatch: manifest={stated_basis} computed={computed_basis}")
        
        return (True, None, stated_basis)
    
    def compute_artifact_hashes(self, target_manifest_path: str) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        Recompute canonical_sha256 for every artifact entry.
        
        Returns:
            (success, error_code, updated_artifacts_list)
        """
        if not os.path.exists(target_manifest_path):
            return (False, "MANIFEST_MISSING", f"Target manifest not found: {target_manifest_path}")
        
        try:
            with open(target_manifest_path, "rb") as f:
                raw = f.read()
            obj = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            return (False, "MANIFEST_IO_ERROR", f"Failed to read target manifest: {exc}")
        
        artifacts = obj.get("artifacts", [])
        updated = []
        
        for entry in artifacts:
            rel_path = entry.get("path", "")
            if not rel_path:
                return (False, "ARTIFACT_MISSING_PATH", "Artifact entry missing path")
            
            full_path = os.path.join(self.repo_root, rel_path)
            if not os.path.exists(full_path):
                return (False, "ARTIFACT_MISSING", f"Missing artifact file: {rel_path}")
            
            try:
                hash_result = canonical_sha256(full_path)
            except (OSError, ValueError) as exc:
                return (False, "ARTIFACT_IO_ERROR", f"Read failed for {rel_path}: {exc}")
            
            # Update entry with computed hash
            updated_entry = dict(entry)
            updated_entry["canonical_sha256"] = hash_result
            updated.append(updated_entry)
        
        return (True, None, updated)
    
    def atomic_rewrite(self, target_manifest_path: str, updated_obj: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
        """
        Atomically rewrite manifest via temp+replace.
        
        Returns:
            (success, error_code, message)
        """
        try:
            canon_text = canonical_json(updated_obj)
            new_bytes = canon_text.encode("utf-8")
        except (TypeError, ValueError) as exc:
            return (False, "CANONICALIZE_ERROR", f"Failed to canonicalize manifest: {exc}")
        
        tmp_path = target_manifest_path + ".tmp"
        
        try:
            with open(tmp_path, "wb") as f:
                f.write(new_bytes)
            os.replace(tmp_path, target_manifest_path)
        except OSError as exc:
            # Clean up temp file if it exists
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            return (False, "REWRITE_IO_ERROR", f"Atomic rewrite failed: {exc}")
        
        return (True, None, f"Manifest rewritten: {target_manifest_path}")
    
    def finalize_manifest(self, target_version: str = "0.9.0", 
                          base_version: str = "0.8.1") -> Tuple[int, str]:
        """
        Full manifest finalization workflow.
        
        Returns:
            (exit_code, message)
            0 = success
            1 = validation failure
            2 = missing file
            3 = IO error
        """
        target_path = os.path.join(self.repo_root, "autonomy-output",
                                   f"babel-manifest-v{target_version}.json")
        base_path = os.path.join(self.repo_root, "autonomy-output",
                                 f"babel-manifest-v{base_version}.json")
        
        # Gate 1: validate base manifest (no placeholders)
        success, error_code, message = self.validate_base_manifest(base_path)
        if not success:
            if error_code == "MANIFEST_MISSING":
                return (2, f"ERROR: missing base manifest: {base_path}")
            return (1, f"ERROR: base manifest validation failed: {message}")
        
        # Gate 2: validate/populate basis_ref
        success, error_code, basis_ref = self.validate_basis_ref(target_path, base_path)
        if not success:
            if error_code == "MANIFEST_MISSING":
                return (2, f"ERROR: missing target manifest: {target_path}")
            return (1, f"ERROR: basis_ref validation failed: {basis_ref}")
        
        # Gate 3: compute artifact hashes
        success, error_code, updated_artifacts = self.compute_artifact_hashes(target_path)
        if not success:
            if error_code in ("MANIFEST_MISSING", "ARTIFACT_MISSING"):
                return (2, f"ERROR: {updated_artifacts if isinstance(updated_artifacts, str) else error_code}")
            return (1, f"ERROR: artifact hash computation failed: {updated_artifacts if isinstance(updated_artifacts, str) else error_code}")
        
        # Load full target manifest for rewrite
        try:
            with open(target_path, "rb") as f:
                raw = f.read()
            target_obj = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError) as exc:
            return (3, f"ERROR: failed to load target manifest: {exc}")
        
        # Update manifest
        target_obj["basis_ref"] = basis_ref
        target_obj["artifacts"] = updated_artifacts
        if not target_obj.get("generated_at"):
            target_obj["generated_at"] = "1970-01-01T00:00:00Z"
        
        # Atomic rewrite
        success, error_code, message = self.atomic_rewrite(target_path, target_obj)
        if not success:
            return (3, f"ERROR: {message}")
        
        return (0, f"OK: basis_ref={basis_ref}; {len(updated_artifacts)} artifact hashes computed")


def main():
    """CLI entry point matching scripts/compute-manifest-sha256.py behavior."""
    repo_root = os.environ.get("BABEL_REPO_ROOT", ".")
    hasher = ManifestHasher(repo_root)
    exit_code, message = hasher.finalize_manifest()
    if exit_code != 0:
        sys.stderr.write(message + "\n")
    else:
        sys.stdout.write(message + "\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
