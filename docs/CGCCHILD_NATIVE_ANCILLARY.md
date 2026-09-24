# Native ancillary receive/disposal mechanics

[Source](lab/child_ancillary.c), [driver](lab/child_ancillary_validate.py),
[evidence](lab/child_ancillary_evidence.json). EXPERIMENTAL mechanical fixture; M4 remains PARTIAL.

The driver compiles a static freestanding x86-64 image using the exact M17 payload-source prefix.
No inherited source is modified. One nonroot process creates an unnamed AF_UNIX SOCK_SEQPACKET
pair and pipe; there is no listening path, external peer, fork, root broker, manager or R6 role.
The process sends fixed READY bytes to itself, allowing receive mechanics to be tested separately
from caller authenticity.

The x86-64 msghdr/cmsghdr/ucred sizes are compile-time checked. A112-byte aligned receive-control
buffer accounts for one credential record and up to16 FDs. The walker bounds every header/length/
alignment step, counts credentials/rights/unknown controls, and closes each received FD before
deciding whether to accept the packet. Real credentials must equal this fixture's getpid/getuid/
getgid observations. Only after that comparison are the M17 dummy ancillary constants used for
the already tested payload model. This normalization does not create a live controller binding.

The native inventory first excludes inherited FD3+ via close_range, then requires exactly
FD0..6 before and after every receive. Received duplicates occupy7..22, are checked for CLOEXEC,
and are closed even though their presence rejects the packet. Truncation never means acceptance.
The kernel handles excess rights in the deliberately truncated ancillary case; the unchanged
post-receive inventory is the exact observed no-leak evidence in this fixture.

[UNIX socket semantics](https://man7.org/linux/man-pages/man7/unix.7.html) describe per-message
SO_PASSCRED credentials and rights transfer; [recvmsg](https://man7.org/linux/man-pages/man2/recvmsg.2.html)
defines ancillary truncation and MSG_CMSG_CLOEXEC. Documentation supports the test design;
the retained output records the actual installed-kernel result.

| Case | Observed result |
|---|---|
| Complete own credentials and canonical READY | Accepted mechanically |
| Expected PID deliberately different | Refused |
| One received pipe descriptor | Refused; descriptor closed |
| Payload buffer capacity8 | Refused; no inventory change |
|16 rights with control capacity32 | Refused; no inventory change |
| SO_PASSCRED disabled for one message | Refused |
|32 iterations with16 rights each | Refused; all512 duplicates explicitly closed |

Total38 messages and513 explicit received-FD closures; maximum received FD22; exit0.
The image has one syscall veneer and no imports/interpreter. Its direct syscall set is
getpid39/getuid102/getgid104, close_range436, socketpair53, pipe2:293, setsockopt54,
sendmsg46, recvmsg47, fcntl72, close3, write1 and exit60. No filter/containment claim follows.
All socket/pipe objects and build directories are disposed at process/context exit.

Missing gates include independently launched caller identity, retained pidfd/channel binding,
credential transitions, anti-injection, raw malformed ancillary structural corpus, reply/state
dispatch and composed per-role filters. Real cgroup/manager/filesystem closure remains unproved.
RO-1..RO-5 and R6 remain NOT_EXECUTED; production quiescence remains NOT_STARTED.
