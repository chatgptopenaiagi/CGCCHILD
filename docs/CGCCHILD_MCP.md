# Experimental version-pinned MCP adapter

M10 delegates both historical profiles through [closed integration](CGCCHILD_PROFILE_INTEGRATION.md).
No new tool or authority is introduced; large responses still refuse.

[Adapter](../src/cgc/experimental/mcp_stdio.py), [core](../src/cgc/experimental/readonly_service.py)
and [owned-process tests](../tests/test_child_mcp.py). V4.2 remains EXPERIMENTAL/PARTIAL.
Independent SDK/client interoperability is NOT_EXECUTED: neither Windows nor Fedora has the
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

Four tool names map directly to the core: cgcchild_capabilities, cgcchild_state,
cgcchild_status, cgcchild_capsule. Each requires the exact snapshot_digest advertised as a
constant in its input schema. No other argument is accepted. Annotations identify read-only,
nondestructive, idempotent, closed-world behavior, but annotations themselves confer no trust.
Text and structured results contain the same core result; stale digests are tool errors.
Unknown methods, malformed params and unsupported tools return protocol errors.

## Launch and lifetime

Set PYTHONPATH=src in an owner-controlled launch from CGCCHILD. Execute Python with argv:

```text
python -B -m cgc.experimental.mcp_stdio --snapshot-hex <canonical-state-bytes-as-hex>
```

The sole startup payload is a reviewed inert model snapshot, bounded before decoding. No path
is opened, environment credential is consumed, shell is invoked or config is modified. Do not
place secrets in snapshot identifiers: startup arguments may be visible to local observers.
The CLI has no live-capture mode. Invalid startup state exits2 without echoing input.

stdin/stdout carry only newline-delimited JSON-RPC2.0 frames, UTF-8 input and ASCII-compatible
UTF-8 output. At most64 messages, each <=8192 bytes; oversize/unterminated frame returns an
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
