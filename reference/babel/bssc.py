"""
BSSC v0.9.0 - Babel Snapshot State Continuity

Implements:
- State snapshot schema validation (Section 2)
- Unique agent_id constraint (Section 2.2)
- Hash chain pointer validation (Section 3)
- Tier-1 validation: schema, unique agent_id, emission bound,
  seq monotonicity, cross-snapshot seq, hash chain (Section 4)
- Crash recovery fallback with 1024-snapshot cap (Section 5)

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.canonical import canonical_json


# =============================================================================
# Error Codes (Section 4, 5)
# =============================================================================

BSSC_SCHEMA_INVALID = "BSSC_SCHEMA_INVALID"
BSSC_DUPLICATE_AGENT = "BSSC_DUPLICATE_AGENT"
BSSC_EMISSION_RATE_EXCEEDED = "BSSC_EMISSION_RATE_EXCEEDED"
BSSC_SEQ_REGRESSION = "BSSC_SEQ_REGRESSION"
BSSC_CROSS_SNAPSHOT_REGRESSION = "BSSC_CROSS_SNAPSHOT_REGRESSION"
BSSC_HASH_MISMATCH = "BSSC_HASH_MISMATCH"
BSSC_CHAIN_BROKEN = "BSSC_CHAIN_BROKEN"


# =============================================================================
# Constants
# =============================================================================

AGENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")
MAX_RECOVERY_SNAPSHOTS = 1024  # Section 5.1
DEFAULT_DTL_HEARTBEAT_INTERVAL = 30.0  # Section 4.3


# =============================================================================
# Types
# =============================================================================

SnapshotTuple = Tuple[str, Dict[str, Any], int, Optional[str]]
ValidationResult = Tuple[bool, Optional[str], str]


# =============================================================================
# Snapshot Validator
# =============================================================================

class SnapshotValidator:
    """
    Tier-1 validator for BSSC v0.9.0 state_snapshot documents.
    
    Maintains per-agent state for emission bound and seq monotonicity checks.
    """
    
    def __init__(
        self,
        dtl_heartbeat_interval: float = DEFAULT_DTL_HEARTBEAT_INTERVAL
    ) -> None:
        """
        Initialize validator with configurable DTL heartbeat interval.
        
        Args:
            dtl_heartbeat_interval: Seconds between allowed snapshot emissions
                                   per agent (default 30s per spec).
        """
        self.dtl_heartbeat_interval = dtl_heartbeat_interval
        self._last_emit_timestamp: Dict[str, float] = {}
        self._last_seq_per_agent: Dict[str, int] = {}
    
    def validate_snapshot(
        self,
        snapshot: Dict[str, Any],
        prior_snapshot_doc: Optional[Dict[str, Any]],
        current_timestamp: float
    ) -> ValidationResult:
        """
        Perform all tier-1 validation checks on a state_snapshot document.
        
        Args:
            snapshot: The snapshot document to validate.
            prior_snapshot_doc: The immediate prior snapshot document (for
                               hash chain and cross-snapshot seq checks).
                               None for genesis snapshot.
            current_timestamp: Unix timestamp of this submission.
        
        Returns:
            Tuple of (success, error_code, message). On success,
            error_code is None and message is "ACCEPT".
        """
        # 4.1 Schema Validation
        result = self._validate_schema(snapshot)
        if not result[0]:
            return result
        
        # 4.2 Unique agent_id Check
        result = self._validate_unique_agent_ids(snapshot)
        if not result[0]:
            return result
        
        # 4.3 Time-Based Emission Bound
        result = self._validate_emission_bound(snapshot, current_timestamp)
        if not result[0]:
            return result
        
        # 4.4 Seq Monotonicity Check
        result = self._validate_seq_monotonicity(snapshot)
        if not result[0]:
            return result
        
        # 4.5 Per-Agent Cross-Snapshot Seq Check
        if prior_snapshot_doc is not None:
            result = self._validate_cross_snapshot_seq(snapshot, prior_snapshot_doc)
            if not result[0]:
                return result
        
        # 4.6 Hash Chain Validation
        if prior_snapshot_doc is not None:
            result = self._validate_hash_chain(snapshot, prior_snapshot_doc)
            if not result[0]:
                return result
        
        # Update internal state on acceptance
        self._update_state(snapshot, current_timestamp)
        
        return (True, None, "ACCEPT")
    
    def _validate_schema(self, snapshot: Dict[str, Any]) -> ValidationResult:
        """Section 4.1: Validate snapshot document schema."""
        # Check required top-level fields
        if not isinstance(snapshot, dict):
            return (False, BSSC_SCHEMA_INVALID, "snapshot must be a JSON object")
        
        if "operation_type" not in snapshot:
            return (False, BSSC_SCHEMA_INVALID, "missing operation_type")
        
        if snapshot["operation_type"] != "state_snapshot":
            return (False, BSSC_SCHEMA_INVALID, "operation_type must be 'state_snapshot'")
        
        if "ext" not in snapshot or not isinstance(snapshot["ext"], dict):
            return (False, BSSC_SCHEMA_INVALID, "missing or invalid ext")
        
        if "kimi" not in snapshot["ext"] or not isinstance(snapshot["ext"]["kimi"], dict):
            return (False, BSSC_SCHEMA_INVALID, "missing or invalid ext.kimi")
        
        kimi = snapshot["ext"]["kimi"]
        
        if "state_snapshot" not in kimi:
            return (False, BSSC_SCHEMA_INVALID, "missing ext.kimi.state_snapshot")
        
        state_snapshot = kimi["state_snapshot"]
        if not isinstance(state_snapshot, list):
            return (Fal