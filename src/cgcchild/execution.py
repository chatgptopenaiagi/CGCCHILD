"""Closed planning/executor vocabulary. No Git, shell, callbacks or host mutation."""
from enum import Enum
from typing import Protocol


class Mode(str, Enum):
    READ_ONLY_SAFE = "READ_ONLY_SAFE"
    EXPERIMENTAL_LOCAL = "EXPERIMENTAL_LOCAL"
    SIMULATION = "SIMULATION"
    DEVELOPER_LAB = "DEVELOPER_LAB"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"


ACTIONS = ("PRESERVE", "RECONCILE", "REVIEW", "REPORT", "RECOVERY_PLAN",
           "SAFE_RESUME", "CHECKPOINT", "PUBLISH", "VERIFY")
GATES = ("MUTATION_GATE", "CHECKPOINT_GATE", "PUBLICATION_GATE", "VERIFICATION_GATE")


def plan(action, mode=Mode.READ_ONLY_SAFE):
    if type(action) is not str or action not in ACTIONS or type(mode) is not Mode:
        raise ValueError("INVALID_PLAN_REQUEST")
    return dict(action=action, mode=mode.value, state="PLAN_ONLY", mutation_authorized=False,
                steps=["CAPTURE_EVIDENCE", "RECONCILE", "REVIEW", "CHECK_CURRENT_AUTHORITY",
                       "REVALIDATE_AT_USE", "VERIFY_RESULT"],
                gates={gate: "BLOCKED" for gate in GATES},
                blockers=["PRODUCTION_EXECUTOR_NOT_ACCEPTED", "FILESYSTEM_EXCLUSIVITY_UNKNOWN",
                          "CURRENT_AUTHORITY_NOT_ESTABLISHED"])


class ExecutorInterface(Protocol):
    def execute(self, action: str, mode: Mode = Mode.READ_ONLY_SAFE) -> dict: ...


class NullExecutor:
    def execute(self, action, mode=Mode.READ_ONLY_SAFE):
        return dict(plan(action, mode), state="REFUSED", reason="NO_ACCEPTED_EXECUTION_ADAPTER")


class DryRunExecutor:
    def execute(self, action, mode=Mode.READ_ONLY_SAFE):
        return dict(plan(action, mode), state="DRY_RUN", effects=[])


class SimulationExecutor:
    def execute(self, action, mode=Mode.READ_ONLY_SAFE):
        result = plan(action, mode)
        if mode not in (Mode.SIMULATION, Mode.DEVELOPER_LAB):
            return dict(result, state="REFUSED", reason="EXPLICIT_SIMULATION_MODE_REQUIRED")
        return dict(result, state="SIMULATED", simulated_steps=result["steps"], effects=[],
                    production_p3="UNKNOWN", simulated_success=True)


class LocalExperimentalExecutor(NullExecutor):
    """Reserved Windows adapter; no inherited POSIX mutation adapter is dispatched."""


class ProductionExecutorPlaceholder(NullExecutor):
    """Mode selection, forged evidence or caller approval cannot enable this adapter."""
