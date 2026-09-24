# Experimental scoped resume review

[Implementation](../src/cgc/experimental/resume_review.py),
[tests](../tests/test_child_resume_review.py).
Status: IMPLEMENTED / VERIFIED OFFLINE on POSIX; full safe resume remains PARTIAL.

The caller explicitly supplies the unchanged verifier's request: project, expected identity,
evidence digest, action, preservation level and test policy. The child performs no collection
or implicit request selection. It delegates proof derivation and validation to the inherited
verifier. A matching in-memory Capture may support YES only for the accepted captured-analysis
scope. Every result still denies mutation and automatic execution. The caller owns any explicit
collection and its scope; no collector is reached by this module.

Review stores immutable canonical strings and returns fresh decoded result copies. It has no
command, path, callback, executor registration or authority parameter. execute_review always
refuses, including forged Review instances and analysis YES. Private Python attributes are not
a hostile-code security boundary.

historical_report recomputes proof without the capture handle, so serialization yields IMPORTED
provenance and UNKNOWN current safety. Historical test results and other evidence remain
available. It does not serialize the live binding, claim fresh repository safety, or feed a
portable report back into an execution path. Original verifier validation remains authoritative.

The inherited verifier import chain includes POSIX fcntl through checkpoint code. The child
detects unsupported platforms before importing that chain and returns
UNSUPPORTED_VERIFIER_PLATFORM on Windows. It does not emulate or edit inherited dependencies.
A first Windows test run exposed this import limitation; the Linux six-test version passed.
The explicit platform refusal and lazy import fix are covered by a seventh test.

Tests use an owned Linux-native disposable Git fixture to obtain a real bounded capture,
verify no file-content/metadata change, obtain captured-analysis YES, test all six actions at
three levels with no executor, reject changed expected evidence, demote imported/forged capture
provenance, and retain historical test evidence in the portable report. Assessment is also
run with file/process creation patched to fail. No real project mutation, quiescence producer,
P3 promotion, recovery action or privileged observation occurs.

Regression limitation: the first458-test full run had one inherited pack-interruption tree
equality failure. The isolated case and ten repetitions passed unchanged. This does not establish
a root cause or erase the failure; B11 preserves it. The child review tests passed in that run.

The second full regression passed458 tests in109.659s. B11 remains open because a passing
rerun does not identify the prior failure cause. No inherited test or runtime was modified.

## Recovery assessment without execution (M42)

[Recovery derivation](../src/cgc/experimental/recovery_review.py) and
[tests](../tests/test_child_recovery_review.py) add a pure review step for CHECKPOINT,
PUBLISH and REPAIR intentions. The caller supplies an original reconciliation result,
expected project string and SHA256 of the entire canonical result (ASCII, sorted keys,
compact separators, no trailing LF). The unchanged reconciler reclassifies and validates
that result before the child derives any steps. This is imported historical evidence;
matching caller expectations is neither live path identity nor sender authentication.

Seven closed action categories map to fixed review instructions, in inherited issue priority
order. Historical free-text next actions and issue subjects are never replayed. A project or
digest mismatch produces REFUSED_EVIDENCE_BINDING with no derived issue instructions. Even
an empty issue set produces REVIEW_REQUIRED_NO_EXECUTOR, UNKNOWN current safety/P3 and false
mutation authority. The output is bounded to16KiB canonical ASCII and copied on access.

The report retains historical phase, generations, attempt status and test result separately
from current proof requirements. It always requires fresh scoped evidence, action proof,
authority and a use-time precondition check. execute unconditionally refuses even a forged
review. There is no repair callback, collector, Git operation, lock deletion, process control,
or new authority grant. Windows explicitly refuses the inherited POSIX-only dependency.

Seven tests cover owned disposable Git capture, unchanged fixture contents/metadata, all
three intentions, all seven categories through explicitly synthetic reclassification, no-I/O
assessment, detached output, forged classification, malformed binding and empty-issue refusal.
The initial test helper incorrectly read project at the result root; correcting it to the
validated evidence field resolved five test errors. No product check was weakened.

## Action-bound composition (M43)

review_action composes recovery assessment with a newly evaluated verifier request. It accepts
no serialized verdict. The closed mappings are CHECKPOINT -> CREATE_CHECKPOINT, PUBLISH ->
PUBLISH_CHECKPOINT, REPAIR -> REPAIR_KNOWN_FAILURE. Project and entire-projection digest must
match both the caller's expectation and the request before any proof evaluation. Preservation
level and test policy remain explicit caller inputs validated by the unchanged verifier.
An analysis-only request cannot enter any of these three paths, even when its separate captured
analysis proof is YES. No request is silently rewritten to a stronger or weaker action.

ActionReview exposes the scoped verdict separately from authority. Its historical_report
recomputes without capture and returns copied imported evidence; it never exports a current
capture handle. execute still refuses all values. There is no collection, path access or repair.
Six tests cover all nine action/level pairs, all cross-action substitutions, live-analysis YES
substitution, project/digest mismatches, malformed requests, immutable results and no-I/O checks.

An initial expectation that a changed repair digest would produce NO was incorrect: the
inherited unsupported repair profile sets P2 UNKNOWN. The child now rejects inconsistent
request/project/digest bindings before invoking the verifier. This strengthens composition
without modifying inherited proof rules or treating UNKNOWN as permission.
