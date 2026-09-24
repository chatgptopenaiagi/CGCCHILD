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
