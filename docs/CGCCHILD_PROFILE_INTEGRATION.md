# Closed historical profile integration

M11 adds a fifth chunk operation and128-message/session bound; see
[bounded data plane](CGCCHILD_CAPSULE_CHUNKS.md). Earlier checkpoint details below remain historical.

M10 extends the child adapters through [snapshot_profiles.py](../src/cgc/experimental/snapshot_profiles.py).
Exactly two reviewed source versions exist: model0.1 and continuity0.1. There is no registration,
dynamic import, caller callback, `$ref` resolution or imported schema execution. Each source
codec still enforces its own exact schema, canonical bytes, size and semantics. Unknown
versions, duplicate keys and cross-profile field substitutions refuse before use.

## Compatibility and containers

Existing model state and capsule0.1 bytes/digests are unchanged and pinned tests still pass.
Continuity uses capsule `cgcchild-capsule-0.2-experimental` with explicit manifest profile
`V3_CONTINUITY_HISTORICAL`. Member names/order and inert deterministic ZIP policy are unchanged.
Continuity state bytes remain bounded to2MiB+4096; its archive to that bound+16384. Model
capsules retain65536 archive/16384 member bounds. Import chooses only a trusted source codec,
checks the exact corresponding manifest/human projection and re-exports byte-identically.
No unknown profile is accepted by treating its payload as generic JSON.

The returned historical view preserves the full source object. Human continuity text shows
latest attempt/error and known-good generations, current UNKNOWN and omitted files/Git objects.
It does not execute or render stored guidance as instructions. Historical paths remain data.

## Core and consumers

ReadOnlyCore, the private stdio adapter, MCP and in-process read-capability lab now use the
same closed dispatcher. Their four operations and refusal semantics are unchanged. Capabilities
report the actual profile. No adapter promotes source claims into live proof or authority.
The96KiB response ceiling remains: a large valid continuity record can be archived directly
but a state/capsule transport response exceeding the ceiling returns RESPONSE_LIMIT. No truncation
or partial record is disguised as success. This is a known data-plane limitation for later work.

The Node SDK and thin Codex skill remain explicitly model-only. The skill now checks the
advertised profile and reports UNSUPPORTED_PROFILE for continuity. They are not silently
upgraded by the server's expanded closed set. MCP startup hex arguments also remain subject to
the host's command-line limits; large snapshots may not be launchable through that CLI.

## Validation

Six integration tests cover both profiles through capsule round trip, cross-profile confusion,
unknown remote schema refusal, core and MCP continuity preservation, unchanged model bytes,
and a valid >96KiB V3 record: capsule succeeds losslessly, transport refuses explicitly.
All49 Windows child tests and692 Node checks pass. Full Linux results are in progress.
The original validators and missions remain unchanged. This extends experimental historical
interoperability only; current P3, production quiescence and mutation acceptance do not change.

## Current implementation clarification (M45 audit)

The M10 validation above is historical. M11 added the fifth, fixed capsule.chunk method for
large records; M12 cached its archive; M33 added bounded digest-bound stdin startup; M40/M41
validated a fixed paired Node client and owned transport refusal. Large state.get/export
responses still refuse above96KiB; explicit chunk reconstruction is the supported alternative.
The Node/skill profile limit and absence of general ecosystem acceptance remain unchanged.
