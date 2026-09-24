import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from cgcchild.live.observers import (FileObserver, git_snapshot, parse_test_output, run_test,
                                     TEST_PARSERS, register_test_parser)


class FileObserverTests(unittest.TestCase):
    def test_secret_like_filenames_never_enter_baseline_or_events(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            observer = FileObserver(root)
            observer.poll()
            synthetic_name = "ghp_" + "SYNTHETICONLY" * 3
            (root / synthetic_name).write_text("fixture content")
            (root / ("sk-proj-" + "SYNTHETICONLY" * 3)).mkdir()
            (root / "ordinary.txt").write_text("fixture content")
            events = observer.poll()
            self.assertEqual(set(observer.last_snapshot["files"]), {"ordinary.txt"})
            self.assertEqual(observer.last_snapshot["excluded_sensitive_count"], 2)
            self.assertNotIn(synthetic_name, json.dumps(observer.last_snapshot))
            self.assertNotIn(synthetic_name, json.dumps(events))
            poisoned = dict(observer.last_snapshot, files={synthetic_name: {"size": 0, "mtime_ns": 0, "file_id": "1:2"}})
            with self.assertRaises(ValueError):
                FileObserver(root, baseline=poisoned)

    def test_create_modify_rename_remove_and_persisted_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            observer = FileObserver(root)
            self.assertEqual(observer.poll()[0]["change"], "BASELINE_ESTABLISHED")
            target = root / "hello.py"
            target.write_text("first", encoding="utf-8")
            created = observer.poll()
            self.assertEqual([(x["path"], x["change"]) for x in created], [("hello.py", "CREATED")])
            self.assertNotIn("content", json.dumps(created))
            observer = FileObserver(root, baseline=json.loads(json.dumps(observer.last_snapshot)))
            target.write_text("second and longer", encoding="utf-8")
            self.assertEqual(observer.poll()[0]["change"], "MODIFIED")
            target.rename(root / "renamed.py")
            event = observer.poll()[0]
            self.assertEqual(event["change"], "RENAMED")
            self.assertEqual(event["previous_path"], "hello.py")
            (root / "renamed.py").unlink()
            self.assertEqual(observer.poll()[0]["change"], "REMOVED")

    def test_content_never_read_and_sensitive_paths_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for path in ("file.py", ".env", "auth.json", "secret.pem"):
                (root / path).write_text("synthetic value")
            (root / ".codex").mkdir()
            (root / ".codex" / "private.json").write_text("synthetic value")
            with patch.object(Path, "open", side_effect=AssertionError("contents must not be read")):
                snapshot = FileObserver(root).snapshot()
            self.assertEqual(set(snapshot["files"]), {"file.py"})
            self.assertEqual(snapshot["production_filesystem_closure"], "UNKNOWN")

    def test_incomplete_scan_does_not_report_false_removals(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a").write_text("a")
            observer = FileObserver(root, max_entries=1)
            observer.poll()
            (root / "b").write_text("b")
            events = observer.poll()
            self.assertEqual(observer.last_snapshot["coverage"], "PARTIAL")
            self.assertEqual(events[0]["change"], "OBSERVATION_INCOMPLETE")
            self.assertNotIn("REMOVED", [event["change"] for event in events])

    def test_reparse_flag_is_excluded_without_recursing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "outside"
            target.mkdir()
            # Simulated stat uses the actual Windows reparse attribute. Actual
            # junction acceptance has its own Windows fixture below.
            with patch("cgcchild.live.observers._reparse", side_effect=lambda info: getattr(info, "st_ino", None) == target.stat().st_ino):
                result = FileObserver(root).snapshot()
            self.assertEqual(result["excluded_count"], 1)

    def test_invalid_baseline_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                FileObserver(folder, baseline={"coverage": "SAMPLED", "files": {"../outside": {}}})

    @unittest.skipUnless(os.name == "nt", "native Windows junction")
    def test_real_windows_junction_stays_outside(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "project"
            outside = Path(folder) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "not-observed.txt").write_text("synthetic")
            # PowerShell remains the Windows orchestration shell; no elevation.
            # Invoke a script file to pass parameters without command parsing.
            script = Path(folder) / "junction.ps1"
            script.write_text("param($LinkPath,$TargetPath)\nNew-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null\n")
            subprocess.run(["pwsh", "-NoProfile", "-File", str(script), str(root / "link"), str(outside)], check=True, capture_output=True, timeout=10)
            try:
                result = FileObserver(root).snapshot()
                self.assertEqual(result["files"], {})
                self.assertEqual(result["excluded_count"], 1)
                with self.assertRaisesRegex(ValueError, "REPARSE"):
                    FileObserver(root / "link")
            finally:
                (root / "link").rmdir()


class GitObserverTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows native executable selection")
    def test_observer_tool_resolution_excludes_project_cwd_relative_and_batch(self):
        from cgcchild.live.observers import _observer_executable, _git, _github_remote
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            project, child, current, trusted = base / "project", base / "project" / "tools", base / "current", base / "trusted"
            for path in (project, child, current, trusted):
                path.mkdir(parents=True, exist_ok=True)
            for path in (project, child, current, trusted):
                for name in ("git.exe", "gh.exe"):
                    (path / name).write_bytes(b"owned fixture only; never executed")
            dangerous = os.pathsep.join(("", ".", "relative-tools", "C:drive-relative", str(project), str(child), str(current)))
            with patch.dict(os.environ, {"PATH": dangerous}), patch.object(Path, "cwd", return_value=current), \
                    patch("cgcchild.live.observers._capture") as capture:
                self.assertIsNone(_observer_executable("git", project))
                self.assertIsNone(_observer_executable("gh", project))
                with self.assertRaisesRegex(ValueError, "GIT_UNAVAILABLE"):
                    _git(project, ["status"])
                self.assertIsNone(_github_remote(project, "https://github.com/owner/project.git"))
                capture.assert_not_called()
            with patch.dict(os.environ, {"PATH": dangerous + os.pathsep + str(trusted)}), \
                    patch.object(Path, "cwd", return_value=current), \
                    patch("cgcchild.live.observers.shutil.which", side_effect=AssertionError("implicit Windows search forbidden")):
                self.assertEqual(_observer_executable("git", project), str((trusted / "git.exe").resolve()))
                self.assertEqual(_observer_executable("gh", project), str((trusted / "gh.exe").resolve()))
            (trusted / "git.exe").unlink()
            (trusted / "git.cmd").write_text("owned fixture; never executed")
            with patch.dict(os.environ, {"PATH": str(trusted)}), patch.object(Path, "cwd", return_value=current):
                self.assertIsNone(_observer_executable("git", project))

    def git(self, root, *args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, timeout=15)
        return result.stdout.decode().strip()

    def fixture(self, root):
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "CGC fixture")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        (root / "file.txt").write_text("initial")
        self.git(root, "add", "file.txt")
        self.git(root, "-c", "core.hooksPath=NUL", "commit", "-m", "fixture")

    def test_local_status_commit_and_independent_remote(self):
        with tempfile.TemporaryDirectory() as folder:
            root, bare = Path(folder) / "project", Path(folder) / "remote.git"
            root.mkdir()
            bare.mkdir()
            self.fixture(root)
            self.git(bare, "init", "--bare")
            self.git(root, "remote", "add", "origin", str(bare))
            self.git(root, "push", "-u", "origin", "main")
            index_before = hashlib.sha256((root / ".git/index").read_bytes()).hexdigest()
            snap = git_snapshot(root, verify_remote=True)
            self.assertEqual(snap["status"], "CLEAN", snap)
            self.assertEqual(snap["publication_state"], "VERIFIED", snap)
            self.assertEqual(snap["head"], snap["live_remote"])
            self.assertTrue(snap["head_object_verified"])
            self.assertTrue(snap["working_tree_clean"])
            self.assertEqual(index_before, hashlib.sha256((root / ".git/index").read_bytes()).hexdigest())
            (root / "file.txt").write_text("changed")
            self.assertEqual(git_snapshot(root)["status"], "DIRTY")
            self.git(root, "add", "file.txt")
            self.assertEqual(git_snapshot(root)["index_state"], "CHANGED")
            self.git(root, "-c", "core.hooksPath=NUL", "commit", "-m", "next")
            snap = git_snapshot(root, verify_remote=True)
            self.assertEqual(snap["publication_state"], "CONTRADICTED")
            self.assertNotEqual(snap["head"], snap["live_remote"])

    def test_stale_tracking_does_not_promote_remote_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root, bare = Path(folder) / "project", Path(folder) / "remote.git"
            root.mkdir()
            bare.mkdir()
            self.fixture(root)
            self.git(bare, "init", "--bare")
            self.git(root, "remote", "add", "origin", str(bare))
            self.git(root, "push", "-u", "origin", "main")
            self.git(root, "update-ref", "-d", "refs/remotes/origin/main")
            snap = git_snapshot(root, verify_remote=True)
            self.assertEqual(snap["head"], snap["live_remote"])
            self.assertEqual(snap["publication_state"], "UNKNOWN")
            self.assertEqual(snap["remote_reason"], "TRACKING_REF_STALE_OR_UNAVAILABLE")

    def test_unknown_nonrepo_and_offline_remote(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(git_snapshot(root)["status"], "UNKNOWN")
            self.fixture(root)
            self.git(root, "remote", "add", "origin", "https://127.0.0.1:1/no-such-repository")
            snap = git_snapshot(root, verify_remote=True)
            self.assertEqual(snap["publication_state"], "UNKNOWN")
            self.assertIsNone(snap["live_remote"])

    def test_config_includes_and_executable_helpers_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            for key in ("include.path", "core.fsmonitor", "remote.origin.uploadpack"):
                self.git(root, "config", key, "synthetic-prohibited-value")
                snap = git_snapshot(root)
                self.assertEqual(snap["reason"], "GIT_CONFIGURATION_REFUSED", snap)
                self.assertEqual(snap["status"], "UNKNOWN")
                self.git(root, "config", "--unset", key)

    def test_secret_url_never_exported_or_used(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            self.git(root, "remote", "add", "origin", "https://synthetic-user:synthetic-password@example.invalid/repo")
            result = git_snapshot(root, verify_remote=True)
            self.assertEqual(result["remote_reason"], "REMOTE_PROFILE_UNSUPPORTED")
            self.assertNotIn("synthetic-password", json.dumps(result))

    def test_fixed_github_api_uses_owner_cli_without_collecting_auth(self):
        from cgcchild.live.observers import _github_remote
        with tempfile.TemporaryDirectory() as folder:
            digest = "1" * 40
            result = {"_stdout": digest.encode(), "exit_code": 0, "interruption": None}
            with patch("cgcchild.live.observers._capture", return_value=result) as capture:
                with patch("cgcchild.live.observers._observer_executable", return_value="gh.exe"):
                    self.assertEqual(_github_remote(Path(folder), "https://github.com/owner/project.git"), digest)
                    command = capture.call_args.args[0]
                    self.assertEqual(command, ["gh.exe", "api", "--hostname", "github.com", "repos/owner/project/git/ref/heads/main", "--jq", ".object.sha"])
                    capture.reset_mock()
                    self.assertIsNone(_github_remote(Path(folder), "https://other.invalid/owner/project.git"))
                    self.assertIsNone(_github_remote(Path(folder), "https://github.com/../project"))
                    capture.assert_not_called()


class TestObserverTests(unittest.TestCase):
    def test_unittest_summary_truth_levels(self):
        result = parse_test_output("Ran 217 tests in 1.1s\n\nOK (skipped=30)\n")
        self.assertEqual(result["verification_state"], "VERIFIED_PASS")
        self.assertEqual(result["parsed_passed"], 187)
        self.assertEqual(parse_test_output("Ran 4 tests in .1s\nFAILED (failures=1, errors=1)\n", exit_code=1)["parsed_failed"], 2)
        self.assertEqual(parse_test_output("done", exit_code=0)["verification_state"], "COMMAND_SUCCESS_TEST_COUNTS_UNKNOWN")
        self.assertEqual(parse_test_output("Ran 1 test in .1s\nOK\n", exit_code=1)["verification_state"], "CONTRADICTED")

    def test_pytest_and_node_counts(self):
        pytest = parse_test_output("==== 4 passed, 2 skipped in 0.23s ====", "pytest")
        self.assertEqual(pytest["parsed_total"], 6)
        self.assertEqual(pytest["verification_state"], "VERIFIED_PASS")
        node = parse_test_output("# tests 5\n# pass 3\n# fail 1\n# skipped 1\n", "npm", 1)
        self.assertEqual(node["verification_state"], "VERIFIED_FAIL")
        self.assertEqual(node["parsed_passed"], 3)

    def test_real_unittest_process_and_secret_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "test_fixture.py").write_text("import unittest\nclass Case(unittest.TestCase):\n def test_one(self): self.assertTrue(True)\n")
            result = run_test(root, [sys.executable, "-m", "unittest", "discover", "-v"])
            self.assertEqual(result["verification_state"], "VERIFIED_PASS", result)
            self.assertEqual(result["parsed_passed"], 1)
            self.assertEqual(len(result["stderr_sha256"]), 64)
            self.assertNotIn("_stderr", result)
            result = run_test(root, [sys.executable, "-c", "print('password=synthetic-secret')"])
            self.assertNotIn("synthetic-secret", json.dumps(result))

    def test_timeout_and_output_bound_never_verify(self):
        with tempfile.TemporaryDirectory() as folder:
            timeout = run_test(folder, [sys.executable, "-c", "import time; time.sleep(20)"], timeout=.1)
            self.assertEqual(timeout["interruption"], "TIMEOUT")
            self.assertEqual(timeout["verification_state"], "UNKNOWN")
            output = run_test(folder, [sys.executable, "-c", "import sys; sys.stdout.write('x'*3000000)"])
            self.assertEqual(output["interruption"], "OUTPUT_LIMIT")
            self.assertEqual(output["verification_state"], "UNKNOWN")
            self.assertLessEqual(len(output["stdout_excerpt"]), 2048)

    @unittest.skipUnless(os.name == "nt", "native Windows pipe lifecycle")
    def test_descendant_inherited_pipe_does_not_strand_capture_thread(self):
        with tempfile.TemporaryDirectory() as folder:
            before = {thread.ident for thread in threading.enumerate()}
            started = time.monotonic()
            command = [sys.executable, "-c", "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(2)'])"]
            result = run_test(folder, command)
            self.assertEqual(result["verification_state"], "UNKNOWN")
            self.assertEqual(result["interruption"], "INCOMPLETE_STREAMS")
            self.assertLess(time.monotonic() - started, 2)
            self.assertEqual({thread.ident for thread in threading.enumerate()}, before)
            # The wrapper explicitly does not kill descendants. Let this known
            # two-second fixture exit before removing its working directory.
            time.sleep(max(0, 2.5 - (time.monotonic() - started)))

    def test_real_npm_test_runs_through_node_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "package.json").write_text(json.dumps({"private": True, "scripts": {"test": "node --test --test-reporter=tap"}}))
            (root / "example.test.cjs").write_text("const test = require('node:test'); test('works', () => {});\n")
            result = run_test(root, ["npm", "test", "--offline"], framework="npm")
            self.assertEqual(result["verification_state"], "VERIFIED_PASS", result)
            self.assertEqual(result["parsed_passed"], 1)

    def test_explicit_local_parser_registry(self):
        try:
            register_test_parser("custom", lambda output, exit_code: {"verification_state": "UNKNOWN"})
            self.assertEqual(parse_test_output("result", "custom")["verification_state"], "UNKNOWN")
            with self.assertRaises(ValueError): register_test_parser("custom", lambda *_: {})
        finally:
            TEST_PARSERS.pop("custom", None)

    def test_shell_batch_and_invalid_limits_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            for command in (["npm.cmd", "test"], [], ["x", "a\0b"]):
                with self.assertRaises(ValueError): run_test(folder, command)
            for timeout in (0, 1000, True):
                with self.assertRaises(ValueError): run_test(folder, [sys.executable], timeout=timeout)


if __name__ == "__main__":
    unittest.main()
