"""Bounded inert analysis report. Imported proof is recomputed without capture."""
from dataclasses import dataclass
import hashlib
import json
import os

VERSION='cgcchild-session-report-0.1-experimental'
MAX_BYTES=512*1024+4096
FIELDS={'version','scope','verification','verification_sha256','freshness','authority',
        'current_repository_safety','mutation_authorized','execution_state'}


class ReportError(ValueError):
    def __init__(self):super().__init__('INVALID_SESSION_REPORT')


def _engine():
    if os.name!='posix':raise RuntimeError('UNSUPPORTED_REPORT_VERIFIER_PLATFORM')
    from cgc import safe_resume
    return safe_resume


def _bytes(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')


def validate(value):
    verifier=_engine()
    try:
        if type(value) is not dict or set(value)!=FIELDS:raise ReportError()
        for key,expected in {'version':VERSION,'scope':'IMPORTED_ANALYSIS_REVIEW',
            'freshness':'HISTORICAL_UNVERIFIED','authority':'NONE','current_repository_safety':'UNKNOWN',
            'execution_state':'NO_ACCEPTED_EXECUTION_ADAPTER'}.items():
            if value[key]!=expected:raise ReportError()
        if value['mutation_authorized'] is not False:raise ReportError()
        proof=verifier.validate_result(value['verification'])
        request=proof['input']['request']
        if (proof['input']['provenance']!='IMPORTED' or request['action']!='READ_ONLY_ANALYSIS'
                or request['level']!='HANDOFF_ONLY' or request['test_policy']!='ACCOUNT_ONLY'):
            raise ReportError()
        if value['verification_sha256']!=hashlib.sha256(_bytes(proof)).hexdigest():raise ReportError()
        raw=_bytes(value)
        if len(raw)>MAX_BYTES:raise ReportError()
        return json.loads(raw)
    except (ValueError,TypeError,KeyError,RecursionError,OverflowError):raise ReportError() from None


def encode(value):return _bytes(validate(value))


def decode(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise ReportError()
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ReportError()
            out[key]=value
        return out
    def invalid(_):raise ReportError()
    try:
        value=validate(json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=invalid))
        if encode(value)!=raw:raise ReportError()
        return value
    except (ValueError,UnicodeError,RecursionError,OverflowError):raise ReportError() from None


@dataclass(frozen=True)
class HistoricalReport:
    _raw: bytes

    def as_dict(self):return decode(self._raw)

    def bytes(self):return bytes(self._raw)


def from_review(review):
    from .resume_review import Review
    if type(review) is not Review:raise ReportError()
    proof=review.historical_report()['verification']
    value=dict(version=VERSION,scope='IMPORTED_ANALYSIS_REVIEW',verification=proof,
               verification_sha256=hashlib.sha256(_bytes(proof)).hexdigest(),
               freshness='HISTORICAL_UNVERIFIED',authority='NONE',current_repository_safety='UNKNOWN',
               mutation_authorized=False,execution_state='NO_ACCEPTED_EXECUTION_ADAPTER')
    return HistoricalReport(encode(value))


def execute(_report):raise RuntimeError('NO_ACCEPTED_EXECUTION_ADAPTER')
