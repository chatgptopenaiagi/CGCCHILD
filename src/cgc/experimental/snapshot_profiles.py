"""Closed historical profile dispatch; no plugin, imported schema or callback API."""
import hashlib
import json
from . import state_protocol as model,continuity

MODEL='QUIESCENCE_MODEL_ONLY'
CONTINUITY='V3_CONTINUITY_HISTORICAL'
MAX_BYTES=continuity.MAX_BYTES


class ProfileError(ValueError):
    def __init__(self):super().__init__('INVALID_SNAPSHOT_PROFILE')


def kind(value):
    if type(value) is not dict:raise ProfileError()
    version=value.get('version')
    if type(version) is not str:raise ProfileError()
    if version==model.VERSION:return MODEL
    if version==continuity.VERSION:return CONTINUITY
    raise ProfileError()


def validate(value):
    try:
        if kind(value)==MODEL:return model.validate(value)
        return continuity.validate(value)
    except ValueError:raise ProfileError() from None


def encode(value):
    v=validate(value)
    return model.encode(v) if kind(v)==MODEL else continuity.encode(v)


def decode(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise ProfileError()
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ProfileError()
            out[k]=v
        return out
    try:
        value=json.loads(raw.decode('ascii'),object_pairs_hook=pairs)
        # The selected original codec performs canonical/number/semantic checks.
        return model.decode(raw) if kind(value)==MODEL else continuity.decode(raw)
    except (ValueError,UnicodeError,RecursionError,OverflowError):raise ProfileError() from None


def digest(value):return hashlib.sha256(encode(value)).hexdigest()


def render_human(value):
    v=validate(value)
    if kind(v)==MODEL:return model.render_human(v)
    s=continuity.summary(v)
    return ('CGCCHILD historical V3 continuity snapshot\n'
            'Project identifier: '+s['project_id']+'\n'
            'Source generation: '+str(s['generation'])+'\n'
            'Latest attempt: '+s['latest_attempt']+'\n'
            'Latest error: '+str(s['latest_error'])+'\n'
            'Last known good generation: '+str(s['last_known_good_generation'])+'\n'
            'Previous known good generation: '+str(s['previous_known_good_generation'])+'\n'
            'Current safe to resume: UNKNOWN; mutation authorized: false\n'
            'Current filesystem, repository and remote: NOT CHECKED\n'
            'Saved: original V3 continuity records; source files and Git objects OMITTED\n'
            'Next: obtain current independent evidence and scoped authority\n')
