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

## Fixed paired MCP conformance client (M40)

mcp_conformance_client.mjs checks a finite read-only transcript against the child Python adapter.
It has no transport or generic tool/method interface. See the exact [paired boundary](../../docs/CGCCHILD_MCP.md#m40-independent-paired-adapter-node-conformance-client).
This is interoperability evidence for those two implementations, not a general-purpose MCP SDK.
mcp_owned_process.mjs and mcp_client_vectors.mjs are bounded owner-controlled test harnesses.

## Bounded capsule byte assembly (M60)

capsule_chunks.mjs implements the [chunk consistency contract](../../docs/CGCCHILD_CAPSULE_CHUNKS.md#m60-independent-node-byte-assembler-separate-from-capsule-acceptance).
It supports bytes up to the core maximum but does NOT validate a capsule or authenticate
its source. Its immutable result says capsule_validation=NOT_PERFORMED and authority=NONE.
Use the core capsule validator separately before treating the bytes as historical state.

```text
node sdk/javascript/test_capsule_chunks.mjs
python -B -m unittest discover -s tests -p test_child_javascript_chunks.py -v
```

## Historical preservation record consistency (M63)

preservation.mjs implements the original pure cgc-preservation-v3.0-provisional
record validator, not an action adapter. It replays phase transitions, checks notes,
reported tests/evidence relations and recomputes derived outcomes. Python's default
ASCII sorted render_json bytes plus one LF are the exact standalone record wire;
encodeRecord/decodeRecord reject duplicate/noncanonical fields. MAX_BYTES262144 is
the original default-spaced JSON record limit (wire may add its one LF).

Unicode text counts code points, ASCII serialization escapes UTF-16 surrogate units,
and canonical UTC timestamps preserve six-digit nonzero microseconds and ordering.
The Python whitespace distinction is explicit (for example U+0085 versus U+FEFF).
No filesystem, network, current observation, command or execution API exists.
validateRecord returns a detached historical record; historicalRecord returns a frozen
view with detached record()/bytes(), authority NONE, current_safe_to_resume UNKNOWN,
mutation_authorized false and receipts_authenticated false. A stored record's reported
safe_to_resume YES is preserved as historical content, never promoted to current proof.

Four cross-language test families compare79 valid lifecycle/receipt combinations,
Unicode/date/size boundaries, all-field substitutions and canonical corruption cases
against the unchanged Python validator. Every accepted corpus entry checks view/input
ownership. The bounded offline preservation_conformance.mjs is a test adapter only.
This is one dependency for full continuity SDK support; it does not yet validate
inspection receipts or full handoff envelopes. No new package or host change.

```text
python -B -m unittest discover -s tests -p test_child_javascript_preservation.py -v
```

## Lossless bounded integer JSON prerequisite (M64)

integer_json.mjs supplies encodeIntegerJson(value, compact=true) and
 decodeIntegerJson(bytes, compact=true) for inert integer-only JSON. It is not a
schema validator. Unsafe exact integers decode to BigInt; safe values decode to
Number. Encoding refuses unsafe Number values rather than serializing a rounded
inode. Canonical compact/default-spaced formats use Python-compatible ASCII escapes,
Unicode code-point key ordering and exactly one LF. No floats/exponents, duplicate
keys, negative zero, alternate whitespace, trailing bytes or noncanonical escapes.

Bounds:2101248 bytes including LF, depth32 (root depth0),262144 value nodes and
4300 decimal integer digits. These are explicit codec-profile bounds, not a claim
that arbitrary JSON/Python settings must accept the same universe. Cycles, sparse
arrays, accessors, symbol keys and custom object prototypes refuse; no getter is
invoked. Parsed objects have null prototypes, including __proto__ keys. Hostile
in-process proxies remain outside this data boundary. No I/O or current authority.

Four Python parity families and20 Node cases cover large signed/unsigned integers,
UTF-16/code-point distinctions, canonical wire mutations, structural bounds and
ownership. This is a prerequisite for inspection/handoff validation, not acceptance
of arbitrary parsed receipts or an implementation of the full continuity profile.

```text
node sdk/javascript/test_integer_json.mjs
python -B -m unittest discover -s tests -p test_child_javascript_integer_json.py -v
```

## Historical continuity receipts (M63-M67)

The separate preservation.mjs, inspection.mjs, handoff.mjs and continuity.mjs modules
validate the original historical record hierarchy without inspecting any project.
integer_json.mjs preserves filesystem integers beyond Number's exact range as BigInt;
unsafe Number inputs are refused. Canonical ASCII bytes, nested SHA256 receipts, project
bindings and timestamps are compared independently with the Python validators.

continuity.mjs exports projectContinuity, validateContinuity, encodeContinuity,
decodeContinuity and summaryContinuity. It preserves the full source envelope, including
failed latest attempts and both known-good slots. Current safety remains UNKNOWN and
mutation authorization false. A historical YES inside an original record is data only.
No receipt is authenticated. Object and byte return values are detached.

This completes a separate Node continuity codec, not capsule0.2 integration: capsule.mjs
still supports only the original model profile. No path is resolved, no store opened,
and no network or subprocess API is present in these modules. The *_conformance.mjs
programs are bounded offline test adapters, not product transports.

## Inert continuity capsule0.2 (M68)

continuity_capsule.mjs separately exports importCapsule/exportCapsule/CapsuleError and
supports only V3_CONTINUITY_HISTORICAL. The original model capsule module remains unchanged.
Three fixed stored ZIP members, metadata and exact reconstruction follow the same narrow
archive contract. The global bound is2117632bytes, each member at most2101248bytes.
Manifest0.2 binds the explicit profile and state/human digests. Nested continuity validation
preserves exact integer identity bytes. No archive member is extracted or path resolved.

Python parity covers positive/large snapshots, hostile metadata, path substitutions,
structural truncations, high-bit mutations and CRC-consistent content tampering. Input
buffer/returned-object mutation cannot alter the frozen historical view. Imports preserve
NONE authority and HISTORICAL_UNVERIFIED freshness. Digest consistency is not authenticity.
The bounded conformance adapter is offline test tooling, not a remote or generic ZIP API.

## Paired continuity MCP test client (M70)

mcp_continuity_client.mjs provides the same finite next/accept/finish lifecycle as the model
conformance client, but validates continuity input and requests capabilities plus fixed
capsule chunks. It has no generic method callback. Every reply must match the independently
computed canonical expected frame. Its owned-process harness is test-only: the test owner
supplies Python, the module/arguments are fixed, shell=false, and failures close that child.
Input is bounded to2101248bytes, replies96KiB, total68 reply-budgets, deadline15seconds.
Small/large sessions and seven fixed fault modes are tested; general MCP interoperability
and live authorization remain unaccepted. No package or service was installed.
