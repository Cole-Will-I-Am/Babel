"""
Unittest suite for BSSC v0.9.0 reference implementation.

Tests cover:
- State snapshot schema validation (Section 2)
- Unique agent_id constraint (Section 2.2)
- Hash chain pointer validation (Section 3)
- Tier-1 validation: schema, unique agent_id, emission bound,
  seq monotonicity, cross-snapshot seq, hash chain (Section 4)
- Crash recovery fallback with 1024-snapshot cap (Section 5)
- Conformance test vectors from spec

All tests are deterministic, use only Python 3.12 stdlib,
and reuse orchestrator/canonical.py for canonical serialization.
"""

import hashlib
import time
import unittest
from typing import Any, Dict, List

from orchestrator.canonical import canonical_json
from reference.babel.bssc import (
    BSSC_CHAIN_BROKEN,
    BSSC_CROSS_SNAPSHOT_REGRESSION,
    BSSC_DUPLICATE_AGENT,
    BSSC_EMISSION_RATE_EXCEEDED,
    BSSC_HASH_MISMATCH,
    BSSC_SCHEMA_INVALID,
    BSSC_SEQ_REGRESSION,
    MAX_RECOVERY_SNAPSHOTS,
    RecoverySimulator,
    SnapshotValidator,
    compute_snapshot_hash,
    create_genesis_snapshot,
    create_snapshot,
)


class TestSnapshotSchema(unittest.TestCase):
    """Section 2: State Snapshot Schema validation."""
    
    def setUp(self) -> None:
        self.validator = SnapshotValidator()
        self.valid_snapshot = {
            "operation_type": "state_snapshot",
            "ext": {
                "kimi": {
                    "state_snapshot": [
                        [
                            "agent_alpha",
                            {"status": "active", "counter": 42},
                            1,
                            "workflow_abc123"
                        ],
                        [
                            "agent_beta",
                            {"status": "idle"},
                            1,
                            None
                        ]
                    ],
                    "previous_snapshot_sha256": None
                }
            },
            "meta": {
                "author": "gateway_01",
                "emitted_at": "2026-06-06T12:00:00Z"
            }
        }
    
    def test_valid_schema(self) -> None:
        """Valid snapshot schema should pass validation."""
        success, error_code, message = self.validator.validate_snapshot(
            self.valid_snapshot, None, time.time()
        )
        self.assertTrue(success)
        self.assertIsNone(error_code)
        self.assertEqual(message, "ACCEPT")
    
    def test_missing_operation_type(self) -> None:
        """Missing operation_type should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        del snapshot["operation_type"]
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_wrong_operation_type(self) -> None:
        """Wrong operation_type value should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["operation_type"] = "wrong_type"
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_invalid_agent_id_format(self) -> None:
        """Agent ID not matching regex should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["state_snapshot"][0][0] = "invalid agent!@#"
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_agent_id_too_long(self) -> None:
        """Agent ID > 64 chars should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["state_snapshot"][0][0] = "a" * 65
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_invalid_last_seen_seq_type(self) -> None:
        """Non-integer last_seen_seq should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["state_snapshot"][0][2] = "not_an_int"
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_negative_last_seen_seq(self) -> None:
        """Negative last_seen_seq should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["state_snapshot"][0][2] = -1
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_invalid_workflow_id_type(self) -> None:
        """Non-string/non-null workflow_id should fail schema validation."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["state_snapshot"][0][3] = 123
        
        success, error_code, message = self.validator.validate_snapshot(
            snapshot, None, time.time()
        )
        self.assertFalse(success)
        self.assertEqual(error_code, BSSC_SCHEMA_INVALID)
    
    def test_invalid_previous_hash_format(self) -> None:
        """previous_snapshot_sha256 not starting with 'sha256:' should fail."""
        snapshot = self.valid_snapshot.copy()
        snapshot["ext"]["kimi"]["previous_snapshot_sha256"] = "invalid_hash"
        
        success, error_code, message = self.validator.vali