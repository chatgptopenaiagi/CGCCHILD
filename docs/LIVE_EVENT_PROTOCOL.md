# cgc-live-event-0.1

Canonical records use ASCII JSON with sorted keys, compact separators and no NaN,
duplicate keys or trailing data. Each journal line is exactly the canonical record
plus LF. Timestamps are timezone-aware ISO 8601. The initial previous hash is 64
zeroes. Each subsequent previous_event_sha256 binds the preceding complete record,
including across segment rollover.

payload_sha256 = SHA256(canonical sanitized payload bytes)

event_sha256 = SHA256(ASCII(previous_event_sha256) + canonical event object without event_sha256)

Event fields: event_version, event_id (UUID), session_id, sequence, project_id,
actor, source, event_type, correlation_id, reported_at, observed_at, verified_at,
evidence_grade, reconciliation_state, payload, payload_sha256,
previous_event_sha256, event_sha256. The published JSON schema is a structural
companion; runtime also enforces semantic and cryptographic relationships.

REPORTED timestamps do not include observed_at/verified_at. VERIFIED requires an
independent observation time and verification time. Reconciliation is independently
SUPPORTED, CONTRADICTED, UNKNOWN, STALE or INVALIDATED. New corroboration adds an
event referencing the old report; no old event is overwritten or promoted.

The vocabulary below includes reserved optional verification/invalidation types.
Metadata-only observation emits no file-content proof. SESSION_* reports from the
agent do not change controller state. Only controller events carry valid transition
edges. NEXT_ACTION_DECLARED enters as AI_PROPOSED_NEXT_ACTION with
UNEXECUTED_FUTURE_ACTION; it is never execution authority.

- `CHECKPOINT_PRESERVED`
- `CHECKPOINT_STARTED`
- `COMMAND_FINISHED`
- `COMMAND_REPORTED`
- `COMMAND_STARTED`
- `COMMIT_OBSERVED`
- `COMMIT_REPORTED`
- `COMMIT_VERIFIED`
- `CONTRADICTION_DETECTED`
- `DECISION_DECLARED`
- `ERROR_OBSERVED`
- `ERROR_REOPENED`
- `ERROR_RESOLVED`
- `EVIDENCE_INVALIDATED`
- `EVIDENCE_RECONCILED`
- `FILESYSTEM_BASELINE_OBSERVED`
- `FILESYSTEM_CHANGE_OBSERVED`
- `FILESYSTEM_CHANGE_VERIFIED`
- `FILE_EDIT_REPORTED`
- `GIT_STATE_OBSERVED`
- `NEXT_ACTION_DECLARED`
- `OBSERVER_COVERAGE`
- `PUSH_CONTRADICTION`
- `PUSH_OBSERVED`
- `PUSH_REPORTED`
- `PUSH_VERIFIED`
- `RECONCILIATION_COMPLETED`
- `RECOVERY_ASSESSED`
- `SESSION_CLOSED_WITH_UNKNOWN`
- `SESSION_ENDING`
- `SESSION_INTERRUPTED`
- `SESSION_PREPARING`
- `SESSION_PRESERVED`
- `SESSION_RECOVERABLE`
- `SESSION_RECOVERING`
- `SESSION_RESUMED`
- `SESSION_STARTED`
- `TEST_FINISHED`
- `TEST_RESULT_VERIFIED`
- `TEST_STARTED`
- `UNFINISHED_WORK_DECLARED`
- `WORKER_LAUNCHED`
