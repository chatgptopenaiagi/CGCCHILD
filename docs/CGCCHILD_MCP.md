# Experimental version-pinned MCP adapter

M11 adds a fifth chunk operation and128-message/session bound; see
[bounded data plane](CGCCHILD_CAPSULE_CHUNKS.md). Earlier checkpoint details below remain historical.

M10 delegates both historical profiles through [closed integration](CGCCHILD_PROFILE_INTEGRATION.md).
No new tool or authority is introduced; large responses still refuse.

[Adapter](../src/cgc/experimental/mcp_stdio.py), [core](../src/cgc/experimental/readonly_service.py)
and [owned-process tests](../tests/test_child_mcp.py). V4.2 remains EXPERIMENTAL/PARTIAL.
Independent SDK interoperability is NOT_EXECUTED: neither Windows nor Fedora has the
Python MCP package installed. No package was installed to remove that limitation.

## Reviewed protocol boundary

The adapter pins **2025-11-25**, not an assertion about the newest MCP version. It implements
initialize, initialized notification, ping, tools/list and tools/call over foreground stdio.
Initialization returns its supported version and tool capability; clients must disconnect if
they cannot use that version. Tools require completed initialization. No server requests,
sampling, roots, elicitation, tasks, resources, prompts or network transport are implemented.
Basis: official [lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle),
[stdio](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) and
[tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) contracts reviewed
2026-09-24. This is a bounded subset, not full protocol conformance certification.

Five tool names map directly to the core: cgcchild_capabilities, cgcchild_state,
cgcchild_status, cgcchild_capsule and cgcchild_capsule_chunk. Each requires the exact
snapshot_digest advertised in its input schema; chunk additionally requires its bounded offset. Annotations identify read-only,
nondestructive, idempotent, closed-world behavior, but annotations themselves confer no trust.
Text and structured results contain the same core result; stale digests are tool errors.
Unknown methods, malformed params and unsupported tools return protocol errors.

## Launch and lifetime

Set PYTHONPATH=src in an owner-controlled launch from CGCCHILD. Execute Python with argv:

```text
python -B -m cgc.experimental.mcp_stdio --snapshot-hex <canonical-state-bytes-as-hex>
```

The hex startup payload is a reviewed inert supported-profile snapshot, bounded before decoding. No path
is opened, environment credential is consumed, shell is invoked or config is modified. Do not
place secrets in snapshot identifiers: startup arguments may be visible to local observers.
The CLI has no live-capture mode. Invalid startup state exits2 without echoing input.

During the MCP phase, stdin/stdout carry only newline-delimited JSON-RPC2.0 frames, UTF-8 input and ASCII-compatible
UTF-8 output. At most128 messages, each <=8192 bytes; oversize/unterminated frame returns an
error and ends the session. Duplicate fields, malformed UTF-8 and excessive parser nesting
refuse. Notifications receive no replies. Unknown notifications grant nothing. Repeated or
out-of-order initialized notification invalidates the handshake. Each tool calls the same
immutable core. EOF ends the foreground process; the parent owns wall-clock timeout/pipe
closure. No service, auto-start, external registration or Codex connection was performed.

## Evidence and limitations

Seven tests cover handshake ordering/reinitialization, all four tools, matching text/structured
content, version negotiation, ping, unknown mutation/shell methods, path injection, duplicate
keys, invalid IDs/UTF-8, stale digest and actual subprocess stdio. Thirty-one child tests passed
on Windows, including session/frame bounds; full Linux results are recorded in [progress](CGCCHILD_PROGRESS.md).
Independent SDK conformance, broader optional MCP metadata, real V3 projection, persistent
events and live authentication remain unaccepted. R6 and production P3 do not change.

## POSIX inherited snapshot descriptor (M13)

An owner-controlled launcher may instead supply argv:

```text
python -B -m cgc.experimental.mcp_stdio --snapshot-fd N --snapshot-digest SHA256
```

N is canonical decimal3..63. The launcher explicitly passes that already-open descriptor;
the adapter does not discover or open a pathname. It requires a regular file owned by its
effective UID, one hard link, no group/other permission bits, read-only access and offset zero.
Size is bounded by the selected-profile maximum before reading. The adapter compares
device/inode/mode/owner/group/link-count/size/mtime/ctime before and after reading, verifies
the exact reviewed SHA256, and runs the strict canonical profile decoder. It consumes and
closes its descriptor on success or refusal. The shared open-file-description offset advances;
the parent must account for that and retain responsibility for its own descriptor and timeout.

Windows refuses this descriptor option before touching it; hex and explicit stdin startup remain available.
A digest authenticates neither the sender nor current authority. Metadata checks do not prove
filesystem exclusivity, freeze other writers, or establish confidentiality against the same UID.
The adapter serves detached historical bytes only. No arbitrary-file-read tool is exposed.

Six focused Linux tests pass, including actual owned-subprocess startup with a110813-byte
continuity envelope, writable/mode/offset/digest/hardlink/pipe/content-change refusals and
descriptor consumption. Five POSIX tests are explicitly skipped on Windows; its unsupported
platform test passes. Temporary Linux files are owned under /tmp and removed by the tests.

## Explicit digest-bound stdin startup (M33)

An owner-controlled launcher can avoid host argument-length limits on either Windows or Linux:

```text
python -B -m cgc.experimental.mcp_stdio --snapshot-stdin --snapshot-digest SHA256
```

The first input line must be the exact canonical supported-profile snapshot, including its LF.
The digest covers that entire line. Reading is bounded to the profile maximum plus one byte;
malformed, oversized, noncanonical or mismatched input exits2 without emitting snapshot content.
Subsequent bytes enter the unchanged MCP phase. A later snapshot cannot replace the bound core.
The input stream remains caller-owned; its launcher must enforce timeout and close the pipe.
No pathname is opened and no filesystem ownership or sender-authentication claim is made.

This explicit startup preamble is private launcher framing, not an MCP protocol extension that
ordinary clients are assumed to understand. It requires a launcher that supplies the snapshot
before initialize. No SDK, plugin registration or automatic host integration was added.

Six new tests cover bounds, malformed/digest/read refusals, retained following bytes, no path
lookup, quiet subprocess refusal and rebind rejection. A110813-byte historical envelope starts
in an actual owned Windows subprocess and round-trips through capsule chunks with authority NONE.
Linux regression and Windows suite results are recorded in child progress.

## M40: independent paired-adapter Node conformance client

[Codec](../sdk/javascript/mcp_conformance_client.mjs),
[owned-process harness](../sdk/javascript/mcp_owned_process.mjs),
[tests](../tests/test_child_mcp_client.py).
The fixed client follows the pinned MCP lifecycle already linked above: initialize/version
agreement, initialized notification, then four owner-selected read-only tools. The official
2025-11-25 lifecycle/tools/stdio specifications were reviewed again for this milestone.

This is a paired conformance client, deliberately narrower than a general MCP SDK. It already
has a validated inert model-state snapshot and independently derives the exact expected core
results using the Node state/capsule codecs. It emits only initialize, initialized, capabilities,
state, status and capsule requests, with fixed sequential IDs and bound digest. There is no
arbitrary method/tool/path/params API. It has one pending reply and accepts only the exact
canonical ASCII frame expected from this adapter, including matching text/structured results.
Errors, extra fields, notifications, reordered IDs, altered content, version changes, duplicates,
truncation and responses over96KiB permanently invalidate. This stricter format is not imposed
on arbitrary MCP servers. Successful comparison means PAIRED_TRANSCRIPT_MATCH, authority NONE.

The codec opens no process, pipe, path or network connection. Encoded requests do not assert
that bytes were sent. next()/accept()/finish()/invalidate() manage only its finite transcript;
returned request/snapshot bytes are detached. It supports model-state0.1 only, not the larger
historical continuity profile, discovery, arbitrary extensions or remote transport.

The separate test harness is owner-controlled and receives the test's existing Python executable.
It launches only the fixed child module/argv with shell disabled and Windows window hidden,
provides the digest-bound private startup line, then exchanges six requests/five replies.
Response bytes are bounded per frame and cumulatively; the total5-second timer only terminates
that owned subprocess. Normal shutdown closes stdin and verifies exit0. No credentials or
existing external application are read. Valid-session cleanup was observed; arbitrary OS kill/
pipe failure behavior is not thereby universally accepted.

Three test families pass Windows/Fedora: two actual model sessions,45 transcript cases (one
positive/44 negative) and19 Node lifecycle/bound/ownership checks. No package installed or
service registered. SDK ecosystem, plugin and live authentication acceptance remain blocked.
