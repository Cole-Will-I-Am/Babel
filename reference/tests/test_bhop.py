"""
Unittest suite for BHOP v0.9.0 reference implementation.

Tests cover:
- human_override schema validation (Section 2)
- Tier-1 dual-authenticity validation (Section 3)
- Action state machine: pause/resume/cancel (Section 4)
- Override hash chain validation (Section 5)
- Gateway enforcement (BHOP_WORKFLOW_PAUSED, BHOP_WORKFLOW_TERMINATED)
- Agent re-check for pause prevention
- BCRP-based observation simulation (Section 7)
- Agent state durability (Section 8)
- XRP cancel cascade simulation (Section 4.3)

All tests use Python 3.12 stdlib unittest only.
"""

import unittest
from typing import Any, Dict, List

from reference.babel.bhop import (
    BHOPErrorCode,
    BHOPGateway,
    HumanOverrideValidator,
    OverrideHashChainTracker,
    WorkflowStateManager,
    WorkflowState,
    OverrideAction,
    AgentOverrideObserver,
    XRPCascadeSimulator,
    validate_workflow_id_format,
    compute_document_sha256,
)


# =============================================================================
# Test Helpers
# =============================================================================

def make_human_override(
    workflow_id: str,
    action: str,
    gateway_agent: str = "hig-gateway-prod-01",
    previous_sha: Any = None,
    author: str = "human",
) -> Dict[str, Any]:
    """Create a valid human_override document template."""
    return {
        "operation_type": "human_override",
        "meta": {
            "author": author,
            "created_at": "2026-06-06T22:00:00Z",
        },
        "ext": {
            "human": {
                "override_action": action,
                "target_workflow_id": workflow_id,
            },
            "kimi": {
                "gateway_agent": gateway_agent,
                "previous_override_sha256": previous_sha,
            },
        },
    }


def make_valid_workflow_id() -> str:
    """Generate a valid workflow_id for testing."""
    return "sha256:" + "a" * 64


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSchemaValidation(unittest.TestCase):
    """Test human_override schema validation per Section 2."""
    
    def setUp(self):
        self.workflow_manager = WorkflowStateManager()
        self.chain_tracker = OverrideHashChainTracker()
        self.validator = HumanOverrideValidator(
            authorized_hig_gateway=["hig-gateway-prod-01"],
            workflow_registry=self.workflow_manager,
            override_chain_tracker=self.chain_tracker,
        )
        self.workflow_id = make_valid_workflow_id()
        self.workflow_manager.register_workflow(self.workflow_id)
    
    def test_valid_schema(self):
        """Test valid human_override schema passes validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertTrue(valid)
        self.assertIsNone(error_code)
    
    def test_missing_operation_type(self):
        """Test missing operation_type fails schema validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        del doc["operation_type"]
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertFalse(valid)
        self.assertEqual(error_code, BHOPErrorCode.SCHEMA_INVALID)
    
    def test_wrong_operation_type(self):
        """Test wrong operation_type fails schema validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        doc["operation_type"] = "task_delegation"
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertFalse(valid)
        self.assertEqual(error_code, BHOPErrorCode.SCHEMA_INVALID)
    
    def test_missing_meta_created_at(self):
        """Test missing meta.created_at fails schema validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        del doc["meta"]["created_at"]
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertFalse(valid)
        self.assertEqual(error_code, BHOPErrorCode.SCHEMA_INVALID)
    
    def test_missing_ext_human_action(self):
        """Test missing ext.human.override_action fails schema validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        del doc["ext"]["human"]["override_action"]
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertFalse(valid)
        self.assertEqual(error_code, BHOPErrorCode.SCHEMA_INVALID)
    
    def test_missing_ext_kimi_gateway(self):
        """Test missing ext.kimi.gateway_agent fails schema validation."""
        doc = make_human_override(self.workflow_id, OverrideAction.PAUSE)
        del doc["ext"]["kimi"]["gateway_agent"]
        valid, error_code, message = self.validator.validate_human_override(doc)
        self.assertFalse(valid)
        self.assertEqual(error_code, BHOPErrorCode.SCHEMA_INVALID)


# =============================================================================
# Dual-Authenticity Tests
# =============================================================================

class TestDualAuthenticity(unittest.TestCase):
    """Test tier-1 dual-authenticity validation per Section 3."""
    
    def setUp(self):
        self.workflow_manager = WorkflowStateManager()
        self.chain_tracker = OverrideHashChainTracker()
        self.validator = HumanOverrideValidator(
            authorized_hig_gateway=["hig-gateway-prod-01", "hig-gateway-prod-02"],
            workflow_registry=self.workflow_manager,
            override_chain_tracker=self.chain_tracker,
        )
        self.workflow_id = make_valid_workflow_id()
        self.workflow_manager.register_workflow(self.workflow_id)
    
    def test_author_not_human(self):
 