# CGCCHILD experimental Node snapshot codec

Independent JavaScript implementation of the [model-only state0.1 contract](../../docs/CGCCHILD_STATE_PROTOCOL.md).
No dependencies; uses installed Node built-ins. Not a browser, TypeScript or live
CGC SDK. The inert model capsule extension is described below. Original [Apache-2.0 license](../../LICENSE) and attribution apply.

Exports: validateState, encodeState, decodeState, stateDigest, humanStatus. Decode requires
Uint8Array/Buffer canonical bytes. No network, filesystem, subprocess or execution API in
state.mjs. Model clocks are validated as BigInt from canonical decimal strings, then retained
as strings. UNKNOWN and false remain distinct; missing/null obligations refuse. Imported
claims remain inert; this SDK cannot evaluate production proof or grant authorization.

Node JSON.parse alone collapses duplicate keys. This decoder never returns that intermediate
value: it validates the fixed shape and requires byte-identical canonical re-encoding, so
duplicate keys and noncanonical encodings refuse. It does not accept arbitrary recursive data.
The small CLI-like conformance file is an offline test harness, not a product transport.

Run from CGCCHILD:

```text
node sdk/javascript/test_state.mjs
```

Windows Node v26.8.1 passed692 checks, including all truncations of the pinned snapshot,
duplicate fields, authority promotion, invalid dates, integer bounds and status preservation.
The Python unittest corpus independently compares acceptance, bytes, digests and full human
output. It skips explicitly if Node is absent; a skip does not establish platform support.

Review found a language-specific pitfall before publication: JavaScript dollar anchors can
match before a final newline. Full-match equality was added for identifiers/clocks, with
LF/CR/CRLF adversarial tests. No safety check was weakened. No package was installed.
V4.4 is EXPERIMENTAL/PARTIAL for this one profile and runtime; generated bindings, browser
compatibility, other languages and full V3 record projection remain unaccepted.

## Inert model capsule0.1

M32 adds exportCapsule/importCapsule/CapsuleError in capsule.mjs, independently of
Python zipfile. Only the model-state0.1 profile is supported; full continuity/capsule0.2
refuses explicitly. This is an in-memory Node SDK, not a general ZIP reader or extractor.

The fixed local/central/end record layout follows the
[PKWARE ZIP specification6.3.10](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT).
The CGCCHILD profile is narrower: exactly three ordered ASCII member names, stored
compression, fixed1980 timestamp, Unix regular0600 attributes, no flags, extras, comments,
encryption, ZIP64, data descriptors, prefixes or trailers. CRC32 and manifest SHA256 are
consistency checks, not signatures or source authentication.

Import checks the64KiB bound before copying, then checks each local header/name/size/CRC.
Every member is limited to16KiB. The strict state decoder validates canonical payload bytes;
human/manifest must exactly match reconstructed values. Re-export must equal the entire
input, validating central records and offsets without a permissive ZIP parser.
No archive path is ever resolved and no member is extracted.

The frozen historical view exposes authority=NONE, freshness=HISTORICAL_UNVERIFIED,
integrity=CONSISTENT_UNSIGNED_BYTES and snapshot(). Each snapshot is detached.
Neither mutation of the input buffer nor mutation of a returned object affects the saved
view. Import preserves historical bytes; it never refreshes clocks or authorizes execution.

Run the independent checks:

~~~text
node sdk/javascript/test_capsule.mjs
python -B -m unittest discover -s tests -p test_child_javascript_capsule.py -v
~~~

The Python test needs src on PYTHONPATH, as for the repository suite. Standalone Node
checks3246 cases, including every truncation/single-byte corruption of the1613-byte pinned
capsule. Five Python/Node families compare23 valid variants,18 hostile metadata archives,
3226 truncation/corruption cases, explicit full-continuity refusal and view ownership.
The canonical digest remains27d2004d96d7c31ba7eb030ab1b70d71d51ea32ad483dffe8cb04f228e6ed2ed.

capsule_conformance.mjs is a bounded stdin corpus adapter for tests only; it is not an
MCP or product transport. capsule.mjs imports only Node crypto and the fixed state codec;
it has no filesystem, network, subprocess or extraction API. No dependency was installed.

## Inert read-event journal0.1 (M39)

read_journal.mjs independently implements the [journal contract](../../docs/CGCCHILD_READ_CAPABILITIES.md#m38-inert-historical-event-journal).
Exports: encodeJournal(events,snapshotDigest), decodeJournal(bytes,expected), JournalError,
VERSION, MAX_BYTES and MAX_EVENTS. expected has exactly expected_snapshot_digest, expected_tip
and expected_count. Clocks use BigInt for comparison and remain decimal strings in the wire.
No source snapshot is read by this codec: its digest is an opaque binding, not validation or
proof of the corresponding state. Grant import/replay and source authentication do not exist.

The32KiB/64-event bounds, canonical ASCII/LF bytes, ordered hash chain, fixed event kinds,
nondecreasing clocks and terminal invalidation match Python. Duplicate fields are rejected by
exact canonical reconstruction. The frozen returned view exposes detached events()/bytes(),
NONE authority, historical freshness, unsigned consistency and EXPECTED_PREFIX_ONLY completeness.
Caller anchors do not authenticate themselves or establish that no unseen tail exists.

~~~text
node sdk/javascript/test_read_journal.mjs
python -B -m unittest discover -s tests -p test_child_javascript_journal.py -v
~~~

Four cross-language families cover73 positive cases (all prefix lengths0..64, each kind and
large clocks),31 semantic/wire/anchor refusals,3940 truncations/high-bit mutations and14 native
Node ownership/pinned checks. The1970-byte vector remains byte-identical to Python. The codec
imports only Node crypto. journal_conformance.mjs is an8MiB/2000-case offline stdin test adapter,
not a product transport, listener, credential reader or authority endpoint. No package installed.
