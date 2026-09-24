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
