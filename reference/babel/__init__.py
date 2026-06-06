# Babel Reference Implementation
# BWCC v0.9.0 - Canonical Command & Control

"""
Babel BWCC v0.9.0 Reference Implementation

Deterministic workflow validation, content-addressed workflow IDs,
amendment chain acyclicity, and XRP cascade simulation.

All code is Python 3.12 stdlib only. Reuses orchestrator/canonical.py
for v0.2.0 canonical JSON serialization.
"""

from .bwcc import (
    WorkflowValidator,
    AmendmentChainValidator,
    XRPCascadeSimulator,
    compute_workflow_id,
    BWCC_CYCLE,
    BWCC_BAD_REFERENCE,
    BWCC_AMEND_CYCLE,
    BWCC_CHAIN_TOO_LONG,
    BWCC_UPSTREAM_FAIL,
    BWCC_RUNTIME_CYCLE,
    ValidationResult,
    AmendmentChainResult,
    CascadeResult,
)

__version__ = "0.9.0"
__all__ = [
    "WorkflowValidator",
    "AmendmentChainValidator",
    "XRPCascadeSimulator",
    "compute_workflow_id",
    "BWCC_CYCLE",
    "BWCC_BAD_REFERENCE",
    "BWCC_AMEND_CYCLE",
    "BWCC_CHAIN_TOO_LONG",
    "BWCC_UPSTREAM_FAIL",
    "BWCC_RUNTIME_CYCLE",
    "ValidationResult",
    "AmendmentChainResult",
    "CascadeResult",
]
