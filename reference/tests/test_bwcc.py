"""
Unittest suite for BWCC v0.9.0 reference implementation.

Tests cover:
- Workflow definition schema validation (Section 2)
- workflow_id computation via canonical JSON SHA-256 (Section 3)
- Tier-1 validation: schema, self-loops, Kahn's algorithm (Section 4)
- Amendment chain acyclicity with 256-ancestor bound (Section 5.2)
- XRP cascade simulation (Section 6)

All tests are deterministic with stable ordering.
"""

import unittest
from typing import Any, Dict, List, Optional

from babel.bwcc import (
    WorkflowValidator,
    AmendmentChainValidator,
    XRPCascadeSimulator,
    compute_workflow_id,
    BWCC_CYCLE,
    BWCC_BAD_REFERENCE,
    BWCC_AMEND_CYCLE,
    BWCC_CHAIN_TOO_LONG,
    BWCC_UPSTREAM_FAIL,
    ValidationResult,
    AmendmentChainResult,
)


class TestWorkflowValidatorSchema(unittest.TestCase):
    """Test schema validation per Section 2 and Section 4 check 1."""

    def setUp(self):
        self.validator = WorkflowValidator()

    def test_valid_minimal_workflow(self):
        """Valid workflow with single task, no dependencies."""
        workflow = {
            "task_ids": ["task_a"],
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertTrue(result.valid)
        self.assertIsNone(result.error_code)

    def test_valid_workflow_with_dependencies(self):
        """Valid workflow with multiple tasks and dependencies."""
        workflow = {
            "task_ids": ["task_a", "task_b", "task_c"],
            "depends_on": {
                "task_b": ["task_a"],
                "task_c": ["task_a", "task_b"],
            },
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertTrue(result.valid)
        self.assertIsNone(result.error_code)

    def test_empty_task_ids_rejected(self):
        """Empty task_ids list must be rejected."""
        workflow = {
            "task_ids": [],
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_missing_task_ids_rejected(self):
        """Missing task_ids field must be rejected."""
        workflow = {
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_duplicate_task_ids_rejected(self):
        """Duplicate task_ids must be rejected."""
        workflow = {
            "task_ids": ["task_a", "task_a"],
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_invalid_task_id_regex(self):
        """Task IDs must match ^[a-zA-Z0-9_.-]{1,64}$."""
        workflow = {
            "task_ids": ["task@a"],  # @ not allowed
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_task_id_too_long(self):
        """Task IDs must be <= 64 characters."""
        workflow = {
            "task_ids": ["a" * 65],
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_task_id_max_length_valid(self):
        """Task IDs can be exactly 64 characters."""
        workflow = {
            "task_ids": ["a" * 64],
            "depends_on": {},
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertTrue(result.valid)

    def test_depends_on_key_not_in_task_ids(self):
        """depends_on keys must be in task_ids."""
        workflow = {
            "task_ids": ["task_a"],
            "depends_on": {
                "task_b": [],  # task_b not in task_ids
            },
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)

    def test_depends_on_value_not_in_task_ids(self):
        """depends_on values must be in task_ids."""
        workflow = {
            "task_ids": ["task_a"],
            "depends_on": {
                "task_a": ["task_b"],  # task_b not in task_ids
            },
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)


class TestWorkflowValidatorSelfLoops(unittest.TestCase):
    """Test self-loop detection per Section 4 check 3."""

    def setUp(self):
        self.validator = WorkflowValidator()

    def test_self_loop_rejected(self):
        """Task cannot depend on itself."""
        workflow = {
            "task_ids": ["task_a"],
            "depends_on": {
                "task_a": ["task_a"],
            },
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertFalse(result.valid)
        self.assertEqual(result.error_code, BWCC_BAD_REFERENCE)
        self.assertIn("self-loop", result.message.lower())

    def test_no_self_loop_valid(self):
        """Task depending on different task is valid."""
        workflow = {
            "task_ids": ["task_a", "task_b"],
            "depends_on": {
                "task_a": ["task_b"],
            },
        }
        result = self.validator.validate_workflow_definition(workflow)
        self.assertTrue(result.valid)


class TestWorkflowValidatorAcyclicity(unittest.TestCase):
    """Test cycle detection via Kahn's algorithm per Section 4 check 2."""

    def 