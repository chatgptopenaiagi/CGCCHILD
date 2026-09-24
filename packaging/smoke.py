"""Native Windows wheel, relocated live product and owned installer acceptance.

Run only after packaging/build.ps1 completes. All projects, installer targets and
retained evidence belong to build/qa; reduced PATH affects subprocesses only.
"""
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import time
import uuid
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
QA = ROOT / "build" / "qa"


def product_version():
    tree = ast.parse((ROOT / "src/cgcchild/__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and all(part.isdigit() for part in value.split(".")) and len(value.split(".")) == 3:
                return value
    raise RuntimeError("PRODUCT_VERSION_UNAVAILABLE")


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def owned(path):
    target = Path(path).resolve()
    require(target.is_relative_to(QA.resolve()) and target != QA.resolve(), "QA_PATH_OUTSIDE_OWNED_ROOT")
    return target


def run(args, cwd, env=None, timeout=90):
    try:
        result = subprocess.run([str(arg) for arg in args], cwd=cwd, env=env,
                                stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"SMOKE_TIMEOUT:{Path(str(args[0])).name}") from None
    if result.returncode:
        # Do not place native output or ambient authentication diagnostics in reports.
        raise RuntimeError(f"SMOKE_FAILED:{Path(str(args[0])).name}:{result.returncode}")
    return result.stdout


def json_run(command, args, cwd, env):
    return json.loads(run([*command, *args], cwd, env))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def git_fixture(project, env):
    project = owned(project)
    project.mkdir()
    git = shutil.which("git", path=env.get("PATH"))
    require(git is not None, "QA_GIT_FIXTURE_EXECUTABLE_REQUIRED")
    git_env = {key: value for key, value in env.items() if not key.upper().startswith("GIT_")}
    git_env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_GLOBAL=os.devnull)
    run([git, "init", "-b", "main", project], project.parent, git_env)
    (project / "README.txt").write_text("Owned CGC Windows release fixture.\n", encoding="utf-8")
    (project / "test_fixture.py").write_text(
        "import unittest\nclass Case(unittest.TestCase):\n def test_fixture(self): self.assertTrue(True)\n", encoding="utf-8")
    run([git, "-C", project, "add", "README.txt", "test_fixture.py"], project, git_env)
    run([git, "-C", project, "-c", "user.name=CGC release fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "core.hooksPath=NUL", "commit", "-m", "Owned release fixture"], project, git_env)
    return project


def live_workflow(command, folder, evidence, env, *, fixture_env, test_python=None, git_unavailable=False):
    project = git_fixture(folder / "project", fixture_env)
    evidence = owned(evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    selected_env = dict(env, LOCALAPPDATA=str(evidence / "localappdata"))
    # Exercise the default external Windows session store, isolated to owned QA data.
    start = json_run(command, ["live", "start", "--project", project], folder, selected_env)
    session = Path(start["storage_location"])
    expected_store = evidence / "localappdata/CGCCHILD/sessions"
    require(session.parent == expected_store and not session.is_relative_to(project), "LIVE_STORE_SCOPE_FAILED")
    require(start["state"] == "RUNNING" and start["mutation_authorized"] is False, "LIVE_START_FAILED")
    if git_unavailable:
        require(start["git"]["status"] == "UNKNOWN", "MISSING_GIT_MUST_DEGRADE_UNKNOWN")
    else:
        require(start["git"]["head_object_verified"] is True, "REAL_GIT_FIXTURE_NOT_OBSERVED")
    (project / "work.txt").write_text("Observed release fixture change.\n", encoding="utf-8")
    reported = json_run(command, ["live", "report", "--session", session, "--event-type", "FILE_EDIT_REPORTED",
                                 "--payload", json.dumps({"path": "work.txt"})], folder, selected_env)
    require(reported["evidence_grade"] == "REPORTED", "AGENT_REPORT_PROMOTION")
    observed = json_run(command, ["live", "observe", "--session", session], folder, selected_env)
    require(any(change.get("path") == "work.txt" and change.get("change") == "CREATED"
                for change in observed["changes"]), "LIVE_FILE_CHANGE_NOT_OBSERVED")
    if test_python is not None:
        attempt = json_run(command, ["live", "test", "--session", session, "--framework", "unittest", "--",
                                    test_python, "-I", "-m", "unittest", "discover", "-v"], folder, selected_env)
        require(attempt["verification_state"] == "VERIFIED_PASS" and attempt["parsed_passed"] == 1,
                "INSTALLED_LIVE_TEST_OBSERVER_FAILED")
    next_action = json_run(command, ["live", "report", "--session", session, "--event-type", "NEXT_ACTION_DECLARED",
                                   "--payload", json.dumps({"text": "Review the retained release fixture evidence."})], folder, selected_env)
    require(next_action["payload"]["status"] == "UNEXECUTED_FUTURE_ACTION", "NEXT_ACTION_AUTHORITY_CHANGED")
    checkpoint = json_run(command, ["live", "checkpoint", "--session", session], folder, selected_env)
    require(checkpoint["checkpoint_count"] == 1 and checkpoint["state"] == "RUNNING", "LIVE_CHECKPOINT_FAILED")
    json_run(command, ["live", "interrupt", "--session", session, "--reason", "QA_RESTART_SIMULATION"], folder, selected_env)
    recovery = json_run(command, ["live", "recover", "--session", session], folder, selected_env)
    require(recovery["mutation_authorized"] is False, "RECOVERY_AUTHORITY_CHANGED")
    resumed = json_run(command, ["live", "resume", "--session", session], folder, selected_env)
    require(resumed["state"] == "RUNNING" and resumed["generation"] == 2, "LIVE_RESUME_FAILED")
    preserved = json_run(command, ["live", "preserve", "--session", session], folder, selected_env)
    capsule = Path(preserved["capsule"])
    require(capsule.is_file() and capsule.is_relative_to(session), "LIVE_CAPSULE_MISSING")
    # Deliberately reopen in a fresh executable invocation.
    reopened = json_run(command, ["live", "open", "--input", capsule], folder, selected_env)
    require(reopened["authority"] == "HISTORICAL_ONLY" and reopened["current_authority"] == "UNKNOWN"
            and reopened["mutation_authorized"] is False, "CAPSULE_IMPORTED_AUTHORITY")
    require(reopened["session"]["generation"] == 2 and reopened["session"]["files_changed"] >= 1,
            "CAPSULE_HISTORY_INCOMPLETE")
    final = json_run(command, ["live", "status", "--session", session], folder, selected_env)
    require(final["state"] == "PRESERVED" and final["preservation_complete"] is True, "LIVE_PRESERVATION_INCOMPLETE")
    listing = json_run(command, ["live", "list", "--store", expected_store], folder, selected_env)
    require(any(item.get("session_id") == start["session_id"] for item in listing["sessions"]), "LIVE_DISCOVERY_FAILED")
    return dict(state="PASSED", session=str(session), capsule=str(capsule), capsule_sha256=digest(capsule),
                event_count=final["event_count"], generation=final["generation"],
                git_state=final["git"]["status"], authority="HISTORICAL_ONLY")


def previous_portable():
    for directory in (DIST / "previous-0.3.0", DIST / "old-releases", DIST):
        candidate = directory / "CGCCHILD-Windows-Portable-0.3.0.zip"
        if candidate.is_file():
            return candidate
    return None


def registration(app_id):
    import winreg
    uuid.UUID(app_id.strip("{}"))
    key = "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\" + app_id + "_is1"
    result = {}
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ | view) as registry:
                result[str(view)] = {name: winreg.QueryValueEx(registry, name)[0]
                                     for name in ("InstallLocation", "DisplayVersion", "DisplayName")}
        except FileNotFoundError:
            continue
    return result


def shipping_registration():
    return registration("{48A3FA0A-F8D0-436A-91A2-19C1FD5F3382}")


def qa_installers(folder, version, run_id, env):
    """Compile the shipping script with a separate, shared QA registration ID.

    Inno AppId owns its uninstall registration: an alternate /DIR alone would
    overwrite a real owner's existing registration. These compile-time overrides
    exercise installer behavior without making that modification.
    """
    compiler = Path(os.environ["LOCALAPPDATA"]) / "Programs/Inno Setup 6/ISCC.exe"
    require(compiler.is_file(), "QA_INNO_COMPILER_REQUIRED")
    output = owned(folder / "qa-installers")
    output.mkdir()
    app_id = "{{" + str(uuid.uuid5(uuid.NAMESPACE_URL, "CGCCHILD-QA:" + run_id)).upper() + "}"
    baseline_archive = previous_portable()
    baseline_source = None
    if baseline_archive is not None:
        payload = owned(folder / "previous-payload")
        payload.mkdir()
        with zipfile.ZipFile(baseline_archive) as archive:
            members = archive.infolist()
            require(len(members) < 20000 and sum(member.file_size for member in members) < 1024 * 1024 * 1024,
                    "BASELINE_PORTABLE_BOUNDS")
            require(len({member.filename for member in members}) == len(members), "BASELINE_PORTABLE_DUPLICATES")
            for member in members:
                name = PurePosixPath(member.filename)
                require(not name.is_absolute() and ".." not in name.parts and ":" not in member.filename
                        and "\\" not in member.filename and name.parts[0] == "CGC"
                        and (member.external_attr >> 16) & 0o170000 != 0o120000, "BASELINE_PORTABLE_PATH")
                target = owned(payload / Path(*name.parts))
                require(target.is_relative_to(payload), "BASELINE_PORTABLE_ESCAPE")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, target.open("xb") as destination:
                        shutil.copyfileobj(source, destination, 1024 * 1024)
        baseline_source = payload / "CGC"

    def compile_variant(source, selected_version):
        basename = "CGCCHILD-QA-Setup-" + selected_version
        defines = {"AppId": app_id, "SourceDir": str(source), "OutputDir": str(output),
                   "OutputBaseFilename": basename, "AppVersion": selected_version,
                   "VersionInfoVersion": selected_version + ".0"}
        args = [compiler, *[f"/D{name}={value}" for name, value in defines.items()], ROOT / "packaging/installer.iss"]
        log = run(args, folder, env, 240)
        (output / (basename + ".log")).write_bytes(log)
        executable = output / (basename + ".exe")
        require(executable.is_file(), "QA_INSTALLER_NOT_BUILT")
        return executable

    baseline = compile_variant(baseline_source, "0.3.0") if baseline_source is not None else None
    current = compile_variant(DIST / "CGC", version)
    return baseline, current, app_id


@contextmanager
def installer_fixture(env):
    with tempfile.TemporaryDirectory(prefix="installer-", dir=QA) as temp:
        folder = owned(temp)
        state = {"uninstalled": False}
        try:
            yield folder, state
        finally:
            uninstaller = owned(folder / "installed/unins000.exe")
            if not state["uninstalled"] and uninstaller.is_file():
                # A failed assertion must not replace uninstall with file deletion.
                run([uninstaller, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], folder, env, 180)


def main():
    require(os.name == "nt", "WINDOWS_NATIVE_REQUIRED")
    version = product_version()
    wheel = DIST / f"cgcchild-{version}-py3-none-any.whl"
    installer = DIST / f"CGCCHILD-Setup-{version}.exe"
    require(wheel.is_file() and installer.is_file() and (DIST / "CGC/CGC.exe").is_file(), "BUILD_ARTIFACTS_REQUIRED")
    QA.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    retained = owned(QA / "retained" / run_id)
    retained.mkdir(parents=True)
    results = dict(state="RUNNING", version=version, run_id=run_id, started_at=datetime.now(timezone.utc).isoformat(),
                   retained_evidence=str(retained), clean_vm="NOT_EXECUTED", security_acceptance="UNCHANGED",
                   input_sha256={str(path.relative_to(ROOT)): digest(path) for path in
                                 (wheel, installer, DIST / "CGC/CGC.exe", DIST / "CGC/CGC-console.exe",
                                  ROOT / "packaging/installer.iss")})

    def record():
        raw = json.dumps(results, indent=2) + "\n"
        (QA / "results.json").write_text(raw, encoding="utf-8")
        (retained / "results.json").write_text(raw, encoding="utf-8")

    record()
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "CGC_SESSION_DIR", "CGC_SESSION_ID", "CGC_EVENT_ENDPOINT", "CGC_SMOKE_LIVE_CAPSULE"):
        env.pop(key, None)
    env["PYTHONNOUSERSITE"] = "1"
    reduced = dict(env, PATH=str(Path(os.environ["SystemRoot"]) / "System32"))
    require(shutil.which("python", path=reduced["PATH"]) is None and shutil.which("git", path=reduced["PATH"]) is None,
            "REDUCED_PATH_HAS_PYTHON_OR_GIT")
    try:
        with tempfile.TemporaryDirectory(prefix="wheel-", dir=QA) as temp:
            folder = owned(temp)
            venv.EnvBuilder(with_pip=True).create(folder / "venv")
            py = folder / "venv/Scripts/python.exe"
            command = [py, "-I", "-m", "cgcchild"]
            run([py, "-m", "pip", "install", "--no-index", "--no-deps", wheel], folder, env)
            run([py, "-I", "-c", "import cgcchild; from cgcchild import sdk; assert sdk.negotiate(sdk.API_VERSION)['mutation_authorized'] is False"], folder, env)
            require(run([*command, "--version"], folder, env).decode().strip() == version, "WHEEL_VERSION_MISMATCH")
            require(json_run(command, ["self-test"], folder, env)["state"] == "PASSED", "WHEEL_SELF_TEST_FAILED")
            run([*command, "example", "--output", folder / "sample.json"], folder, env)
            require(json_run(command, ["inspect", "--input", folder / "sample.json"], folder, env)["snapshot_loaded"], "WHEEL_HISTORICAL_READ_FAILED")
            results["fresh_wheel_live"] = live_workflow(command, folder, retained / "wheel", env, fixture_env=env, test_python=py)
            run([py, "-m", "pip", "uninstall", "-y", "cgcchild"], folder, env)
            run([py, "-I", "-c", "import importlib.util; assert importlib.util.find_spec('cgcchild') is None"], folder, env)
            require(Path(results["fresh_wheel_live"]["capsule"]).is_file(), "WHEEL_UNINSTALL_REMOVED_EVIDENCE")
            results["fresh_wheel"] = "INSTALL_IMPORT_HISTORICAL_LIVE_RECOVER_PRESERVE_REOPEN_UNINSTALL_PASSED"
            record()

        with tempfile.TemporaryDirectory(prefix="portable-", dir=QA) as temp:
            folder = owned(temp)
            shutil.copytree(DIST / "CGC", folder / "app")
            command = [folder / "app/CGC-console.exe"]
            require(run([*command, "--version"], folder, reduced).decode().strip() == version, "FROZEN_VERSION_MISMATCH")
            require(json_run(command, ["self-test"], folder, reduced)["state"] == "PASSED", "FROZEN_SELF_TEST_FAILED")
            run([*command, "capsule-export", "--input", folder / "app/example.json", "--output", folder / "test.cgcpack"], folder, reduced)
            run([*command, "report", "--input", folder / "test.cgcpack", "--output", folder / "test.html"], folder, reduced)
            run([*command, "capsule-import", "--input", folder / "test.cgcpack", "--output", folder / "roundtrip.json"], folder, reduced)
            require((folder / "roundtrip.json").read_bytes() == (folder / "app/example.json").read_bytes(), "FROZEN_HISTORICAL_ROUNDTRIP_FAILED")
            for name in ("plugin/.codex-plugin/plugin.json", "schemas/state-0.1.schema.json", "sdk/javascript/index.mjs", "LICENSE"):
                require((folder / "app" / name).is_file(), "FROZEN_RESOURCE_MISSING")
            results["relocated_live"] = live_workflow(command, folder, retained / "portable", reduced, fixture_env=env, git_unavailable=True)
            screenshot = folder / "frozen-gui.png"
            gui_env = dict(reduced, CGC_SMOKE_LIVE_CAPSULE=results["relocated_live"]["capsule"],
                           LOCALAPPDATA=str(retained / "portable/localappdata"))
            run([folder / "app/CGC.exe", "gui", "--smoke-output", screenshot], folder, gui_env)
            require(screenshot.stat().st_size > 1000, "FROZEN_GUI_RENDER_FAILED")
            shutil.copy2(screenshot, owned(QA / "frozen-gui.png"))
            shutil.copy2(screenshot, retained / "frozen-gui.png")
            results["relocated_frozen"] = "NO_PYTHON_OR_GIT_ON_PATH_HISTORICAL_LIVE_RECOVER_CAPSULE_GUI_PASSED"
            results["screenshot"] = str(retained / "frozen-gui.png")
            record()

        existing_registration = shipping_registration()
        with installer_fixture(reduced) as (folder, install_state):
            target = owned(folder / "installed")
            switches = ["/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS", f"/DIR={target}"]
            evidence = owned(retained / "installer")
            evidence.mkdir()
            outside = evidence / "retained-export.json"
            baseline, qa_installer, qa_app_id = qa_installers(folder, version, run_id, env)
            results["installer_profile"] = "REGISTRATION_ISOLATED_SAME_SCRIPT_AND_PRODUCT_PAYLOAD"
            results["qa_installer_app_id"] = qa_app_id
            results["shipping_installer_lifecycle"] = "NOT_EXECUTED_EXISTING_OWNER_INSTALLATION" if existing_registration else "NOT_EXECUTED_QA_REGISTRATION_PROFILE"
            results["shipping_installer_sha256"] = digest(installer)
            if baseline:
                run([baseline, *switches], folder, reduced, 180)
                require(run([target / "CGC-console.exe", "--version"], folder, reduced).decode().strip() == "0.3.0", "BASELINE_INSTALL_VERSION_MISMATCH")
                run([target / "CGC-console.exe", "example", "--output", outside], folder, reduced)
                results["installer_previous_version"] = "0.3.0_INSTALLED"
            else:
                results["installer_previous_version"] = "NOT_EXECUTED_BASELINE_INSTALLER_UNAVAILABLE"
            run([qa_installer, *switches], folder, reduced, 180)
            command = [target / "CGC-console.exe"]
            require(run([*command, "--version"], folder, reduced).decode().strip() == version, "UPGRADED_INSTALL_VERSION_MISMATCH")
            require(json_run(command, ["self-test"], folder, reduced)["state"] == "PASSED", "INSTALLER_SELF_TEST_FAILED")
            if not outside.exists():
                run([*command, "example", "--output", outside], folder, reduced)
            export_hash = digest(outside)
            results["installer_live"] = live_workflow(command, folder, evidence, reduced, fixture_env=env, git_unavailable=True)
            session = Path(results["installer_live"]["session"])
            capsule = Path(results["installer_live"]["capsule"])
            journal = sorted(session.glob("events-*.jsonl"))
            retained_hashes = {str(path): digest(path) for path in [outside, capsule, session / "manifest.json", *journal]}
            # Reinstall the same version after evidence exists, then verify it again.
            run([qa_installer, *switches], folder, reduced, 180)
            require(json_run(command, ["status"], folder, reduced)["mode"] == "READ_ONLY_SAFE", "INSTALLER_SAFE_DEFAULT_FAILED")
            require(json_run(command, ["live", "open", "--input", capsule], folder, reduced)["authority"] == "HISTORICAL_ONLY", "UPGRADE_LIVE_REOPEN_FAILED")
            run([target / "unins000.exe", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], folder, reduced, 180)
            install_state["uninstalled"] = True
            for _ in range(100):
                if not (target / "CGC.exe").exists() and not (target / "CGC-console.exe").exists():
                    break
                time.sleep(.1)
            require(not (target / "CGC.exe").exists() and not (target / "CGC-console.exe").exists(), "INSTALLER_UNINSTALL_INCOMPLETE")
            require(digest(outside) == export_hash and all(Path(path).is_file() and digest(path) == expected for path, expected in retained_hashes.items()),
                    "INSTALLER_REMOVED_OR_CHANGED_RETAINED_EVIDENCE")
            results["installer"] = "PER_USER_INSTALL_UPGRADE_REINSTALL_UNINSTALL_HISTORICAL_AND_LIVE_RETENTION_PASSED"
            results["retained_after_uninstall"] = retained_hashes
            require(shipping_registration() == existing_registration, "OWNER_INSTALLATION_REGISTRATION_CHANGED")
            require(not registration(qa_app_id[1:]), "QA_INSTALLATION_REGISTRATION_NOT_REMOVED")
            results["owner_installation_registration"] = "UNCHANGED"
            results["qa_installation_registration"] = "REMOVED_BY_UNINSTALLER"
            record()
        results["state"] = "PASSED"
        results["finished_at"] = datetime.now(timezone.utc).isoformat()
        record()
        print(json.dumps(results, indent=2))
    except BaseException as error:
        results["state"] = "FAILED"
        results["failure_class"] = type(error).__name__
        results["failure_code"] = str(error) if type(error) is RuntimeError else "SMOKE_EXCEPTION"
        record()
        raise


if __name__ == "__main__":
    main()
