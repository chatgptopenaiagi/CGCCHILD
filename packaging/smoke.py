"""Native Windows fresh-wheel, relocated bundle and owned installer smoke tests."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import venv

root = Path(__file__).resolve().parents[1]
dist = root/'dist'
qa = root/'build/qa'
qa.mkdir(parents=True, exist_ok=True)
results = {}

def run(args, cwd, env=None, timeout=90):
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'SMOKE_FAILED: {Path(str(args[0])).name}: {result.returncode}: {result.stderr[-1000:]!r}')
    return result.stdout

# Isolate imports and runtime PATH. No host-wide configuration change.
env = dict(os.environ)
env.pop('PYTHONPATH', None)
env.pop('PYTHONHOME', None)
env['PYTHONNOUSERSITE'] = '1'
with tempfile.TemporaryDirectory(prefix='wheel-', dir=qa) as temp:
    folder = Path(temp)
    venv.EnvBuilder(with_pip=True).create(folder/'venv')
    py = folder/'venv/Scripts/python.exe'
    wheel = dist/'cgcchild-0.3.0-py3-none-any.whl'
    run([py,'-m','pip','install','--no-index','--no-deps',wheel], folder, env)
    run([py,'-I','-c','import cgcchild; from cgcchild import sdk; assert sdk.negotiate(sdk.API_VERSION)["mutation_authorized"] is False'], folder, env)
    result = json.loads(run([py,'-I','-m','cgcchild','self-test'], folder, env))
    assert result['state'] == 'PASSED'
    run([py,'-I','-m','cgcchild','example','--output',folder/'sample.json'],folder,env)
    assert json.loads(run([py,'-I','-m','cgcchild','inspect','--input',folder/'sample.json'],folder,env))['snapshot_loaded']
    run([py,'-m','pip','uninstall','-y','cgcchild'],folder,env)
    run([py,'-I','-c','import importlib.util; assert importlib.util.find_spec("cgcchild") is None'],folder,env)
    results['fresh_wheel'] = 'INSTALL_IMPORT_CLI_READ_UNINSTALL_PASSED'

env['PATH'] = str(Path(os.environ['SystemRoot'])/'System32')
with tempfile.TemporaryDirectory(prefix='portable-', dir=qa) as temp:
    folder=Path(temp)
    shutil.copytree(dist/'CGC',folder/'app')
    exe=folder/'app/CGC-console.exe'
    assert json.loads(run([exe,'self-test'],folder,env))['state'] == 'PASSED'
    run([exe,'capsule-export','--input',folder/'app/example.json','--output',folder/'test.cgcpack'],folder,env)
    run([exe,'report','--input',folder/'test.cgcpack','--output',folder/'test.html'],folder,env)
    run([exe,'capsule-import','--input',folder/'test.cgcpack','--output',folder/'roundtrip.json'],folder,env)
    assert (folder/'roundtrip.json').read_bytes() == (folder/'app/example.json').read_bytes()
    for name in ('plugin/.codex-plugin/plugin.json','schemas/state-0.1.schema.json','sdk/javascript/index.mjs','LICENSE'):
        assert (folder/'app'/name).is_file()
    run([folder/'app/CGC.exe','gui','--smoke-output',qa/'frozen-gui.png'],folder,env)
    assert (qa/'frozen-gui.png').stat().st_size > 1000
    results['relocated_frozen'] = 'REDUCED_PATH_CLI_CAPSULE_REPORT_RESOURCES_GUI_PASSED'

# Inno operates only on this explicitly owned test directory. No elevation requested.
with tempfile.TemporaryDirectory(prefix='installer-', dir=qa) as temp:
    folder=Path(temp)
    target=folder/'installed'
    command=[dist/'CGCCHILD-Setup-0.3.0.exe','/CURRENTUSER','/VERYSILENT',
             '/SUPPRESSMSGBOXES','/NORESTART','/NOICONS',f'/DIR={target}']
    run(command,folder,env,180)
    assert json.loads(run([target/'CGC-console.exe','self-test'],folder,env))['state'] == 'PASSED'
    outside=folder/'retained-export.json'
    run([target/'CGC-console.exe','example','--output',outside],folder,env)
    run(command,folder,env,180)
    assert json.loads(run([target/'CGC-console.exe','status'],folder,env))['mode'] == 'READ_ONLY_SAFE'
    run([target/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],folder,env,180)
    for _ in range(100):
        if not (target/'CGC.exe').exists(): break
        time.sleep(.1)
    assert not (target/'CGC.exe').exists()
    assert outside.exists()
    results['installer'] = 'PER_USER_INSTALL_UPGRADE_START_UNINSTALL_EXPORT_RETENTION_PASSED'

(qa/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
