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
LOCAL_READ_HANDLE_ISSUED, LOCAL_READ_HANDLE_REVOKED, READ_COMPLETE, READ_DENIED and
SNAPSHOT_INVALIDATED. Event retrieval returns independent copies. No handle material,
principal identity or authentication token is serialized. The in-memory hash chain detects
changed covered bytes; it is neither authenticated audit storage nor durable history.

Six tests cover method/principal/digest/handle scope, forged and cross-router handles, no
JSON serialization, expiry, revocation, generation invalidation, backwards clock, event
capacity, hash-chain recomputation and malformed issue requests. No privileged action,
network activity, host policy or new dependency is required. This advances the interface
foundation only; production agent-fabric acceptance remains NOT_STARTED.
