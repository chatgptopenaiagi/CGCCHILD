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


## M77: owned Windows sharing fixture

[Fixed fixture](lab/child_windows_share.py) and [captured evidence](lab/child_windows_share_evidence.json).
This script accepts no paths or arguments. It creates only a bounded temporary directory
under the Windows temporary root, verifies that absolute boundary, and closes owned handles
before cleanup. It does not run against either repository or inspect unrelated processes.
No privilege is enabled. Source hash uses UTF8/LF-normalized bytes; evidence is historical,
not authenticated or a current filesystem receipt.

OBSERVED_FACT on Windows10.0.19045/Python3.14.7/NTFS, two completed fixture runs:

| Test | Exact observation |
|---|---|
| Existing data-write handle, SHARE_ALL | Opening READ/SHARE_READ guard fails error32 |
| Held READ/SHARE_READ file guard | New WRITE/SHARE_ALL open fails error32 |
| Compatible read | Opens and matches volume/file-index handle identity |
| Guard closed | WRITE open succeeds and exact replacement bytes are read back |
| Held READ/SHARE_READ directory handle | Existing child data write succeeds |
| Same directory guard | New child creation/write succeeds |
| Verified same-object hard-link alias | Write open through alias fails error32 |
| Cleanup | Zero owned active handles; temporary directory removed |

All handle operations occurred in the one owned fixture process. The directory was opened
with FILE_FLAG_BACKUP_SEMANTICS, without adjusting process privileges. No assertion of
cross-process, cross-OS, system-wide or production coverage follows from these observations.

DERIVATION: this tested directory-handle mechanism cannot establish recursive closed writer
admission. A per-file sharing guard is only a candidate ingredient. It neither enumerates
new names nor closes the complete repository mutation domain. The hard-link case covers one
constructed alias, not every alternate route. PID absence and Linux containment remain
independent of this filesystem proof obligation.

The official [CreateFileW contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
describes incompatible access/sharing failures and handle-lifetime sharing restrictions.
It separately excludes attribute/extended-attribute access from those sharing flags. This
supports the narrow intended mechanism, not a claim of recursive exclusion or full quiescence.

UNKNOWN / NOT_EXECUTED: writable mappings, pending writes, metadata writers, alternate streams,
other processes, WSL/distro/container paths, hostile aliases/reparse changes, manager/deputy
routes, controller death and complete domain enumeration. No observed result changes real
filesystem exclusivity or P3 from UNKNOWN. No production exclusion adapter is implemented.

Next bounded work: challenge the same owned-file guard with a preexisting writable mapping
and a metadata-only write. This can refine two concrete gaps without touching a repository,
calling privileged interfaces or assuming a directory-wide exclusion exists.


## M78: retained views and metadata writers

[Fixed fixture](lab/child_windows_mapping.py), [evidence](lab/child_windows_mapping_evidence.json).
Two owned Windows10.0.19045/Python3.14.7 runs completed, with no privilege/configuration change.
All paths are fixed children of a freshly allocated, boundary-checked temporary directory.
All mappings/handles are tracked and closed before owned-directory cleanup; no user paths.

OBSERVED_FACT:

1. Create a PAGE_READWRITE mapping and FILE_MAP_WRITE view of a4096-byte owned file.
2. Close the ordinary file handle and mapping handle; retain only the mapped view.
3. READ/SHARE_READ guard acquisition still fails ERROR_SHARING_VIOLATION32.
4. The retained view writes eight fixed bytes; after flush/unmap, ordinary read verifies them.
5. After unmapping, the same guard acquisition succeeds.
6. While that guard is held, FILE_WRITE_ATTRIBUTES/SHARE_ALL open succeeds. SetFileTime changes
   the last-write timestamp; GetFileTime on the still-held guard observes the exact new value.
7. Zero owned views/handles remain and the temporary directory is removed.

DERIVATION: ordinary file-handle closure is not disappearance of every writable capability.
The tested mapping blocked guard acquisition, rather than silently becoming quiescent. A
successful data-read sharing guard does not exclude metadata writes, demonstrated directly.
Flushing this view and reading back bytes is not a power-loss durability or global pending-I/O
proof. These results refine the mechanism; they do not provide a production filesystem gate.

The official [mapping contract](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-createfilemappingw)
describes retained view references and the need to unmap views as well as close mapping handles.
[SetFileTime](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfiletime)
requires the appropriate attribute-write access. Neither API authenticates a CGC proof claim.

UNKNOWN: other-process mappings, alternate streams/reparse paths, pending asynchronous I/O,
WSL access, other distros, external deputies, and full namespace admission. Historical M77
limitations remain historically accurate; this section supplies only the tested refinement.
Production filesystem exclusivity and P3 remain UNKNOWN; producer NOT_STARTED.

Next: owned Windows-temp/Fedora interoperability witnesses, with bounded subprocess pipes
and explicit cleanup. Challenge a Windows-held guard using one Fedora write-open; separately
challenge a Fedora-held advisory flock with one Windows write-open. Do not generalize either
outcome to other mounts/distros or claim full cross-OS closure.
