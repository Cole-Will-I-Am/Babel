"""Babel v0.10.3 Manifest Basis Reference Computation.

Implements basis_ref hash computation for manifest chain validation.
Reuses orchestrator/canonical.py for v0.2.0 canonical JSON serialization.

Exports:
- ManifestError: exception class with code, version, path attributes
- compute_basis_ref(manifest_path: Path) -> str: compute predecessor hash
- MANIFEST_BASIS_MISMATCH: error code for hash mismatch
- MANIFEST_INVALID_BASIS_REF: error code for malformed basis_ref
- MANIFEST_MISSING_PREDECESSOR: error code for missing predecessor manifest
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.canonical import canonical_json, canonical_sha256


# Error codes per manifest validation spec
MANIFEST_BASIS_MISMATCH = "MANIFEST_BASIS_MISMATCH"
MANIFEST_INVALID_BASIS_REF = "MANIFEST_INVALID_BASIS_REF"
MANIFEST_MISSING_PREDECESSOR = "MANIFEST_MISSING_PREDECESSOR"

# Regex pattern for basis_ref: sha256:[0-9a-f]{64}
BASIS_REF_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ManifestError(Exception):
    """Structured manifest error with deterministic JSON output."""

    def __init__(
        self,
        code: str,
        version: str,
        path: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
    ):
        self.code = code
        self.version = version
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(code)

    def to_json(self) -> str:
        """Return deterministic JSON error object."""
        return json.dumps(
            {
                "code": self.code,
                "version": self.version,
                "path": self.path,
                "expected": self.expected,
                "actual": self.actual,
            },
            sort_keys=True,
            indent=2,
        )


def compute_basis_ref(manifest_path: Path) -> str:
    """
    Compute the basis_ref (predecessor hash) for a manifest.

    Loads the manifest at manifest_path, extracts basis_target,
    computes canonical_sha256 of the predecessor manifest, and returns
    the computed hash.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        The computed SHA-256 hash of the predecessor manifest.

    Raises:
        ManifestError: On validation failure (missing predecessor,
            invalid basis_ref format, hash mismatch).
        FileNotFoundError: If manifest_path does not exist.
    """
    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    version = manifest.get("version", "unknown")
    basis_ref = manifest.get("basis_ref")
    basis_target = manifest.get("basis_target")

    # Genesis (v0.1.0) has no basis_ref
    if basis_ref is None:
        if version == "v0.1.0":
            # Genesis is valid with null basis_ref
            return ""
        else:
            # Non-genesis without basis_ref is invalid
            raise ManifestError(
                code=MANIFEST_INVALID_BASIS_REF,
                version=version,
                path=str(manifest_path),
                expected="sha256:[0-9a-f]{64}",
                actual="null/missing",
            )

    # Validate basis_ref format
    if not BASIS_REF_PATTERN.match(basis_ref):
        raise ManifestError(
            code=MANIFEST_INVALID_BASIS_REF,
            version=version,
            path=str(manifest_path),
            expected="sha256:[0-9a-f]{64}",
            actual=basis_ref,
        )

    # Check predecessor exists
    if not basis_target:
        raise ManifestError(
            code=MANIFEST_MISSING_PREDECESSOR,
            version=version,
            path=str(manifest_path),
            expected="basis_target present",
            actual="null/missing",
        )

    # Compute predecessor path
    base_dir = manifest_path.parent
    predecessor_path = base_dir / f"babel-manifest-{basis_target}.json"

    if not predecessor_path.exists():
        raise ManifestError(
            code=MANIFEST_MISSING_PREDECESSOR,
            version=version,
            path=str(predecessor_path),
        )

    # Compute hash using Path object (not string)
    computed_hash = canonical_sha256(predecessor_path)

    # Verify hash matches basis_ref
    if computed_hash != basis_ref:
        raise ManifestError(
            code=MANIFEST_BASIS_MISMATCH,
            version=version,
            path=str(manifest_path),
            expected=basis_ref,
            actual=computed_hash,
        )

    return computed_hash


def validate_manifest_chain(
    start_path: Path, base_dir: Optional[Path] = None
) -> bool:
    """
    Validate an entire manifest chain from start_path back to genesis.

    Args:
        start_path: Path to the starting manifest.
        base_dir: Base directory for manifest discovery (defaults to start_path.parent).

    Returns:
        True if chain is valid.

    Raises:
        ManifestError: On any validation failure.
    """
    if base_dir is None:
        base_dir = start_path.parent

    current_path = start_path
    visited: set[str] = set()

    while True:
        # Prevent infinite loops
        current_str = str(current_path)
        if current_str in visited:
            raise ManifestError(
                code=MANIFEST_INVALID_BASIS_REF,
                version="unknown",
                path=current_str,
                expected="acyclic chain",
                actual="cycle detected",
            )
        visited.add(current_str)

        # Load and validate
        with open(current_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        version = manifest.get("version", "unknown")
        basis_ref = manifest.get("basis_ref")
        basis_target = manifest.get("basis_target")

        # Genesis check
        if basis_ref is None:
            if version != "v0.1.0":
                raise ManifestError(
                    code=MANIFEST_INVALID_BASIS_REF,
                    version=version,
                    path=str(current_path),
                    expected="sha256:[0-9a-f]{64}",
                    actual="null/missing",
                )
            # Valid genesis
            return True

        # Compute and verify hash
        compute_basis_ref(current_path)

        # Move to predecessor
        if not basis_target:
            raise ManifestError(
                code=MANIFEST_MISSING_PREDECESSOR,
                version=version,
                path=str(current_path),
            )

        current_path = base_dir / f"babel-manifest-{basis_target}.json"

        if not current_path.exists():
            raise ManifestError(
                code=MANIFEST_MISSING_PREDECESSOR,
                version=version,
                path=str(current_path),
            )
