"""Inert bounded read-event journal. Hash chains establish consistency, not authority."""
from dataclasses import dataclass
import hashlib
import json
import re

VERSION='cgcchild-read-journal-0.1-experimental'
EVENT_VERSION='cgcchild-read-events-0.1'
MAX_EVENTS=64
MAX_BYTES=32768
KINDS=('LOCAL_READ_HANDLE_ISSUED','READ_DENIED','CORE_REFUSED','READ_COMPLETE',
       'LOCAL_READ_HANDLE_REVOKED','SNAPSHOT_INVALIDATED')
FIELDS={'version','sequence','kind','observed_ns','snapshot_digest','previous','digest'}
ENVELOPE={'version','snapshot_digest','events','completeness','authority','freshness','clock'}
ZERO='0'*64


class JournalError(ValueError):
    def __init__(self):super().__init__('INVALID_READ_JOURNAL')


def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def _digest(value):
    if type(value) is not str or not re.fullmatch(r'[0-9a-f]{64}',value):raise JournalError()


def _validate(value):
    if type(value) is not dict or set(value)!=ENVELOPE:raise JournalError()
    if value['version']!=VERSION or value['completeness']!='EXPECTED_PREFIX_ONLY' or value['authority']!='NONE':raise JournalError()
    if value['freshness']!='HISTORICAL_UNVERIFIED' or value['clock']!='SOURCE_MONOTONIC_NOT_PORTABLE':raise JournalError()
    _digest(value['snapshot_digest'])
    events=value['events']
    if type(events) is not list or len(events)>MAX_EVENTS:raise JournalError()
    previous=ZERO;clock=-1;ended=False
    for number,event in enumerate(events,1):
        if ended or type(event) is not dict or set(event)!=FIELDS:raise JournalError()
        if event['version']!=EVENT_VERSION or type(event['sequence']) is not int or event['sequence']!=number:raise JournalError()
        if type(event['kind']) is not str or event['kind'] not in KINDS:raise JournalError()
        now=event['observed_ns']
        if type(now) is not str or not re.fullmatch(r'0|[1-9][0-9]{0,18}',now):raise JournalError()
        if not clock<=int(now)<1<<63:raise JournalError()
        clock=int(now)
        if event['snapshot_digest']!=value['snapshot_digest'] or event['previous']!=previous:raise JournalError()
        _digest(event['digest'])
        body={key:item for key,item in event.items() if key!='digest'}
        if hashlib.sha256(_json(body)).hexdigest()!=event['digest']:raise JournalError()
        previous=event['digest'];ended=event['kind']=='SNAPSHOT_INVALIDATED'
    return value


def encode(events,*,snapshot_digest):
    """Copy closed event dictionaries; no handles, principal labels or credentials."""
    try:
        if type(events) not in (tuple,list) or len(events)>MAX_EVENTS:raise JournalError()
        value=dict(version=VERSION,snapshot_digest=snapshot_digest,events=list(events),
                   completeness='EXPECTED_PREFIX_ONLY',authority='NONE',freshness='HISTORICAL_UNVERIFIED',
                   clock='SOURCE_MONOTONIC_NOT_PORTABLE')
        raw=_json(_validate(value))+b'\n'
        if len(raw)>MAX_BYTES:raise JournalError()
        return raw
    except (ValueError,TypeError,OverflowError,RecursionError):raise JournalError() from None


@dataclass(frozen=True)
class HistoricalJournal:
    journal_bytes: bytes

    @property
    def authority(self):return 'NONE'

    @property
    def freshness(self):return 'HISTORICAL_UNVERIFIED'

    @property
    def integrity(self):return 'CONSISTENT_UNSIGNED_BYTES'

    def events(self):return tuple(json.loads(self.journal_bytes)['events'])


def decode(raw,*,expected_snapshot_digest,expected_tip,expected_count):
    """Require caller's expected prefix anchor; never proves an unseen tail absent."""
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise JournalError()
            out[key]=value
        return out
    def invalid(_):raise JournalError()
    try:
        _digest(expected_snapshot_digest);_digest(expected_tip)
        if type(expected_count) is not int or not 0<=expected_count<=MAX_EVENTS:raise JournalError()
        if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise JournalError()
        value=_validate(json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=invalid))
        if _json(value)+b'\n'!=raw:raise JournalError()
        events=value['events'];tip=events[-1]['digest'] if events else ZERO
        if value['snapshot_digest']!=expected_snapshot_digest or len(events)!=expected_count or tip!=expected_tip:raise JournalError()
        return HistoricalJournal(raw)
    except (ValueError,TypeError,UnicodeError,OverflowError,RecursionError):raise JournalError() from None
