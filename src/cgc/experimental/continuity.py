"""Lossless inert V3 handoff projection. Uses the original pure validator.

No HandoffStore is opened. No project path is resolved. A historical source
digest establishes covered bytes, never source authenticity/current authority.
"""
import hashlib
import json
import re
from ..handoff import validate_state,SCHEMA_VERSION,MAX_HANDOFF_BYTES,HandoffError

VERSION='cgcchild-continuity-0.1-experimental'
MAX_BYTES=MAX_HANDOFF_BYTES+4096
FIELDS={'version','source_schema','source_digest','source_state','portable_project_id',
        'freshness','current_safe_to_resume','current_mutation_authorized','omissions'}
OMISSIONS=['SOURCE_FILES','GIT_OBJECTS','CURRENT_OBSERVATION','CURRENT_AUTHORITY']


class ContinuityError(ValueError):
    def __init__(self):super().__init__('INVALID_CONTINUITY_PROJECTION')


def _bytes(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')


def project(source_state,*,portable_project_id):
    try:source=validate_state(source_state)
    except HandoffError:raise ContinuityError() from None
    value=dict(version=VERSION,source_schema=SCHEMA_VERSION,
               source_digest=hashlib.sha256(_bytes(source)).hexdigest(),source_state=source,
               portable_project_id=portable_project_id,freshness='HISTORICAL_UNVERIFIED',
               current_safe_to_resume='UNKNOWN',current_mutation_authorized=False,omissions=list(OMISSIONS))
    return validate(value)


def validate(value):
    try:
        if type(value) is not dict or set(value)!=FIELDS:raise ContinuityError()
        if value['version']!=VERSION or value['source_schema']!=SCHEMA_VERSION:raise ContinuityError()
        if (type(value['portable_project_id']) is not str or
                not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value['portable_project_id'])):raise ContinuityError()
        if (value['freshness']!='HISTORICAL_UNVERIFIED' or value['current_safe_to_resume']!='UNKNOWN'
                or value['current_mutation_authorized'] is not False or value['omissions']!=OMISSIONS):raise ContinuityError()
        source=validate_state(value['source_state'])
        if value['source_digest']!=hashlib.sha256(_bytes(source)).hexdigest():raise ContinuityError()
        raw=_bytes(value)
        if len(raw)>MAX_BYTES:raise ContinuityError()
        return json.loads(raw)
    except (HandoffError,ValueError,TypeError,RecursionError,OverflowError):raise ContinuityError() from None


def encode(value):return _bytes(validate(value))


def decode(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise ContinuityError()
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ContinuityError()
            out[key]=value
        return out
    def invalid(_):raise ContinuityError()
    try:
        value=validate(json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=invalid))
        if encode(value)!=raw:raise ContinuityError()
        return value
    except (ValueError,UnicodeError,RecursionError,OverflowError):raise ContinuityError() from None


def summary(value):
    v=validate(value);source=v['source_state']
    return dict(project_id=v['portable_project_id'],source_digest=v['source_digest'],
                generation=source['generation'],latest_attempt=source['latest_attempt']['status'],
                latest_error=source['latest_attempt']['error_code'],
                last_known_good_generation=source['last_known_good']['generation'] if source['last_known_good'] else None,
                previous_known_good_generation=source['previous_known_good']['generation'] if source['previous_known_good'] else None,
                source_outer_safe_to_resume=source['safe_to_resume'],current_safe_to_resume='UNKNOWN',
                current_mutation_authorized=False,freshness='HISTORICAL_UNVERIFIED')
