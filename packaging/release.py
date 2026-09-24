"""Create source/plugin/portable archives and a hash-bound release inventory at HEAD."""
import datetime
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from cgcchild import __version__
from cgcchild.execution import Mode

root = Path(__file__).resolve().parents[1]
dist = root/'dist'
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip():
    raise SystemExit('Commit reviewed source before generating a release')

def archive(output, paths, base):
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(paths):
            z.write(path,path.relative_to(base).as_posix())

tracked = subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
archive(dist/f'CGCCHILD-{__version__}-source.zip',[root/p for p in tracked if p],root)
archive(dist/f'CGCCHILD-Windows-Portable-{__version__}.zip',[p for p in (dist/'CGC').rglob('*') if p.is_file()],dist)
plugin = root/'plugins/cgcchild-readonly'
archive(dist/f'cgcchild-readonly-{__version__}.zip',[p for p in plugin.rglob('*') if p.is_file()],plugin.parent)
(dist/'RELEASE_NOTES.md').write_bytes((root/'docs/RELEASE_NOTES.md').read_bytes())
artifacts=[]
for p in sorted(dist.iterdir()):
    if p.is_file() and p.name not in ('SHA256SUMS.txt','release-manifest.json'):
        with p.open('rb') as stream:
            digest = hashlib.file_digest(stream,'sha256').hexdigest()
        artifacts.append(dict(artifact_name=p.name,artifact_type=p.suffix.lstrip('.'),size=p.stat().st_size,
                              sha256=digest))
exe=dist/'CGC/CGC.exe'
artifacts.append(dict(artifact_name='CGC/CGC.exe',artifact_type='exe-directory-entry',size=exe.stat().st_size,
                      sha256=hashlib.sha256(exe.read_bytes()).hexdigest()))
for p in dist.glob('*.zip'):
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None:
            raise SystemExit('Archive CRC validation failed')
        if any(name.startswith('/') or '..' in Path(name).parts for name in z.namelist()):
            raise SystemExit('Invalid archive member')
with zipfile.ZipFile(dist/f'cgcchild-{__version__}-py3-none-any.whl') as z:
    if z.testzip() is not None or 'cgcchild/resources/example.json' not in z.namelist():
        raise SystemExit('Wheel resource validation failed')
tests=json.loads((root/'docs/WINDOWS_TEST_RESULTS.json').read_text())
tests['tier_e_release_smoke']='ARCHIVE_CRC_PATHS_WHEEL_RESOURCES_AND_ARTIFACT_HASHES_PASSED'
manifest=dict(project='CGCCHILD',version=__version__,commit=head,
    build_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),windows_version=platform.platform(),
    python_version=platform.python_version(),artifacts=artifacts,
    tests=tests,
    known_blockers=['Clean Windows VM acceptance deferred','Unsigned binaries','Plugin host acceptance deferred',
                    'RO-1..RO-5 and R6 not executed','Filesystem closure and real P3 UNKNOWN'],
    security_acceptance_state='EXPERIMENTAL; PRODUCTION_MUTATION_DISABLED',supported_modes=[m.value for m in Mode])
mp=dist/'release-manifest.json'
mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
lines=[a['sha256']+'  '+a['artifact_name'] for a in artifacts]
lines.append(hashlib.sha256(mp.read_bytes()).hexdigest()+'  release-manifest.json')
(dist/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='ascii')
for line in lines:
    digest,name=line.split('  ',1)
    with (dist/name).open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
            raise SystemExit('Final checksum validation failed')
print(json.dumps({'commit':head,'artifacts':len(artifacts)}))
