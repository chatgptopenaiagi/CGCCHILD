"""Experimental inert state protocol, fixed quiescence-model-only profile.

Not a replacement schema for V3 records. No migration, file access or authority.
Decode preserves bytes/claims; interpretation always creates a historical view.
"""
import copy
import datetime
import hashlib
import json
import re
from .quiescence import Claim, Profile, Truth, OBLIGATIONS

VERSION = 'cgcchild-state-0.1-experimental'
MAX_BYTES = 16384
OMISSIONS = ['SOURCE_CONTENT', 'GIT_OBJECTS', 'V3_RECEIPTS', 'LIVE_AUTHORITY', 'FILESYSTEM_PROOF']
FIELDS = {'version','profile','source_instance','snapshot_id','captured_at','clock',
          'model','production_p3','safe_to_resume','mutation_authorized','omissions'}
MODEL_FIELDS = {'project','generation','observed_ns','expires_ns','claims','provenance'}


class ProtocolError(ValueError):
    def __init__(self, code='INVALID_STATE'):
        super().__init__(code)


def _identifier(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', value):
        raise ProtocolError()


def _stamp(value):
    if type(value) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',value):
        raise ProtocolError()
    try:
        datetime.datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        raise ProtocolError() from None


def _canonical(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')


def validate(value):
    try:
        if type(value) is not dict or set(value)!=FIELDS:
            raise ProtocolError()
        if value['version']!=VERSION:
            raise ProtocolError('UNSUPPORTED_VERSION')
        if value['profile']!='QUIESCENCE_MODEL_ONLY' or value['clock']!='SOURCE_MONOTONIC_NOT_PORTABLE':
            raise ProtocolError()
        _identifier(value['source_instance']);_identifier(value['snapshot_id']);_stamp(value['captured_at'])
        if value['production_p3']!='UNKNOWN' or value['safe_to_resume']!='UNKNOWN' or value['mutation_authorized'] is not False:
            raise ProtocolError('AUTHORITY_PROMOTION')
        if type(value['omissions']) is not list or value['omissions']!=OMISSIONS:
            raise ProtocolError()
        model=value['model']
        if type(model) is not dict or set(model)!=MODEL_FIELDS or type(model['claims']) is not dict or set(model['claims'])!=set(OBLIGATIONS):
            raise ProtocolError()
        if any(type(v) is not str for v in model['claims'].values()):
            raise ProtocolError()
        for field in ('observed_ns','expires_ns'):
            if type(model[field]) is not str or not re.fullmatch(r'0|[1-9][0-9]{0,18}',model[field]):
                raise ProtocolError('INVALID_CLOCK_ENCODING')
        Profile(**dict(model,observed_ns=int(model['observed_ns']),expires_ns=int(model['expires_ns']),
                       claims=tuple(Claim(k,Truth(model['claims'][k])) for k in OBLIGATIONS)))
        raw=_canonical(value)
        if len(raw)>MAX_BYTES:
            raise ProtocolError('SIZE_LIMIT')
        return copy.deepcopy(value)
    except (TypeError,ValueError,OverflowError,RecursionError) as err:
        if type(err) is ProtocolError:raise
        raise ProtocolError() from None


def snapshot(profile, *, source_instance, snapshot_id, captured_at):
    if type(profile) is not Profile:raise ProtocolError()
    return validate(dict(version=VERSION,profile='QUIESCENCE_MODEL_ONLY',
        source_instance=source_instance,snapshot_id=snapshot_id,captured_at=captured_at,
        clock='SOURCE_MONOTONIC_NOT_PORTABLE',
        model=dict(project=profile.project,generation=profile.generation,
                   observed_ns=str(profile.observed_ns),expires_ns=str(profile.expires_ns),
                   claims={c.obligation:c.status.value for c in profile.claims},provenance=profile.provenance),
        production_p3='UNKNOWN',safe_to_resume='UNKNOWN',mutation_authorized=False,omissions=list(OMISSIONS)))


def encode(value):
    return _canonical(validate(value))


def decode(data):
    if type(data) is not bytes or not 1<=len(data)<=MAX_BYTES:raise ProtocolError('SIZE_LIMIT')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ProtocolError('DUPLICATE_KEY')
            out[k]=v
        return out
    def invalid(_):raise ProtocolError('INVALID_NUMBER')
    def integer(s):
        if len(s)>19:raise ProtocolError('INVALID_NUMBER')
        return int(s)
    try:
        value=json.loads(data.decode('ascii'),object_pairs_hook=pairs,
                         parse_int=integer,parse_float=invalid,parse_constant=invalid)
        value=validate(value)
        if encode(value)!=data:raise ProtocolError('NONCANONICAL')
        return value
    except (UnicodeError,ValueError,RecursionError,OverflowError) as err:
        if type(err) is ProtocolError:raise
        raise ProtocolError() from None


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def imported_profile(value):
    model=validate(value)['model']
    return Profile(**dict(model,provenance='IMPORTED',observed_ns=int(model['observed_ns']),expires_ns=int(model['expires_ns']),
        claims=tuple(Claim(k,Truth(model['claims'][k])) for k in OBLIGATIONS)))


def render_human(value):
    v=validate(value)
    return ('CGCCHILD experimental historical model snapshot\n'
            'Project identifier: '+v['model']['project']+'\n'
            'Snapshot: '+v['snapshot_id']+'; captured: '+v['captured_at']+'\n'
            'P3: UNKNOWN; safe to resume: UNKNOWN; mutation authorized: false\n'
            'Current filesystem, repository and remote: NOT CHECKED\n'
            'Saved: synthetic model claims only; not a source-code backup\n'
            'Next: obtain current independent evidence and scoped authority\n')
