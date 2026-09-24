# Fixed native lab-protocol payload validation

[Native source](lab/child_protocol.c), [driver](lab/child_protocol_validate.py),
[evidence](lab/child_protocol_evidence.json).

M17 closes a previously unprivileged mechanical gap, not a privileged acceptance gate.
The freestanding C11/x86-64 image has one raw-syscall site and no interpreter, dynamic dependency
or undefined import. It refuses root, reads no argv/input/path, opens no sockets and performs
no broker operation. Embedded immutable vectors exercise a finite parser and encoder.

The parser accepts only canonical READY and the five fixed request operations from
[Protocol V1](V3_QUIESCENCE_LAB_ABI.md#4-cgc_lab_proto_v1). It validates literal key order,
lowercase32-hex fields, fixed cgcq- prefix, operation enum, uint64 decimal overflow/no leading zero,
epoch grammar, exact end and1024-byte ceiling. No general JSON engine or arbitrary method
dispatch exists. Parsed fields must equal the fixture's expected structure; native re-encoding
must reproduce the exact input bytes.

Normalized ancillary facts are explicit test inputs. Wrong credential counts/tuple, rights,
unknown control or truncation flags refuse in that model. They are not recvmsg observations,
live-instance binding or kernel authentication. Native CMSG walking, received-FD disposal,
reply encoding and lifecycle dispatch remain incomplete and block full M4/R6 readiness.

The generated corpus contains all19 inherited V-P vectors, six additional invalid sequence
forms, uint64 maximum, two ancillary model negatives, every high-bit single-byte mutation of
the six positive packets, and bounded truncations:1541 cases,7 positive/1534 negative.
No corpus bytes are supplied to a privileged process. The native fixture exited0 and both
same-environment builds were byte-identical. Source/driver/generated-header/image hashes,
flags and compiler/kernel identity are recorded. This is one measured build reproducibility
result, not a toolchain-independent guarantee.

First driver execution exposed eager evaluation of a missing default vector; explicit branch
selection fixed it. The next compile refused misleading indentation under -Werror; braces
fixed it without changing warning policy. The complete corpus then passed. Temporary build
directories were removed on failed and successful paths by the driver context manager.

Repeat only from Windows-controlled child cwd through Fedora:

```text
wsl.exe -d FedoraLinux-44 -- python3 -B /mnt/c/Codex-Projects/CGCCHILD/docs/lab/child_protocol_validate.py
```

Production source and inherited lab sources remain unchanged. No RO/R6, account, unit,
manager operation, cgroup, credential transition or production producer was executed.

## M20 native admission lifecycle and replies

[Model source](lab/child_lifecycle.c), [driver](lab/child_lifecycle_validate.py),
[evidence](lab/child_lifecycle_evidence.json).

This extends native mechanics after the M17 payload milestone. M18 separately exercised
actual ancillary receipt/disposal and M19 exercised an owned gated sender/pidfd. These are
separate fixtures, not one accepted broker image or composed security boundary.

The pure native lifecycle is NEW -> CREATED -> ATTACHED -> SEALED -> CLOSED, with terminal
INVALIDATED on malformed/unauthenticated/stale/out-of-order/uncovered requests. QUERY is
allowed only after creation; REMOVE requires SEALED and explicit modeled EMPTY, never UNKNOWN
or POPULATED. Neither CLOSED nor INVALIDATED reopens. At most8 accepted operations; sequence
wrap refuses before a modeled effect. Post-seal requests must carry the fixed fixture epoch.
All failures retire the modeled channel without a reply; authenticated INVALIDATED replies
are optional in the inherited contract and are tested as codec values only.

Effects are in-memory create/attach/remove counters. Authentication, controller/manager
continuity and domain emptiness are supplied synthetic booleans/enums. The seal epoch is a
fixed test constant, not a live generated nonce. There is no syscall dispatch, callback,
filesystem/cgroup/manager action or production result.

Native reply encoding inserts only RESULT=OK/INVALIDATED in canonical position; reply parsing
removes that exact finite field, applies the request grammar and requires byte-exact re-encoding.
No free text, arbitrary operation or general JSON decoder is introduced. Positive SEAL replies
contain the modeled new epoch. Negative cases cover unknown/duplicate RESULT, trailing bytes,
every high-bit mutation and bounded truncations.

The static nonroot fixture passed15 scenarios/49 transitions and636 reply cases
(2 positive/634 negative), with exact expected reply bytes generated independently in Python.
Source/driver/payload/generated-header/image identities are retained. No interpreter/import,
one syscall site, temporary directory removed. Full native D-Bus codec and composed filtered
B/C/W effects remain gaps; M4 stays PARTIAL, RO/R6 NOT_EXECUTED and real P3 UNKNOWN.

## M26: owned native request/reply session

[Source](lab/child_session.c), [driver](lab/child_session_validate.py) and
[evidence](lab/child_session_evidence.json) compose the payload and lifecycle prefixes with
actual nonroot socketpair messages. The parent is a broker MODEL and its fork child a fixed
controller fixture. Neither is a protected or privileged production identity.

The trusted prelude creates one SEQPACKET pair, enables per-message credentials on both ends,
creates a release gate, sets no_new_privs and lowers only the fixture FD limit to64.
Each role retains a pidfd for its peer. The receiver validates one credential record,
exact expected PID/UID/GID, flags and pidfd non-readiness; connection-time identity alone
is not accepted. This remains a point-in-time check, not atomic protected authorization.

Six fixed requests are CREATE, ATTACH, SEAL, QUERY, REMOVE and a late CREATE. The first five
receive exact canonical OK replies, parsed independently by the child. SEAL installs the
broker_sealed syscall filter before its reply. The sixth request is refused in terminal
CLOSED with no reply; closing the socket lets the child observe EOF and exit. Parent reaps
the exact child, observes readable pidfd and confirms descriptors3..63 empty.

Generated broker_sealed rules are a strict subset of broker_open; the final controller and
sealed broker deny filter installation, exec, socket creation, fork and ptrace.
Both peer directions have fixed send/receive FDs and flags. Scalar poll rules cannot inspect
pointed-to FD memory; fixed trusted code supplies it. The new receiver closes kernel rights
outside protected3/4 before refusing, but this session sends no rights packet; M24 provides
separate rights-test evidence. M25 full stat/type/access preflight is not yet composed here.

All effects remain the M20 counters. Continuity=1 and empty=1 are explicitly synthetic inputs,
even while the controller is alive. They make no claim that a real domain is empty or safe.
Generations/nonces remain fixed fixture values. No cgroup, filesystem mutation, manager
request, production producer or R6 operation occurs. Static ELF and source/prefix/filter/
vector/image hashes are retained; build directory removed. First compile/run passed.

Next: integrate the already tested FD identity checks into this bidirectional session and
test descriptor drift refusal without introducing a new authority surface.
