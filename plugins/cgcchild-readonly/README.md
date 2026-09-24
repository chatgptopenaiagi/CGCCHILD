# CGCCHILD read-only experimental plugin

Repository-local, uninstalled thin skill package. Canonical original:
[CREDID GUARDIAN CODEX](https://github.com/chatgptopenaiagi/CREDID-GUARDIAN-CODEX).
License and attribution: [Apache-2.0](../../LICENSE).

The package provides an inspection skill for an already-connected CGCCHILD core.
It has no hooks, MCP auto-launch file, apps, marketplace entry or executable script.
It does not install or start the core. A missing connection returns CORE_UNAVAILABLE.
Owner-controlled MCP setup and independent Codex interoperability remain untested.

Core contract: [experimental MCP](../../docs/CGCCHILD_MCP.md).
Only historical model snapshots are supported; no full V3 handoff, live P3,
filesystem exclusivity, mutation/recovery or safe-resume authorization is provided.

The package was scaffolded and statically validated using the installed plugin-creator
skill tooling. Static validation does not mean that Codex has installed or accepted it.
