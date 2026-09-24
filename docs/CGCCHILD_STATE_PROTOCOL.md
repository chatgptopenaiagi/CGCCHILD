# Experimental state protocol and inert capsule

Child V4.0/V4.1 implementation is experimental and profile-limited. It does not mean V3
acceptance or implement the complete V4 mission. The original mission files remain unchanged.
No live service, MCP, plugin, SDK, remote gateway or agent fabric is included in this checkpoint.

## State 0.1

Runtime: [state_protocol.py](../src/cgc/experimental/state_protocol.py).
Language-neutral shape: [schema](child-schemas/state-0.1.schema.json). The trusted runtime
enforces additional relational and canonical rules; schemas are never downloaded or imported
as executable validation policy. Only `QUIESCENCE_MODEL_ONLY` is supported. Original V3
handoff, inspection and receipt records are not converted or silently replaced. Their absence
is an explicit omission, not a fresh UNKNOWN observation of the underlying project.

| Field | Exact meaning |
|---|---|
| version | `cgcchild-state-0.1-experimental`; other versions refuse |
| profile | `QUIESCENCE_MODEL_ONLY` |
| source_instance, snapshot_id | ASCII `[A-Za-z0-9_.-]`, length1..128; labels, not authentication |
| captured_at | Valid UTC second-resolution `YYYY-MM-DDTHH:MM:SSZ`; historical input, never refreshed on read |
| clock | `SOURCE_MONOTONIC_NOT_PORTABLE`; archived ns values cannot establish freshness on another process/host |
| model.project, generation | Opaque labels; never interpreted as paths or mutation targets |
| model.observed_ns, expires_ns | Canonical unsigned decimal strings0..2^63-1; no leading zero except0; ordered; lifetime <=60 billion ns |
| model.claims | All six exact obligation keys; values YES/NO/UNKNOWN; required, never omitted or null |
| model.provenance | SYNTHETIC or IMPORTED; no caller-declared LIVE mode |
| production_p3, safe_to_resume | UNKNOWN only |
| mutation_authorized | Boolean false only |
| omissions | Exact ordered list SOURCE_CONTENT, GIT_OBJECTS, V3_RECEIPTS, LIVE_AUTHORITY, FILESYSTEM_PROOF |

Canonical bytes: ASCII JSON, recursively lexicographically sorted keys, no optional whitespace,
compact separators, one trailing LF. Maximum16384 bytes. All strings are constrained ASCII
identifiers, enum values, decimal clocks or timestamps. Noncanonical bytes, duplicate keys,
unknown fields/enums/versions, floats, nonfinite numbers, BOM, extra documents, invalid dates,
and deep malformed JSON refuse with bounded error codes. No migration or permissive extension.
The snapshot preserves original claims on round trip; `imported_profile` independently changes
interpretation to IMPORTED. Claims and integrity never authenticate themselves.

Human text derives from the same validated object, explicitly says historical model/not a
source-code backup, UNKNOWN resume/P3 and no current repository/remote check. No untrusted
command or free-text instruction is embedded. AI consumers can consume this validated object
as inert evidence; no separate model-generated interpretation is authoritative.

## Capsule 0.1

Runtime: [capsule.py](../src/cgc/experimental/capsule.py). Container is a deterministic,
unsigned, uncompressed ZIP with exactly three ordered members: manifest.json, state.json,
HUMAN-STATUS.txt. All dates1980-01-01 00:00:00, Unix regular0600 mode, no extras/comments/flags.
Archive <=65536 bytes; each member <=16384 bytes. No filesystem extraction, output filename,
network access, executable content, credentials, bundled schema or signature support.

Manifest version is `cgcchild-capsule-0.1-experimental`, signature label UNSIGNED. SHA256 covers
state.json and HUMAN-STATUS.txt, excluding manifest/container metadata to avoid self-reference.
Importer validates trusted protocol, derived human text and exact manifest, then requires
byte-identical re-export of the entire archive. This also refuses ambiguous local headers,
prefixes, trailers, metadata changes, duplicate records, unexpected members, traversal/absolute
paths, links, encrypted/compressed entries and central/local header discrepancies. Exported
bytes depend only on the validated snapshot. Import returns an immutable byte-backed historical
view; each decoded snapshot is a new object. Integrity is CONSISTENT_UNSIGNED_BYTES, freshness
HISTORICAL_UNVERIFIED and authority NONE. Hashes are not signer authentication or factual proof.

## Validation and limits

Tests: [protocol](../tests/test_child_state_protocol.py), [capsule](../tests/test_child_capsule.py),
[model/orchestration](../tests/test_child_quiescence.py). Nineteen focused tests pass on Windows
and Fedora, including729 model combinations, canonical round trips, duplicate keys at every
level, all packet/archive truncations, authority escalation, hostile archive metadata and
model->capsule->historical profile->refused repair integration. No external dependency.

The full Linux regression passed407 tests in108.814s; the subsequent pinned-vector test
passed in the19-test focused suite on both platforms.
No real producer, proof source, filesystem exclusivity, mutation/recovery execution or full
safe-resume acceptance exists. Broader V3 continuity projection, event streams, source instance
authentication, portability tests in other languages, signatures, service transport and plugin
acceptance remain separate milestones. Imported data cannot be promoted by adding a flag.
