"""Canonical cgc-live-event-0.1 facts; integrity never establishes truth."""
import datetime
import hashlib
import json
import uuid
from .redaction import redact, redact_text

EVENT_VERSION = "cgc-live-event-0.1"
MAX_EVENT_BYTES = 32768
MAX_PAYLOAD_BYTES = 24000
ZERO_HASH = "0" * 64
GRADES = {"REPORTED", "OBSERVED", "VERIFIED"}
STATES = {"SUPPORTED", "CONTRADICTED", "UNKNOWN", "STALE", "INVALIDATED"}
EVENT_TYPES = set("""SESSION_PREPARING SESSION_STARTED SESSION_INTERRUPTED SESSION_RESUMED
SESSION_ENDING SESSION_PRESERVED SESSION_RECOVERING SESSION_RECOVERABLE SESSION_CLOSED_WITH_UNKNOWN
COMMAND_REPORTED COMMAND_STARTED COMMAND_FINISHED FILE_EDIT_REPORTED FILESYSTEM_CHANGE_OBSERVED
FILESYSTEM_CHANGE_VERIFIED TEST_STARTED TEST_FINISHED TEST_RESULT_VERIFIED ERROR_OBSERVED
ERROR_RESOLVED ERROR_REOPENED DECISION_DECLARED COMMIT_REPORTED COMMIT_OBSERVED COMMIT_VERIFIED
PUSH_REPORTED PUSH_OBSERVED PUSH_VERIFIED PUSH_CONTRADICTION CHECKPOINT_STARTED CHECKPOINT_PRESERVED
NEXT_ACTION_DECLARED CONTRADICTION_DETECTED EVIDENCE_INVALIDATED EVIDENCE_RECONCILED
GIT_STATE_OBSERVED FILESYSTEM_BASELINE_OBSERVED OBSERVER_COVERAGE RECONCILIATION_COMPLETED
RECOVERY_ASSESSED WORKER_LAUNCHED UNFINISHED_WORK_DECLARED""".split())
REPORT_TYPES = set("""COMMAND_REPORTED FILE_EDIT_REPORTED TEST_STARTED TEST_FINISHED
ERROR_OBSERVED ERROR_RESOLVED ERROR_REOPENED DECISION_DECLARED COMMIT_REPORTED PUSH_REPORTED
NEXT_ACTION_DECLARED UNFINISHED_WORK_DECLARED SESSION_STARTED SESSION_ENDING""".split())


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("DUPLICATE_KEY")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE")))
    except (UnicodeError, RecursionError, TypeError, json.JSONDecodeError):
        raise ValueError("INVALID_JSON") from None


def make_event(session_id, project_id, sequence, previous, event_type, payload,
               grade="OBSERVED", state="UNKNOWN", actor="CGC", source="CONTROLLER",
               correlation_id=None):
    if (type(event_type) is not str or type(grade) is not str or type(state) is not str
            or event_type not in EVENT_TYPES or grade not in GRADES or state not in STATES):
        raise ValueError("INVALID_EVENT_ENUM")
    if correlation_id is not None:
        if not isinstance(correlation_id, str) or len(correlation_id) > 128:
            raise ValueError("CORRELATION_ID_LIMIT")
        correlation_id = redact_text(correlation_id)
    payload = redact(payload)
    if not isinstance(payload, dict) or len(canonical(payload)) > MAX_PAYLOAD_BYTES:
        raise ValueError("PAYLOAD_LIMIT")
    timestamp = now()
    event = dict(event_version=EVENT_VERSION, event_id=str(uuid.uuid4()), session_id=session_id,
                 sequence=sequence, project_id=project_id, actor=redact_text(actor), source=source,
                 event_type=event_type, correlation_id=correlation_id, reported_at=timestamp if grade == "REPORTED" else None,
                 observed_at=timestamp if grade != "REPORTED" else None,
                 verified_at=timestamp if grade == "VERIFIED" else None, evidence_grade=grade,
                 reconciliation_state=state, payload=payload, payload_sha256=sha(canonical(payload)),
                 previous_event_sha256=previous)
    event["event_sha256"] = sha(previous.encode("ascii") + canonical(event))
    validate_event(event, previous, sequence, session_id)
    return event


def validate_event(event, previous, sequence, session_id):
    keys = {"event_version", "event_id", "session_id", "sequence", "project_id", "actor", "source",
            "event_type", "correlation_id", "reported_at", "observed_at", "verified_at", "evidence_grade",
            "reconciliation_state", "payload", "payload_sha256", "previous_event_sha256", "event_sha256"}
    try:
        raw = canonical(event)
    except (TypeError, OverflowError, RecursionError):
        raise ValueError("INVALID_EVENT_SCHEMA") from None
    if not isinstance(event, dict) or set(event) != keys or len(raw) > MAX_EVENT_BYTES:
        raise ValueError("INVALID_EVENT_SCHEMA")
    if event["event_version"] != EVENT_VERSION or type(event["event_type"]) is not str or event["event_type"] not in EVENT_TYPES:
        raise ValueError("INVALID_EVENT_VERSION_OR_TYPE")
    for key in ("session_id", "project_id", "actor", "source", "event_id"):
        if type(event[key]) is not str or not 1 <= len(event[key]) <= 128:
            raise ValueError("INVALID_EVENT_FIELD")
    try:
        uuid.UUID(event["event_id"])
        for key in ("reported_at", "observed_at", "verified_at"):
            if event[key] is not None:
                if not isinstance(event[key], str) or datetime.datetime.fromisoformat(event[key]).tzinfo is None:
                    raise ValueError("INVALID_EVENT_TIME")
    except (TypeError, AttributeError, OverflowError):
        raise ValueError("INVALID_EVENT_TIME") from None
    if event["correlation_id"] is not None and (type(event["correlation_id"]) is not str or len(event["correlation_id"]) > 128):
        raise ValueError("CORRELATION_ID_LIMIT")
    if type(event["sequence"]) is not int or event["sequence"] != sequence or event["session_id"] != session_id:
        raise ValueError("EVENT_SEQUENCE_OR_SESSION")
    if (type(event["evidence_grade"]) is not str or type(event["reconciliation_state"]) is not str
            or event["evidence_grade"] not in GRADES or event["reconciliation_state"] not in STATES):
        raise ValueError("INVALID_EVIDENCE_LEVEL")
    if event["previous_event_sha256"] != previous or not isinstance(event["payload"], dict):
        raise ValueError("EVENT_CHAIN_MISMATCH")
    for key in ("error_id", "test_id"):
        if key in event["payload"] and (type(event["payload"][key]) is not str or not 1 <= len(event["payload"][key]) <= 2048):
            raise ValueError("INVALID_EVENT_IDENTITY")
    if sha(canonical(event["payload"])) != event["payload_sha256"]:
        raise ValueError("PAYLOAD_HASH_MISMATCH")
    body = {k: v for k, v in event.items() if k != "event_sha256"}
    if sha(previous.encode("ascii") + canonical(body)) != event["event_sha256"]:
        raise ValueError("EVENT_HASH_MISMATCH")
    if event["evidence_grade"] == "REPORTED" and event["verified_at"] is not None:
        raise ValueError("REPORTED_VERIFICATION_REFUSED")
    grade = event["evidence_grade"]
    if ((grade == "REPORTED" and (event["reported_at"] is None or event["observed_at"] is not None))
            or (grade == "OBSERVED" and (event["observed_at"] is None or event["verified_at"] is not None))
            or (grade == "VERIFIED" and (event["observed_at"] is None or event["verified_at"] is None))):
        raise ValueError("INVALID_PROVENANCE_TIME")
    return event
