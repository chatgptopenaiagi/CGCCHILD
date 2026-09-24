# Experimental staged native bootstrap

Status: IMPLEMENTED / NONPRIVILEGED INERT FIXTURE VALIDATED. Not R6, a production
broker, a filesystem proof or an accepted privileged bootstrap. Historical source M4
tables remain unchanged. Reproduce from the child directory with:

```powershell
wsl.exe -d FedoraLinux-44 -- python3 -B /mnt/c/Codex-Projects/CGCCHILD/docs/lab/child_bootstrap_validate.py
```

The Python harness reads repository source but compiles, runs and creates all experiment
objects under its own Linux-native `/tmp/cgcchild-bootstrap-*` directory. No dependency
installation. Native image refuses root. No D-Bus connection, cgroup write or credential drop.

## Boundary revision

An inherited union covering future peer rights is not a setup-only policy. This child
experiment instead has an explicitly trusted **unfiltered prelude**. It closes FDs above2,
sets no_new_privs/nondumpable, creates a private inert directory and regular membership file,
creates two gates and forks one child. There is no attacker-controlled code or exec branch.
The prelude is not accepted as an independent security boundary against hostile same-UID peers.

The child closes broker descriptors, checks its bounded FD inventory, installs its final
filter, emits READY and waits for a one-byte release. Parent retains the unreaped child
relationship, specializes three generated comparison slots to that exact PID, installs B_BOOT
and obtains its pidfd. Wrong PID acquisition is denied. READY precedes the inert membership
write/readback. The parent closes the membership FD, installs B_SEALED and releases the child.
Child termination is waited for using the exact PID; the retained pidfd becomes readable.

This fixed image has no signal handler or competing reaper. The launch contract must preserve
the unreaped-child condition before pidfd acquisition; it must not be generalized to arbitrary
PID lookup. See [pidfd_open lifecycle conditions](https://man7.org/linux/man-pages/man2/pidfd_open.2.html).
The stacked filter only narrows; seccomp checks scalar arguments, not pointee contents or
filesystem ownership. See [kernel filter semantics](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html).

## Exact fixture stages

The immutable Python tables are the executable rule specification. Default EPERM;
unsupported architecture and x32 kill. All stages allow exit60 status0..255.

| Stage | Additional allowed operations | FD/identity specialization |
|---|---|---|
| Trusted prelude | getuid102, close_range436, prctl157 options38/4, mkdir83, openat257, pipe2293, fork57, close3, fcntl72, seccomp317 | Fixed literals and branches in C; not filtered |
| B_BOOT | read0, write1, close3, poll7, pread6417, wait461, pidfd_open434, seccomp317 | READY read7 count1; membership write/pread4 <=20 offset0; release write6 count1; closes3/4/5/6/7; poll one entry timeout0; wait exact child options0; pidfd exact child flags0; seccomp mode1 flags0 |
| B_SEALED | write1, close3, poll7, wait461 | Strict subset: release6 count1; closes3/5/6/7; poll one entry timeout0; wait exact child options0 |
| Child final | read0, write1, close3 | gate read5 count1; READY write8 count1; close5/8; no fork, exec or additional filter |

FD0..2 are harness stdin/stdout/stderr. Parent dir3, inert file4, gate read5/write6,
READY read7/write8 before fork. Parent closes5/8, pidfd allocation must return5. Child
closes3/4/6/7 and retains only0/1/2/5/8. Native fcntl confirms no unexpected FD below64;
close_range before allocation excludes higher inherited FDs. This is a fixed owned-fixture
inventory, not object-identity attestation for a privileged controller. No descriptors are
received from peers. The regular file is deliberately named `membership.inert`.

## Evidence and remaining gates

[C source](lab/child_bootstrap.c), [generator/driver](lab/child_bootstrap_validate.py),
and [recorded evidence](lab/child_bootstrap_evidence.json) are retained. Compilation uses
freestanding static C11/x86-64, no interpreter, imports or dynamic dependencies. Disassembly
contains one raw syscall veneer. Source/image digests, compiler/argv, full filter instructions
and exact PID-relocation slots are recorded. Model checks cover deterministic generation,
instruction bound, unsupported arch/x32, every allowed clause and three PID specializations.
The B_SEALED clause set is a strict subset of B_BOOT. Kernel fixture exited0, including wrong
PID, post-seal write/open/pidfd/filter-broadening denials and child exec/socket/filter denial.

Both development runs passed. The second added native inventory/model checks; its evidence
is canonical for this milestone. Temporary directories were removed by the harness. Parent
failure closes release pipe; child receives EOF and exits. A timeout kills only the owned
fixture parent; EOF permits its child to exit, but failure cleanup is not a production guarantee.

M1/M3/M4 remain PARTIAL: actual C/W credentials, controller authentication, peer filters,
native incoming codec and privileged cgroup FD attestations are not implemented here. No
full native broker conformance or continuously closed admission is claimed. RO/R6 remain
NOT_EXECUTED. Filesystem exclusivity and real-project P3 remain UNKNOWN. Production producer
remains NOT_STARTED. This milestone isolates the native setup mechanics so independent
refusal interfaces can advance without granting authority to synthetic records.

## M31: child conformance reconciliation

This section supersedes only current child status, not historical source acceptance.
The15 retained child native source/evidence pairs match their recorded SHA256 at this audit.
Drivers with recorded digests also match. Native execution is evidence of the named fixture,
not proof that every component has been composed into a future privileged image.

| Component | Child evidence | Actual execution | Remaining boundary |
|---|---|---|---|
| Trusted prelude/inert membership | M1 | Owned nonroot file, gates, child and filters | Protected bootstrap, real cgroup and credentials absent |
| Payload/canonical replies | M17/M20 | Native finite parsing and negative corpus | Fixed model generations, no authenticated issuance |
| Ancillary/received rights | M18/M24 | Kernel socket credentials, truncation,48 closures in composed layout | Only specified kernel-origin buffers and inventories |
| Launch instance | M19/M23 | Retained pidfd, live/dead queued message, filtered syscalls | Point-in-time observation; same-UID injection not excluded |
| FD identity | M25/M27 | Creation-bound type/access/stat checks and substitutions | Not OFD identity or filesystem exclusivity |
| Admission session | M26/M27 | Six requests/five replies, monotonic filters | Effects counters; continuity/empty synthetic |
| Incoming D-Bus | M21/M29 | Typed decoder and bounded fragmented/coalesced frames | No bus connection or live request scheduler |
| Outgoing D-Bus | M22 |11 exact native frames,3862 short-buffer refusals | Dummy targets; runtime manifest/launch adapter absent |
| EXTERNAL transcript | M28 |85 lines,2489 split runs | Encoded is not sent; no authenticated connection |
| Owner/request correlation | M30 |21 scenarios/107 steps | Synthetic generation/disconnect/reexec events |
| Original16 profile candidates | Inherited d7cb evidence | Not rerun without cause | Not accepted final privileged role policy |

Wrong-architecture/x32 checks in the child generators are interpreter/model checks.
Named child role filters were actually installed in their owned kernel fixtures, with
specified syscall-denial probes. Neither class implies privileged or production acceptance.
All production-accepted cells remain false. The original M4 generic/native branch gaps are
reduced by these fixtures, not declared universally resolved.

Canonical proof gates remain:
- M1 PARTIAL: identity allocation and authorized privileged launch not executed.
- M2 PARTIAL: installed effective manager/deputy policy still needs scoped RO approval.
- M3 PARTIAL: real root-to-C/W transition and uninterrupted anti-injection proof absent.
- M4 PARTIAL: tested native components; final protected image/runtime manifest and actual
  credential/owned-object policy specialization not implemented or accepted.
- M5 PARTIAL: live system-manager continuity/reexec and system-unit survivor proof absent.
- RO-1..5 and R6 NOT_EXECUTED; filesystem exclusivity/P3 UNKNOWN; production producer NOT_STARTED.

The next dependency-safe master-plan work is portable inert capsule interoperability in the
existing Node SDK. The model-state0.1 codec and capsule0.1 bytes already have stable pinned
Python evidence. A Node capsule implementation can be independently tested without privileged
proof, network/host configuration or broadening the model-only SDK into full V3 acceptance.
Full continuity0.2 remains explicitly unsupported by that SDK until its own validator exists.

Audit checks:92 tracked Python ASTs,24 JSON files,15 native source hashes and88 relative links
in child documents pass. Canonical inherited modifications are only authorized child banners
in README/AGENTS; original runtime/tests/missions/license remain unchanged. Original live
main is still d7cb43de3ac001bf28470d6d2f561ed70f106e6a, and its sole untracked owner plan remains.
Child repository remains private. No original push, privileged read or host configuration
change occurred. Full Linux468 tests remain the latest runtime regression; B11 remains UNKNOWN.

## M35 composition update

The sixteenth retained child fixture composes inert AUTH/frame/request-owner state and passes
66 scenario runs. See [native D-Bus evidence](CGCCHILD_NATIVE_DBUS.md#m35-composed-inert-authentication-framing-and-correlation).
The protected-image, real-credential, runtime-manifest and live-policy boundaries above remain.
Composition here does not supply a live transport, authenticated manager or production producer.

## M48 repeatable retained-source audit

Run from CGCCHILD:

~~~text
python -B docs/lab/child_evidence_audit.py
~~~

The [read-only auditor](lab/child_evidence_audit.py) checks a fixed21-fixture inventory and65
bounded regular source/evidence files, importing no fixture and running no compiler/process.
It verifies current raw source/driver bytes against the retained digests, including selected
source prefixes, query sources and recorded filter-generator source. Fixed binding/header sets
prevent removal of a covered field from silently reducing audit coverage. Duplicate JSON keys,
missing/oversized files, wrong hashes, nonregular artifacts and unknown prefix headers refuse.
There is no caller-selected path, fixture selector or execution option on the CLI.

Five [test families](../tests/test_child_evidence_audit.py) pass on Windows and Fedora, including
changed source/driver, missing source, omitted binding, malformed header sets and duplicate JSON.
One test deliberately replaces both source and its expected hash: consistency still passes,
while production acceptance remains false and live proof UNKNOWN. This explicitly demonstrates
that the auditor is not source authentication. Reads are bounded point observations of a trusted
workspace, not an atomic filesystem snapshot or protection from concurrent hostile replacement.

The earliest bootstrap evidence has no driver hash: UNRECORDED is reported, never inferred.
Generated headers, preprocessed output, stream/vector bytes and removed binaries are NOT_REBUILT;
current fixture execution is NOT_EXECUTED. Their historical digests/results are not revalidated
by this audit. No historical test was repeated merely to obtain a current green label.

## M49 inert kernel effects before model acknowledgement

[Fixture](lab/child_effect_session.c), [driver](lab/child_effect_session_validate.py),
[evidence](lab/child_effect_session_evidence.json).
This twenty-second native fixture composes fixed lifecycle packets with owned Linux-native
regular-file effects. CREATE first derives a candidate state, then exclusively creates its
private domain/membership file, then commits the state and canonical model acknowledgement.
ATTACH launches one gated child, binds its retained pidfd while unreaped, waits for readiness,
writes its decimal PID to the owned regular file and reads it back before committing the
candidate. PID text is inert test data, never a write to cgroup.procs or an arbitrary PID input.

SEAL closes the writable membership FD and installs a narrower filter before acknowledgement.
QUERY observes the still-gated child's pidfd as not ready. The fixture releases and reaps only
that child, verifies pidfd readiness, removes its own file/directory, and only then commits
REMOVE. Candidate dispatch counters are not published as completed effects before success.
These acknowledgements are local model commits; no C-to-B authenticated IPC is claimed here.
The protocol authenticated/continuity inputs remain synthetic. No filesystem exclusivity follows.

Three cases pass: five successful model acknowledgements after effects; CREATE collision with
zero acknowledgements and untouched pre-existing fixture material; injected closed membership
FD during ATTACH with only the earlier CREATE acknowledged and no attach counter committed.
The failure case invalidates proof, releases/reaps its owned child and removes only its own
objects as fixture cleanup. It does not reopen admission or claim successful ATTACH/REMOVE.
Two exact children are reaped per run. Worker gate polls are bounded to2000ms. The driver gives
its owned session10s; timeout cleanup targets only that fixture's process group. No timeout
was observed. Normal filesystem cleanup is independently checked by the driver.

Review corrected a boolean poll helper that conflated errors with not-ready. The final helper
returns separate error/not-ready/ready values, and an invalid FD must produce error. Two final
builds/runs have identical static image SHA256:
78ede121cea879719aa1622538c0db7db581b91a7749f836314f4b16b4a91625.
The three generated role policies retain exact owned-child PID comparisons; b_boot to b_sealed
is a strict rule-set narrowing. Actual post-seal write/open/filter-regain denials are checked.

Pathname and poll-buffer contents are trusted native literals/memory, not enforced by scalar
seccomp. mkdir/open occur in the disposable trusted prelude; teardown allows unlinkat on the
owned directory FD and rmdir of the fixed relative domain path. This is not a sandbox against
compromised native code or same-UID peers. Worker/control credentials are not separated.
No real broker, cgroup, RO/R6, privileged action or production runtime was implemented.
The static evidence auditor now explicitly covers22 fixtures/68 files; five audit tests pass
on Windows/Fedora. Build directories and owned test objects were removed.

## M50 malformed/stale requests refuse before the next inert effect

[Fixture](lab/child_effect_rejection.c), [driver](lab/child_effect_rejection_validate.py),
[evidence](lab/child_effect_rejection_evidence.json).
The twenty-third fixture extends M49's owned effect path with17 fixed negative packets before
CREATE or after one successful CREATE: truncation, wrong generation, future/stale sequence,
wrong epoch, wrong operation phase, duplicate key, extra pathname field and trailing data.
The exact parser/dispatcher runs before the next effect. Refusal invalidates the active model
without copying candidate success counters; a subsequent correct packet also refuses.

All17 negative cases pass with zero worker launches. Before CREATE, no domain is created;
after CREATE, one acknowledgement remains, attachment count stays zero and the membership
file remains empty before fixture-owned cleanup. The earlier positive, collision and injected
ATTACH failure cases run in the same image and pass. The driver verifies expected remaining
objects in each owned directory. Authentication/continuity inputs remain synthetic; these are
not hostile live controller requests and are not R6 tests.

Two final builds/runs are byte-identical with image SHA256:
77546888edf8f53e4cb3820b63f7a0a2d16ed56e1efd232a88bfe35f73bedfe5.
No new syscall/filter allowance is added; bad-packet branches stop before worker/bootstrap
filter setup. Owned children from the two earlier effect cases are reaped and temporary
builds removed. The static auditor explicitly includes23 fixtures/71 files. Unknown malformed
cases outside this finite corpus are not claimed tested; syscall pointer and same-UID trust
limitations from M49 remain.

Next composition issue: a live C channel and a subsequently created W need separate retained
launch handles. The current fork-then-pidfd pattern specializes predicates after birth, which
complicates an already-filtered B setup. Before broadening PID lookup, evaluate whether the
installed kernel's unprivileged clone3/CLONE_PIDFD can return an owned-child handle atomically
in a bounded disposable fixture. Existing final-role clone3 denial must remain unchanged.
An unavailable capability must refuse; this is not permission for privileged launch or R6.

## M51: atomic owned-child launch capability

OBSERVED_FACT: the nonroot x86-64 fixture uses raw clone3(435), an88-byte
clone_args with flags=CLONE_PIDFD(4096), exit_signal=SIGCHLD(17), a parent
pidfd output pointer, and all remaining fields zero. Three runs per build
passed; two final builds/runs produced identical evidence and static ELF bytes.
The installed header defines the same88-byte layout. The child retains a copied
address space/stack; no thread, namespace, selected PID or cgroup is requested.
The [Linux clone manual](https://man7.org/linux/man-pages/man2/clone.2.html)
specifies the launch-returned pidfd, automatic CLOEXEC and separate copied stack
when CLONE_VM is absent. These semantics support the narrow observed result.

Parent inventory: pipe3/4, returned pidfd5. Child inherits pipe3/4 but not the
new parent pidfd; it closes4, waits at most2000ms for byte G on3, then exits.
Parent checks pidfd CLOEXEC and not-ready while gated, releases the child,
observes readiness, reaps the exact returned child PID/status, checks readiness
again and closes every extra FD. Invalid FD63 produces an observation error.
The driver bounds each process to6s, owns its process group for timeout cleanup,
and removes Linux-native temporary build files. No timeout occurred.

[Source](lab/child_atomic_launch.c), [driver](lab/child_atomic_launch_validate.py),
[evidence](lab/child_atomic_launch_evidence.json). No dynamic interpreter/imports;
one raw syscall veneer. Source operations map to getuid102, close_range436,
prctl157(NNP/nondumpable), pipe2 293, clone3 435, poll7, fcntl72(GETFD), read0,
write1, close3, wait4 61 and exit60. No generic argv, exec or PID lookup surface.
ENOSYS/EPERM are explicit unavailable outcomes; other launch errors remain unresolved.

DERIVATION: a later trusted launcher could obtain two separate launch-bound handles
without pidfd_open on arbitrary integer PIDs. UNKNOWN: full broker/channel/effect
composition and filtered launch acceptance. This fixture installs no seccomp filter.
cBPF cannot dereference clone_args, so permitting clone3 by pointer/size does NOT
prove its pointed-to flags immutable. Do not widen final C/W filters on this evidence.
Next compare scalar raw clone(CLONE_PIDFD|SIGCHLD), which exposes flags directly,
against the same bounded owned-child lifecycle before selecting a bootstrap policy.
Production acceptance=false; R6=NOT_EXECUTED; filesystem exclusivity/P3=UNKNOWN.

## M52: scalar atomic launch under inherited narrowing filters

OBSERVED_FACT: raw x86-64 clone56(flags=0x1011, stack=0, parent_tid=&pidfd,
child_tid=0, tls=0) launches one owned child and returns its pidfd under a
207-instruction bootstrap filter. The scalar flags combine CLONE_PIDFD and SIGCHLD.
Both branches inherit that filter and stack another: child85 instructions,
parent141. Their immutable rule sets are strict subsets of the bootstrap set;
architecture mismatch/x32 kill is model-checked, default syscall denial is EPERM.
Kernel fixture checks reject clone3, wrong flags, shared-VM flags and nonzero
stack before launch; after narrowing both branches reject clone and broader
filter installation. Parent also checks exec/socket/pidfd_open denial.

The parent observes the same pipe3/4/pidfd5 lifecycle as M51, then uses
waitid(P_PIDFD=3, id=5, WEXITED=4) with null rusage, checking SIGCHLD,
CLD_EXITED, matching returned child PID and zero status. No arbitrary PID lookup
or broad wait4 rule is introduced. FD numbers are justified by the owned launch
sequence; they are not universally authentic identities. GETFD queries allow3..63
for the final no-extra-FD check, not FD mutation. poll pointer contents remain
trusted native code, not cBPF-enforced. The pidfd output pointer writes caller
memory only; no CLONE_VM is allowed. Trusted bootstrap still has repeat-launch
capability until it narrows: this is not an untrusted broker/worker acceptance.

[Source](lab/child_scalar_launch.c), [driver](lab/child_scalar_launch_validate.py),
[evidence](lab/child_scalar_launch_evidence.json). Three runs per final build pass;
two final builds/evidence are identical. One static raw syscall veneer, no dynamic
imports. M51 syscall map changes: clone56 replaces clone3 launch; waitid247 replaces
wait4; seccomp317 installs filters; exec59/socket41/pidfd_open434/clone3 435 are
negative probes. NNP/nondumpable and pipe creation precede filter installation.
No privileged change, cgroup, bus, R6 or production code. Temporary builds removed.
LF attributes now explicitly preserve M51/M52 source/driver digest bytes on Windows.

DERIVATION: scalar launch can avoid the clone3 pointed-to-flags gap for this fixed
process form. UNKNOWN: two separately bound live C/W roles and composed effect
channel. Next build a two-owned-child launch/handle-separation fixture using the
same scalar restriction and pidfd-based waits before attempting full composition.

## M53: two owned launch handles stay separate across both release orders

OBSERVED_FACT: fixed C/W analogue children are launched through scalar clone under
an inherited297-instruction bootstrap filter. Gates are3/4 and5/6; launch pidfds
are7 and8. C never inherits its parent pidfd; later W inherits C's pidfd7 and
explicitly closes it before checking its sole extra gate FD5. Both children
check bounded FD3..63 inventories and CLOEXEC; C retains only3, W only5.
Each narrows before gate use (C123/W133 instructions); B narrows to215 after the
second launch. All three rule sets are strict bootstrap subsets. Both children
and B test refusal to clone or reinstall bootstrap after narrowing.

Two fixed compiled release orders, three runs each: release one child, observe
only its pidfd ready while the other remains gated, reap through that exact pidfd
and verify the returned PID/status, then release/reap the second. Parent closes
its gates/pidfds and verifies no FD3..63 remains. No cgroup, manager or credentials
are changed. Readiness is bounded2000ms; driver deadline6s/group cleanup applies
only to its own fixture. No timeout occurred. Two final builds produce identical
per-order images/evidence, with no dynamic imports or binary retained.

[Source](lab/child_dual_launch.c), [driver](lab/child_dual_launch_validate.py),
[evidence](lab/child_dual_launch_evidence.json). Exact syscall inventory: read0,
write1, close3, poll7, clone56, exit60, fcntl72, getuid102, prctl157, waitid247,
pipe2 293, seccomp317, close_range436. Filters do not inspect poll memory.

Development failure preserved: first C-only ELF entry build exited SIGSEGV(-11).
An explicit assembly entry now aligns rsp to16 bytes and CALLs the C entry,
establishing the System V function-entry stack convention. The same lifecycle
checks then passed; driver verifies the alignment/CALL in each image disassembly.
Stack alignment is the supported correction; the exact original fault address
was not captured. No filter or lifecycle assertion was weakened.

DERIVATION: independently launched owned handles can coexist without later generic
PID lookup. UNKNOWN: authenticated C requests actually triggering W effects. These
are same-UID trusted fixture branches, not protected identities or closed admission.
Next compose the bound C request channel with the inert effect sequence using
launch-time W pidfds, retaining per-message identity and FD checks.

## M54: authenticated owned channel composed with inert effects

OBSERVED_FACT: one fixed B/C/W image now joins M27 per-message credential/live-pidfd
checks, native protocol/lifecycle parsing and M49 effect-before-ack ordering.
B's trusted prelude captures its own pidfd, a private SO_PASSCRED seqpacket pair,
a worker gate and the owned temporary cwd descriptor. Scalar atomic launches bind
C and later W without post-filter pidfd_open or PID relocation. The fixture checks
FD dev/inode/type/owner/access/CLOEXEC against captured objects before channel use.
Unexpected SCM_RIGHTS is rejected and received holes are closed, preserving the
expected inventory. Earlier rights/hostile sender fixtures remain historical tests;
this composition milestone runs only the positive dialogue and final closed refusal.

Exact initial FD inventory:3 C socket,4 B socket,5 B pidfd,6/7 W gate,8 owned cwd.
C launch produces parent pidfd9; C closes4/6/7/8, retains3/5. CREATE produces
owned domain directory10 and membership regular file11. ATTACH launches W with
parent pidfd12; W closes3..11 except6, checks its inventory, narrows, and waits.
B writes W's returned PID decimal to file11 and reads it back before ACK. B closes
3/5/6 after attachment, closes11 at SEAL and narrows. QUERY observes W still gated.
After its reply B releases/reaps W via pidfd12; REMOVE is permitted only afterward,
unlinks the owned file/domain and closes10/8. The sixth post-CLOSED request is
refused without reply; B closes4, C sees EOF/exits, B reaps C via9. Extra FDs absent.

Filters: bootstrap1043, sealed843, C739, W723 instructions; all final rules are
strict bootstrap subsets. Default EPERM; unsupported arch/x32 KILL model checks.
The bootstrap permits fixed scalar clone and fixed-dirfd file operations. Pointer
contents (including literal pathnames and poll arrays) remain trusted native-code
obligations; syscall rules are not path/DAC proof. C/W final rules contain no clone,
exec, socket creation, openat, ptrace, namespace or filter-install authority.

[Source](lab/child_channel_effect.c), [driver](lab/child_channel_effect_validate.py),
[evidence](lab/child_channel_effect_evidence.json). Three runs/build pass, two final
build/evidence sets match. Static ELF, one syscall veneer, no dynamic imports.
Raw syscall map:0 gate read;1 membership/gate writes;3 close;5 fstat;7 poll;17
membership pread;39/102/104 current credentials;46/47 fixed-channel messages;53/54
prelude socketpair/SO_PASSCRED;56 scalar launch;60 exit;72 FD flags;157 restrictions;
247 owned pidfd wait;257/258 owned file/domain creation;263 owned removal;302
fixture-only FD limit64;317 filters;434 prelude self pidfd;436 initial FD closure.
All temporary Linux-native builds/objects removed. No timeout or privileged action.

Development correction: -Werror caught the omitted reply_parse call while it was
unused in the first composition. Restored finite reply parsing alongside byte
comparison; did not remove the warning or parser. No failing runtime claim retained.
UNKNOWN: continuous controller liveness between request check and effect, adverse
packet/effect/cleanup composition, protected credentials, cgroup/manager policy.
Generations and manager continuity remain synthetic. This fixture never establishes
closed admission, filesystem exclusivity or production P3. R6 remains NOT_EXECUTED.
Next exercise fixed pre/post-CREATE bad controller packets against this actual
channel/effect composition, proving no subsequent effect or admission reopening.

Static audit initially refused the expanded pretty-printed filter evidence above its
262144-byte bound. Canonical compact instruction rows reduced evidence size without
removing any instruction or increasing the validator bound. Both audit suites rerun.
