# Build with: .venv/Scripts/python.exe -m PyInstaller packaging/CGC.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files
root = Path(SPECPATH).parent
a = Analysis([str(root/'packaging/desktop_entry.py')], pathex=[str(root/'src')],
             binaries=[], datas=collect_data_files('cgcchild'), hiddenimports=[],
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=['tkinter'],
             noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CGC', console=False,
          debug=False, strip=False, upx=False,
          version=str(root/'packaging/version-info.txt'))
cli = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CGC-console', console=True,
          debug=False, strip=False, upx=False,
          version=str(root/'packaging/version-info.txt'))
coll = COLLECT(gui, cli, a.binaries, a.datas, strip=False, upx=False, name='CGC')
