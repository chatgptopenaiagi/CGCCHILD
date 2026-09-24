# Release process

Current target: Windows `0.4.0`, private GitHub prerelease `v0.4.0-experimental`.
The M85/M86 implementation is staged; the release is not considered published or verified
until the final receipts in WINDOWS_RELEASE_ACCEPTANCE.md and WINDOWS_TEST_RESULTS.json
say so. Run all orchestration from C:\Codex-Projects\CGCCHILD using native PowerShell.

1. Verify workspace/root, clean source intent, private child repository and origin-only push
   destination. Upstream push remains disabled. Preserve user changes, license/attribution,
   original-source bytes and immutable master-plan snapshot bytes. Never force tags/history.
2. Run product, live Q1-Q6 and Windows-compatible child tests. Record exact passed/failed/skipped
   counts and scope in WINDOWS_TEST_RESULTS.json. Do not execute skipped POSIX fixtures.
   Run both plugin validators plus historical/live Node checks and offline package installation.
3. Build with packaging/build.ps1. Validate a fresh wheel venv, relocated frozen app with Python
   removed from PATH, all desktop pages, real temporary live sessions and capsule preservation/
   fresh-process reopen. Test installer install, actual 0.3.0-to-0.4.0 upgrade, uninstall and
   retained exports using explicitly owned directories. A reduced PATH is not a clean VM.
   If the shipping AppId is already installed outside QA, preserve it and compile QA-only
   AppId variants from the same installer script and old/new payloads. Record that narrower
   registration-isolated acceptance; do not claim the exact shipping-AppId lifecycle ran.
4. Finalize reviewed source and test records, commit normally and push only child origin.
   Verify local HEAD, origin/main and live refs/heads/main equality. Use this resolved source
   commit for the release, rebuilding/rechecking final artifacts when source changes require it.
   Do not bind an older executable to a newer implementation merely by changing its manifest.
5. At clean release-source HEAD run packaging/release.py. Inspect the exact `dist` inventory;
   do not accidentally upload previous-version or unrelated artifacts. Validate source/portable/
   both-plugin ZIPs, wheel, Node tarball, installer, preview, release notes, manifest and checksums.
   The EXE directory entries are verified inside the portable bundle even when not separately
   uploaded. SHA256SUMS includes the manifest digest; the manifest never hashes itself.
6. Create the child-only private draft prerelease at the verified source commit, upload the
   reviewed asset set and compare every GitHub asset size/SHA256 against the local file.
   Download-and-hash where a server digest is unavailable. A successful upload exit code alone
   does not establish asset equality. Publish the prerelease after those checks pass.
7. Verify the published release, tag target, asset inventory and remote main ref independently.
   Record actual source SHA/tag, publication URL and asset receipts. A later documentation-only
   receipt commit may advance main; verify its local/origin/live equality separately.

The native GUI smoke can exercise an explicitly selected live capsule under reduced PATH:

```powershell
$env:CGC_SMOKE_LIVE_CAPSULE = 'C:\owned-qa\preserved-session.cgcpack'
& 'C:\owned-qa\relocated\CGC.exe' gui --smoke-output 'C:\owned-qa\live-gui.png'
Remove-Item Env:CGC_SMOKE_LIVE_CAPSULE
```

Use new export filenames. The smoke option validates the imported capsule, visits all 18 pages
and captures historical Live Session. Without that smoke-only variable it retains the synthetic
Dashboard path. Ordinary desktop startup does not read or import the variable's path. Running
session preview generation is available through packaging/live_preview.py with explicit new
`--output` and `--capsule` paths; it uses an owned temporary Windows project and preserves after
capture. No network account, real Codex task or production project is required for those fixtures.

The manifest binds assets to source commit. Later documentation-only receipts can
advance main; they do not imply rebuilding assets. SHA256SUMS includes manifest hash;
the manifest never hashes itself. Checksums are not signatures or production proof.

Keep unexecuted pristine-VM/signing/installed-Codex-host acceptance explicit. Optional AF_PIPE
is deferred; the release provides tested bounded foreground MCP stdio. No persistent Windows
service, network listener, source-tree preservation, automatic project Git mutation, privileged
collector or security-control bypass is introduced to make package acceptance pass.
