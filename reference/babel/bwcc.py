"""
Babel Canonical Command & Control (BWCC) v0.9.0 Reference Implementation.

This module implements workflow validation, amendment chain validation,
and XRP cascade simulation per the BWCC v0.9.0 specification.

Exports:
    WorkflowValidator, AmendmentChainValidator, XRPCascadeSimulator,
    compute_workflow_id,
    BWCC_CYCLE, BWCC_BAD_REFERENCE, BWCC_AMEND_CYCLE, BWCC_CHAIN_TOO_LONG,
    BWCC_UPSTREAM_FAIL, BWCC_RUNTIME_CYCLE,
    ValidationResult, AmendmentChainResult, CascadeResult
"""

from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from orchestrator.canonical import canonical_json


# =============================================================================
# Error Code Constants (string constants as per spec)
# =============================================================================

BWCC_CYCLE = "BWCC_CYCLE"
BWCC_BAD_REFERENCE = "BWCC_BAD_REFERENCE"
BWCC_AMEND_CYCLE = "BWCC_AMEND_CYCLE"
BWCC_CHAIN_TOO_LONG = "BWCC_CHAIN_TOO_LONG"
BWCC_UPSTREAM_FAIL = "BWCC_UPSTREAM_FAIL"
BWCC_RUNTIME_CYCLE = "BWCC_RUNTIME_CYCLE"

# Amendment chain length limit (DOS bound per spec Section 5.2)
BWCC_MAX_ANCESTORS = 256

# Task ID regex pattern per spec Section 2
TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


# =============================================================================
# Result Dataclasses
# =============================================================================

@dataclass
class ValidationResult:
    """
    Result of workflow definition validation (Tier-1).
    
    Attributes:
        ok: True if all validation checks passed.
        error_code: One of BWCC_* constants if ok=False, None otherwise.
        error_message: Human-readable error description if ok=False.
        valid_task_order: Topological order of tasks if ok=True (from Kahn's).
    """
    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    valid_task_order: list[str] | None = None


@dataclass
class AmendmentChainResult:
    """
    Result of amendment chain validation (Section 5.2).
    
    Attributes:
        ok: True if chain is valid (no cycle, within length limit).
        error_code: BWCC_AMEND_CYCLE or BWCC_CHAIN_TOO_LONG if ok=False.
        error_message: Human-readable error description if ok=False.
        chain_length: Number of workflows in the chain (including current).
        ancestor_ids: List of workflow_ids from current to oldest ancestor.
    """
    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    chain_length: int = 0
    ancestor_ids: list[str] = field(default_factory=list)


@dataclass
class CascadeResult:
    """
    Result of XRP cascade simulation (Section 6).
    
    Attributes:
        ok: True if cascade completed without runtime cycle.
        error_code: BWCC_RUNTIME_CYCLE if ok=False.
        error_message: Human-readable error description if ok=False.
        task_results: Final status of all tasks after cascade propagation.
    """
    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    task_results: dict[str, dict[str, Any]] = field(default_factory=dict)


# =============================================================================
# Workflow ID Computation
# =============================================================================

def compute_workflow_id(workflow_definition: dict) -> str:
    """
    Compute the content-addressed workflow_id from a workflow definition.
    
    Per spec Section 3:
    - Serialize workflow_definition using v0.2.0 canonical JSON
      (NFC Unicode, sorted keys, deterministic numbers, single LF terminator)
    - Compute SHA-256 hash of the canonical bytes
    - Return "sha256:" + hex digest
    
    Args:
        workflow_definition: Dict with "task_ids" and "depends_on" keys.
    
    Returns:
        String of form "sha256:<64-char-hex-digest>"
    """
    canonical_text = canonical_json(workflow_definition)
    canonical_bytes = canonical_text.encode("utf-8")
    sha256_hash = hashlib.sha256(canonical_bytes).hexdigest()
    return f"sha256:{sha256_hash}"


# =============================================================================
# WorkflowValidator - Tier-1 Validation
# =============================================================================

class WorkflowValidator:
    """
    Validates workflow definitions per BWCC v0.9.0 Tier-1 validation rules.
    
    Implements Section 4 checks:
    1. Schema validation (task_ids format, uniqueness, depends_on subset)
    2. Self-loop detection (BWCC_BAD_REFERENCE)
    3. Acyclicity via Kahn's algorithm (BWCC_CYCLE)
    
    Usage:
        validator = WorkflowValidator(workflow_definition)
        result = validator.validate()
        if result.ok:
            # workflow is valid, result.valid_task_order has topological sort
    """
    
    def __init__(self, workflow_definition: dict):
        """
        Initialize validator with a workflow definition.
        
        Args:
            workflow_definition: Dict with "task_ids" and "depends_on" keys.
        """
        self.workflow_definition = workflow_definition
        self.task_ids = workflow_definition.get("task_ids", [])
        self.depends_on = workflow_definition.get("depends_on", {})
    
    def validate(self) -> ValidationResult:
        """
        Run all Tier-1 validation checks in order.
        
        Returns ValidationResult with ok=True if all checks pass,
        or ok=False with appropriate error_code on first failure.
        
        Check order:
        1. Schema validation
        2. Self-loop detection
        3. Acyclicity (Kahn's algorithm)
        """
        # Check 1: Schema validation
        schema_result = self._validate_schema()
        if not schema_result.ok:
            return schema_result
        
        # Check 2: Self-loop detection
        self_loop_result = self._check_self_loops()
        if not self_loop_result.ok:
            return self_loop_result
        
        # Check 3: Acyclicity (Kahn's algorithm)
        acyclicity_result = self._check_acyclicity()
        if not acyclicity_result.ok:
            return acyclicity_result
        
        return ValidationResult(
            ok=True,
            valid_task_order=acyclicity_result.valid_task_order
        )
    
    def _validate_schema(self) -> ValidationResult:
        """
        Validate schema constraints per spec Section 2.
        
        Checks:
        - task_ids is non-empty
        - task_ids entries are unique
        - Each task_id matches regex ^[a-zA-Z0-9_.-]{1,64}$
        - depends_on keys are subset of task_ids
        - depends_on values are subsets of task_ids
        
        Uses hash-set for O(1) membership tests, O(n+e) total.
        """
        # task_ids must be non-empty
        if not self.task_ids:
            return ValidationResult(
                ok=False,
                error_code=BWCC_BAD_REFERENCE,
                error_message="task_ids must be non-empty"
            )
        
        # task_ids must be unique
        if len(self.task_ids) != len(set(self.task_ids)):
            return ValidationResult(
                ok=False,
                error_code=BWCC_BAD_REFERENCE,
                error_message="task_ids must be unique"
            )
        
        # Each task_id must match the regex pattern
        for task_id in self.task_ids:
            if not TASK_ID_PATTERN.match(task_id):
                return ValidationResult(
                    ok=False,
                    error_code=BWCC_BAD_REFERENCE,
                    error_message=f"task_id '{task_id}' does not match required pattern"
                )
        
        # Build hash-set for O(1) membership tests
        task_id_set = set(self.task_ids)
        
        # depends_on keys must be subset of task_ids
        for key in self.depends_on:
            if key not in task_id_set:
                return ValidationResult(
                    ok=False,
                    error_code=BWCC_BAD_REFERENCE,
                    error_message=f"depends_on key '{key}' is not in task_ids"
                )
        
        # depends_on values must be subset of task_ids
        for task_id, dependencies in self.depends_on.items():
            if not isinstance(dependencies, list):
                return ValidationResult(
                    ok=False,
                    error_code=BWCC_BAD_REFERENCE,
                    error_message=f"depends_on['{task_id}'] must be a list"
                )
            for dep in dependencies:
                if dep not in task_id_set:
                    return ValidationResult(
                        ok=False,
                        error_code=BWCC_BAD_REFERENCE,
                        error_message=f"dependency '{dep}' for task '{task_id}' is not in task_ids"
                    )
        
        return ValidationResult(ok=True)
    
    def _check_self_loops(self) -> ValidationResult:
        """
        Check for self-loops in dependencies.
        
        Per spec Section 4: For any task t, t MUST NOT appear in depends_on[t].
        Reject with BWCC_BAD_REFERENCE if found.
        """
        for task_id, dependencies in self.depends_on.items():
            if task_id in dependencies:
                return ValidationResult(
                    ok=False,
                    error_code=BWCC_BAD_REFERENCE,
                    error_message=f"task '{task_id}' has a self-loop"
                )
        
        return ValidationResult(ok=True)
    
    def _check_acyclicity(self) -> ValidationResult:
        """
        Check for cycles using Kahn's algorithm (O(n+e)).
        
        Per spec Section 4:
        - Compute in-degree per task
        - Initialize queue of zero-in-degree tasks
        - Repeatedly dequeue and decrement neighbors' in-degrees
        - If emitted count < n, graph contains a cycle
        
        Returns valid topological order if acyclic.
        """
        # Build adjacency list and in-degree count
        # Edge direction: dependency -> dependent (upstream -> downstream)
        in_degree = {task_id: 0 for task_id in self.task_ids}
        adjacency = {task_id: [] for task_id in self.task_ids}
        
        for task_id, dependencies in self.depends_on.items():
            for dep in dependencies:
                # dep is upstream of task_id, so edge dep -> task_id
                adjacency[dep].append(task_id)
                in_degree[task_id] += 1
        
        # Initialize queue with zero in-degree tasks
        # Use deque for O(1) popleft
        queue = deque([
            task_id for task_id, degree in in_degree.items() if degree == 0
        ])
        
        valid_order = []
        
        while queue:
            task_id = queue.popleft()
            valid_order.append(task_id)
            
            # Decrement in-degree of all downstream neighbors
            for neighbor in adjacency[task_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If we didn't process all tasks, there's a cycle
        if len(valid_order) != len(self.task_ids):
            return ValidationResult(
                ok=False,
                error_code=BWCC_CYCLE,
                error_message="workflow contains a cycle"
            )
        
        return ValidationResult(
            ok=True,
            valid_task_order=valid_order
        )


# =============================================================================
# AmendmentChainValidator - Section 5.2
# =============================================================================

class AmendmentChainValidator:
    """
    Validates amendment chains per BWCC v0.9.0 Section 5.2.
    
    Checks:
    - No duplicate workflow_ids in the chain (amendment cycle)
    - Chain length does not exceed 256 ancestors (DOS bound)
    
    The amendment chain is the sequence:
    W -> amend -> W' -> amend -> W'' -> ...
    linked by previous_workflow_id references.
    
    Usage:
        validator = AmendmentChainValidator(workflow_id, amendment_lookup)
        result = validator.validate()
    """
    
    def __init__(self, workflow_id: str, amendment_lookup: dict[str, str]):
        """
        Initialize validator.
        
        Args:
            workflow_id: The workflow_id to validate the chain for.
            amendment_lookup: Dict mapping workflow_id -> previous_workflow_id
                             (i.e., which workflow this one amends).
                             If a workflow_id is not in the dict, it has no ancestor.
        """
        self.workflow_id = workflow_id
        self.amendment_lookup = amendment_lookup
    
    def validate(self) -> AmendmentChainResult:
        """
        Validate the amendment chain.
        
        Traverses ancestors via previous_workflow_id links and checks:
        - For cycles (duplicate workflow_id in chain) -> BWCC_AMEND_CYCLE
        - For length > 256 -> BWCC_CHAIN_TOO_LONG
        
        Uses hash-set for O(1) membership; total work bounded by 256 cap.
        """
        visited = set()
        current_id = self.workflow_id
        ancestor_ids = []
        
        while current_id is not None:
            # Check for cycle (duplicate workflow_id)
            if current_id in visited:
                return AmendmentChainResult(
                    ok=False,
                    error_code=BWCC_AMEND_CYCLE,
                    error_message=f"Amendment cycle detected at workflow_id '{current_id}'",
                    chain_length=len(ancestor_ids),
                    ancestor_ids=ancestor_ids
                )
            
            # Check chain length limit (DOS bound)
            if len(ancestor_ids) >= BWCC_MAX_ANCESTORS:
                return AmendmentChainResult(
                    ok=False,
                    error_code=BWCC_CHAIN_TOO_LONG,
                    error_message=f"Amendment chain exceeds {BWCC_MAX_ANCESTORS} ancestors",
                    chain_length=len(ancestor_ids),
                    ancestor_ids=ancestor_ids
                )
            
            visited.add(current_id)
            ancestor_ids.append(current_id)
            
            # Move to previous workflow in the chain
            current_id = self.amendment_lookup.get(current_id)
        
        return AmendmentChainResult(
            ok=True,
            chain_length=len(ancestor_ids),
            ancestor_ids=ancestor_ids
        )


# =============================================================================
# XRPCascadeSimulator - Section 6
# =============================================================================

class XRPCascadeSimulator:
    """
    Simulates XRP cascade propagation per BWCC v0.9.0 Section 6.
    
    When a task emits an XRP, the cascade follows depends_on:
    - A task's XRP is published only after every upstream task in
      depends_on[t] has either completed or failed.
    - A failed upstream task propagates BWCC_UPSTREAM_FAIL to every
      transitive downstream task.
    - Downstream tasks emit XRP with status: "cancelled" and MUST NOT
      execute their handler.
    - A cycle detected at runtime yields BWCC_RUNTIME_CYCLE.
    
    Usage:
        simulator = XRPCascadeSimulator(workflow_definition)
        result = simulator.simulate(initial_task_results)
    """
    
    def __init__(self, workflow_definition: dict):
        """
        Initialize simulator with a workflow definition.
        
        Args:
            workflow_definition: Dict with "task_ids" and "depends_on" keys.
        """
        self.workflow_definition = workflow_definition
        self.task_ids = workflow_definition.get("task_ids", [])
        self.depends_on = workflow_definition.get("depends_on", {})
    
    def simulate(
        self,
        task_results: dict[str, dict[str, Any]]
    ) -> CascadeResult:
        """
        Simulate XRP cascade given initial task results.
        
        Args:
            task_results: Dict mapping task_id -> result dict with at least
                         'status' key ('completed', 'failed', or 'cancelled').
        
        Returns:
            CascadeResult with ok=True if cascade completes without runtime cycle,
            or ok=False with BWCC_RUNTIME_CYCLE if a cycle is detected at runtime.
            task_results contains final status of all tasks after propagation.
        """
        # Build reverse dependency graph (who depends on whom)
        # depends_on[t] = [upstream tasks that t depends on]
        # We need: for each task, who are its downstream dependents?
        downstream = {task_id: [] for task_id in self.task_ids}
        for task_id, deps in self.depends_on.items():
            for dep in deps:
                downstream[dep].append(task_id)
        
        # Track which tasks have been processed
        processed = set()
        final_results = dict(task_results)  # Copy initial results
        
        # Queue of tasks to process (start with tasks that have initial results)
        queue = deque(task_results.keys())
        
        while queue:
            task_id = queue.popleft()
            
            if task_id in processed:
                # This shouldn't happen in an acyclic graph
                # If it does, we have a runtime cycle
                return CascadeResult(
                    ok=False,
                    error_code=BWCC_RUNTIME_CYCLE,
                    error_message=f"Runtime cycle detected at task '{task_id}'",
                    task_results=final_results
                )
            
            processed.add(task_id)
            
            # Get this task's result status
            task_result = final_results.get(task_id, {})
            status = task_result.get("status", "pending")
            
            # If this task failed, propagate failure to downstream tasks
            if status == "failed":
                for downstream_task in downstream[task_id]:
                    if downstream_task not in final_results:
                        final_results[downstream_task] = {
                            "status": "cancelled",
                            "error_code": BWCC_UPSTREAM_FAIL,
                            "upstream_failed_task": task_id
                        }
                        queue.append(downstream_task)
            
            # If this task completed, check if downstream tasks can proceed
            elif status == "completed":
                for downstream_task in downstream[task_id]:
                    # Check if all upstream dependencies are now satisfied
                    upstream_deps = self.depends_on.get(downstream_task, [])
                    all_upstream_done = all(
                        dep in final_results for dep in upstream_deps
                    )
                    
                    if all_upstream_done and downstream_task not in final_results:
                        # Check if any upstream failed
                        any_upstream_failed = any(
                            final_results.get(dep, {}).get("status") in ("failed", "cancelled")
                            for dep in upstream_deps
                        )
                        
                        if any_upstream_failed:
                            final_results[downstream_task] = {
                                "status": "cancelled",
                                "error_code": BWCC_UPSTREAM_FAIL
                            }
                        else:
                            # All upstream completed successfully, task can execute
                            # (In simulation, we mark it as ready but don't execute)
                            final_results[downstream_task] = {
                                "status": "ready"
                            }
                        queue.append(downstream_task)
        
        # Check if all tasks have been processed
        if len(processed) < len(self.task_ids):
            # Some tasks were never reached - could indicate a cycle
            unprocessed = set(self.task_ids) - processed
            return CascadeResult(
                ok=False,
                error_code=BWCC_RUNTIME_CYCLE,
                error_message=f"Runtime cycle detected, unprocessed tasks: {unprocessed}",
                task_results=final_results
            )
        
        return CascadeResult(
            ok=True,
            task_results=final_results
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def validate_workflow(workflow_definition: dict) -> ValidationResult:
    """
    Convenience function to validate a workflow definition.
    
    Args:
        workflow_definition: The workflow definition dict with task_ids and depends_on.
    
    Returns:
        ValidationResult indicating whether the workflow is valid.
    """
    validator = WorkflowValidator(workflow_definition)
    return validator.validate()


def validate_amendment_chain(
    workflow_id: str,
    amendment_lookup: dict[str, str]
) -> AmendmentChainResult:
    """
    Convenience function to validate an amendment chain.
    
    Args:
        workflow_id: The workflow_id to validate.
        amendment_lookup: Dict mapping workflow_id -> previous_workflow_id.
    
    Returns:
        AmendmentChainResult indicating whether the chain is valid.
    """
    validator = AmendmentChainValidator(workflow_id, amendment_lookup)
    return validator.validate()


def simulate_xrp_cascade(
    workflow_definition: dict,
    task_results: dict[str, dict[str, Any]]
) -> CascadeResult:
    """
    Convenience function to simulate XRP cascade.
    
    Args:
        workflow_definition: The workflow definition.
        task_results: Initial task results to propagate from.
    
    Returns:
        CascadeResult with the cascade simulation results.
    """
    simulator = XRPCascadeSimulator(workflow_definition)
    return simulator.simulate(task_results)
