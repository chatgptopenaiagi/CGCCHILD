# CREDID GUARDIAN CODEX (CGC)

## CGCCHILD Windows experimental product — 0.3.0

The current child product provides a Windows desktop historical-evidence workbench,
CLI, Python/Node SDKs, bounded MCP stdio, capsules, reports, explicit modes and
security-debt reporting. Start with [Windows product guide](docs/PRODUCT_GUIDE.md),
[build](docs/WINDOWS_BUILD.md) and [release notes](docs/RELEASE_NOTES.md).
READ_ONLY_SAFE is the default. Production mutation remains disabled.
The inherited sections below preserve historical source status and are not the
current child feature inventory. See [child progress](docs/CGCCHILD_PROGRESS.md).

> **CGCCHILD is an experimental descendant/fork of CREDID GUARDIAN CODEX.**
> Canonical original: [chatgptopenaiagi/CREDID-GUARDIAN-CODEX](https://github.com/chatgptopenaiagi/CREDID-GUARDIAN-CODEX).
> CGCCHILD may contain speculative, partial or unverified implementations.
> Current child state: [CGCCHILD progress](docs/CGCCHILD_PROGRESS.md).
> The inherited status sections below describe canonical source history, not child acceptance.

## V3 current frontier

V3 is authorized and PARTIAL. The pure attempt contract, bounded non-mutating project
inspection, and external human/machine handoff persistence are IMPLEMENTED and VERIFIED
OFFLINE. A deliberate manual local-checkpoint Python adapter is also IMPLEMENTED and
VERIFIED OFFLINE in disposable Linux Git fixtures. Handoff state grants no mutation
authority. Explicit local-bare publication and independent verification are also verified
offline; general push/network transport, full safe resume and automation remain pending.
Opt-in manual SIGINT/SIGTERM cancellation and active Git ref-transaction exclusion are
verified offline. Active local-bare loose-object transfer cancellation is also verified offline.
Real in-command commit interruption at fixture pre/post-commit stages is verified offline;
broader mutation/crash hardening remains PARTIAL.
Active local-bare index-pack interruption after temporary pack arrival is also verified
offline; V4 remains ARCHITECTED / runtime NOT_STARTED.
Real active git add interruption before/after index replacement is verified offline with
a fixture-only loader shim. Abrupt parent death at these gates and fresh-invocation refusal
are verified offline; broader crash safety and full resume remain PARTIAL. No orphan cleanup
is promised by production CGC.
The [fresh-process reconciliation engine](docs/V3_RECONCILIATION.md#14-first-engine-implementation-and-conformance)
is implemented as a bounded read-only Python API with first-engine A–R acceptance. A new mutation after uncertain
interruption needs fresh review when durable review digests are missing; old intent grants
neither new authority nor safe-resume promotion.
The [external safe-resume verifier](docs/V3_SAFE_TO_RESUME.md#13-minimal-verifier-implementation) implements
pure scoped proof for READ_ONLY_ANALYSIS / HANDOFF_ONLY of captured evidence. Its YES grants no
repository action or mutation authority. Wider evidence gaps remain UNKNOWN; the reconciler is unchanged.
The inspect and handoff-status CLIs are observational; there is no preserve or reconcile CLI.
V1/V2 remain accepted. See the local-checkpoint contract in docs/V3_CONTRACT.md.
Resume by present repository evidence and [V3 progress](docs/V3_PROGRESS.md), under the complete
[V3 mission](docs/V3_MISSION.md) and current user instructions. Historical V2 notes
that V3 was not authorized describe the earlier boundary; this explicit V3 mission
supersedes that boundary without authorizing unrelated project mutation or V4.

## V4 future design

[CGC V4 — INTEROPERABILITY, PORTABLE STATE & AGENT CONNECTIVITY](docs/V4_MISSION.md)
is **ARCHITECTED / runtime NOT_STARTED**. V1 observes, V2 understands, V3 preserves and
V4 connects: one verified CGC state, many authorized consumers. The future design covers
inert portable capsules, language-neutral state, local MCP, a thin plugin and optional
Guardian surfaces/gateway. It grants no implementation authority. V3 remains active and
PARTIAL; its [next exact action](docs/V3_PROGRESS.md#next_exact_action) is unchanged.


CREDID GUARDIAN CODEX (CGC) is a concept-first, local usage-awareness, quota-observation and intelligent project-preservation architecture for Codex workflows.

**THE GUARDIAN OBSERVES. CODEX PRESERVES.**

Long-running development can approach a usage boundary while discoveries, partial changes and next steps remain only in conversation context. CGC is intended to act like an aircraft fuel gauge: report available capacity, observation reliability and preservation policy. It does not fly the aircraft or take control of repositories.

## Current status

**CGC V2 — COMPLETE OFFLINE POSIX ACCEPTANCE: GUARDIAN ENGINE, POLICY, CACHE, STATUS CLI AND BOUNDED DAEMON**

| Classification | Status |
|---|---|
| IMPLEMENTED | Existing V1 reader, configurable policy with explicit per-window evidence, freshness/provenance, atomic last-known-good cache, cache-only status CLI, one-shot refresh CLI and finite foreground daemon |
| VERIFIED | 153 tests pass using Linux-native temporary storage; one historical V1 observation. See V2_PROGRESS.md |
| COMPLETE | V2 mission offline acceptance; see V2_ACCEPTANCE.md for evidence and limits |
| NOT IMPLEMENTED | Automatic preservation; hooks, GUI/tray and services |
| UNKNOWN | Backend sample age, complete bucket applicability, supported polling cadence and sustained live reliability |
| PLANNED | Preservation integration/hooks, desktop meter and native Windows support |

The accepted V2 specification is [V2 mission](docs/V2_MISSION.md). Active development
follows [V3 mission](docs/V3_MISSION.md) and
[NEXT_EXACT_ACTION in V3 progress](docs/V3_PROGRESS.md#next_exact_action).
The Codex app-server source remains experimental. V2 consumed **zero live quota reads**.
Independent human `/status` comparison remains PENDING / NOT VERIFIED. The retained
V1 percentages are historical evidence, not current quota.

```bash
PYTHONPATH=src python3 -B -m cgc status --json
TMPDIR=/tmp PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Status reads only the shared cache and reports UNKNOWN if none exists. The finite daemon
requires explicit `--live`, `--bucket` and `--max-reads` arguments. No service is installed.
Read [V2 operation, safety limits and commands](docs/V2_OPERATIONS.md) before invoking it.
See [V1 source discovery](docs/QUOTA_SOURCE_DISCOVERY.md) for historical protocol evidence.

## V3 inspection only

```bash
PYTHONPATH=src python3 -B -m cgc inspect --project /absolute/project/root --json
```

Requires an explicitly selected ordinary Git root on Linux-native storage with safe
ownership/modes. Outputs metadata only; does not write a handoff or preserve work.
Exit 0 means OBSERVED, 1 means REFUSED (including operational failure/cancellation),
2 means invalid CLI arguments. Gitfiles/linked-worktree targets and unsupported Git
configuration are explicitly refused. Remote URLs and document contents are not exported.
See [inspection contract and limits](docs/V3_CONTRACT.md#bounded-project-inspection).

## V3 durable handoff

```bash
PYTHONPATH=src python3 -B -m cgc handoff-status --store-dir /absolute/private/store --project /absolute/project/root --json
```

Reads an explicitly selected external store; never creates missing storage or runs a
project command. Omit `--json` for the human view derived from the same validated state.
Exit 0 means valid continuity state available, including a recorded failed latest attempt;
it does not mean safe to close or resume. Exit 1 means unavailable/refused; 2 means invalid
CLI arguments. Python `HandoffStore.publish` / `record_failure` under `writer()` provide
bounded writes; there is no write/preserve CLI. See the [handoff contract](docs/V3_CONTRACT.md#durable-handoff-persistence).

The manual local-checkpoint Python adapter requires current project-policy approval,
expected HEAD/branch and explicitly reviewed file digests. It has been exercised only in
disposable Linux repositories. See [local checkpoint contract](docs/V3_CONTRACT.md#deliberate-manual-local-checkpoint).
The manual publication adapter supports explicitly approved local bare remotes using
forward-only expected-tip ref updates and independent verification. General target Git push,
network transport, test runner, preserve CLI and automation remain unimplemented. See the
[publication contract](docs/V3_CONTRACT.md#explicit-local-bare-publication-and-independent-verification).

## Initial policy

These are CGC defaults, not claims about Codex limits or available quota fields. Evaluate the most constrained usable remaining percentage across any number of applicable windows.

| State | Remaining capacity | Intended response |
|---|---|---|
| GREEN | > 20% | Continue authorized development normally |
| AMBER | > 10% and <= 20% | Continue with awareness; consider checkpoint readiness |
| RED | > 5% and <= 10% | Stop starting major new work; prepare a resumable checkpoint |
| EMERGENCY | <= 5% | Minimum safe preservation only |

Policy inputs must be valid percentages in [0, 100]. The V1 reader clamps derived values as requested but marks out-of-range source values INVALID. Unknown, invalid or stale readings do not become 0% or GREEN. Incomplete window coverage cannot establish that all capacity is healthy. See [policy](docs/PRESERVATION_POLICY.md).

## Architecture (V2 engine/cache/CLI implemented; integrations planned)

```text
Usage source → Quota reader → Normalizer → Validator
                                               ↓
                                 Policy engine + atomic state cache
                                               ↓
                  CLI / Codex hook / future desktop meter
                                               ↓
                    Codex preserves only when authorized
```

**ONE SENSOR. MULTIPLE CONSUMERS.** One normalized state supplies every consumer; interfaces do not independently fetch or recalculate quota. Multiple durations, quota buckets and future windows are supported by the design, without assuming a fixed window count.

The implemented default cache is `~/.codex/cgc/state.json`; it was not created during
development. `python -m cgc status` and `python -m cgc status --json` consume this same
state. The daemon uses one finite writer with an explicit selected bucket scope.
Selection is not applicability evidence: live windows currently remain UNKNOWN. Synthetic
contracts verify policy behavior offline; they cannot authorize live policy.
`hook-check` and desktop integration remain PLANNED, not working commands.

## Security and authority

CGC consumes usage information, never authentication material. It must not read or export authentication files, tokens, browser cookies or password stores. Authentication remains with its owner. A future reader must use a verified, permitted source without bypassing controls.

CGC reports policy; it does not autonomously edit, commit, push or otherwise modify external repositories. Codex remains the reasoning/preservation actor and must follow the current repository's rules and explicit authorization. A RED reading is not permission to publish.

## Documents and roadmap

- [Concept](docs/CONCEPT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Preservation policy and exact directives](docs/PRESERVATION_POLICY.md)
- [Security model](docs/SECURITY_MODEL.md)
- [Provisional data model](docs/DATA_MODEL.md)
- [Staged roadmap](docs/ROADMAP.md)
- [Decisions and genesis evidence](docs/DECISIONS.md)
- [Future deterministic tests](tests/README.md)
- [Agent instructions](AGENTS.md)

## Limitations and next mission

V2 is verified offline on POSIX, with private temporary caches and injected sensors.
No live daemon run, native Windows transport, supported polling cadence or preservation
hook is claimed. Unknown/partial coverage cannot establish global all-clear. The V2 Guardian never executes preservation actions; the V3 manual adapter requires
current explicit target authority. See the [V2 handoff](docs/V2_OPERATIONS.md#handoff).

Product name: **CREDID GUARDIAN CODEX**. Acronym: **CGC**. GitHub identifier: `CREDID-GUARDIAN-CODEX` (a space-free repository identifier only). Licensed under [Apache-2.0](LICENSE).

Freshness/provenance is IMPLEMENTED and VERIFIED OFFLINE: separate age, refresh health
and policy authority; failed refresh withholds current policy while retaining evidence.
See [V2 operations](docs/V2_OPERATIONS.md) for canonical semantics and schema details.

One-shot refresh CLI is IMPLEMENTED and VERIFIED OFFLINE. It requires --live and
--bucket, shares the daemon writer lock/configuration/cache path, and makes at most
one bounded read without retry. Unknown applicability remains UNKNOWN; no preservation
action is executed. See [V2 operations](docs/V2_OPERATIONS.md) for output and exit semantics.

Crash/interruption safety is VERIFIED OFFLINE with synchronized process tests: old/new
canonical state survives tested SIGKILL publication stages, locks release, and graceful
CLI signals preserve bounded read cleanup. Power-loss durability and descendant cleanup
after SIGKILL of CGC are not guaranteed. Default-target metadata preflight and final offline acceptance audit are complete.

Final V2 offline acceptance: [evidence matrix](docs/V2_ACCEPTANCE.md).
153 deterministic tests pass. Zero V2 live reads; optional live verification skipped.
V3 remains NOT_STARTED and requires separate authorization.

## V3 quiescence design boundary

The [bounded quiescence contract](docs/V3_QUIESCENCE.md) is SPECIFICATION COMPLETE; producer runtime NOT_STARTED. Current shared WSL writer coverage remains UNKNOWN. A future closed writer domain must prove descendant containment and filesystem exclusivity separately; no new mutation authority or V4 runtime exists.
