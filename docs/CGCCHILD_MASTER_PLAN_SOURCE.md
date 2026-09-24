# CREDID GUARDIAN CODEX (CGC)

## Full Architecture Tree and Master Plan

**Snapshot date:** 2026-09-24  
**Repository:** `chatgptopenaiagi/CREDID-GUARDIAN-CODEX`  
**Branch:** `main`  
**Verified checkpoint:** `ce41ad2020ddfcaa7a2a3687ade86c6eb8358ea4`  
**Checkpoint message:** `docs: record M1-M5 evidence and native lab ABI gaps`

> This document is a readable architecture snapshot and forward plan. The live repository, especially `docs/V3_PROGRESS.md`, `docs/V3_QUIESCENCE.md`, `docs/V3_QUIESCENCE_LAB_ABI.md`, and `docs/DECISIONS.md`, remains the operational source of truth.

---

## 1. CGC in one sentence

CGC is a model-agnostic, evidence-preserving, failure-aware engineering continuity layer designed to preserve **engineering truth**, not merely conversational memory.

Core progression:

```text
V0 FOUNDATION
   |
V1 OBSERVE
   |
V2 UNDERSTAND
   |
V3 PRESERVE      <-- ACTIVE NOW
   |
V4 CONNECT       <-- ARCHITECTED, RUNTIME NOT STARTED
```

Core product law:

```text
THE GUARDIAN OBSERVES. CODEX PRESERVES.
THE PRODUCT IS NOT MORE CODE.
THE PRODUCT IS VERIFIED CONTINUITY.
THE PRODUCT IS HUMAN TIME RETURNED.
```

---

## 2. Whole CGC tree

```text
CREDID GUARDIAN CODEX (CGC)
|
+-- V0 - FOUNDATION                                      [COMPLETE]
|   +-- project genesis / naming
|   +-- evidence-first architecture
|   +-- security and authority boundaries
|   +-- repository rules and decision journal
|
+-- V1 - OBSERVE                                         [COMPLETE]
|   +-- quota/source discovery
|   +-- minimal usage reader
|   +-- normalization
|   +-- validation
|   +-- first law: observation != authority
|
+-- V2 - UNDERSTAND                                      [COMPLETE]
|   +-- Guardian engine
|   +-- configurable policy / thresholds
|   +-- limiting-window reasoning
|   +-- freshness + provenance
|   +-- atomic last-known-good cache
|   +-- status CLI
|   +-- one-shot refresh CLI
|   +-- finite foreground daemon
|   +-- crash/interruption safety acceptance
|
+-- V3 - PRESERVE                                        [ACTIVE / PARTIAL]
|   |
|   +-- 3.1 Pure attempt contract                        [DONE]
|   +-- 3.2 Bounded non-mutating project inspection      [DONE]
|   +-- 3.3 Durable human/machine handoff                 [DONE]
|   +-- 3.4 Manual local checkpoint                      [DONE]
|   +-- 3.5 Local-bare publication + verification        [DONE]
|   +-- 3.6 Interruption/crash hardening                  [ADVANCED / PARTIAL]
|   |   +-- signal interruption
|   |   +-- ref transaction interruption
|   |   +-- object transfer interruption
|   |   +-- commit interruption
|   |   +-- index-pack interruption
|   |   +-- git-add index replacement interruption
|   |   +-- parent-death semantics
|   |
|   +-- 3.7 Fresh-process reconciliation engine          [DONE]
|   +-- 3.8 External SAFE_TO_RESUME verifier             [DONE / SCOPED]
|   |   +-- READ_ONLY_ANALYSIS / HANDOFF_ONLY can yield YES
|   |   +-- YES does NOT grant mutation authority
|   |
|   +-- 3.9 Positive quiescence proof                    [CURRENT MAJOR FRONTIER]
|   |   +-- bounded quiescence contract                  [DONE]
|   |   +-- Windows-controlled Fedora experiment         [DONE]
|   |   +-- pidfd / fork / exec / reparent evidence      [DONE]
|   |   +-- same-UID cgroup escape witness               [DONE]
|   |   +-- same-UID ingress witness                     [DONE]
|   |   +-- controller/worker authority audit            [DONE]
|   |   +-- owner-approved protected Linux boundary      [DONE / CONDITIONAL]
|   |   +-- selected candidate:
|   |   |      ROOT_OWNED_BROKER_WITH_BOUND_CONTROLLER
|   |   +-- R1-R5 symbolic lab manifest                  [PARTIAL]
|   |   +-- M1 identity + launch                         [PARTIAL]
|   |   +-- M2 effective manager/policy evidence         [PRIVILEGED READ NEEDED]
|   |   +-- M3 bootstrap integrity                       [PARTIAL]
|   |   +-- M4 native filters + D-Bus codecs             [CURRENT POSITION]
|   |   |   +-- bootstrap filter specialization          [NEXT]
|   |   |   +-- per-role seccomp stages                  [NEXT]
|   |   |   +-- syscall-to-image conformance             [NEXT]
|   |   |   +-- FD-specialized rules                     [NEXT]
|   |   |   +-- D-Bus launch codec                       [NEXT]
|   |   |   +-- D-Bus peer codec                         [NEXT]
|   |   |   +-- deterministic positive/negative vectors  [NEXT]
|   |   +-- M5 lifecycle / survivor semantics            [PARTIAL]
|   |   +-- RO-1..RO-5 privileged read-only package      [PREPARE / NOT EXECUTED]
|   |   +-- owner approval for RO-1..RO-5                [FUTURE GATE]
|   |   +-- execute approved read-only observations      [FUTURE]
|   |   +-- resolve remaining M1-M5 gates                [FUTURE]
|   |   +-- R6 adversarial falsification T1-T14          [NOT EXECUTED]
|   |   +-- closed-admission acceptance / rejection      [FUTURE]
|   |   +-- production quiescence producer               [NOT STARTED]
|   |   +-- filesystem writer exclusivity                [UNKNOWN / SEPARATE GATE]
|   |   +-- real-project P3                              [UNKNOWN]
|   |
|   +-- 3.10 Mutation / preservation execution           [NOT STARTED]
|   +-- 3.11 Recovery engine                             [NOT STARTED]
|   +-- 3.12 Full repository-touching SAFE_TO_RESUME     [NOT STARTED]
|   +-- 3.13 Benchmark gate                              [FUTURE]
|   +-- V3 acceptance                                    [FUTURE GATE]
|
+-- V4 - CONNECT                                         [ARCHITECTED / NOT STARTED]
|   +-- V4.0 CGC State Protocol
|   +-- V4.1 CGC State Capsule
|   +-- V4.2 Local CGC Service / MCP
|   +-- V4.3 Codex CGC Plugin
|   +-- V4.4 Portable SDKs
|   +-- V4.5 Guardian Surfaces
|   |   +-- desktop
|   |   +-- web
|   |   +-- Android
|   |   +-- iOS / tablet
|   +-- V4.6 Optional Remote Gateway
|
+-- LONG-TERM AGENT FABRIC                              [FUTURE]
    +-- Guardian Core
    +-- Agent Gateway / Router
    +-- Capability Model / Policy Engine
    +-- Control Plane
    +-- Data Plane
    +-- Event Model
    +-- Local AI consumers
    +-- Cloud AI through scoped secure transport
    +-- Multi-agent orchestration under policy
```

---

## 3. Where Codex is now

```text
WINDOWS CODEX CLI
Sole primary worker
C:\Codex-Projects\CREDID-GUARDIAN-CODEX
        |
        +-- owns repository / Git / docs / validation
        +-- orchestrates Fedora with wsl.exe
        |
        v
V3 / POSITIVE QUIESCENCE
        |
        v
M4 MECHANICAL SPECIFICATION  <=== YOU ARE HERE
        |
        +-- native bootstrap/filter specialization
        +-- exact seccomp stages
        +-- syscall-to-image conformance
        +-- exact FD policy
        +-- fixed D-Bus launch codec
        +-- fixed D-Bus peer codec
        +-- deterministic protocol vectors
        |
        v
RO-1..RO-5 OWNER READ-ONLY APPROVAL PACKAGE
        |
        v
Privileged evidence collection
        |
        v
Resolve M1..M5
        |
        v
R6 falsification experiment
```

Current state at this snapshot:

| Item | Status |
|---|---|
| V3 | ACTIVE / PARTIAL |
| Candidate profile | ROOT_OWNED_BROKER_WITH_BOUND_CONTROLLER |
| M1 | PARTIAL |
| M2 | Requires privileged read-only confirmation |
| M3 | PARTIAL |
| M4 | PARTIAL - current engineering frontier |
| M5 | PARTIAL |
| RO-1..RO-5 | NOT EXECUTED |
| R6 | NOT EXECUTED |
| Filesystem exclusivity | UNKNOWN |
| Real-project P3 | UNKNOWN |
| Production quiescence producer | NOT STARTED |
| V4 runtime | NOT STARTED |

---

## 4. Runtime architecture now

```text
HUMAN / OWNER
      |
      v
WINDOWS CODEX CLI
PRIMARY WORKER / PROJECT CONTROLLER
      |
      +-- PowerShell / Windows Git / repository
      +-- documentation / tests / commit / push
      +-- Windows-side observation when authorized
      |
      +---- wsl.exe ----------------------+
                                         |
                                         v
                                  FedoraLinux-44
                                  SUBORDINATE LAB
                                         |
                                         +-- fork / exec
                                         +-- pidfd
                                         +-- cgroup v2
                                         +-- namespaces
                                         +-- Linux-native /tmp fixtures
                                         +-- native security experiments
```

The Windows Codex process is the only project worker. Fedora is an execution environment, not a second project authority.

---

## 5. CGC layer model

```text
COLLECTION
  observes bounded facts
       |
       v
RECONCILIATION
  classifies evidence-supported state
       |
       v
VERIFICATION
  evaluates proof obligations
       |
       v
AUTHORITY
  determines current permission
       |
       v
EXECUTION
  acts only after boundary revalidation
```

**Hard law:** no layer may silently become the next layer.

---

## 6. Core engineering laws

```text
INTENT != EXECUTION
ATTEMPT != SUCCESS

SELECTED != STAGED
STAGED != COMMITTED
COMMITTED != PUBLISHED
PUBLISHED != VERIFIED
VERIFIED != SAFE_TO_RESUME

RECONCILED != SAFE_TO_RESUME
SAFE_TO_RESUME_YES != MUTATION_AUTHORIZED
MUTATION_AUTHORIZED != PRECONDITIONS_STILL_TRUE_AT_USE_TIME

HISTORICAL_INTENT != CURRENT_REALITY
HISTORICAL_AUTHORITY != CURRENT_AUTHORITY

PATH_IDENTITY != CONTENT_IDENTITY
DIGEST != AUTHORIZATION
IDENTITY != AUTHORITY
CAPABILITY != AUTHORIZATION

LOCK_ABSENCE != QUIESCENCE
PID_ABSENCE != QUIESCENCE
STABLE_HEAD != QUIESCENCE
STABLE_INDEX != QUIESCENCE
PROCESS_DEATH != SUCCESS
PROCESS_DEATH != FAILURE
PARENT_DEATH != DESCENDANT_DEATH

CLEAN_WORKTREE != SAFE
DIRTY_WORKTREE != UNSAFE

MISSING_EVIDENCE => UNKNOWN
UNKNOWN IS NOT FAILURE
UNKNOWN IS NOT PERMISSION
ACCEPTED_RISK IS NOT KNOWLEDGE
```

Quiescence-specific additions:

```text
PROCESS_GROUP != CONTAINMENT
CGROUP_MEMBERSHIP != CLOSED_ADMISSION
CGROUP_POPULATED_ZERO != CLOSED_LAUNCH_UNIVERSE_EMPTY
PATH_DENIAL != CAPABILITY_DENIAL
ONE_BLOCKED_INTERFACE != CLOSED_ADMISSION
PROCESS_CONTAINMENT != FILESYSTEM_EXCLUSIVITY
LINUX_PROCESS_QUIESCENCE != FILESYSTEM_WRITER_QUIESCENCE
```

---

## 7. V1 - Observe

### Purpose
Read and normalize bounded usage/engineering evidence without turning observation into action authority.

### Completed concepts
- quota/source discovery
- minimal reader
- normalization
- validation
- bounded source semantics
- no credential collection

### Output
Evidence that later layers may interpret, but never an execution grant.

---

## 8. V2 - Understand

### Implemented
- Guardian engine
- configurable threshold policy
- limiting-window reasoning
- freshness/provenance separation
- last-known-good state cache
- cache-only status CLI
- one-shot refresh CLI
- finite foreground daemon
- crash/interruption validation

### Product model

```text
Usage source
   -> reader
   -> normalizer
   -> validator
   -> policy engine + atomic cache
   -> multiple consumers
```

One sensor, multiple consumers. Consumer interfaces must not invent their own truth.

---

## 9. V3 - Preserve

V3 is where CGC turns state awareness into durable, verifiable engineering continuity. It is deliberately slower and proof-heavy because future repository mutation depends on it.

### 9.1 Pure attempt contract
Separates what an actor intended from what actually occurred.

### 9.2 Bounded project inspection
Collects explicit local Git/project evidence with refusal boundaries.

### 9.3 Durable handoff
Persists machine-readable continuity for fresh processes and humans.

### 9.4 Local checkpoint
Allows a narrowly approved checkpoint primitive under explicit evidence and policy.

### 9.5 Publication and independent verification
Separates object transfer, ref update, publication state, and verification.

### 9.6 Interruption safety
Tests real failure boundaries rather than assuming command completion.

### 9.7 Fresh-process reconciliation
Reconstructs current engineering state from bounded evidence, not from chat memory.

### 9.8 SAFE_TO_RESUME verifier
Pure proof engine with action-scoped obligations. Current real YES is deliberately narrow: captured READ_ONLY_ANALYSIS / HANDOFF_ONLY.

### 9.9 Positive quiescence
Current major frontier. The central question is not simply whether the repository looks stable, but whether all relevant writers for a specific future action are positively accounted for.

---

## 10. Quiescence program

### Why this exists
A stable Git HEAD, absent PID, absent lock, or quiet interval is not proof that another process cannot still mutate the relevant state.

### Target concept

`QUIESCENT_WITHIN_ACCEPTED_SCOPE`

It means positive finite writer coverage for an exact project/action/observation interval.

It does **not** mean no process anywhere can mutate anything.

### Required properties
- exact project and Git identity
- action-scoped mutation domains
- finite observation interval
- stable process-instance identity
- descendant accounting
- writer universe coverage
- admission closure
- contradiction retention
- provenance
- invalidation on change
- fresh execution-boundary revalidation

---

## 11. What the Linux experiment proved

Windows Codex used FedoraLinux-44 as a subordinate Linux-native lab.

Observed useful primitives:
- cgroup v2
- pidfd
- fork/exec/reparent tracking
- user/PID namespace creation
- Linux-native temporary fixtures

Important negative witnesses:

```text
worker migrated OUT of delegated cgroup
        +
another same-UID process migrated IN
        =
closed admission NOT proven
```

Also:

```text
original cgroup populated=0
while escaped descendant remained alive
```

Therefore current same-UID delegated cgroup containment is only PARTIAL and admission was observed OPEN.

---

## 12. Authority separation program

The problem moved from visibility to authority:

```text
Can a trusted controller possess control-plane authority
that workers, descendants, and untrusted peers cannot exercise?
```

An audit showed that a worker-only namespace, distinct worker UID, path hiding, or same-owner permissions do not automatically solve the controller-UID peer problem.

The owner approved designing a stronger separate Linux controller/control-plane boundary.

Selected conditional candidate:

`ROOT_OWNED_BROKER_WITH_BOUND_CONTROLLER`

---

## 13. Candidate protected broker architecture

```text
Windows Codex / owner
        |
        v
Authorized Linux administrator / system manager
        |
        v
B = one-shot root-owned broker
        |
        +-- owns raw cgroup/control authority
        +-- fixed closed operation grammar
        +-- no generic shell / arbitrary PID attach
        |
        v
C = dedicated non-root controller
        |
        +-- private process-bound request channel
        +-- no raw cgroup authority
        |
        v
W = separate untrusted worker identity
        |
        +-- restricted FDs
        +-- restricted syscalls
        +-- no controller channel
        +-- descendants inherit restrictions
```

Trust is separated by kernel credentials and a tiny broker, not by labels alone.

---

## 14. R1-R6 proof program

| Gate | Goal | Current state |
|---|---|---|
| R1 | Exact identity allocation + authorized root launch | PARTIAL |
| R2 | Effective system-manager / PolicyKit / deputy authorization | Privileged read required |
| R3 | Bootstrap integrity + credential/dumpability race closure | PARTIAL |
| R4 | Exact FD/syscall/helper/codec policy | PARTIAL / current frontier |
| R5 | Seal, death, restart, cleanup and continuity semantics | PARTIAL |
| R6 | Adversarial falsification of all relevant boundaries | NOT EXECUTED |

R6 is intentionally blocked until earlier gates are sufficiently precise.

---

## 15. M1-M5 blocker program

### M1 - identity and launch
Needs collision-free C/W identities, NSS/session/service review, concrete allocation/reservation, and an exact authorized root launch route.

### M2 - installed manager policy
Upstream documentation and method existence are insufficient. Effective PolicyKit/systemd/deputy authorization must be observed.

### M3 - bootstrap integrity
The project needs proof that the controller can move from privileged bootstrap to the restricted identity without a same-UID injection window or authority leak.

### M4 - native filter and protocol mechanics
**This is the current Codex frontier.**

Required next work:
- distinct bootstrap/final seccomp stages
- exact syscall-to-image mapping
- FD-specialized filter rules
- native x86-64 ABI contract
- fixed CGC_LAB_PROTO_V1 vectors
- fixed D-Bus authentication state machine
- fixed StartTransientUnit codec
- fixed T7/T8 peer codecs
- positive and rejection vectors
- prove absence of a generic D-Bus client capability

### M5 - lifecycle
Must distinguish main process exit from unit/cgroup/process survival and bind manager generation, unit InvocationID, boot identity and restart/reexec invalidation.

---

## 16. RO-1 through RO-5 privileged read-only package

These reads are designed to be separately approved by the owner. They are **not executed** at this snapshot.

### RO-1 - identity allocation metadata
Read bounded NSS/login/subuid/subgid information for proposed candidate identities.

### RO-2 - candidate identity usage
Check only proposed IDs for process/session/service/namespace collisions.

### RO-3 - installed PolicyKit rules
Read bounded relevant local/vendor rules to determine actual authorization policy.

### RO-4 - deputy policy
Review bounded sudo/pkexec/run0/D-Bus-related authorization routes affecting the lab.

### RO-5 - kernel/manager continuity metadata
Read dumpability/ptrace/LSM/systemd continuity properties without restart/reexec or mutation.

The package explicitly excludes secrets, authentication material, environment dumps, browser data, token values, and unrelated account content.

---

## 17. R6 future falsification experiment

R6 is designed to try to BREAK the selected profile. Normal success is not enough.

Planned attack families include:

```text
T1  worker self-egress
T2  descendant egress
T3  external UID_W peer ingress
T4  external UID_C peer ingress + bootstrap injection attempts
T5  retained writable control FD
T6  alternate cgroup path / alias
T7  manager AttachProcesses routes
T8  unauthorized transient unit / property mutation
T9  wrong-sender duplicated controller endpoint
T10 stale/queued request after seal
T11 authority-changing exec
T12 controller death
T13 broker death
T14 descriptor transfer attempt
```

Any successful forbidden transition falsifies its corresponding claim.

---

## 18. Production quiescence producer

Status: **NOT STARTED**.

The production producer must not be implemented merely because the disposable Linux profile passes R6. It must also solve the remaining production evidence questions and integrate with the verifier without turning evidence into authority.

---

## 19. Filesystem exclusivity

This is separate from process containment.

The real repository lives on Windows storage and may be writable from:
- Windows editors
- Windows Git
- host tools
- WSL distros
- Docker/shared mounts
- background developer tools
- other filesystem writers

Therefore:

```text
LINUX PROCESS QUIESCENCE
!=
FILESYSTEM WRITER QUIESCENCE
```

Real-project P3 remains UNKNOWN until this separate gate is honestly solved for the intended action scope.

---

## 20. Future mutation and recovery

Only after adequate quiescence, evidence, review, tests, current authority, and use-time revalidation can CGC consider repository-touching preservation execution.

Future chain:

```text
proof sufficiently complete
        |
        v
authority separately established
        |
        v
execution preconditions revalidated
        |
        v
scoped mutation / checkpoint / publication
        |
        v
independent verification
        |
        v
durable handoff
```

Recovery remains separate and must never invent causal history.

---

## 21. Benchmark gate

Before aggressive expansion, CGC intends to measure practical value against a normal fresh-agent workflow.

Metrics include:
- recovery time
- token consumption
- duplicate commands
- duplicate tests
- duplicate work
- incorrect mutation attempts
- false completion
- valid work reverted
- human intervention
- unsafe recovery attempts
- CGC overhead

The product metric is human time returned plus AI capacity returned plus recovery confidence.

---

## 22. V4 - Connect

V4 is fully architectural at this snapshot. Runtime implementation has not started.

### V4.0 - State Protocol
Stable schemas and portable semantics after V3 acceptance.

### V4.1 - State Capsule
Inert deterministic export/import with integrity, never executable authority.

### V4.2 - Local CGC Service / MCP
Bounded local API, read-only first.

### V4.3 - Codex CGC Plugin
Thin integration layer. The plugin is not the brain; CGC core remains state authority.

### V4.4 - Portable SDKs
Selected language bindings and semantic parity.

### V4.5 - Guardian Surfaces
Desktop, web, Android, iOS/tablet. Local/offline views first.

### V4.6 - Optional Remote Gateway
Enterprise/multi-device/cloud-agent connectivity only after local security/capability models are accepted.

V4 dependency chain:

```text
finish V3
  -> stable state protocol
  -> inert capsule
  -> local service / MCP
  -> plugin
  -> SDKs
  -> Guardian surfaces
  -> optional remote gateway
```

---

## 23. Long-term Agent Fabric

Possible future CGC ecosystem:

```text
                        HUMAN / POLICY
                             |
                             v
                        CONTROL PLANE
                             |
            +----------------+----------------+
            |                                 |
            v                                 v
      CAPABILITY MODEL                   EVENT MODEL
            |                                 |
            +----------------+----------------+
                             |
                             v
                      AGENT GATEWAY / ROUTER
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
          CODEX          LOCAL AI        CLOUD AI
             |               |               |
             +---------------+---------------+
                             |
                             v
                          CGC CORE
                             |
                             v
                VERIFIED ENGINEERING STATE
```

Identity, capabilities, and transport never automatically imply authorization.

---

## 24. Current Windows/Fedora operating model

```text
PRIMARY:
Windows Codex CLI
  - repository owner/worker
  - Git operations
  - PowerShell
  - documentation
  - validation
  - commit/push

SUBORDINATE LAB:
FedoraLinux-44 through wsl.exe
  - Linux-only process/security experiments
  - no independent Codex project worker
  - no concurrent repository control
```

This avoids two agents writing the same repository while preserving Linux-specific evidence capability.

---

## 25. Current next exact direction

At checkpoint `ce41ad2020ddfcaa7a2a3687ade86c6eb8358ea4` the current frontier is:

```text
COMPLETE FIXED NATIVE BOOTSTRAP/FILTER SPECIALIZATION
        +
COMPLETE D-BUS LAUNCH/PEER CODEC SPECIFICATION
        +
ADD DETERMINISTIC POSITIVE/NEGATIVE VECTORS
        |
        v
REVIEW RO-1..RO-5
        |
        v
PREPARE SEPARATE OWNER READ-ONLY APPROVAL
        |
        v
STOP
```

R6 remains blocked.

---

## 26. Stop boundaries

At this snapshot the following remain explicitly not started or not authorized by architecture alone:

- production quiescence producer
- production mutation executor
- recovery engine
- accepted-risk runtime
- automatic repair
- full repository-touching SAFE_TO_RESUME
- V4 runtime
- MCP server
- plugin runtime
- SDK runtime
- desktop/mobile Guardian runtime
- remote gateway
- general Agent Fabric runtime

---

## 27. Final map

```text
PAST
  V0 FOUNDATION                   COMPLETE
  V1 OBSERVE                      COMPLETE
  V2 UNDERSTAND                   COMPLETE

PRESENT
  V3 PRESERVE                     ACTIVE / PARTIAL
    -> Quiescence proof
       -> Protected controller/worker design
          -> M4 exact mechanical specification   <=== NOW

NEAR FUTURE
  -> RO-1..RO-5 review and owner approval
  -> privileged read-only evidence
  -> resolve M1..M5
  -> R6 falsification
  -> accept/reject closed admission
  -> production quiescence producer
  -> filesystem writer proof
  -> real P3
  -> mutation/recovery acceptance
  -> complete V3

LATER
  V4 CONNECT
    -> State Protocol
    -> Capsule
    -> Local Service / MCP
    -> Plugin
    -> SDKs
    -> Guardian Surfaces
    -> Optional Remote Gateway

LONG TERM
  Agent Fabric under explicit capability + authority policy
```

---

## 28. Terminal principle

```text
CGC DOES NOT PRESERVE WHAT AI REMEMBERS.
CGC PRESERVES WHAT ENGINEERING EVIDENCE SUPPORTS.

THE PRODUCT IS NOT CONTINUITY OF CONVERSATION.
THE PRODUCT IS CONTINUITY OF ENGINEERING TRUTH.
```
