# Experimental read-only core and foreground reference surface

M10 supports two explicit historical profiles; see [closed integration](CGCCHILD_PROFILE_INTEGRATION.md).
The four methods and96KiB response refusal boundary remain unchanged.

[Implementation](../src/cgc/experimental/readonly_service.py) and
[tests](../tests/test_child_readonly_service.py). V4.2 PARTIAL: private stdio framing,
not MCP or JSON-RPC. No installed service, listener, background daemon or authentication claim.
V4.5 has a minimal text status projection only. No GUI/mobile implementation.

The core takes one canonical `QUIESCENCE_MODEL_ONLY` snapshot as bytes, validates it and
retains canonical bytes and digest. It never reloads state or changes capture times. Each
request names that exact digest. A mismatch returns STALE_SNAPSHOT. This is generation
selection, not freshness or authentication. All responses say mutation_authorized=false.

Request is an ASCII JSON line of at most1024 bytes with exactly id, method, snapshot_digest.
id is `[A-Za-z0-9_-]{1,32}`; snapshot_digest is64 lowercase hex. Duplicate fields, invalid
types, extra parameters and unknown methods refuse. No path, PID, argv, shell, unit or
executable field exists. Errors contain only fixed codes and never echo rejected input.

| Method | Result from the same validated snapshot |
|---|---|
| capabilities.get | Fixed four-method list, model-only scope, network=false, historical freshness, session request bound |
| state.get | Original inert state object |
| status.get | Core-generated historical human text |
| capsule.export | Core-generated deterministic capsule encoded as base64 |

Responses are compact sorted ASCII JSON plus LF, <=96KiB. There is no dispatch to plugin
callbacks, subprocesses, Git, filesystem writes or generic RPC. Transport calls the core;
it cannot add a proof source or convert an imported claim to current evidence.

## Foreground process contract

From the CGCCHILD directory with `PYTHONPATH=src`, the entrypoint is:

```text
python -B -m cgc.experimental.readonly_service
```

There are no command-line arguments. A controlling program supplies the canonical snapshot
as the first stdin line, followed by request lines; EOF ends the process. At most32 requests
are consumed. Oversized or unterminated lines cause a bounded error and exit. No extra bytes
are drained or interpreted as a second snapshot. stdout contains only response frames.
The controller must impose a wall-clock timeout and close pipes: bounded message counts do
not guarantee a blocking stdin read will finish. Tests use a five-second subprocess timeout.

This is a reference transport for owner-supplied inert state, not a trusted server boundary
against a malicious caller sharing Python memory. No network, service registration, MCP
negotiation, access-control claim, local account policy or new dependency is involved.

## Validation

Five service tests cover all four projections, matching digests, capsule import parity,
unknown mutation/shell methods, extra path parameter, stale digest, duplicate fields, wrong
types, Unicode/malformed/oversized input,32-request cap, no snapshot rebinding and actual
subprocess stdin/stdout. All24 child tests pass on Windows. Linux full regression is recorded
in [progress](CGCCHILD_PROGRESS.md). No inherited runtime API changed.

The next transport integration must preserve these four fixed capabilities and source
semantics. Full V3 record projection and authentic live state remain separate gates;
adding MCP compatibility would not make this model snapshot a production guardian.
