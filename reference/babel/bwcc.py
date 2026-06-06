"""
BWCC v0.9.0 - Babel Canonical Command & Control

Implements:
- Workflow definition schema validation (Section 2)
- workflow_id computation via canonical JSON SHA-256 (Section 3)
- Tier-1 validation: schema check, Kahn's algorithm cycle detection,
  self-loop detection (Section 4)
- workflow_amend operation with non-retroactivity (Section 5)
- Amendment chain acyclicity with 256-ancestor DOS bound (Section 5.2)
- Workflow-level XRP cascade simulation (Section 6)

All validation is deterministic with stable ordering and byte-exact outputs.
"""

import hashlib
import re
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

# Import canonical serializer from orchestrator (v0.2.0)
import sys
from pathlib import Path

# Add orchestrator to path for canonical import
_orchestrator_path = Path(__file__).parent.parent.parent / "orchestrator"
if _orchestrator_path.exists() and _orchestrator_path not in sys.path:
    sys.path.insert(0, str(_orchestrator_path.parent))

from orchestrator.canonical import canonical_json


# Error codes (Section 4, 5.2, 6)
BWCC_CYCLE = "BWCC_CYCLE"
BWCC_BAD_REFERENCE = "BWCC_BAD_REFERENCE"
BWCC_AMEND_CYCLE = "BWCC_AMEND_CYCLE"
BWCC_CHAIN_TOO_LONG = "BWCC_CHAIN_TOO_LONG"
BWCC_UPSTREAM_FAIL = "BWCC_UPSTREAM_FAIL"
BWCC_RUNTIME_CYCLE = "BWCC_RUNTIME_CYCLE"

# Constants
TASK_ID_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")
MAX_AMENDMENT_CHAIN_LENGTH = 256


@dataclass
class ValidationResult:
    """Result of workflow definition validation."""

    valid: bool
    error_code: Optional[str] = None
    message: str = ""


@dataclass
class AmendmentChainResult:
    """Result of amendment chain validation."""

    valid: bool
    error_code: Optional[str] = None
    message: str = ""
    ancestor_count: int = 0


@dataclass
class CascadeResult:
    """Result of XRP cascade simulation."""

    task_id: str
    status: str  # "completed", "cancelled", "failed"
    error_code: Optional[str] = None
    executed: bool = True


class WorkflowValidator:
    """
    Tier-1 validation for workflow_definition per BWCC v0.9.0 Section 4.

    Validates:
    1. Schema check: task_ids non-empty, unique, regex match; depends_on
       keys/values subset of task_ids (O(n+e) via hash-set)
    2. No self-loops: task t must not appear in depends_on[t]
    3. Acyclicity: Kahn's algorithm O(n+e)
    """

    def __init__(self):
        self.task_id_regex = TASK_ID_REGEX

    def validate_workflow_definition(
        self, workflow_definition: Dict[str, Any]
    ) -> ValidationResult:
        """
        Perform tier-1 validation on workflow_definition.

        Returns ValidationResult with valid=True if all checks pass,
        or valid=False with appropriate error_code and message.
        """
        # Check 1: Schema validation
        schema_result = self._validate_schema(workflow_definition)
        if not schema_result.valid:
            return schema_result

        task_ids = workflow_definition["task_ids"]
        depends_on = workflow_definition["depends_on"]

        # Check 2: No self-loops (Section 4, check 3)
        self_loop_result = self._check_self_loops(task_ids, depends_on)
        if not self_loop_result.valid:
            return self_loop_result

        # Check 3: Acyclicity via Kahn's algorithm (Section 4, check 2)
        acyclic_result = self._check_acyclicity(task_ids, depends_on)
        if not acyclic_result.valid:
            return acyclic_result

        return ValidationResult(valid=True)

    def _validate_schema(
        self, workflow_definition: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate workflow_definition schema per Section 2.

        Checks:
        - task_ids: non-empty, unique, all match regex ^[a-zA-Z0-9_.-]{1,64}$
        - depends_on: object<string,string[]>, all keys/values in task_ids
        """
        # Check task_ids exists and is non-empty list
        if "task_ids" not in workflow_definition:
            return ValidationResult(
                valid=False,
                error_code=BWCC_BAD_REFERENCE,
                message="Missing required field: task_ids",
            )

        task_ids = workflow_definition["task_ids"]
        if not isinstance(task_ids, list) or len(task_ids) == 0:
            return ValidationResult(
                valid=False,
                error_code=BWCC_BAD_REFERENCE,
                message="task_ids must be non-empty list",
            )

        # Check uniqueness
        if len(task_ids) != len(set(task_ids)):
            return ValidationResult(
                valid=False,
                error_code=BWCC_BAD_REFERENCE,
                message="task_ids contains duplicates",
            )

        # Check regex match for all task_ids
        for task_id in task_ids:
            if not isinstance(task_id, str):
                return ValidationResult(
                    valid=False,
                    error_code=BWCC_BAD_REFERENCE,
                    message=f"task_id must be string, got {type(task_id).__name__}",
                )
            if not self.task_id_regex.match(task_id):
                return ValidationResult(
                    valid=False,
                    error_code=BWCC_BAD_REFERENCE,
                    message=f"task_id '{task_id}' does not match regex ^[a-zA-Z0-9_.-]{{1,64}}$",
                )

        # Check depends_on exists and is dict
        if "depends_on" not in workflow_definition:
            return ValidationResult(
                valid=False,
                error_code=BWCC_BAD_REFERENCE,
                message="Missing required field: depends_on",
            )

        depends_on = workflow_definition["depends_on"]
        if not isinstance(depends_on, dict):
            return ValidationResult(
                valid=False,
                error_code=BWCC_BAD_REFERENCE,
                message="depends_on must be object",
            )

        # Build hash-set for