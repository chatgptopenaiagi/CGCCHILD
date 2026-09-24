# Release process

Run test tiers and record WINDOWS_TEST_RESULTS.json. Build with packaging/build.ps1.
Review tracked contents, immutable plan hash, license and source isolation. Commit,
push only child origin and verify local/tracking/live equality. At clean HEAD run
packaging/release.py for archives, checksums and manifest. Never force tags/history.

```powershell
gh release create v0.3.0-experimental --repo chatgptopenaiagi/CGCCHILD --target (git rev-parse HEAD) --prerelease --title 'CGCCHILD Experimental Windows Release' --notes-file docs/RELEASE_NOTES.md
Get-ChildItem dist -File | ForEach-Object { gh release upload v0.3.0-experimental $_.FullName --repo chatgptopenaiagi/CGCCHILD }
```

The manifest binds assets to source commit. Later documentation-only receipts can
advance main; they do not imply rebuilding assets. SHA256SUMS includes manifest hash;
the manifest never hashes itself. Checksums are not signatures or production proof.
