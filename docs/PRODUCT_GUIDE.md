# CREDID GUARDIAN CODEX — Windows preview

CGCCHILD 0.4.0 adds Live Continuity to the historical-evidence workbench. Select
Live Session, choose an explicit project and external session store, and start a
guarded session. CGC observes metadata/Git state every five seconds while the window
is open and writes an evidence checkpoint every twelve polls. Start Codex separately
or use the optional native launcher. End & preserve creates a durable session capsule.
No automatic Git commit, push, source backup or project repair occurs.
READ_ONLY_SAFE names a product mode;
it does not claim hostile-file isolation or production security acceptance.

Start CGC.exe in the portable CGC directory or use the installed Start Menu shortcut.
Open a reviewed canonical CGC JSON snapshot or .cgcpack. Load synthetic example gives
an offline tour. The 13 historical pages and five live pages retain explicit truth
levels and uncertainty. Imported safe-resume is
UNKNOWN. Exports require new filenames. Keep the portable directory together.

```powershell
./CGC-console.exe status
./CGC-console.exe self-test
./CGC-console.exe inspect --input ./example.json
./CGC-console.exe review --input ./example.json
./CGC-console.exe capsule-export --input ./example.json --output ./review.cgcpack
./CGC-console.exe report --input ./review.cgcpack --output ./review.html
./CGC-console.exe dry-run CHECKPOINT
./CGC-console.exe --mode SIMULATION simulate CHECKPOINT
./CGC-console.exe serve --input ./example.json
```

The wheel exposes the same commands through cgcchild or python -m cgcchild. Install
the gui extra for the Python desktop dependency. Standalone Windows includes Python
and Qt. Runtime needs no account, API key, quota read or Internet connection.
serve runs foreground MCP stdio until EOF or a bounded message limit. The caller
controls timeout. No generic command or repository executor is exposed.

inspect reads an inert document, not a live repository. reconcile, review and
safe-resume provide historical offline review, not the inherited POSIX current-capture
reconciler. That collector remains deferred. Invalid input exits 2, executor refusal
exits 1, successful analysis exits 0. Rejected document contents are not echoed.

Live sessions store bounded sanitized metadata in the exact displayed external path,
by default `%LOCALAPPDATA%/CGCCHILD/sessions/<id>`. Source contents, Git objects,
credentials, complete transcripts and hidden AI reasoning are excluded. Explicit
test wrappers execute selected tests; execution alone does not prove a passing result.
On startup the GUI lists unclosed sessions only from CGC's store; recovery is explicit
because another foreground owner may still be active. Resume creates a new generation
for observation and grants no project mutation authority. Reopening a session capsule
is historical review. See [live CLI/SDK/MCP guide](LIVE_CODEX_INTEGRATION.md) and
[observer limitations](LIVE_OBSERVERS.md). Review private notes before sharing. Exports are unsigned,
and consistency is not authenticity. Concurrent file races on untrusted storage are
not excluded; hostile same-user isolation and filesystem closure are not claimed.
