# CGC Live Continuity — 0.4 experimental

Baseline reconstructed before implementation: clean main/local tracking/live remote
63dd46037b9c62574058c0546cdac5c9caa3215f. The 0.3 release source is
9ab0435f60e1bdf6dd9f5c051d4dd7b5f57cc16b. Original repository is read-only;
upstream push remains disabled. This mission supersedes historical product stop notes.

## Current component map

| Existing component | Responsibility | Evolution |
|---|---|---|
| cgcchild.core.Workbench | Inert historical review | Retain independent model |
| cgcchild.gui | 13 PySide6 pages | Add Live Session, Timeline, Git, Tests, Errors |
| cgcchild.cli / sdk | Shared bounded product facade | Add explicit live operations |
| cgc.experimental | Historical protocols, capsules, MCP, reconciliation | Preserve semantics |
| plugins/cgcchild-readonly | Historical skill package | Retain; separate live plugin |
| sdk/javascript | Independent historical codecs | Add thin live event/client facade |
| packaging | Wheel, frozen GUI/CLI, Inno, archives, smoke | Extend existing release pipeline |
| tests/test_product* and test_child* | Existing Windows acceptance | Retain and add live tiers |

## New subsystem and authority boundary

`cgcchild.live` composes a Session controller, canonical versioned protocol,
redaction, segmented durable journal, metadata-only Windows filesystem observer,
read-only Git observer, explicit bounded test wrapper, evidence reconciler,
checkpoint/capsule builder and recovery assessment. GUI, CLI, Python SDK and local
MCP share this core. No hidden model reasoning or Codex session files are read.

Agent reports are REPORTED; independent observations are OBSERVED; specific
corroboration produces separate VERIFIED events. Reconciliation state is orthogonal.
Contradictions remain in the immutable history. Hash chains establish integrity,
not authenticity or truth. Imported capsules are always historical evidence.

The default store is `%LOCALAPPDATA%/CGCCHILD/sessions/<id>`. Each canonical event
is bounded and flushed; segment rollover binds the preceding event hash. A finite
overall session limit refuses further writes explicitly instead of dropping history.
Derived summaries/checkpoints use atomic replacement and can be rebuilt by replay.
Recovery preserves a torn final suffix as a digest-bound recovery artifact, removes
only that incomplete uncommitted suffix and continues the intact prefix. Complete
records are never rewritten; internal corruption refuses recovery. Single-writer
Windows file locking serializes writes across foreground clients, not project IO.

Filesystem polling uses Windows-native Python APIs on the explicitly selected
root and excludes reparse/credential boundaries. Polling can miss transient edits;
observations never imply exclusive access. Git commands are read-only. Explicit
test wrappers execute owner-selected tests and do not derive authority from events.
Managed Codex launch is optional and never required for observer-only operation.
No network listener, persistent service, host security change or production
repository executor is introduced. Checkpoints preserve evidence, not source code.

## Acceptance scope

Q1 protocol/journal/redaction/state; Q2 filesystem/Git/tests; Q3 adapters and real
Windows fixtures; Q4 complete guarded session; Q5 process death/truncation/replay;
Q6 GUI; Q7 wheel/frozen/installer/Node/plugin; Q8 source/manifest/asset digest release.
Clean VM, trusted signing, installed Codex lifecycle integration, hostile same-user
isolation, power-loss durability, filesystem closure and production P3 remain
separate acceptance debt. No unavailable proof blocks safe product engineering.

## Finite storage and replay contract

Event size is at most 32 KiB, sanitized payload at most 24,000 bytes, recursion at
most eight levels and string retention at most 2,048 characters. Segments rotate
at 1 MiB, with at most 64 segments and 20,000 events per session. Capacity refusal
is explicit; no history is silently dropped. Every event is fsynced. Windows
atomic replacement protects derived metadata and checkpoint/capsule publication;
power-loss durability and hostile same-user race exclusion are not established.
Filesystem samples cover at most 10,000 entries and 64 directory levels. Capsules
have 13 exact members, total decoded/archive bound 64 MiB and per-member 32 MiB.
No archive extraction occurs. Capsule indexes/summary are checked against replay.

Startup discovery examines at most 1,024 entries/256 sessions in CGC's selected
store. It reports unclosed history as requiring recovery review; it never silently
completes a session or marks a possibly active peer dead. Explicit recovery journals
INTERRUPTED -> RECOVERING -> RECOVERABLE; resume journals generation N -> N+1.
A missing, corrupt or mismatched final capsule makes a PRESERVED record incomplete.
The original corrupt artifact is retained by digest when recovery proceeds.

Implemented event vocabulary is defined by `cgcchild.live.protocol.EVENT_TYPES`.
Some types (for example optional bounded file-content verification) are reserved
protocol vocabulary and are not emitted by the metadata-only observer. REPORTED
events are never mutated into VERIFIED events. Verified commit evidence is scoped
to the local HEAD object; verified publication requires local/tracking/live equality;
test verification is scoped to the independently captured process exit and parsed
summary. No claim proves correctness of source code or authenticity of a same-user
producer. Next actions always enter as UNEXECUTED_FUTURE_ACTION, without execution.
