# CGCCHILD native incoming D-Bus mechanics

M21 is an experimental, nonprivileged parser fixture, not a transport or manager client.
[Source](lab/child_dbus.c), [driver](lab/child_dbus_validate.py) and
[recorded execution](lab/child_dbus_evidence.json) are independently reviewable.
The driver generates immutable frames using the inherited Python analogue; the C
decoder independently checks their bytes and exact typed results.

## Finite scope

Only incoming METHOD_RETURN, ERROR and SIGNAL are accepted. Outbound method calls
are refused by direction; this is not evidence that their nested bodies were checked.
The existing outbound encoder and full native bootstrap composition remain separate gaps.

The decoder permits little-endian protocol version1, flags bits0/1 only, nonzero serial,
65536-byte maximum frame/body and4096-byte header. Every cursor read uses subtract-before-add
bounds, with zero padding, ASCII strings, terminators and object-path grammar checked.
No allocation, recursive variant parser, path opening, socket or manager operation exists.

Header codes1..8 have fixed variant types; duplicate/unknown fields and code9 UNIX_FDS
are refused. Header order may vary. This child profile additionally restricts field sets:
returns5/6/7/8; errors4/5/6/7/8; signals1/2/3/6/7/8. It is deliberately narrower than
the inherited analogue, which does not enforce these per-kind masks.
Sender must match the compiled expected context; replies must match its reply serial.
Context is fixture data, not authenticated live manager evidence.

Returns support empty, s, o and property-bound v. The five property selectors are
ControlGroup:s, InvocationID:ay(length16), MainPID:u, Version:s and Features:s.
There is no general variant/type negotiation. Parsing a returned path/name does not bind
it to a live unit/process; a future adapter must verify those relationships.

Errors support only AccessDenied or InteractiveAuthorizationRequired in T7/T8 contexts.
Remote error text is parsed with bounds then discarded. DENIED here means the fixed
synthetic test result; without a live authorized context it is not installed policy proof.
NameOwnerChanged is accepted only for the exact D-Bus route, systemd name and unchanged
old/new owner. Changed owner, Reloading, unknown routes and other signals invalidate.
No automatic rebind is implemented. Bus disconnect handling needs a future transport.

## Executed evidence

259 native cases passed:12 positive,247 negative, including215 deterministic structural
mutations/truncations. Positive results compare typed strings/scalars/byte arrays, not merely
success. Four retained incoming witnesses V-D30/31/32/35 are replayed. Full fixed frame
bytes and expected logical values are retained in JSON; mutations are deterministically
regenerated. This milestone does not claim native encoding or round-trip completion.

Review corrected a negative vector initially labelled padding that changed a scalar
instead; the final vector changes actual header padding and still refuses. No parser
assertion was weakened. Both native runs passed; the recorded result is the final corpus.

The static freestanding x86-64 ELF has no interpreter, dynamic dependency or undefined
import and one syscall veneer used only for getuid, failure-index write and exit.
The decoder itself makes no syscall. Source, driver, generated header and image SHA256,
compiler flags/version and kernel are recorded. Existing GCC only; temporary builds
under Linux-native /tmp are removed. No binary is retained.

## Boundaries and next gate

No filter is installed by this parser fixture. No socket connects, no peer attacks run,
and no system-manager state changes. Native incoming mechanical validation does not
complete M4, R6, filesystem exclusivity or P3. Source production modules and tests are
unchanged.

Next: fixed native outgoing encoding and exact comparison with retained canonical frames,
then composition with the separate payload/ancillary/lifecycle/filter fixtures. Privileged
RO requests remain pending; approving them would not close these native implementation gaps.

## M22: fixed native outgoing encoding

[Encoder source](lab/child_dbus_encode.c), [driver](lab/child_dbus_encode_validate.py)
and [execution](lab/child_dbus_encode_evidence.json) implement exactly11 closed dummy selectors.
No caller supplies method, interface, property, path, PID, executable, unit, serial or manifest.
The canonical dummy values are compiled into fixed branch logic; a runtime manifest adapter
and live-instance substitution remain unimplemented. Internal string writers are not an
external API. There is no transport or command-line selector.

All V-D01..11 frames match byte-for-byte, including the22 launch properties, nested ExecStart,
empty auxiliary unit array, peer attachment and unauthorized peer-unit/property probes.
The native code independently writes aligned fields and patches array lengths; expected
frames come from the retained specification, not from this encoder. The Python finite decoder
also recovers the retained logical structures. This is native-encode/Python-decode parity,
not a native outgoing decoder or live systemd property acceptance.

11 exact-size successful writes,3862 insufficient-capacity refusals and3 unknown-selector
refusals passed. Every short-capacity case checks the entire4098-byte output region remains
unchanged; successful cases check both guard bytes. The output is copied only after bounded
internal encoding completes. Static ELF/import/syscall checks passed; no temporary artifact
remains. No assertion or wire contract changed.

Next composition target: combine the owned live sender/ancillary parser with exact per-role
seccomp restrictions, preserving inherited-filter monotonicity and no protected-UID claim.

## M28: finite EXTERNAL transcript mechanics

[Source](lab/child_dbus_auth.c), [driver](lab/child_dbus_auth_validate.py) and
[evidence](lab/child_dbus_auth_evidence.json) implement inert authentication bytes only.
States deliberately say NEW -> AUTH_ENCODED -> GUID_PARSED -> BEGIN_ENCODED, with terminal
INVALID. Encoding does not mean a socket exists or a write succeeded.

Four synthetic UID values cover0,1,62001 and4294967294. Decimal ASCII has no leading zero;
its lowercase hexadecimal encoding follows one NUL and AUTH EXTERNAL, ending CRLF.
The invalid unsigned UID sentinel refuses. Insufficient output capacity invalidates without
changing the output region. No caller can select an authentication mechanism.

Only OK plus32 ASCII hex digits and CRLF is accepted. Lower/uppercase GUID spelling is
retained exactly as metadata. Input is bounded to64 bytes per feed and37 total accepted bytes;
zero-size feeds, extra lines, challenge, rejected-mechanism and FD negotiation responses refuse.
Incomplete input cannot encode BEGIN. The fixture explicitly invalidates incomplete EOF.
There is no reconnect, fallback or live timeout implementation; transport remains absent.

85 exact transcripts(2 positive/83 negative) pass2489 two-chunk split runs and a bytewise
positive run. Four UID outputs pass106 capacity cases. Early BEGIN, repeated AUTH and input
after BEGIN are terminal refusals. Full transcript bytes, build hashes and static ELF checks
are retained. First compile/run passed; Linux-native temporary directory removed.

Next: finite incoming-frame accumulation under arbitrary bounded fragmentation, then exact
composition with the existing decoder. No bus connection or manager call is required.

## M29: bounded incoming stream accumulation

[Source](lab/child_dbus_stream.c), [driver](lab/child_dbus_stream_validate.py) and
[evidence](lab/child_dbus_stream_evidence.json) compose the existing native decoder prefix
with a fixed65536-byte frame buffer. No pointer into that buffer escapes; typed results are
compared immediately before reuse. Test comparison mismatches do not turn an accepted frame
into a protocol refusal, so negative tests cannot hide an unexpected decoder acceptance.

A16-byte header is accumulated first; lengths/architecture-independent wire flags are checked
before further accumulation. Body plus aligned header must fit65536. Per-feed input is bounded
to65536 and lifetime bytes to1048576; at most16 fixed expected contexts are allowed.
The executed stream uses12 contexts. Context selection is compiled fixture state, not a live
request/manager-generation binding. An unexpected extra frame, zero feed, incomplete EOF or
input after finish invalidates; no resynchronization or rebind exists.

The1025-byte concatenated stream passes all1026 split positions plus bytewise/17-byte chunks.
All1025 incomplete prefixes refuse at finish, as do247 retained negative frame cases.
Typed positive values remain exact. First static compile/run passed; no bus/transport call,
filter installation or system mutation occurred. Prefix/generated corpus/image hashes and
cleanup are recorded. Parsing/framing success remains distinct from authenticated policy.

Next: a finite request-correlation/manager-owner binding MODEL over these decoded values,
with disconnect/owner-change/stale-reply terminal invalidation. No live manager generation
or systemd reexec acceptance can be inferred from that model.

## M30: finite request/owner binding model

[Source](lab/child_dbus_owner.c), [driver](lab/child_dbus_owner_validate.py) and
[evidence](lab/child_dbus_owner_evidence.json) model Hello -> GetNameOwner -> Version requests.
Only one request may be pending, at most8 may be issued, and serial exhaustion refuses before
wrap. Reply sender/signature/serial are derived from pending state, not supplied by the frame.
The synthetic generation argument must match the model's generation.

Hello and manager-owner replies must contain the finite profile's colon-prefixed numeric
dotted names, bounded to255 bytes. Client and owner are copied into owned arrays, never kept
as pointers into a frame. This is deliberately narrower than a general D-Bus name parser.
The owner must differ from the client. Version replies must come from that exact owner.
An unchanged NameOwnerChanged signal must also name that bound owner, including while a
request is pending. Changed owner, unrelated owner, duplicate/stale reply, wrong order,
disconnect and suspected reexec invalidate permanently. There is no automatic rebind.

21 scenarios/107 steps pass. Scratch frame buffers are overwritten through volatile stores
after each decode, testing retained-value independence. The initial static link failed with
an unexpected memset import generated for the large aggregate state initializer. Explicit
field initialization removed that dependency; no no-import check or assertion was weakened.
Final ELF/import/syscall checks pass and temporary builds are removed.

Disconnect/reexec are injected MODEL events, not observed manager behavior. The generation is
synthetic, not an authenticated boot/manager epoch. No bus connects, request sends, privileged
policy reads or manager mutations occur. SAME_MANAGER_PID != SAME_MANAGER_GENERATION remains
unresolved for live acceptance. M4 is not accepted merely because these models pass.

Next: consolidate child mechanical evidence against the current M1-M5/production blockers and
reconcile the next independent master-plan milestone. Do not turn missing live proof into YES.

## M35: composed inert authentication, framing and correlation

[Source](lab/child_dbus_connection.c), [driver](lab/child_dbus_connection_validate.py) and
[evidence](lab/child_dbus_connection_evidence.json) combine the exact M28 authentication and
M30 owner-model prefixes with the M29 bounded frame-assembly rules. Prefix hashes are recorded.
No outgoing bytes are sent. AUTH/BEGIN remain ENCODED states, and generation7 remains synthetic.

Only an explicit completed BEGIN encoding enables request issuance or binary input. One request
may be pending; partial input prevents issuing a new request. A completed frame goes directly
to the owner's pending-context decoder, then its buffer is overwritten before reuse. Coalesced
unsolicited replies cannot invent the next request. Relevant owner changes invalidate the entire
composition, including authentication and request state, without fallback/reconnect/rebinding.
The65536-byte frame/per-feed,1048576-byte lifetime,16-frame and8-request bounds remain explicit.
Finish needs no partial bytes or pending request, an owner binding and at least3 accepted frames.
This finish is a fixture boundary, not live quiescence or manager continuity.

22 scenarios run with1-byte,17-byte and whole-frame chunks:66 scenario runs/471 scripted steps.
Two positive scenarios cover ordered replies and a coalesced unchanged-owner signal. Negative
cases cover early binary/request input, AUTH/binary smuggling, unsolicited/duplicate replies,
wrong sender/serial/generation, changed owner, incomplete EOF, issue during partial input,
zero feed, injected disconnect/reexec, unknown selector and malformed lengths/endian.
Every terminal state refuses another request. Static x86-64 ELF has no interpreter/dependencies/
undefined imports and one syscall veneer: getuid(102), diagnostic write(1), exit(60).

Two owned nonroot builds/runs passed; the second added explicit ELF architecture and syscall
contract evidence. Both produced the same image SHA256. Temporary build directories were removed.
No production module, filter policy, bus socket, installed authorization or R6 test was exercised.
M1-M5 remain PARTIAL. Next: exercise these byte boundaries on a private owned socketpair with a
fixed dummy responder, preserving the distinction between transport and authenticated authority.

## M36: private owned socketpair composition

[Source](lab/child_dbus_socket.c), [driver](lab/child_dbus_socket_validate.py) and
[evidence](lab/child_dbus_socket_evidence.json) deliver AUTH/BEGIN and fixed Hello/owner/Version
request/reply bytes through a same-process AF_UNIX STREAM socketpair. It is deliberately not
an independent server, system bus, credential boundary or installed authorization experiment.
Requests are immutable generated frames; this does not validate a runtime manifest encoder.

Both endpoints are NONBLOCK/CLOEXEC with flags checked. Empty reads report EAGAIN. The fixture
writes bounded1/17-byte pieces and reads actual available bytes through the composed M35 parser.
Short positive writes/reads are handled within the fixed piece; errors/zero writes refuse.
No polling wait or retry on EAGAIN is used. Each transfer is at most4096 bytes and each scenario
has an8192-I/O-call ceiling; the process also has a5-second harness timeout. MSG_NOSIGNAL avoids
SIGPIPE. Auth, binary and request state remain explicit; a real EOF invalidates partial or
completed-but-not-finished state. Model finish remains unrelated to process quiescence.

Seven scenarios at two fragment sizes pass14 runs: valid, wrong owner, changed owner, duplicate,
partial EOF, completed reply then EOF and wrong serial. Endpoints are closed, and FD3..63 are
empty after every run. The prelude closes inherited descriptors3+ before allocation. No fork,
child cleanup, pathname lookup, connect, live manager call, filter installation or privilege occurs.
The only raw syscall site serves the exact recorded read/close/sendto/socketpair/exit/fcntl/
getuid/close_range inventory. Static ELF/import checks and Linux-native build cleanup pass.

The first run passed; a second added the explicit empty-read EAGAIN assertion and passed again.
All80 protected original source byte hashes remain unchanged, including the owner's untracked
plan. Original local/live main remains d7cb43d. Next: specialize and install a fixture-only
post-setup I/O filter; its acceptance must remain separate from protected controller proof.
