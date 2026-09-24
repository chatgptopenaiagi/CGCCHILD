# CREDID GUARDIAN CODEX — Windows preview

CGCCHILD 0.3.0 is an experimental historical-evidence workbench for saved continuity,
capsules, recovery planning and inert reports. It never automatically checkpoints,
pushes, repairs or runs project commands. READ_ONLY_SAFE names a product mode;
it does not claim hostile-file isolation or production security acceptance.

Start CGC.exe in the portable CGC directory or use the installed Start Menu shortcut.
Open a reviewed canonical CGC JSON snapshot or .cgcpack. Load synthetic example gives
an offline tour. All 13 pages share one validated snapshot. Imported safe-resume is
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

The desktop stores no user data automatically. Reports/capsules go to explicit
export paths. Review private continuity notes before sharing. Exports are unsigned,
and consistency is not authenticity. Concurrent file races on untrusted storage are
not excluded; hostile same-user isolation and filesystem closure are not claimed.
