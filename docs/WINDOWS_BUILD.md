# Windows build

Host: Windows 10 19045 x64, PowerShell 7, Python 3.14. Existing VS Community MSVC 14.51
and Windows SDK tools were found. Native compilation was unnecessary. PyInstaller,
Nuitka, WiX and per-user Inno Setup are present. NSIS was not located. This mission
does not use WSL, Fedora, Linux or Bash.

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r packaging/requirements-build.txt
./packaging/build.ps1
```

The build creates a pure Python wheel and PyInstaller onedir with CGC.exe (GUI) and
CGC-console.exe (CLI). Both share relative _internal resources. Schemas, plugin, SDK,
docs and licenses are copied before Inno compilation. Select an existing compiler
with -InnoCompiler. Dependencies stay in .venv. No plugin/service/security change.

Tiers: A product unit/API; B Windows child integration/Node parity; C frozen resources
and GUI; D fresh wheel venv/owned installer directory; E archive/hash/release smoke.
Separate pristine-VM acceptance remains debt: reduced PATH is not a clean machine.

References: [Qt packaging](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html),
[Inno Setup](https://jrsoftware.org/isdl.php).
