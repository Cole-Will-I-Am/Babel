"""
BHOP v0.9.0 - Babel Human Override Protocol

Implements:
- human_override schema validation (Section 2)
- Tier-1 dual-authenticity validation (Section 3)
- Action state machine: pause/resume/cancel (Section 4)
- Override hash chain validation (Section 5)
- Agent observation via BCRP scan (Section 7)
- Agent state durability via BSSC ext.kimi.state (Section 8)

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.canonical import canonical_json


# =============================================================================
# Error Codes (Deterministic)
# =============================================================================

class BHOPErrorCode:
    """Deterministic error codes per BHOP v0.9.0 Section 9."""
    AUTH_FAILURE = "BHOP_AUTH_FAILURE"
    INVALID_WORKFLOW = "BHOP_INVALID_WORKFLOW"
    UNKNOWN_WORKFLOW = "BHOP_UNKNOWN_WORKFLOW"
    INVALID_ACTION = "BHOP_INVALID_ACTION"
    CHAIN_BROKEN = "BHOP_CHAIN_BROKEN"
    WORKFLOW_PAUSED = "BHOP_WORKFLOW_PAUSED"
    WORKFLOW_TERMINATED = "BHOP_WORKFLOW_TERMINATED"
    SCHEMA_INVALID = "BHOP_SCHEMA_INVALID"


# =============================================================================
# Workflow States
# =============================================================================

class WorkflowState:
    """Workflow states per BHOP v0.9.0 Section 4."""
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"


# =============================================================================
# Override Actions
# =============================================================================

class OverrideAction:
    """Override actions per BHOP v0.9.0 Section 2."""
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"

    VALID_ACTIONS = {PAUSE, RESUME, CANCEL}


# =============================================================================
# Workflow ID Validation
# =============================================================================

WORKFLOW_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def validate_workflow_id_format(workflow_id: str) -> bool:
    """Validate workflow_id matches ^sha256:[0-9a-f]{64}$ per BWCC v0.9.0."""
    return bool(WORKFLOW_ID_PATTERN.match(workflow_id))


def compute_document_sha256(document: Dict[str, Any]) -> str:
    """Compute canonical SHA-256 of a document per v0.2.0."""
    canonical = canonical_json(document)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# Human Override Validator (Tier-1 Dual-Authenticity)
# =============================================================================

class HumanOverrideValidator:
    """
    Tier-1 dual-authenticity validation for human_override documents.
    
    Per BHOP v0.9.0 Section 3, gateway MUST reject drafts where:
    - meta.author != "human" (exact match)
    - ext.kimi.gateway_agent not in authorized_hig_gateway list
    - target_workflow_id malformed or unknown
    - override_action not in enum
    - previous_override_sha256 chain broken
    """
    
    def __init__(
        self,
        authorized_hig_gateway: List[str],
        workflow_registry: "WorkflowStateManager",
        override_chain_tracker: "OverrideHashChainTracker",
    ):
        """
        Initialize validator with genesis-configured gateway list.
        
        Args:
            authorized_hig_gateway: Immutable list of authorized gateway agents.
            workflow_registry: WorkflowStateManager for existence checks.
            override_chain_tracker: OverrideHashChainTracker for chain validation.
        """
        self.authorized_hig_gateway = set(authorized_hig_gateway)
        self.workflow_registry = workflow_registry
        self.override_chain_tracker = override_chain_tracker
    
    def validate_human_override(
        self,
        document: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], str]:
        """
        Validate a human_override document at tier-1.
        
        Returns:
            (success, error_code, message) tuple.
        """
        # Schema validation
        schema_valid, error_code, message = self._validate_schema(document)
        if not schema_valid:
            return False, error_code, message
        
        # Dual-authenticity: meta.author
        meta = document.get("meta", {})
        if meta.get("author") != "human":
            return False, BHOPErrorCode.AUTH_FAILURE, "meta.author must be exactly 'human'"
        
        # Dual-authenticity: gateway_agent
        ext = document.get("ext", {})
        kimi = ext.get("kimi", {})
        gateway_agent = kimi.get("gateway_agent")
        if gateway_agent not in self.authorized_hig_gateway:
            return False, BHOPErrorCode.AUTH_FAILURE, f"gateway_agent '{gateway_agent}' not authorized"
        
        # Workflow ID validation
        human = ext.get("human", {})
        workflow_id = human.get("target_workflow_id")
        
        if not validate_workflow_id_format(workflow_id):
            return False, BHOPErrorCode.INVALID_WORKFLOW, f"target_workflow_id malformed: {workflow_id}"
        
        # Workflow existence check
        workflow_state = self.workflow_registry.get_workflow_state(workflow_id)
        if workflow_state is None:
            return False, BHOPErrorCode.UNKNOWN_WORKFLOW, f"target_workflow_id not found: {workflow_id}"
        
        # Action validation
        override_action = human.get("override_action")
        if override_action not in OverrideAction.VALID_ACTIONS:
            return False, BHOPErrorCode.INVALID_ACTION, f"invalid override_action: {override_action}"
        
        # Hash chain validation
        previous_sha = kimi.get("previous_override_sha256")
        chain_valid, chain_error = self.override_chain_tracker.validate_