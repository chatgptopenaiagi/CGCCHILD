# Windows 0.4.0 Live Continuity release acceptance

Current status: **WINDOWS SOFTWARE AND FINAL PACKAGE TESTS PASSED; PRIVATE RELEASE
PUBLICATION PENDING**. The target is private prerelease `v0.4.0-experimental`.
Release-source commit, published tag and uploaded asset receipts are pending; this document
does not assert publication. The earlier 0.3.0 acceptance record is preserved below.

| Feature / tier | Classification | Verified scope or remaining final gate |
|---|---|---|
| Q1 event/schema/truth/redaction | VERIFIED ON WINDOWS | Bounded cgc-live-event-0.1, hash chain, central redaction, distinct grade/reconciliation state and controller transitions |
| Q2 Windows filesystem observer | VERIFIED / EXPERIMENTAL | Explicit-root metadata polling and reparse boundaries; transient edits may be missed; no exclusivity claim |
| Q2 Git observer | VERIFIED / EXPERIMENTAL | Read-only local refs/object checks and explicit remote-ref comparison; unavailable/unsupported evidence remains UNKNOWN |
| Q2 test observer | VERIFIED / EXPERIMENTAL | Explicit unittest/pytest/npm parsing, process metadata/digests and unknown-count fallback; no proof of honest test code or containment |
| Q2 errors/decisions/reconciliation | VERIFIED / EXPERIMENTAL | Durable reports, resolutions/reopening, evidence links and retained contradictions; no report-to-verified shortcut |
| Q3 structured Codex adapter | VERIFIED IN OWNED PROCESSES | Foreground bounded MCP stdio, reporting plugin and SDK calls; real installed host lifecycle NOT_EXECUTED |
| Optional Windows AF_PIPE | DEFERRED | No named-pipe listener/service claimed; tested local stdio remains available |
| Managed native Codex executable launcher | CONTRACT-TESTED | Explicit native executable/cwd/ephemeral metadata; actual Codex host lifecycle NOT_EXECUTED; observer-only fallback |
| Q4 live Windows session | VERIFIED IN TEMPORARY PROJECTS | Start, real file/Git changes, parsed tests, reports, checkpoints, capsule preserve/reopen and remote fixture verification |
| Q5 interruption/recovery | VERIFIED WITH BOUNDED FIXTURES | Process interruption, replay, torn-tail retention, recovery assessment and generation linkage; power-loss guarantees and automatic source repair excluded |
| Q6 desktop GUI | VERIFIED ON WINDOWS | 18 pages; live controls, timeline/Git/tests/errors, background I/O, interruption on close, historical capsule reopen and source preview |
| Fresh-process live capsule GUI | VERIFIED FROM SOURCE | Explicit smoke capsule selection and historical rendering; final frozen reduced-PATH render PASSED |
| Historical workbench | VERIFIED REGRESSION | Existing snapshots, capsules, modes, reports and safety/refusal boundaries retained |
| Python SDK | VERIFIED FROM SOURCE | Live controller facade and historical APIs; final fresh-wheel install/live/recovery/reopen/uninstall PASSED |
| Node SDK | VERIFIED / PACKAGED OFFLINE | 61 live and five historical contract checks pass after offline package installation |
| Historical/live plugin packages | VALIDATED OFFLINE | Both manifest/skill packages pass; no host installation or automatic lifecycle acceptance inferred |
| Q7 wheel | VERIFIED_CURRENT_HOST | Final wheel fresh-venv install/import/live tests/recovery/preserve/reopen/uninstall passed |
| Q7 CGC.exe / CGC-console.exe / portable ZIP | VERIFIED_CURRENT_HOST | Final relocated payload, no Python/Git on PATH, UNKNOWN Git fallback, live recovery/capsule and native GUI passed; archive integrity checked at release |
| Q7 installer | VERIFIED_QA_APPID / SHIPPING_ID_PARTIAL | QA-only AppId variants use the same installer script and old/new payloads for real 0.3-to-0.4 upgrade; shipping-AppId lifecycle NOT_EXECUTED because an existing owner installation is preserved |
| Q8 source/plugin/Node/preview/manifest/checksums | FINAL ACCEPTANCE PENDING | Inventory, archive validation and hashes must bind the final reviewed release source |
| Q8 private GitHub prerelease | NOT YET VERIFIED | Publish only child origin; compare every uploaded asset size/digest against local bytes |
| Clean independent Windows 10 x64 VM | NOT_EXECUTED | Current-host relocation/reduced PATH is not pristine-machine acceptance |
| Trusted signing | NOT_EXECUTED | Experimental binaries and capsules remain unsigned |
| Production mutation / filesystem closure | DISABLED / UNKNOWN | No production repository executor or acceptance promotion; inherited proof debt remains |

Current regression evidence: 14 product tests passed; 203 child tests ran, 173 passed and
30 POSIX-only tests skipped without executing Linux. The final Live Continuity suite passed 61/61 tests. Total Python results are 248 passed
and 30 explicit POSIX skips. [Windows test results](WINDOWS_TEST_RESULTS.json) contain
the final package input digests and retained evidence. Node offline checks total 66.
The final package run finished 2026-09-24T13:31:03Z; original owner registration was
unchanged and the isolated QA registration was removed by its uninstaller.

The reviewed running-session preview uses a real temporary Windows Git project, two actual
passing unittest tests, an evidence checkpoint and a subsequently preserved/reopened capsule.
`packaging/live_preview.py` reproduces it using new explicit export filenames. Explicit
`gui --smoke-output` can load `CGC_SMOKE_LIVE_CAPSULE` for historical live-capsule rendering;
ordinary GUI startup does not read that variable or open its path.

No live quota, WSL/Linux/Bash, privileged proof collection, authentication change or host
security bypass is part of this mission. RO-1..RO-5/R6 remain NOT_EXECUTED. Original-source
and immutable-plan verification must be repeated for the final receipt. Software completion
does not close protected identity/effective policy, hostile same-user isolation or current P3.

NEXT_EXACT_ACTION: complete the final Windows rebuild/package checks, commit reviewed source,
publish the child-only private experimental release and verify asset digests and Git refs.
Record release-source SHA/tag separately from any later documentation receipt HEAD.

## Historical Windows 0.3.0 release acceptance

Published private prerelease: [v0.3.0-experimental](https://github.com/chatgptopenaiagi/CGCCHILD/releases/tag/v0.3.0-experimental).
Release source/tag: 9ab0435f60e1bdf6dd9f5c051d4dd7b5f57cc16b.
Subsequent main commits record publication evidence only. They do not change asset provenance.

| Feature | Classification | Accepted software scope / limitation |
|---|---|---|
| Wheel | COMPLETE | Fresh venv install/import/CLI/read/uninstall |
| Windows EXE | COMPLETE | Relocated onedir, reduced PATH, real GUI smoke |
| Installer | COMPLETE | Current-host per-user install/upgrade/uninstall; exports retained |
| Portable/source/checksums/manifest | COMPLETE | Archive/member/resource/hash validation |
| Desktop GUI | COMPLETE | 13 historical-workbench pages; screenshot reviewed |
| Reporting | COMPLETE | Inert HTML from validated snapshots/capsules |
| Product modes/security debt | COMPLETE | Five explicit modes; nine tracked debt records |
| Plugin package | COMPLETE | Offline manifest/skill validation; no automatic installation |
| Installed plugin interoperability | PARTIAL | Host acceptance NOT_EXECUTED |
| Python/Node SDK facade | COMPLETE | Version negotiation, both-profile byte parity, packaged Node smoke |
| V3 planning/recovery review | EXPERIMENTAL | Historical offline analysis; no current capture or execution |
| Windows fresh repository capture | PARTIAL | Inherited POSIX capture not ported; no current-safety claim |
| Production mutation | BLOCKED | Null/refusal executor in all modes |
| V4 state/capsule/local MCP | EXPERIMENTAL | Canonical codecs, integrity, bounded foreground stdio |
| Local Agent Fabric | EXPERIMENTAL | Scoped grants/routes/expiry/revocation/audit; trusted local caller |
| Remote gateway / distributed Fabric | NOT_STARTED | Optional, no transport/authentication/executor |
| Clean independent Windows VM | PARTIAL | Current-host isolation tests passed; separate VM NOT_EXECUTED |
| Release signing | NOT_STARTED | Explicitly unsigned experimental assets |

Windows tests: 14 product tests passed; 203 child tests ran, 173 passed and 30 POSIX
skips. Node facade checks: five passed, repeated after offline tarball install.
Three package smoke groups passed. All ten GitHub asset sizes/digests independently
matched local bytes before publication. No WSL/Linux/Bash, quota or privileged proof
operation ran. Offscreen Qt warnings did not occur as a real Windows rendering failure.

Filesystem closure/current P3 remain UNKNOWN. Protected identity/effective policy
remain unresolved; RO-1..RO-5/R6 remain NOT_EXECUTED. B11 stays historical unresolved
debt. Read [security debt](SECURITY_ACCEPTANCE_DEBT.md); software completion does not
promote any of these claims. Original source and immutable plan are unchanged.

NEXT_EXACT_ACTION: validate the published portable/installer on a separate clean
Windows 10 x64 context when available. Keep production execution disabled. This is
follow-up acceptance, not a blocker to the published experimental software release.
