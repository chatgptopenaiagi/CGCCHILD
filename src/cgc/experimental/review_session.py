"""Explicit two-step bounded read-only capture/review. No execution authority.

Trusted Python caller boundary only; opaque instance state is not hostile-code isolation.
A template is proposed scope, not reviewed intent. Caller must supply the review request.
"""
import copy
import os


class SessionError(ValueError):
    def __init__(self):super().__init__('READ_ONLY_REVIEW_SESSION_REFUSED')


def _engine():
    if os.name!='posix':raise RuntimeError('UNSUPPORTED_REVIEW_SESSION_PLATFORM')
    from cgc import verification_capture,safe_resume,reconciliation
    return verification_capture,safe_resume,reconciliation


class ReadOnlyReviewSession:
    __slots__=('_capture','_state')

    def __init__(self,capture):
        self._capture=capture
        self._state='PREPARED'

    @property
    def state(self):return self._state

    def _open(self):
        if self._state!='PREPARED':raise SessionError()

    def projection(self):
        self._open()
        return self._capture.projection

    def request_template(self):
        self._open()
        _,verifier,_=_engine()
        return verifier.request_for(self._capture.projection,action='READ_ONLY_ANALYSIS',
                                    level='HANDOFF_ONLY',test_policy='ACCOUNT_ONLY')

    def review(self,request):
        self._open()
        capture=self._capture
        self._state='CLOSED'
        self._capture=None
        # Consume even a rejected request. No retry with wider scope on this capture.
        if (type(request) is not dict or request.get('action')!='READ_ONLY_ANALYSIS'
                or request.get('level')!='HANDOFF_ONLY' or request.get('test_policy')!='ACCOUNT_ONLY'):
            raise SessionError()
        from .resume_review import review
        return review(capture.projection,copy.deepcopy(request),capture=capture)

    def close(self):
        self._state='CLOSED'
        self._capture=None


def prepare(project,*,store_dir,now):
    """Explicit local I/O once. No remote/review/test callbacks or authority parameters.

    Original collector bounds, refusals and repeated non-atomic observations apply.
    Nothing is persisted, no store is created, and no request is evaluated here.
    """
    bridge,_,_=_engine()
    capture=bridge.capture(project,store_dir=store_dir,now=now,requested_operation='OBSERVE')
    return ReadOnlyReviewSession(capture)


def execute(_session_or_review):
    raise RuntimeError('NO_ACCEPTED_EXECUTION_ADAPTER')
