"""Pure recovery-review derivation; never collects, repairs, resumes or grants authority."""
from dataclasses import dataclass
import json
import os
import re
from .orchestration import Action

VERSION='cgcchild-recovery-review-0.1-experimental'
MAX_BYTES=16384
STEPS={
    'TARGET':'RECAPTURE_TARGET_IDENTITY',
    'DURABLE':'REVIEW_DURABLE_HANDOFF_WITHOUT_ALTERATION',
    'MUTATION':'ESTABLISH_PENDING_MUTATION_FACTS_WITHOUT_CLEANUP',
    'CONFLICT':'EXPLAIN_HISTORICAL_CURRENT_DIFFERENCE',
    'REVIEW':'OBTAIN_FRESH_CONTENT_REVIEW',
    'TESTS':'ESTABLISH_TESTED_STATE_BINDING',
    'REMOTE':'REQUEST_EXPLICIT_SCOPED_REMOTE_OBSERVATION',
}


class RecoveryError(ValueError):
    def __init__(self):super().__init__('INVALID_RECOVERY_REVIEW')


def _engine():
    if os.name!='posix':raise RuntimeError('UNSUPPORTED_RECOVERY_PLATFORM')
    from cgc import reconciliation
    return reconciliation


@dataclass(frozen=True)
class RecoveryReview:
    _json: str

    def as_dict(self):return json.loads(self._json)


def assess(projection,action,*,expected_project,expected_projection_digest):
    """Explicit imported projection/intent binding; serialization authenticates nothing."""
    rc=_engine()
    try:
        if type(action) is not Action:raise RecoveryError()
        if type(expected_project) is not str or not 1<=len(expected_project)<=4096:raise RecoveryError()
        if type(expected_projection_digest) is not str or not re.fullmatch(r'[0-9a-f]{64}',expected_projection_digest):raise RecoveryError()
        result=rc.validate_result(projection);basis=result['evidence']
        projection_digest=rc.digest(result)
        bound=expected_project==basis['project'] and expected_projection_digest==projection_digest
        handoff=basis['handoff'];slot=handoff['last_known_good'];previous=handoff['previous_known_good']
        issues=[];steps=['PRESERVE_SUPPLIED_EVIDENCE']
        if bound:
            for issue in result['issues']:
                issues.append({key:issue[key] for key in ('priority','domain','reason','action')})
                step=STEPS[issue['action']]
                if step not in steps:steps.append(step)
            steps+=['CAPTURE_FRESH_SCOPED_EVIDENCE','VERIFY_ACTION_PROOF','OBTAIN_FRESH_SCOPED_AUTHORITY','RECHECK_PRECONDITIONS_AT_USE']
        else:steps.append('REVIEW_PROJECTION_TARGET_AND_DIGEST_MISMATCH')
        report=dict(version=VERSION,action=action.value,
            state='REVIEW_REQUIRED_NO_EXECUTOR' if bound else 'REFUSED_EVIDENCE_BINDING',
            provenance='IMPORTED_RECONCILIATION',freshness='HISTORICAL_UNVERIFIED',
            supplied_projection_digest=projection_digest,target_binding='MATCHES_SUPPLIED_EXPECTATION' if bound else 'MISMATCH',
            source_collection_outcome=result['collection_outcome'],
            historical_attempt_status=handoff['latest_attempt']['status'] if handoff['latest_attempt'] else None,
            historical_phase=slot['phase'] if slot else None,
            last_known_good_generation=slot['generation'] if slot else None,
            previous_known_good_generation=previous['generation'] if previous else None,
            historical_test_result=result['historical_test_result'],
            current_repository_safety='UNKNOWN',production_p3='UNKNOWN',mutation_authorized=False,
            execution_state='NO_ACCEPTED_EXECUTION_ADAPTER',issues=issues,steps=steps,
            blockers=['CURRENT_EVIDENCE_REQUIRED','LIVE_QUIESCENCE_UNAVAILABLE','CURRENT_SCOPED_AUTHORITY_REQUIRED'])
        raw=rc.canonical(report)
        if len(raw.encode('ascii'))>MAX_BYTES:raise RecoveryError()
        return RecoveryReview(raw)
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError):raise RecoveryError() from None


def execute(_review):
    raise RuntimeError('NO_ACCEPTED_EXECUTION_ADAPTER')


PROOF_ACTIONS={
    Action.CHECKPOINT:'CREATE_CHECKPOINT',
    Action.PUBLISH:'PUBLISH_CHECKPOINT',
    Action.REPAIR:'REPAIR_KNOWN_FAILURE',
}


@dataclass(frozen=True)
class ActionReview:
    _recovery: RecoveryReview
    _proof: object

    @property
    def verification(self):
        """Exact requested scope, never a repair authorization."""
        return self._proof.verification

    def historical_report(self):
        # Recompute without a live capture rather than serializing current provenance.
        return dict(version='cgcchild-action-review-0.1-experimental',
                    recovery=self._recovery.as_dict(),
                    proof=self._proof.historical_report(),
                    execution_state='NO_ACCEPTED_EXECUTION_ADAPTER',
                    mutation_authorized=False,current_repository_safety='UNKNOWN')


def review_action(projection,action,request,*,expected_project,expected_projection_digest,capture=None):
    """Bind explicit action to freshly evaluated proof; never accept a supplied verdict."""
    _engine()
    if type(action) is not Action or type(request) is not dict:
        raise RecoveryError()
    if request.get('action')!=PROOF_ACTIONS[action]:raise RecoveryError()
    if request.get('project')!=expected_project or request.get('evidence_digest')!=expected_projection_digest:
        raise RecoveryError()
    recovery=assess(projection,action,expected_project=expected_project,
                    expected_projection_digest=expected_projection_digest)
    if recovery.as_dict()['state']!='REVIEW_REQUIRED_NO_EXECUTOR':raise RecoveryError()
    from .resume_review import review
    proof=review(projection,request,capture=capture)
    return ActionReview(recovery,proof)
