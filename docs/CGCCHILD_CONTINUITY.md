# Lossless historical V3 continuity projection

[Implementation](../src/cgc/experimental/continuity.py) and
[tests](../tests/test_child_continuity.py). EXPERIMENTAL/PARTIAL V4.0 extension. It is a
separate versioned profile, not an implicit upgrade of the existing model-only capsule,
Node codec, service or MCP tools. Those adapters still accept only model snapshots.

`cgcchild-continuity-0.1-experimental` wraps a complete original V3 handoff state after
calling the existing pure `cgc.handoff.validate_state`. No HandoffStore, path resolution,
repository observation, process creation or Git action occurs. The original source
schema, canonical source digest and all source fields are retained. The source path is
historical data, not the destination of any operation. A separate portable_project_id is
an ASCII opaque label, length1..128, and grants no rebinding authority.

Exact fields: version, source_schema, source_digest, source_state, portable_project_id,
freshness=HISTORICAL_UNVERIFIED, current_safe_to_resume=UNKNOWN,
current_mutation_authorized=false, omissions=[SOURCE_FILES,GIT_OBJECTS,CURRENT_OBSERVATION,
CURRENT_AUTHORITY]. Unknown fields/versions refuse. Omissions are exact and ordered.
Canonical bytes use sorted compact ASCII JSON with one LF. Duplicate keys, trailing bytes,
noncanonical representation, invalid original V3 records and digest mismatch refuse.
The source uses its existing2MiB bound; the envelope is bounded to2MiB+4096 bytes.

This preserves latest-attempt FAILED independently of retained last_known_good and
previous_known_good generations. Source notes, test evidence, nested attempt outcomes,
receipts and outer UNKNOWN are never overwritten by a new summary. The summary is a
projection of original fields and hard-coded historical/current-unknown interpretation;
it does not reinterpret a nested attempt YES as permission to continue. The entire source
can be recovered byte-canonically from the envelope. Hashes establish consistency only.

Stored next-action text and commands remain inert data and are never evaluated. The
original sensitive-content validator still applies. No automatic path mapping, schema
migration, live refresh, current authorization or source-code backup is supplied.

## Evidence and corrections

Five tests cover byte/object round trip, latest failure and both continuity slots, digest
tampering, authority promotion, duplicate keys, truncation/size and invalid original state.
The pure source validator is usable on Windows; no POSIX storage operation is invoked.
All43 child tests passed on Windows. Full Linux results are in child progress.

First test run had five setup errors: the synthetic FAILED test record omitted required
tests_run/test_results. The fixture was corrected to satisfy the original contract.
The next run found two error-type failures: HandoffError is not a ValueError subclass.
The new adapter now catches that precise source error and emits ContinuityError. Existing
V3 validators/tests were not modified or weakened. The focused rerun and child integration
suite passed. These failed approaches are retained as engineering evidence.

Next integration gate is an explicit closed registry of historical profiles with tested
size/semantic dispatch. Do not make the existing model-only transport silently accept
arbitrary payloads or imported schemas to accommodate this new envelope.
