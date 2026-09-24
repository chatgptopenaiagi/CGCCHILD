# CGCCHILD read-only experimental plugin

Repository-local, uninstalled thin skill package. Canonical original:
[CREDID GUARDIAN CODEX](https://github.com/chatgptopenaiagi/CREDID-GUARDIAN-CODEX).
License and attribution: [Apache-2.0](../../LICENSE).

The package provides an inspection skill for an already-connected CGCCHILD core.
It has no hooks, MCP auto-launch file, apps, marketplace entry or executable script.
It does not install or start the core. A missing connection returns CORE_UNAVAILABLE.
Owner-controlled MCP setup and independent Codex interoperability remain untested.

Core contract: [experimental MCP](../../docs/CGCCHILD_MCP.md).
Supported profiles: QUIESCENCE_MODEL_ONLY and V3_CONTINUITY_HISTORICAL.
The latter carries lossless historical V3 handoff receipts; it provides no live P3,
filesystem exclusivity, mutation/recovery or current safe-resume authorization.

The package was scaffolded and statically validated using the installed plugin-creator
skill tooling. Static validation does not mean that Codex has installed or accepted it.


M80 aligns the skill with the existing five fixed core tools. Status is the default;
large state/export responses may refuse. Chunk export requires an already available
bounded validating receiver, unchanged snapshot binding and available request budget.
No generic transport, local executable launcher or automatic service configuration
was added. Node/Python paired conformance is tested separately from Codex acceptance.

The plugin-creator reinstall/cachebuster workflow does not apply: this repository-local
package has no marketplace entry and is not being installed into a running Codex host.
Version0.2.0 describes the expanded historical-profile instructions only. Static plugin
and skill validation are necessary shape checks, not live integration evidence.
