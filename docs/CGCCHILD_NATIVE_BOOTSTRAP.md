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
