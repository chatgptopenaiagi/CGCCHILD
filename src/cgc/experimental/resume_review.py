"""Pure child integration of the unchanged scoped verifier; no execution adapter.

Current capture provenance is only the inherited trusted-Python boundary. Portable
reports are recomputed as imported evidence, never serialized current authority.
"""
import json
import os
from dataclasses import dataclass

VERSION = 'cgcchild-resume-review-0.1-experimental'


def _engine():
    # Inherited verifier imports POSIX-only checkpoint dependencies. Do not fake them.
    if os.name != 'posix':raise RuntimeError('UNSUPPORTED_VERIFIER_PLATFORM')
    from cgc import reconciliation as rc, safe_resume as verifier
    return rc, verifier


@dataclass(frozen=True)
class Review:
    _projection_json: str
    _request_json: str
    _verification_json: str

    @property
    def verification(self):
        """Independent copy; YES remains exact captured-analysis scope only."""
        return json.loads(self._verification_json)

    def historical_report(self):
        """Re-evaluate without capture; stored provenance cannot authenticate itself."""
        _, verifier = _engine()
        result = verifier.verify(json.loads(self._projection_json),
                                 json.loads(self._request_json))
        return {
            'version': VERSION,
            'scope': 'IMPORTED_EVIDENCE_REVIEW',
            'verification': result,
            'execution_state': 'NO_EXECUTION_ADAPTER',
            'mutation_authorized': False,
            'current_repository_safety': 'UNKNOWN',
        }


def review(projection, request, *, capture=None):
    """No implicit collection, request selection, authority issuance or mutation.

    The caller explicitly supplies the existing verifier request, including exact
    project/identity/evidence digest/action/level. Imported evidence stays imported.
    """
    rc, verifier = _engine()
    result = verifier.verify(projection, request, capture=capture)
    return Review(rc.canonical(rc.validate_result(projection)),
                  rc.canonical(request), verifier.render_json(result, capture=capture))


def execute_review(_review):
    """Even a fabricated Review or an analysis YES cannot authorize execution."""
    raise RuntimeError('NO_ACCEPTED_EXECUTION_ADAPTER')
