# In-process read-capability and event laboratory

Status: EXPERIMENTAL/PARTIAL agent-fabric and gateway-policy foundation. No remote gateway,
cloud connector, local AI execution, tunnel, authenticated IPC or live grant exists.
[Implementation](../src/cgc/experimental/read_capabilities.py),
[tests](../tests/test_child_read_capabilities.py).

An owner-created ReadCapabilityLab holds exactly one immutable historical model snapshot
and the existing ReadOnlyCore. The explicit local issue operation creates an opaque Python
object handle stored by identity in that lab's registry. Methods must be a nonempty duplicate-free
subset of the four core read operations. At most16 handles exist and lifetime is <=60 billion
source monotonic ns. Every read checks handle identity, principal label, method, snapshot digest
and expiry. Other lab instances, freshly constructed handles, dictionaries, revocation and
generation invalidation cannot recreate a registered handle. There is no grant serialization.

Principal labels are **not authenticated identities**. The host caller and its clock are trusted
inputs in this laboratory. Hostile code inside the same Python interpreter is outside this
boundary. No handle is exposed by MCP, the private service or the plugin. The module is not
an authorization source for Git, filesystems, processes or a remote peer. It cannot convert
model output into execution permission. A future authenticated adapter needs independent
caller binding and reviewed policy before any real grant API can exist.

Reads delegate to the same fixed core. No caller-provided path, shell, callback, arbitrary
method or destination is accepted. Global backwards clock observation clears all grants and
permanently closes the lab. Expired or revoked handles deny; invalidated generations do not
reopen. Event-capacity exhaustion refuses before another read occurs.

Events are bounded to64, with monotonic sequence, source clock encoded as decimal text,
snapshot digest, previous-event hash and canonical event digest. Exact kinds are
LOCAL_READ_HANDLE_ISSUED, LOCAL_READ_HANDLE_REVOKED, READ_COMPLETE, CORE_REFUSED, READ_DENIED and
SNAPSHOT_INVALIDATED. Event retrieval returns independent copies. No handle material,
principal identity or authentication token is serialized. The in-memory hash chain detects
changed covered bytes; it is neither authenticated audit storage nor durable history.

Six tests cover method/principal/digest/handle scope, forged and cross-router handles, no
JSON serialization, expiry, revocation, generation invalidation, backwards clock, event
capacity, hash-chain recomputation and malformed issue requests. No privileged action,
network activity, host policy or new dependency is required. This advances the interface
foundation only; production agent-fabric acceptance remains NOT_STARTED.

## M38: inert historical event journal

[Codec](../src/cgc/experimental/read_journal.py), [schema](child-schemas/read-journal-0.1.schema.json),
[tests](../tests/test_child_read_journal.py) and [pinned vector](lab/child_read_journal_vectors.json).
The journal copies existing event records unchanged into a closed versioned envelope. No
principal label, handle identifier, credential or executable command is added.

Canonical ASCII JSON uses recursively sorted keys, compact separators and exactly one trailing
LF, with a32768-byte ceiling and at most64 events. Events require exact fields/kinds, sequence1..N,
nondecreasing canonical decimal clocks0..2^63-1, one snapshot digest and a SHA256 chain rooted in
64 zeroes. Event digest covers the canonical event excluding digest and without LF, preserving
the existing producer's convention. SNAPSHOT_INVALIDATED must be terminal. Duplicate/extra keys,
noncanonical bytes, malformed/overflow clocks, reordered records and inconsistent hashes refuse.
The envelope fixes authority NONE, freshness HISTORICAL_UNVERIFIED and SOURCE_MONOTONIC_NOT_PORTABLE.

Import also requires the caller's expected snapshot digest, event count and tip. Those inputs
can detect a missing or changed expected prefix; they do not authenticate the source or prove
that no later/unreported events exist. Completeness is explicitly EXPECTED_PREFIX_ONLY. An
attacker able to replace all bytes and the expected anchor can recompute a consistent journal.
Imported views remain inert and cannot be used as opaque handles in the capability laboratory.
Each events() call returns detached copies. No replay, persistence, service method or grant
import was implemented. The host caller remains trusted against hostile code in its interpreter.

Seven focused test families pass on Windows/Fedora: actual issued/read/denied/revoked/invalidated
records, empty/64-event bounds, expected-prefix mismatch, recomputed semantic violations, byte/
hash corruption, detached view and replay refusal. The1970-byte pinned example has SHA256
`d36e5defb1bace89c867a3b2186034d276351e35e6d879cb9d78402426370a7b`.
Schema parsing/field-enum consistency checks pass; an independent JSON Schema validator is not
installed, and none was installed. Schema shape alone cannot enforce relational/hash rules.
