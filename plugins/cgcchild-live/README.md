# CGC Live Continuity plugin

Repository-local experimental plugin for CREDID GUARDIAN CODEX. This Apache-2.0
descendant retains the [original project's attribution](https://github.com/chatgptopenaiagi/CREDID-GUARDIAN-CODEX).

The plugin bundles a reporting skill and a foreground stdio MCP configuration.
It is distributed for explicit installation, not installed by the release process.
No marketplace or host settings are changed. Actual Codex host interoperability
remains NOT_EXECUTED; paired protocol tests validate the CGC side.

Install the CGC wheel in a reviewed environment so `cgcchild` is available, or set
the MCP command to the absolute `CGC-console.exe` location. Before starting the
host, set `CGC_SESSION_DIR` to an existing session selected by the owner. The
managed launcher provides this variable for its launched process. Alternatively
configure args as `live serve --session <explicit session directory>`.
The server refuses to start without that session and never creates one implicitly.

```powershell
cgcchild live start --project 'C:\MyProject'
$env:CGC_SESSION_DIR = 'C:\Users\Owner\AppData\Local\CGCCHILD\sessions\selected-id'
cgcchild live serve --session $env:CGC_SESSION_DIR
```

The session path is metadata, not authentication. Foreground stdio is owned by its
parent host and has finite frame, response and message limits. There is no TCP
listener, Windows service, named-pipe authentication material, private transcript
reader or arbitrary project command tool. Same-user hostile isolation is unproven.

Each `cgc_live_*` reporting tool appends only REPORTED claims; it cannot set the
grade/source, verify a push, run a test or transition the session controller.
`cgc_live_status` reads a compact summary. A receipt is not proof of claim truth.
The independent observers and user-started test wrapper supply separate evidence.
No lifecycle hook is installed and complete automatic capture is not claimed.

The supported compatibility layout and stdio configuration follow the official
[plugin packaging guide](https://developers.openai.com/plugins/build/plugins) and
[Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), reviewed
2026-09-24. These docs support the integration mechanism, not this plugin's host
acceptance. Static plugin and skill validation are separate checks.
