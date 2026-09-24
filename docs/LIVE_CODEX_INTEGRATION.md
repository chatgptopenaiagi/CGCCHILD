# Live Codex integration — 0.4.0 experimental

CGC uses explicit structured agent reports, independent Windows project observation,
read-only Git inspection and deliberate test wrappers. There is no private Codex
history reader, hidden reasoning collector, lifecycle scraper or network listener.
Host authentication remains owned by Codex. CGC never reads account credentials.

Read-only observers resolve `git.exe` and `gh.exe` only from bounded absolute PATH
directories outside the current directory and selected project. Empty, relative,
project-local and batch-script candidates are refused. This avoids implicit
Windows current-directory executable search; it is not binary attestation or
hostile same-user isolation. Metadata filenames matching the central secret
redaction rules are excluded before baseline persistence.

The supported integration route is local MCP stdio, documented in the official
[Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). The
[plugin packaging guide](https://developers.openai.com/plugins/build/plugins)
confirms support for the compatibility `.codex-plugin/plugin.json` layout used
here. Documentation was reviewed on 2026-09-24. Available lifecycle hooks depend
on host support and trust; this release installs no hooks and does not claim full
automatic Codex lifecycle coverage. Actual Codex host acceptance is NOT_EXECUTED.

The new `plugins/cgcchild-live` package contains the manifest, reporting skill,
capabilities, Apache-2.0 license and `.mcp.json`. Its default command is
`cgcchild live serve`; it requires a reviewed CGC installation on PATH and an
explicit session selected through inherited `CGC_SESSION_DIR`. A configured
absolute `CGC-console.exe` plus `live serve --session <directory>` also works.
No marketplace, account, plugin installation or existing host settings are changed.
The previous read-only historical plugin remains available independently.

The adapter exposes `cgc_live_status` and fixed reporting tools for session start/end,
commands, edits, tests, errors/resolutions/reopening, decisions, commits, pushes,
unfinished work and proposed next actions. Reports always enter as REPORTED with
UNKNOWN reconciliation; client-selected actor, source, grade, internal events or
executables are refused. Embedded payload labels remain claims. The core can append
separate observation/reconciliation events; it never rewrites a report into proof.
Session start/end report tools do not change the controller's state.

MCP uses protocol negotiation for the implemented 2025-11-25 initialize, ping and
tools subset. It requires initialization, rejects duplicate JSON keys, bounds frames
to 16 KiB and responses to 128 KiB, and terminates after at most 4096 input messages
or EOF. The owner controls process lifetime and may select a lower message limit.
Report calls write the CGC store and correctly advertise readOnlyHint=false;
the compact status tool is read-only. No tool runs tests, launches a worker,
creates sessions, mutates a project, commits, pushes or grants execution authority.
Transport ownership is not source authentication; hostile same-user isolation is
not claimed. The optional AF_PIPE transport is DEFERRED; owned stdio supplies the
tested nonnetwork local transport without persisted authentication material.

The optional managed launcher is explicit: `cgcchild live launch --session ...`
or the GUI's Launch Codex control. It invokes an existing native `codex.exe`, or an
explicit selected `.exe`, through Windows process creation with the selected project
as its working directory. It uses no shell, WSL or prompt injection. Session ID,
directory, generation and stdio endpoint metadata are inherited in the child
environment. No credentials, environment dump or process transcript are persisted.
The native interactive worker receives its own console. Process creation is not
task success. A missing executable or `.cmd`-only installation refuses the launch;
observer-only continuity remains available. The launcher does not discover or
install executable dependencies.

The CLI adds these explicit commands:

```powershell
cgcchild live start --project 'C:\MyProject'
cgcchild live list
cgcchild live status --session 'C:\CGCStore\selected-session'
cgcchild live observe --session 'C:\CGCStore\selected-session'
cgcchild live observe --session 'C:\CGCStore\selected-session' --verify-remote
cgcchild live watch --session 'C:\CGCStore\selected-session' --duration 60
cgcchild live report --session 'C:\CGCStore\selected-session' --event-type DECISION_DECLARED --payload '{"text":"Keep the public API stable"}'
cgcchild live test --session 'C:\CGCStore\selected-session' --framework unittest -- python -m unittest discover
cgcchild live checkpoint --session 'C:\CGCStore\selected-session'
cgcchild live preserve --session 'C:\CGCStore\selected-session'
cgcchild live open --input 'C:\CGCStore\selected-session\capsules\final.cgcpack'
cgcchild live recover --session 'C:\CGCStore\interrupted-session'
cgcchild live resume --session 'C:\CGCStore\interrupted-session'
```

`end` aliases `preserve`; `interrupt` records a deliberate interruption. A finite
foreground `watch` observes at a selected interval and writes evidence checkpoints;
it does not create Git commits or save source content. These checkpoints record
evidence only. Watch duration is 1–3600 seconds; interval is 0.1–60 seconds and
checkpoint interval is 1–3600 seconds. Ctrl+C records interruption. No hidden
Windows service is installed, and a watch finishing does not imply session completion.

`live test` exits 0 only for VERIFIED_PASS. It exits 1 for VERIFIED_FAIL,
CONTRADICTED, or an observed unsuccessful command whose test counts are unknown.
It exits 2 when verification is unavailable: launch refusal, incomplete capture,
unparsed output despite command exit 0, or no tests. The JSON result preserves the
child's actual exit code separately. Thus a successful command cannot be mistaken
for verified tests by a script checking the CGC exit status.
Its timeout defaults to 60 seconds. Set `--timeout 600` before the `--` command
separator for longer suites; the supported range is greater than 0 through 600
seconds. `Session.run_test(..., timeout=600)` exposes the same bound in Python.

The Python facade adds `sdk.live_start`, `live_open`, `live_capsule_open` and
`live_sessions`; returned Session methods preserve the same truth/authority laws.
The Node facade adds a bounded Windows subprocess client and report builder while
retaining existing historical codecs. Independent paired process tests cover these
interfaces. Capsule import remains historical and cannot reactivate a session or
convert AI_PROPOSED_NEXT_ACTION into permission.
