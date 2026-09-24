# Native fork/pidfd sender binding mechanics

[Source](lab/child_sender.c), [driver](lab/child_sender_validate.py),
[evidence](lab/child_sender_evidence.json). Nonroot disposable fixture, not protected-controller acceptance.

The static image creates one socketpair and gate, forks exactly one fixed child, and retains a
pidfd for that unreaped launch PID. The child sends two fixed READY messages, closes forbidden
ends and waits for a release token. The parent closes its unused ends, observes socket
connection credentials, then receives per-message credentials and compares them with the bound
child PID and inherited UID/GID. Parent/child keep the same UID; no authority separation is claimed.

The child is held alive at a known gate for the positive case. Its first message is accepted
mechanically only with the expected tuple and a non-readable retained pidfd. Connection
SO_PEERCRED identifies the original socketpair creator (the parent), while received credentials
identify the child. Using the parent identity as the expected sender is rejected.

After the parent releases the gate, waits for the exact child and observes pidfd readability,
the second queued READY message is refused. A closed pidfd poll also refuses. All child/parent
FDs are closed and the parent verifies no descriptor3..63 remains. No PID exhaustion/reuse is
induced; the retained handle remains attached to the dead instance after reaping.

The driver reuses exact source fragments from M17 payload and M18 ancillary handling, hashes
both generated prefixes, and checks static ELF properties. Only trusted fixed child messages
are emitted; this does not compose the M18 descriptor-attack inventory with the new parent
FD map. Unknown/rights-bearing hostile traffic and protected identity enforcement still need
a separately reviewed composed fixture.

New direct syscalls beyond the receive fixture are fork57, pidfd_open434, poll7, read0,
wait4:61 and getsockopt55. No exec, cgroup, manager, credential transition, root action or
R6 peer is present. Poll/receive are separate observations, not an atomic authorization
transaction; child death immediately after a liveness check remains a production race to
account for. Same-UID injection/controller authority remains unproved.

One compile initially refused ambiguous indentation under -Werror; braces fixed it. Review
then identified that poll errors must never look like a live instance. Explicit error/NVAL
refusal and a closed-pidfd negative case were added before the final passing execution.
The fixture reported two messages, one accepted live sender, differing connection identity,
and one refused dead queued message; exit0, exact child reaped, build directory removed.

The [UNIX socket contract](https://man7.org/linux/man-pages/man7/unix.7.html) distinguishes
connection-time and per-message credentials. That distinction is also directly witnessed
here; it is not a proof of closed admission, filesystem exclusivity or production P3.

## M23: composed role filters

[Filtered source](lab/child_filtered_sender.c), [driver](lab/child_filtered_sender_validate.py)
and [evidence](lab/child_filtered_sender_evidence.json) repeat the owned two-packet scenario
with actual per-role filters. No protected identity or privileged broker is introduced.

Trusted unfiltered setup closes inherited extras, sets no_new_privs, creates the socket/gate,
forks and acquires the child pidfd. The child closes parent ends then installs sender_filter.
The parent binds its own unreaped child PID into receiver_live after connection observations.
After exact child reaping it installs receiver_drain, a strict rule-set subset. Kernel filter
stacking cannot restore earlier denied operations. Each final role refuses further installation.

Sender allows sendmsg on3(flags0), read5(count1), close3/5 and bounded exit.
Receiver allows recvmsg4(flags MSG_CMSG_CLOEXEC|MSG_DONTWAIT), poll(count1,timeout0/2000),
GETFD on3..63, close3/4 and7..63, fixed32-byte report write1 and exit.
Live additionally allows one-byte gate write6, close6, wait4 for exact bound child(options0)
and seccomp installation for narrowing. Full scalar rules, generated instructions, relocation
slots and hashes are retained. Sizes:69 sender,747 live,689 drain instructions.

Poll points at user memory; seccomp cannot validate the pointed-to FD. Trusted fixed code,
not the scalar filter alone, supplies that FD. Likewise recvmsg/sendmsg ancillary memory
requires parser validation. No pathname/socket creation, exec/execveat, fork/clone3, namespace
change or ptrace is permitted after installation. Native probes verify these denials; wrong
send FD and wrong wait PID refuse. The drain role refuses gate writes/waits and broadening.

Both packets retain the M19 live/dead classification; child reaped and descriptors3..63 empty.
No SCM_RIGHTS packet was sent in this composition. Review identified a concrete next gap:
the inherited ancillary disposer assumes received descriptors7..63, whereas this profile has
free lower slots. It must not be claimed correct for hostile descriptor transfer yet.
M24 must bind disposal to the actual live/drain inventory and bound the owned FD limit.
This is not a production defect: these are separate disposable lab fixtures only.
