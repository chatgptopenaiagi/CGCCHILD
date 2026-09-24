# Windows 0.3.0 release acceptance

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
