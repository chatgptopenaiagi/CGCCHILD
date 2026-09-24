# Experimental filesystem closure model

[Implementation](../src/cgc/experimental/filesystem_model.py),
[tests](../tests/test_child_filesystem_model.py).
Status: pure bounded model only. Production filesystem exclusivity and P3 remain UNKNOWN.

This makes the action/domain obligations in [the inherited contract](V3_QUIESCENCE.md#5-action-and-mutation-domain-binding)
executable without inventing a live filesystem observer. It reads no filesystem, clock, process,
environment, credential or manager state. It does not discover writers, hold an exclusion,
open paths, acquire locks or authorize execution.

## Finite model

A Model binds opaque project/generation labels, one fixed action, source-monotonic observation
and expiry, ordered unique cells, and SYNTHETIC or IMPORTED provenance. Labels are never paths.
Each Cell is one domain/channel pair and YES/NO/UNKNOWN. YES means the synthetic scenario
stipulates that route is accounted for and excluded from uncontrolled writing throughout its
epoch; NO models an unclosed route; UNKNOWN or omission means missing coverage. These are
model inputs, not observed facts or self-authenticating receipts.

| Action | Required model domains |
|---|---|
| READ_ONLY_ANALYSIS | None; model NOT_APPLICABLE for captured inert analysis only |
| CONTINUE_EDITING | WORKTREE, INDEX, REFS, OBJECTS, CONFIG, OPERATIONS, HANDOFF_STORE |
| RUN_TESTS | Base seven plus TEST_INPUTS, TEST_OUTPUTS |
| CREATE_CHECKPOINT | Base seven |
| PUBLISH_CHECKPOINT | Base seven plus DESTINATION_OBJECTS, DESTINATION_REFS, DESTINATION_CONFIG |
| REPAIR_KNOWN_FAILURE | Unsupported; UNKNOWN even with no cells |

Every relevant domain requires all nine channels, in fixed order:
WINDOWS_HOST, LINUX_DOMAIN, OTHER_LINUX_PEERS, OTHER_WSL, CONTAINER_OR_NETWORK,
ALIASES, PREOPENED_DESCRIPTORS, DEPUTIES, QUEUED_IO. Aggregated channels are conservative
categories; a future accepted environment must enumerate their concrete routes and justify
exclusions. This table is not proof that the real writer universe is finite or complete.
No caller-selected channel omission can create model YES.

At most108 cells are structurally possible. Current largest action requires90. Duplicate,
out-of-scope or out-of-order cells refuse. Empty/missing cells remain UNKNOWN. A model
contradiction produces model NO while retaining its exact pair; missing pairs remain explicit.
Project/action/generation mismatch, stale/future time or imported provenance yields UNKNOWN.
TTL is <=60 billion source-monotonic ns and never proves event continuity.

## Production boundary

All assessments return production_filesystem=UNKNOWN, production_p3=UNKNOWN,
mutation_authorized=false and NO_ACCEPTED_FILESYSTEM_ADAPTER, including all-YES scenarios.
There is no LIVE provenance, callback, adapter registration or route from this model into the
accepted verifier. The model does not generalize Linux containment to filesystem closure.

A later production design still needs independently enforced access to every concrete
worktree/Git/store/destination object, aliases and preopened capabilities; host/other-distro/
container/deputy coverage; pending-write completion; generation continuity; and use-time
revalidation under separately scoped authority. RO/R6 approval alone would not discharge these.
No privileged discovery was executed here.

Six tests cover every omitted/UNKNOWN pair in the90-cell publication scope, every single
contradiction in the63-cell checkpoint scope, Linux-only coverage, all actions, binding/epoch/
import refusal and malformed input. File/process creation is denied during the pure assessment
test. This is model conformance, not kernel or production acceptance.
