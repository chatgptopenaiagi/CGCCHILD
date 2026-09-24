# Bounded inert capsule data plane

M11 adds core method `capsule.chunk` and MCP tool `cgcchild_capsule_chunk`. The original four
operations and96KiB per-response bound remain. The private session and MCP session bounds
are now128 requests/messages, enough for every accepted archive at32768 bytes per chunk.
The largest archive needs at most65 chunks plus handshake/discovery. No network or filesystem
operation is added. [Implementation](../src/cgc/experimental/capsule_chunks.py) and
[tests](../tests/test_child_chunks.py).

Request adds exactly one field, offset: integer, not boolean, nonnegative, a multiple of32768,
strictly below the archive length. Chunk size is fixed by the core; there is no arbitrary
byte-range length, path, destination, selector or executable field. Every request still names
the exact immutable snapshot digest. The result contains offset, total_bytes, capsule_sha256,
chunk_sha256, canonical base64 data, encoding=base64 and a boolean done. Last chunk has the
exact remaining byte length. Export remains unsigned/inert; hashes are consistency evidence.

Receiver takes an expected snapshot digest and accepts only sequential chunks. It checks exact
fields/types, bounds, canonical base64, per-chunk digest, consistent total/archive digest,
expected size and done flag. Duplicate/out-of-order/mixed/tampered input permanently invalidates
that receiver and clears buffered data. Finish requires all bytes, validates whole-archive
digest, performs the strict inert capsule import, then verifies the decoded snapshot digest.
No partial view is returned. A completed receiver cannot be replayed or reopened. No extraction,
source path rebinding, imported grant, remote freshness claim or execution occurs.

Read-capability laboratory policy intentionally remains limited to its original four methods;
chunk offsets are not silently added to its grant grammar. The thin plugin also remains its
reviewed model-only subset. MCP/core explicitly advertise the new fifth method.

## Evidence and review fixes

Six new tests cover >96KiB continuity record MCP chunk reconstruction, all response sizes,
tamper/duplicate/reorder/mixed archive refusal, terminal digest mismatch, incomplete/closed
receiver refusal, malformed offsets and unchanged mutation authority. All55 child tests pass
on Windows. Original model bytes and Node vectors remain unchanged; full Linux result is in
progress. No acceptance claim extends beyond owned-process/synthetic evidence.

Review identified two child defects and added regression tests. A core RESPONSE_LIMIT must
produce CORE_REFUSED rather than READ_COMPLETE in the event lab. Capsule export now detaches
and revalidates one input object before generating all members; a deterministic injected
caller mutation between member generation cannot create mixed state/human output. No original
CGC code or safety test was changed.

The present chunk function deterministically regenerates archive bytes for each request.
This is bounded but not yet optimized or benchmark-accepted. Startup hex CLI remains subject
to host command-line limits; chunking solves response size, not large-input launch transport.
Independent MCP SDK compatibility and production V3 proof remain separate blockers.

## Current implementation clarification (M45 audit)

The paragraph above describes M11's original state. M12 caches one immutable archive per core;
only the standalone stateless chunk helper regenerates it. M33 provides bounded digest-bound
stdin startup for large snapshots on Windows/Linux. Neither update removes the96KiB response
limit, changes chunk grammar, authenticates a caller, or accepts a general MCP SDK.

## M60: independent Node byte assembler, separate from capsule acceptance

[Node module](../sdk/javascript/capsule_chunks.mjs) exports createAssembler(expected)
with exactly total_bytes and capsule_sha256 caller anchors. These bind bytes; they do
not authenticate themselves. accept takes canonical ASCII JSON/LF chunk bytes only,
not arbitrary method/path strings. It checks the seven exact fields, duplicates by
byte reconstruction, sequential offsets, fixed32768-byte pieces, canonical base64,
piece/full digest, stable total/digest, final marker and hard2117632-byte/65-piece bounds.
Every malformed frame invalidates permanently; early finish, replay, reorder and extra
chunks refuse. Returned bytes are detached and the finished object is frozen.

Unlike the Python Receiver, this Node component performs NO capsule or snapshot-semantic
validation. Its result explicitly says EXPECTED_BYTES_MATCH, capsule_validation=
NOT_PERFORMED, source_authenticated=false, authority=NONE, safe_to_resume=UNKNOWN and
mutation_authorized=false. It imports only Node crypto, not filesystem/network/process
APIs; it offers no extraction or persistence. Expected anchor objects are supplied by
trusted local JavaScript callers; hostile in-process code is outside this boundary.
The paired Python test explicitly imports the reassembled bytes through core validation.
A non-archive whose bytes match supplied anchors passes assembly but fails core import:
this distinction is required, not an assembler acceptance bug.

[Cross-language tests](../tests/test_child_javascript_chunks.py) exercise both profiles,
semantic/wire/anchor refusal, deterministic corruption/truncation and unchanged core
import. Seventeen independent Node cases cover sizes1/32767/32768/32769/MAX, ownership,
replay/order/terminal state and anchor refusal. The offline conformance adapter is a
bounded12MiB/128-case stdin test helper, not a product listener or generic transport.
No dependency installed. Full continuity validation still belongs to the Python core;
this does not resolve B06's independent full-continuity SDK validator gap.
