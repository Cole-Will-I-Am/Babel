"""
Babel v0.10.3 Spec-Index Bootstrap Reference Implementation

Implements the recursive basis_ref traversal procedure from v0.9.0 manifest
back to v0.1.0 genesis, aggregating canonical_sha256 values from every
historical manifest entry, with deterministic gap detection.

Exit codes:
  0 = success, bootstrap JSON written to stdout
  1 = gap detection failure (structured JSON error on stderr)

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical serialization.
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from orchestrator.canonical import canonical_json, canonical_sha256


# Error codes per spec Section 4
BOOTSTRAP_MISSING_MANIFEST = "BOOTSTRAP_MISSING_MANIFEST"
BOOTSTRAP_PLACEHOLDER_HASH = "BOOTSTRAP_PLACEHOLDER_HASH"
BOOTSTRAP_INVALID_BASIS_REF = "BOOTSTRAP_INVALID_BASIS_REF"
BOOTSTRAP_BASIS_MISMATCH = "BOOTSTRAP_BASIS_MISMATCH"
BOOTSTRAP_GENESIS_HAS_BASIS = "BOOTSTRAP_GENESIS_HAS_BASIS"
BOOTSTRAP_BAD_PATH = "BOOTSTRAP_BAD_PATH"
BOOTSTRAP_DUPLICATE_KEY = "BOOTSTRAP_DUPLICATE_KEY"

# Regex patterns per spec
BASIS_REF_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
VERSION_PATTERN = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
PATH_PATTERN = re.compile(r"^(autonomy-output|scripts)/[^/]+(?:/[^/]+)*$")
PLACEHOLDER_PATTERNS = [
    r"^sha256:PENDING",
    r"^$",
]


class BootstrapError(Exception):
    """Structured bootstrap error with deterministic JSON output."""

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


def _parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semver version string to tuple (major, minor, patch)."""
    match = VERSION_PATTERN.match(version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _compute_predecessor_version(
    current_version: str, available_versions: List[str]
) -> Optional[str]:
    """
    Compute the semver predecessor of current_version.

    Per spec Section 2.3: V_pred is the highest version < V with the same
    major version. Pre-release tags are NOT used in Babel versioning.
    """
    current_tuple = _parse_version(current_version)
    candidates = []

    for v in available_versions:
        try:
            v_tuple = _parse_version(v)
            if v_tuple[0] == current_tuple[0] and v_tuple < current_tuple:
                candidates.append(v)
        except ValueError:
            continue

    if not candidates:
        return None

    # Return highest version < current
    candidates.sort(key=_parse_version, reverse=True)
    return candidates[0]


def _is_placeholder_hash(hash_value: str) -> bool:
    """Check if hash is a placeholder per spec Section 3."""
    if not hash_value:
        return True
    for pattern in PLACEHOLDER_PATTERNS:
        if re.match(pattern, hash_value):
            return True
    return False


def _validate_path(path: str) -> bool:
    """
    Validate artifact path per spec Section 3.

    Must be relative POSIX path: no leading '/', no backslashes,
    no '..' segments, first segment is 'autonomy-output/' or 'scripts/'.
    """
    if not path:
        return False
    if path.startswith("/"):
        return False
    if "\\" in path:
        return False
    if ".." in path.split("/"):
        return False
    return bool(PATH_PATTERN.match(path))


class SpecIndexBootstrap:
    """
    Babel v0.10.3 Spec-Index Bootstrap Procedure.

    Recursively traverses manifest chain from v0.9.0 back to v0.1.0,
    aggregating canonical_sha256 values and detecting gaps.
    """

    def __init__(self, base_path: str = "autonomy-output"):
        self.base_path = Path(base_path)
        self._version_cache: Dict[str, Dict[str, Any]] = {}
        self._available_versions: List[str] = []

    def _load_manifest(self, version: str) -> Dict[str, Any]:
        """Load manifest from disk, caching result."""
        if version in self._version_cache:
            return self._version_cache[version]

        manifest_path = self.base_path / f"babel-manifest-{version}.json"
        if not manifest_path.exists():
            raise BootstrapError(
                code=BOOTSTRAP_MISSING_MANIFEST,
                version=version,
                path=str(manifest_path),
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise BootstrapError(
                code=BOOTSTRAP_MISSING_MANIFEST,
                version=version,
                path=str(manifest_path),
                expected="valid JSON",
                actual=f"JSON parse error: {e}",
            )

        self._version_cache[version] = data
        return data

    def _discover_versions(self, start_version: str) -> List[str]:
        """
        Discover all versions in the chain from start_version to genesis.

        Returns list of versions in descending order [v0.9.0, v0.8.1, ..., v0.1.0].
        """
        versions = [start_version]
        current = start_version

        while True:
            manifest = self._load_manifest(current)
            basis_target = manifest.get("basis_target")

            if basis_target is None:
                # Genesis reached
                break

            versions.append(basis_target)
            current = basis_target

        return versions

    def _verify_basis_chain(self, versions: List[str]) -> None:
        """
        Verify basis_ref chain integrity per spec Section 2.2.

        For each manifest M at version V with basis_ref B and basis_target T:
        1. Verify B is well-formed (sha256:hex64)
        2. Verify T exists on disk
        3. Compute hash of T via v0.2.0 canonicalization
        4. Verify computed hash equals B
        5. Termination: v0.1.0 must have null basis_ref
        """
        for i, version in enumerate(versions):
            manifest = self._load_manifest(version)
            basis_ref = manifest.get("basis_ref")
            basis_target = manifest.get("basis_target")

            # Check genesis termination
            if version == "v0.1.0":
                if basis_ref is not None:
                    raise BootstrapError(
                        code=BOOTSTRAP_GENESIS_HAS_BASIS,
                        version=version,
                        expected="null",
                        actual=basis_ref,
                    )
                if basis_target is not None:
                    raise BootstrapError(
                        code=BOOTSTRAP_GENESIS_HAS_BASIS,
                        version=version,
                        expected="absent",
                        actual=basis_target,
                    )
                continue

            # Verify basis_ref format
            if not basis_ref or not BASIS_REF_PATTERN.match(basis_ref):
                raise BootstrapError(
                    code=BOOTSTRAP_INVALID_BASIS_REF,
                    version=version,
                    expected="sha256:[0-9a-f]{64}",
                    actual=basis_ref,
                )

            # Verify basis_target exists
            if not basis_target:
                raise BootstrapError(
                    code=BOOTSTRAP_MISSING_MANIFEST,
                    version=version,
                    expected="basis_target present",
                    actual="null/missing",
                )

            if basis_target not in versions:
                raise BootstrapError(
                    code=BOOTSTRAP_MISSING_MANIFEST,
                    version=version,
                    path=f"autonomy-output/babel-manifest-{basis_target}.json",
                )

            # Compute hash of predecessor manifest
            predecessor_path = self.base_path / f"babel-manifest-{basis_target}.json"
            computed_hash = canonical_sha256(predecessor_path)
            expected_hash = basis_ref

            if computed_hash != expected_hash:
                raise BootstrapError(
                    code=BOOTSTRAP_BASIS_MISMATCH,
                    version=version,
                    expected=expected_hash,
                    actual=computed_hash,
                )

    def _aggregate_artifacts(
        self, versions: List[str]
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Aggregate artifact entries from all manifests per spec Section 3.

        Returns (seed_entries, manifest_entries) where:
        - seed_entries: one tuple per artifact in artifacts[]
        - manifest_entries: one tuple per manifest itself
        """
        seed_entries: List[Dict[str, str]] = []
        manifest_entries: List[Dict[str, str]] = []
        seen_keys: Set[Tuple[str, str]] = set()

        for version in versions:
            manifest = self._load_manifest(version)

            # Add manifest entry
            manifest_path = f"autonomy-output/babel-manifest-{version}.json"
            manifest_hash = manifest.get("canonical_sha256")

            if _is_placeholder_hash(manifest_hash):
                raise BootstrapError(
                    code=BOOTSTRAP_PLACEHOLDER_HASH,
                    version=version,
                    path=manifest_path,
                )

            manifest_entry = {
                "version": version,
                "type": "manifest",
                "path": manifest_path,
                "canonical_sha256": manifest_hash,
            }
            manifest_entries.append(manifest_entry)

            # Check for duplicate manifest key
            manifest_key = (version, "manifest")
            if manifest_key in seen_keys:
                raise BootstrapError(
                    code=BOOTSTRAP_DUPLICATE_KEY,
                    version=version,
                    path=manifest_path,
                )
            seen_keys.add(manifest_key)

            # Process artifacts[]
            artifacts = manifest.get("artifacts", [])
            for artifact in artifacts:
                artifact_type = artifact.get("type")
                artifact_path = artifact.get("path")
                artifact_hash = artifact.get("canonical_sha256")

                # Validate hash
                if _is_placeholder_hash(artifact_hash):
                    raise BootstrapError(
                        code=BOOTSTRAP_PLACEHOLDER_HASH,
                        version=version,
                        path=artifact_path,
                    )

                # Validate path
                if not _validate_path(artifact_path):
                    raise BootstrapError(
                        code=BOOTSTRAP_BAD_PATH,
                        version=version,
                        path=artifact_path,
                    )

                # Check for duplicate key
                artifact_key = (version, artifact_type)
                if artifact_key in seen_keys:
                    raise BootstrapError(
                        code=BOOTSTRAP_DUPLICATE_KEY,
                        version=version,
                        path=artifact_path,
                    )
                seen_keys.add(artifact_key)

                seed_entry = {
                    "version": version,
                    "type": artifact_type,
                    "path": artifact_path,
                    "canonical_sha256": artifact_hash,
                }
                seed_entries.append(seed_entry)

        return seed_entries, manifest_entries

    def run(self, start_version: str = "v0.9.0") -> str:
        """
        Execute the bootstrap procedure per spec Section 1-5.

        Returns deterministic JSON output to stdout.
        """
        # Discover version chain
        versions = self._discover_versions(start_version)

        # Verify basis_ref chain integrity
        self._verify_basis_chain(versions)

        # Aggregate artifacts
        seed_entries, manifest_entries = self._aggregate_artifacts(versions)

        # Compute frozen_base hash
        frozen_base_path = self.base_path / f"babel-manifest-{start_version}.json"
        frozen_base_hash = canonical_sha256(frozen_base_path)

        # Build output per spec Section 5
        output = {
            "bootstrap_version": "v0.10.3",
            "generated_by": "babel-spec-index-bootstrap-v0.10.3",
            "frozen_base": {
                "version": start_version,
                "path": f"autonomy-output/babel-manifest-{start_version}.json",
                "canonical_sha256": frozen_base_hash,
            },
            "seed_entries": seed_entries,
            "manifest_entries": manifest_entries,
        }

        return json.dumps(output, sort_keys=True, indent=2) + "\n"


def main() -> int:
    """CLI entry point for bootstrap procedure."""
    try:
        bootstrap = SpecIndexBootstrap()
        output = bootstrap.run()
        sys.stdout.write(output)
        return 0
    except BootstrapError as e:
        sys.stderr.write(e.to_json() + "\n")
        return 1
    except Exception as e:
        sys.stderr.write(
            json.dumps({"code": "BOOTSTRAP_INTERNAL_ERROR", "message": str(e)})
            + "\n"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
