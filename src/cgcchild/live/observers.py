"""Explicit, bounded Windows project observations; no repository preservation.

Polling records sampled metadata, not every intermediate edit. These observations
neither establish filesystem exclusivity nor authenticate a test framework's output.
Test execution is an explicit caller action and is never dispatched from events.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import ctypes
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import threading
import time
import uuid
from urllib.parse import urlsplit

from .redaction import redact, redact_text


MAX_ENTRIES = 10000
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_PARSE_BYTES = 64 * 1024
_REPARSE = 0x400
_IGNORED_DIRS = {".git", ".codex", ".ssh", ".aws", ".azure", ".venv", "venv",
                 "node_modules", "__pycache__", ".pytest_cache"}
_SENSITIVE_NAMES = {"auth.json", "credentials.json", "credentials", "id_rsa", "id_ed25519",
                    "id_ecdsa", "id_dsa", ".env", ".npmrc", ".pypirc", ".netrc"}
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _reparse(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & _REPARSE)


def _project(project):
    path = Path(os.path.abspath(os.fspath(project)))
    if any(part.lower() in {".codex", ".ssh", ".aws", ".azure"} for part in path.parts):
        raise ValueError("SENSITIVE_PROJECT_ROOT_REFUSED")
    # Resolve no links. Reject a selected reparse root and reparse ancestors.
    for part in (path, *path.parents):
        if _reparse(part.lstat()):
            raise ValueError("PROJECT_REPARSE_REFUSED")
    if not path.is_dir():
        raise ValueError("PROJECT_DIRECTORY_REQUIRED")
    return path


def _sensitive(path):
    # Metadata names can themselves contain credentials. Exclude rather than
    # retaining raw names in a baseline or collapsing distinct names by redaction.
    return redact_text(path) != path or any(part.lower() in _IGNORED_DIRS or part.lower() in _SENSITIVE_NAMES or
               part.lower().startswith(".env.") or part.lower().endswith((".pem", ".key", ".pfx", ".p12"))
               for part in Path(path).parts)


class FileObserver:
    """Metadata-only polling under one explicit root. No source content is read."""

    def __init__(self, project, max_entries=MAX_ENTRIES, baseline=None):
        if type(max_entries) is not int or not 1 <= max_entries <= MAX_ENTRIES:
            raise ValueError("INVALID_OBSERVER_LIMIT")
        self.project = _project(project)
        self.max_entries = max_entries
        self._previous = None
        self.last_snapshot = None
        if baseline is not None:
            if (type(baseline) is not dict or type(baseline.get("files")) is not dict or
                    len(baseline["files"]) > max_entries or baseline.get("coverage") not in ("SAMPLED", "PARTIAL")):
                raise ValueError("INVALID_FILESYSTEM_BASELINE")
            for path, value in baseline["files"].items():
                if (type(path) is not str or len(path) > 32768 or Path(path).is_absolute() or
                        ".." in Path(path).parts or _sensitive(path) or type(value) is not dict or
                        set(value) != {"size", "mtime_ns", "file_id"} or
                        type(value["size"]) is not int or value["size"] < 0 or
                        type(value["mtime_ns"]) is not int or type(value["file_id"]) is not str or
                        not re.fullmatch(r"\d+:\d+", value["file_id"])):
                    raise ValueError("INVALID_FILESYSTEM_BASELINE")
            self._previous = dict(baseline, files={key: dict(value) for key, value in baseline["files"].items()})

    def snapshot(self):
        _project(self.project)
        files, stack = {}, [(self.project, 0)]
        excluded, reparse_count, sensitive_count, errors, visited = 0, 0, 0, [], 0
        bounded = False
        while stack and not bounded:
            directory, depth = stack.pop()
            if depth > 64:
                errors.append("DEPTH_LIMIT")
                continue
            try:
                if _reparse(directory.lstat()):
                    excluded += 1
                    reparse_count += 1
                    continue
                with os.scandir(directory) as entries:
                    for entry in entries:
                        visited += 1
                        if visited > self.max_entries:
                            errors.append("ENTRY_LIMIT")
                            bounded = True
                            break
                        rel = Path(entry.path).relative_to(self.project).as_posix()
                        if _sensitive(rel):
                            excluded += 1
                            sensitive_count += 1
                            continue
                        try:
                            # Windows DirEntry.stat caches find-data with st_ino=0;
                            # lstat opens metadata to obtain an actual file identity.
                            info = os.stat(entry.path, follow_symlinks=False)
                            if _reparse(info):
                                excluded += 1
                                reparse_count += 1
                            elif stat.S_ISDIR(info.st_mode):
                                stack.append((Path(entry.path), depth + 1))
                            elif stat.S_ISREG(info.st_mode):
                                files[rel] = dict(size=info.st_size, mtime_ns=info.st_mtime_ns,
                                                 file_id=f"{info.st_dev}:{info.st_ino}")
                        except OSError:
                            errors.append("ENTRY_UNAVAILABLE")
            except OSError:
                errors.append("DIRECTORY_UNAVAILABLE")
        result = dict(files=files, observed_at=_now(), coverage="PARTIAL" if errors else "SAMPLED",
                      limitations=sorted(set(errors)), excluded_count=excluded,
                      excluded_reparse_count=reparse_count, excluded_sensitive_count=sensitive_count,
                      production_filesystem_closure="UNKNOWN", transient_changes="MAY_BE_MISSED")
        self.last_snapshot = result
        return result

    def poll(self):
        current = self.snapshot()
        previous = self._previous
        self._previous = current
        if previous is None:
            return [dict(change="BASELINE_ESTABLISHED", path=None,
                         observed_at=current["observed_at"], coverage=current["coverage"],
                         limitations=current["limitations"])]
        old, new = previous["files"], current["files"]
        events = []
        if current["coverage"] == "PARTIAL" or previous["coverage"] == "PARTIAL":
            # Missing entries in incomplete samples cannot establish removals.
            events.append(dict(change="OBSERVATION_INCOMPLETE", path=None,
                               observed_at=current["observed_at"], coverage="PARTIAL",
                               limitations=current["limitations"]))
            common = old.keys() & new.keys()
            for path in sorted(common):
                if old[path] != new[path]:
                    events.append(dict(path=path, change="MODIFIED", observed_at=current["observed_at"],
                                       **new[path]))
            return events
        removed, created = set(old) - set(new), set(new) - set(old)
        # Only unambiguous identities establish a sampled rename; hard links do not.
        old_ids, new_ids = {}, {}
        for path, value in old.items():
            old_ids.setdefault(value["file_id"], []).append(path)
        for path, value in new.items():
            new_ids.setdefault(value["file_id"], []).append(path)
        for path in sorted(tuple(created)):
            identity = new[path]["file_id"]
            origins = old_ids.get(identity, [])
            if not identity.endswith(":0") and len(origins) == 1 and len(new_ids[identity]) == 1 and origins[0] in removed:
                prior = origins[0]
                removed.remove(prior)
                created.remove(path)
                events.append(dict(path=path, previous_path=prior, change="RENAMED",
                                   observed_at=current["observed_at"], basis="SAMPLED_FILE_ID_MATCH", **new[path]))
        for change, paths in (("REMOVED", removed), ("CREATED", created)):
            for path in sorted(paths):
                events.append(dict(path=path, change=change, observed_at=current["observed_at"],
                                   **(new if change == "CREATED" else old)[path]))
        for path in sorted(old.keys() & new.keys()):
            if old[path] != new[path]:
                events.append(dict(path=path, change="MODIFIED", observed_at=current["observed_at"],
                                   **new[path]))
        return events


class _Capture:
    def __init__(self, limit):
        self.count = 0
        self.digest = hashlib.sha256()
        self.tail = bytearray()
        self.limit = limit
        self.exceeded = threading.Event()
        self.stop = threading.Event()
        self.complete = False

    def consume(self, stream):
        try:
            while not self.stop.is_set():
                amount = 8192
                if os.name == "nt":
                    # Peek before reading so an inherited pipe held open by an
                    # uncontained descendant cannot leave a blocked reader.
                    import msvcrt
                    available = ctypes.c_ulong()
                    peek = ctypes.WinDLL("kernel32", use_last_error=True).PeekNamedPipe
                    peek.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
                                     ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong), ctypes.c_void_p)
                    peek.restype = ctypes.c_int
                    if not peek(msvcrt.get_osfhandle(stream.fileno()), None, 0, None,
                                ctypes.byref(available), None):
                        if ctypes.get_last_error() == 109:  # ERROR_BROKEN_PIPE
                            self.complete = True
                        break
                    if not available.value:
                        self.stop.wait(.01)
                        continue
                    amount = min(amount, available.value)
                block = os.read(stream.fileno(), amount)
                if not block:
                    self.complete = True
                    break
                self.count += len(block)
                self.digest.update(block)
                self.tail.extend(block)
                if len(self.tail) > MAX_PARSE_BYTES:
                    del self.tail[:-MAX_PARSE_BYTES]
                if self.count > self.limit:
                    self.exceeded.set()
                    break
        except (OSError, ValueError):
            pass
        finally:
            stream.close()


def _capture(command, project, timeout, env=None, output_limit=MAX_OUTPUT_BYTES):
    stdout, stderr = _Capture(output_limit), _Capture(output_limit)
    started, monotonic = _now(), time.monotonic()
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(command, cwd=project, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                               creationflags=flags)
    readers = [threading.Thread(target=capture.consume, args=(stream,), daemon=True)
               for capture, stream in ((stdout, process.stdout), (stderr, process.stderr))]
    for reader in readers:
        reader.start()
    stopped = None
    while process.poll() is None:
        if stdout.exceeded.is_set() or stderr.exceeded.is_set():
            stopped = "OUTPUT_LIMIT"
        elif time.monotonic() - monotonic >= timeout:
            stopped = "TIMEOUT"
        if stopped:
            process.kill()  # Only the owned direct process; no process scanning.
            break
        time.sleep(.01)
    process.wait(timeout=5)
    for reader in readers:
        reader.join(timeout=.5)
    complete = stdout.complete and stderr.complete
    # Descendants may retain a pipe. Daemon drains are bounded in retained bytes;
    # incomplete streams can never support complete digest/test-result claims.
    if not complete and stopped is None:
        stopped = "INCOMPLETE_STREAMS"
    if stdout.exceeded.is_set() or stderr.exceeded.is_set():
        stopped = stopped or "OUTPUT_LIMIT"
    stdout.stop.set()
    stderr.stop.set()
    for reader in readers:
        reader.join(timeout=.5)
    return dict(started_at=started, ended_at=_now(), duration_seconds=round(time.monotonic() - monotonic, 6),
                exit_code=process.returncode, stdout_bytes=stdout.count, stderr_bytes=stderr.count,
                stdout_sha256=stdout.digest.hexdigest() if complete else None,
                stderr_sha256=stderr.digest.hexdigest() if complete else None,
                streams_complete=complete, interruption=stopped,
                _stdout=bytes(stdout.tail), _stderr=bytes(stderr.tail))


def _git_environment():
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_GLOBAL=os.devnull,
               GIT_ALLOW_PROTOCOL="https:file", GCM_INTERACTIVE="Never")
    return env


def _observer_executable(name, project):
    """Resolve fixed tools from absolute PATH directories outside project/cwd.

    Windows executable search can otherwise implicitly prepend the working
    directory even with an explicit PATH. Do not use that search or PATHEXT;
    observers accept only named native .exe files and return an absolute path.
    This is bounded selection, not hostile same-user executable attestation.
    """
    if name not in ("git", "gh"):
        raise ValueError("OBSERVER_EXECUTABLE_REFUSED")
    search = os.environ.get("PATH", "")
    if len(search) > 65536:
        return None
    try:
        project = Path(project).resolve(strict=True)
        current = Path.cwd().resolve(strict=True)
    except OSError:
        return None
    for entry in search.split(os.pathsep)[:256]:
        # No expansion of empty, relative, drive-relative or environment entries.
        entry = entry.strip().strip('"')
        if not entry:
            continue
        directory = Path(entry)
        if not directory.is_absolute():
            continue
        try:
            directory = directory.resolve(strict=True)
            if directory == current or directory == project or directory.is_relative_to(project):
                continue
            candidate = (directory / (name + ".exe")).resolve(strict=True)
            if (candidate.parent == current or candidate == project or candidate.is_relative_to(project)
                    or candidate.suffix.lower() != ".exe" or not candidate.is_file()):
                continue
        except (OSError, ValueError):
            continue
        return str(candidate)
    return None


def _git(project, args, *, timeout=10):
    executable = _observer_executable("git", project)
    if executable is None:
        raise ValueError("GIT_UNAVAILABLE")
    command = [executable, "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
               "-c", "core.hooksPath=" + os.devnull, "-c", "credential.helper=", "-c", "core.askPass=",
               "-c", "http.extraHeader=", "-c", "submodule.recurse=false", "-C", str(project), *args]
    result = _capture(command, project, timeout, env=_git_environment(), output_limit=MAX_PARSE_BYTES)
    if result["interruption"]:
        raise ValueError("GIT_OBSERVATION_INCOMPLETE")
    return result["exit_code"], result["_stdout"].decode("utf-8", "replace")


def _safe_git_config(project):
    gitdir = project / ".git"
    if not gitdir.is_dir() or _reparse(gitdir.lstat()):
        raise ValueError("ORDINARY_GIT_DIRECTORY_REQUIRED")
    config = gitdir / "config"
    if not config.is_file() or _reparse(config.lstat()) or config.stat().st_size > MAX_PARSE_BYTES:
        raise ValueError("GIT_CONFIG_UNAVAILABLE")
    # --file avoids repository setup and --no-includes prevents discovery outside
    # the explicitly selected config. Values are neither listed nor retained.
    code, output = _git(project, ["config", "--file", str(config), "--no-includes", "--name-only", "--list"])
    if code:
        raise ValueError("GIT_CONFIG_UNAVAILABLE")
    keys = output.lower().splitlines()
    forbidden = ("include.", "includeif.", "filter.", "url.", "http.", "credential.")
    executable_keys = {"core.fsmonitor", "core.sshcommand", "core.gitproxy", "core.worktree",
                       "core.hookspath", "core.attributesfile", "core.excludesfile",
                       "extensions.worktreeconfig", "extensions.partialclone"}
    if any(key.startswith(forbidden) or key in executable_keys or
           (key.startswith("remote.") and key.endswith((".uploadpack", ".receivepack", ".proxy", ".vcs", ".promisor")))
           for key in keys):
        raise ValueError("GIT_CONFIGURATION_REFUSED")
    for name in ("commondir", "objects/info/alternates", "objects/info/http-alternates"):
        if (gitdir / name).exists():
            raise ValueError("GIT_EXTERNAL_OBJECTS_REFUSED")


def _oid(project, ref):
    code, output = _git(project, ["rev-parse", "--verify", ref])
    value = output.strip()
    return value if not code and _OID.fullmatch(value) else None


def _github_remote(project, destination):
    """Supported owner-authenticated CLI; CGC never accesses credential material."""
    parsed = urlsplit(destination)
    match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", parsed.path)
    executable = _observer_executable("gh", project)
    if parsed.hostname != "github.com" or parsed.port not in (None, 443) or not match or not executable:
        return None
    owner, repository = match.groups()
    if owner in (".", "..") or repository in (".", ".."):
        return None
    env = dict(os.environ, GH_PROMPT_DISABLED="1")
    command = [executable, "api", "--hostname", "github.com",
               f"repos/{owner}/{repository}/git/ref/heads/main", "--jq", ".object.sha"]
    result = _capture(command, project, 15, env=env, output_limit=MAX_PARSE_BYTES)
    value = result["_stdout"].decode("ascii", "replace").strip()
    return value if result["exit_code"] == 0 and not result["interruption"] and _OID.fullmatch(value) else None


def git_snapshot(project, verify_remote=False):
    """Read local state and optionally independently compare origin's main ref.

    Includes, command-valued config, SSH/custom transports, credentials in URLs,
    partial clones and alternate object stores are refused, not worked around.
    HTTPS uses anonymous Git, then owner-authenticated gh for github.com only.
    Missing supported access remains UNKNOWN; no credentials are collected by CGC.
    """
    project = _project(project)
    result = dict(root=str(project), head=None, branch=None, origin_main=None,
                  status="UNKNOWN", changed_paths=[], index_state="UNKNOWN", remotes=[],
                  live_remote=None, publication_state="UNKNOWN", observed_at=_now(),
                  evidence_grade="OBSERVED", configuration_state="UNKNOWN", working_tree_clean=None,
                  head_object_verified=False)
    try:
        _safe_git_config(project)
        result["configuration_state"] = "ACCEPTED_BOUNDED_PROFILE"
        result["head"] = _oid(project, "HEAD^{commit}")
        if result["head"]:
            code, object_type = _git(project, ["cat-file", "-t", result["head"]])
            result["head_object_verified"] = code == 0 and object_type.strip() == "commit"
            if not result["head_object_verified"]:
                result["head"] = None
        result["origin_main"] = _oid(project, "refs/remotes/origin/main")
        code, branch = _git(project, ["symbolic-ref", "--quiet", "--short", "HEAD"])
        result["branch"] = redact_text(branch.strip()) if code == 0 else None
        code, status = _git(project, ["status", "--porcelain=v1", "-z", "--untracked-files=normal",
                                      "--ignore-submodules=all", "--no-renames"])
        if code:
            raise ValueError("GIT_STATUS_UNAVAILABLE")
        entries = [item for item in status.split("\0") if item]
        paths = []
        for item in entries:
            if len(item) < 4:
                raise ValueError("GIT_STATUS_INVALID")
            path = item[3:]
            if not _sensitive(path):
                paths.append(dict(path=redact_text(path), index=item[0], worktree=item[1]))
        result.update(status="DIRTY" if entries else "CLEAN", working_tree_clean=not entries, changed_paths=paths,
                      index_state="CHANGED" if any(item[0] not in (" ", "?") for item in entries) else "UNCHANGED",
                      excluded_sensitive_paths=len(entries) - len(paths))
        code, remotes = _git(project, ["remote"])
        if not code:
            result["remotes"] = [redact_text(name) for name in remotes.splitlines()][:128]
        if verify_remote and "origin" in result["remotes"]:
            code, remote = _git(project, ["config", "--no-includes", "--local", "--get", "remote.origin.url"])
            destination = remote.strip()
            valid = False
            if not code and destination.startswith("https://"):
                parsed = urlsplit(destination)
                valid = bool(parsed.hostname and not parsed.username and not parsed.password and
                             not parsed.query and not parsed.fragment)
            elif not code and Path(destination).is_absolute():
                try:
                    _project(destination)
                    valid = True
                except (OSError, ValueError):
                    pass
            if valid:
                try:
                    code, refs = _git(project, ["ls-remote", "--refs", "--", destination, "refs/heads/main"], timeout=15)
                except (OSError, ValueError, subprocess.SubprocessError):
                    code, refs = 1, ""
                rows = [line.split() for line in refs.splitlines()]
                if code == 0 and len(rows) == 1 and len(rows[0]) == 2 and rows[0][1] == "refs/heads/main" and _OID.fullmatch(rows[0][0]):
                    result["live_remote"] = rows[0][0]
                    result["remote_verifier"] = "GIT_LS_REMOTE"
                    if result["head"]:
                        result["publication_state"] = "VERIFIED" if rows[0][0] == result["head"] else "CONTRADICTED"
                elif code == 0 and not rows:
                    result["remote_reason"] = "REMOTE_REF_ABSENT"
                else:
                    result["remote_reason"] = "REMOTE_UNAVAILABLE"
                if result["live_remote"] is None and destination.startswith("https://"):
                    github_ref = _github_remote(project, destination)
                    if github_ref:
                        result["live_remote"] = github_ref
                        result["remote_verifier"] = "GITHUB_API_OWNER_AUTH"
                        result.pop("remote_reason", None)
                        if result["head"]:
                            result["publication_state"] = "VERIFIED" if github_ref == result["head"] else "CONTRADICTED"
            else:
                result["remote_reason"] = "REMOTE_PROFILE_UNSUPPORTED"
        if result["publication_state"] == "VERIFIED" and result["origin_main"] != result["head"]:
            result["publication_state"] = "UNKNOWN"
            result["remote_reason"] = "TRACKING_REF_STALE_OR_UNAVAILABLE"
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error)
        result["reason"] = code if isinstance(error, ValueError) and re.fullmatch(r"[A-Z_]{1,64}", code) else "GIT_UNAVAILABLE"
    return redact(result)


def _parse_builtin(output, framework="unittest", exit_code=0):
    """Parse bounded terminal summaries; an exit code alone never proves tests."""
    if framework not in ("unittest", "pytest", "npm"):
        raise ValueError("UNSUPPORTED_TEST_FRAMEWORK")
    text = output.decode("utf-8", "replace") if isinstance(output, bytes) else str(output)
    text = text[-MAX_PARSE_BYTES:]
    counts = dict(parsed_total=None, parsed_passed=None, parsed_failed=None, parsed_skipped=None)
    if framework == "unittest":
        runs = list(re.finditer(r"^Ran (\d+) tests? in [^\r\n]+", text, re.MULTILINE))
        endings = list(re.finditer(r"^(OK|FAILED)(?: \(([^\r\n]*)\))?\s*$", text, re.MULTILINE))
        if runs and endings and endings[-1].start() > runs[-1].start():
            total = int(runs[-1].group(1))
            fields = dict((key.strip(), int(value)) for key, value in re.findall(r"([a-zA-Z ]+)=(\d+)", endings[-1].group(2) or ""))
            skipped = fields.get("skipped", 0) + fields.get("expected failures", 0)
            failed = fields.get("failures", 0) + fields.get("errors", 0) + fields.get("unexpected successes", 0)
            if (endings[-1].group(1) == "OK" and failed == 0 or endings[-1].group(1) == "FAILED" and failed > 0) and skipped + failed <= total:
                counts.update(parsed_total=total, parsed_passed=total - skipped - failed,
                              parsed_failed=failed, parsed_skipped=skipped)
    elif framework == "pytest":
        candidates = [line for line in text.splitlines() if re.search(r"\b\d+ (?:passed|failed|skipped|error|errors|xfailed|xpassed)\b", line)
                      and re.search(r"\bin \d+(?:\.\d+)?s\b", line)]
        if candidates:
            fields = {key: int(value) for value, key in re.findall(r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed)\b", candidates[-1])}
            failed = fields.get("failed", 0) + fields.get("error", 0) + fields.get("errors", 0) + fields.get("xpassed", 0)
            skipped = fields.get("skipped", 0) + fields.get("xfailed", 0)
            passed = fields.get("passed", 0)
            counts.update(parsed_total=passed + failed + skipped, parsed_passed=passed,
                          parsed_failed=failed, parsed_skipped=skipped)
    else:
        # Node's TAP and spec summaries used by npm test. Other npm runners remain
        # COMMAND_SUCCESS/TEST_COUNTS_UNKNOWN until an explicit parser is added.
        fields = {key: int(value) for key, value in re.findall(r"^[#ℹ]\s*(tests|pass|fail|skipped)\s+(\d+)\s*$", text, re.MULTILINE)}
        if {"tests", "pass", "fail", "skipped"} <= fields.keys() and fields["tests"] == fields["pass"] + fields["fail"] + fields["skipped"]:
            counts.update(parsed_total=fields["tests"], parsed_passed=fields["pass"],
                          parsed_failed=fields["fail"], parsed_skipped=fields["skipped"])
    if counts["parsed_total"] is None:
        state = "COMMAND_SUCCESS_TEST_COUNTS_UNKNOWN" if exit_code == 0 else "COMMAND_FAILED_TEST_COUNTS_UNKNOWN"
    elif exit_code == 0 and counts["parsed_failed"] == 0 and counts["parsed_total"] > 0:
        state = "VERIFIED_PASS"
    elif exit_code != 0 and counts["parsed_failed"] > 0:
        state = "VERIFIED_FAIL"
    elif counts["parsed_total"] == 0:
        state = "NO_TESTS"
    else:
        state = "CONTRADICTED"
    return dict(counts, verification_state=state)


TEST_PARSERS = {name: (lambda output, exit_code, selected=name: _parse_builtin(output, selected, exit_code))
                for name in ("unittest", "pytest", "npm")}


def register_test_parser(name, parser):
    """Trusted local Python extension only; event payloads cannot register code."""
    if (type(name) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name) or
            not callable(parser) or name in TEST_PARSERS or len(TEST_PARSERS) >= 32):
        raise ValueError("INVALID_TEST_PARSER")
    TEST_PARSERS[name] = parser


def parse_test_output(output, framework="unittest", exit_code=0):
    if framework not in TEST_PARSERS:
        raise ValueError("UNSUPPORTED_TEST_FRAMEWORK")
    if not isinstance(output, (str, bytes)):
        raise ValueError("INVALID_TEST_OUTPUT")
    return TEST_PARSERS[framework](output[-MAX_PARSE_BYTES:], exit_code)


def _test_command(command, framework):
    name = Path(command[0]).name.lower()
    if framework == "npm" and name in ("npm", "npm.cmd", "npm.exe"):
        npm = shutil.which(command[0])
        node = shutil.which("node")
        if npm and node:
            # Official Node for Windows distributions place npm's JS entrypoint
            # here. Invoke Node directly; never construct a cmd.exe command line.
            cli = Path(npm).parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
            if cli.is_file():
                return [node, str(cli), *command[1:]]
        raise ValueError("NPM_NODE_LAUNCHER_UNAVAILABLE")
    if Path(command[0]).suffix.lower() in (".cmd", ".bat"):
        raise ValueError("BATCH_LAUNCHER_REFUSED_USE_NODE_NPM_CLI")
    return command


def run_test(project, command, framework="unittest", timeout=60):
    """Run one explicitly requested test command, retaining digests and summaries.

    Tests are executable project code and may mutate their selected project. This
    wrapper is not a sandbox, authority inference, or descendant containment tool.
    """
    project = _project(project)
    if (not isinstance(command, list) or not 1 <= len(command) <= 128 or
            any(type(arg) is not str or not arg or "\0" in arg or len(arg) > 2048 for arg in command) or
            sum(len(arg) for arg in command) > 16384):
        raise ValueError("INVALID_TEST_COMMAND")
    if framework not in TEST_PARSERS:
        raise ValueError("UNSUPPORTED_TEST_FRAMEWORK")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 600:
        raise ValueError("INVALID_TEST_TIMEOUT")
    launched_command = _test_command(command, framework)
    result = _capture(launched_command, project, timeout)
    stdout = result.pop("_stdout")
    stderr = result.pop("_stderr")
    parsed = parse_test_output(stdout + b"\n" + stderr, framework, result["exit_code"])
    if result["interruption"]:
        parsed["verification_state"] = "UNKNOWN"
    result.update(parsed, test_id=uuid.uuid4().hex, framework=framework,
                  normalized_command=redact(command), command_classification="EXPLICIT_TEST_COMMAND",
                  stdout_excerpt=redact_text(stdout[-2048:].decode("utf-8", "replace")),
                  stderr_excerpt=redact_text(stderr[-2048:].decode("utf-8", "replace")),
                  evidence_grade="VERIFIED" if parsed["verification_state"] in ("VERIFIED_PASS", "VERIFIED_FAIL") else "OBSERVED",
                  descendants_contained=False)
    return result
