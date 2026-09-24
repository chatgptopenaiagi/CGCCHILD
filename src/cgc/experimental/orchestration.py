"""Refusal-first preservation/recovery planning. No filesystem or Git actions."""
from dataclasses import dataclass
from enum import Enum
from .quiescence import assess, Truth


class Action(str, Enum):
    CHECKPOINT = 'CHECKPOINT'
    PUBLISH = 'PUBLISH'
    REPAIR = 'REPAIR'


@dataclass(frozen=True)
class Plan:
    action: Action
    state: str
    production_p3: Truth
    mutation_authorized: bool
    steps: tuple
    blockers: tuple


def plan_attempt(action, profile, *, project, generation, now_ns, previous_attempt='NONE'):
    if type(action) is not Action or previous_attempt not in ('NONE','SUCCEEDED','FAILED','UNCERTAIN'):
        raise ValueError('INVALID_ATTEMPT')
    evidence = assess(profile, project=project, generation=generation, now_ns=now_ns)
    steps = ('CAPTURE_CURRENT_STATE', 'RECONCILE', 'VERIFY_ACTION_PROOF',
             'OBTAIN_CURRENT_SCOPED_AUTHORITY', 'RECHECK_AT_USE')
    blockers = ('LIVE_QUIESCENCE_UNAVAILABLE', 'CURRENT_AUTHORITY_REQUIRED')
    if previous_attempt != 'NONE':
        steps = ('PRESERVE_PREVIOUS_ATTEMPT_EVIDENCE',)+steps
    if previous_attempt == 'UNCERTAIN':
        blockers += ('UNCERTAIN_PREVIOUS_ATTEMPT_REQUIRES_REVIEW',)
    return Plan(action, 'BLOCKED', evidence.production_p3, False, steps, blockers)


def execute(plan):
    """Stable explicit refusal boundary, including forged or replayed plans.

    A future live adapter requires a separately reviewed authority and atomicity
    contract. This function intentionally has no dispatch/callback parameter.
    """
    raise RuntimeError('NO_ACCEPTED_EXECUTION_ADAPTER')
