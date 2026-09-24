"""Explicit Windows live sessions. Evidence preservation grants no project authority."""
from contextlib import contextmanager
import os
from pathlib import Path
import uuid
from .journal import Journal, atomic_write, safe_path
from .protocol import canonical, decode, sha, now, REPORT_TYPES
from .redaction import redact, redact_text

SESSION_VERSION = "cgc-live-session-0.1"
TRANSITIONS = {
    "IDLE": {"PREPARING"}, "PREPARING": {"RUNNING", "INTERRUPTED"},
    "RUNNING": {"CHECKPOINTING", "ENDING", "INTERRUPTED"},
    "CHECKPOINTING": {"RUNNING", "INTERRUPTED"}, "ENDING": {"PRESERVED", "INTERRUPTED"},
    "PRESERVED": {"INTERRUPTED"}, "INTERRUPTED": {"RECOVERING"},
    "RECOVERING": {"RECOVERABLE", "CLOSED_WITH_UNKNOWN", "INTERRUPTED"},
    "RECOVERABLE": {"RUNNING", "INTERRUPTED"}, "CLOSED_WITH_UNKNOWN": set(),
}


def default_store():
    if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
        raise ValueError("WINDOWS_LOCALAPPDATA_REQUIRED")
    return Path(os.environ["LOCALAPPDATA"]) / "CGCCHILD" / "sessions"


def _read_json(path, limit=4 * 1024 * 1024):
    path = safe_path(path)
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("SESSION_FILE_LIMIT")
    return decode(raw)


def _bounded(value):
    """Observations may exceed one event; preserve explicit omission counts."""
    if isinstance(value, dict):
        return {k: _bounded(v) for k, v in value.items()}
    if isinstance(value, list):
        result = [_bounded(v) for v in value[:64]]
        if len(value) > 64:
            result.append({"omitted_items": len(value) - 64, "coverage": "PARTIAL"})
        return result
    return value


class Session:
    def __init__(self, path, manifest):
        self.path = safe_path(path)
        self.manifest = manifest
        self.journal = Journal(self.path, manifest["session_id"], manifest["project_id"])
        self._events, self._tail = self.journal.replay(allow_tail=True)
        self._project = safe_path(manifest["project_root"])
        self._validate_history()

    @classmethod
    def start(cls, project, store=None, worker_type="Codex", worker_version=None):
        if os.name != "nt":
            raise ValueError("WINDOWS_NATIVE_REQUIRED")
        if worker_version is not None and (type(worker_version) is not str or len(worker_version) > 128):
            raise ValueError("INVALID_WORKER_VERSION")
        project = safe_path(project)
        if not project.is_dir() or redact_text(str(project)) != str(project):
            raise ValueError("PROJECT_DIRECTORY_REQUIRED")
        store = safe_path(store if store is not None else default_store())
        if store == project or store.is_relative_to(project):
            raise ValueError("SESSION_STORE_MUST_BE_OUTSIDE_PROJECT")
        from .observers import FileObserver
        FileObserver(project)  # Reject prohibited roots before creating any session.
        session_id = "CGC-" + uuid.uuid4().hex
        path = store / session_id
        path.mkdir(parents=True, exist_ok=False)
        manifest = dict(session_version=SESSION_VERSION, session_id=session_id,
                        project_id="project-" + uuid.uuid4().hex, project_root=str(project),
                        project_name=redact_text(project.name), created_at=now(),
                        worker_type=redact_text(worker_type), worker_version=redact_text(worker_version) if worker_version else None,
                        mutation_authorized=False)
        atomic_write(path / "manifest.json", canonical(manifest))
        session = cls(path, manifest)
        with session._writer():
            session._transition("PREPARING", "SESSION_PREPARING")
            session._observe()
            session._transition("RUNNING", "SESSION_STARTED", {"generation": 1})
        return session

    @classmethod
    def open(cls, path):
        path = safe_path(path)
        manifest = _read_json(path / "manifest.json", 16384)
        if (not isinstance(manifest, dict) or manifest.get("session_version") != SESSION_VERSION
                or manifest.get("mutation_authorized") is not False
                or not isinstance(manifest.get("project_root"), str)
                or not isinstance(manifest.get("session_id"), str)
                or not isinstance(manifest.get("project_id"), str)):
            raise ValueError("INVALID_SESSION_MANIFEST")
        project = safe_path(manifest["project_root"])
        if path == project or path.is_relative_to(project):
            raise ValueError("SESSION_STORE_MUST_BE_OUTSIDE_PROJECT")
        return cls(path, manifest)

    def _validate_history(self):
        state = "IDLE"
        for event in self._events:
            payload = event["payload"]
            if event["source"] == "CONTROLLER" and "transition" in payload:
                transition = payload["transition"]
                if (type(transition) is not dict or transition.get("from") != state
                        or type(transition.get("to")) is not str or transition.get("to") not in TRANSITIONS.get(state, set())):
                    raise ValueError("INVALID_SESSION_TRANSITION_HISTORY")
                state = transition["to"]
        return state

    @contextmanager
    def _writer(self, recover=False):
        with self.journal.writer():
            self._events, self._tail = self.journal.replay(allow_tail=recover)
            self._validate_history()
            yield
            atomic_write(self.path / "summary.json", canonical(self._summary()))

    def _emit(self, event_type, payload, **kwargs):
        return self.journal.append(self._events, event_type, payload, **kwargs)

    def _transition(self, state, event_type, payload=None):
        previous = self._validate_history()
        if state not in TRANSITIONS[previous]:
            raise ValueError("INVALID_SESSION_TRANSITION")
        data = dict(payload or {})
        data["transition"] = {"from": previous, "to": state}
        return self._emit(event_type, data, state="SUPPORTED")

    def _running(self):
        if self._validate_history() != "RUNNING":
            raise ValueError("SESSION_NOT_RUNNING")

    def events(self):
        self._events, self._tail = self.journal.replay(allow_tail=True)
        self._validate_history()
        return decode(canonical(self._events))

    def summary(self):
        self.events()
        return self._summary()

    def _summary(self, capsule_present=None):
        result = dict(self.manifest, state=self._validate_history(), generation=1,
                      storage_path=str(self.path), event_count=len(self._events), checkpoint_count=0,
                      files_changed=0, tests=[], errors=[], decisions=[], commits=[], git={},
                      push_verification="UNKNOWN", next_action=None, unfinished_work=[], contradictions=[],
                      confidence="PARTIAL", current_authority="UNKNOWN", production_p3="UNKNOWN",
                      filesystem_exclusivity="UNKNOWN", start_time=None, end_time=None,
                      last_checkpoint=None, initial_git_state=None, final_git_state=None,
                      journal_integrity="TORN_TAIL" if self._tail else "VALID", recovery_assessment=None)
        errors, tests, paths = {}, {}, set()
        for event in self._events:
            kind, p = event["event_type"], event["payload"]
            fact = dict(p, evidence_grade=event["evidence_grade"], reconciliation_state=event["reconciliation_state"],
                        event_id=event["event_id"])
            if event["source"] == "CONTROLLER" and kind in ("SESSION_STARTED", "SESSION_RESUMED"):
                result["generation"] = p.get("generation", result["generation"])
                result["start_time"] = result["start_time"] or event["observed_at"]
            if kind == "SESSION_PRESERVED" and event["source"] == "CONTROLLER":
                result["end_time"] = event["observed_at"]
            if kind == "GIT_STATE_OBSERVED":
                result["git"] = p
                result["initial_git_state"] = result["initial_git_state"] or p
                result["final_git_state"] = p
                result["push_verification"] = p.get("publication_state", "UNKNOWN")
            if kind == "FILESYSTEM_CHANGE_OBSERVED":
                paths.add(p.get("path", "UNKNOWN"))
            if kind in ("TEST_STARTED", "TEST_FINISHED", "TEST_RESULT_VERIFIED"):
                tests[p.get("test_id", event["event_id"])] = fact
            if kind in ("ERROR_OBSERVED", "ERROR_RESOLVED", "ERROR_REOPENED"):
                key = p.get("error_id", event["event_id"])
                errors[key] = dict(fact, error_id=key, status="RESOLVED" if kind == "ERROR_RESOLVED" else "OPEN")
            if kind == "DECISION_DECLARED":
                result["decisions"].append(fact)
            if kind in ("COMMIT_REPORTED", "COMMIT_OBSERVED", "COMMIT_VERIFIED"):
                result["commits"].append(fact)
            if kind in ("CONTRADICTION_DETECTED", "PUSH_CONTRADICTION"):
                result["contradictions"].append(fact)
            if kind == "CHECKPOINT_PRESERVED":
                result["checkpoint_count"] += 1
                result["last_checkpoint"] = event["observed_at"]
            if kind == "NEXT_ACTION_DECLARED":
                result["next_action"] = fact
            if kind == "UNFINISHED_WORK_DECLARED":
                result["unfinished_work"].append(fact)
            if kind == "RECOVERY_ASSESSED":
                result["recovery_assessment"] = fact
        result["tests"], result["errors"] = list(tests.values()), list(errors.values())
        result["files_changed"] = len(paths)
        result["open_errors"] = sum(e["status"] == "OPEN" for e in errors.values())
        result["resolved_errors"] = sum(e["status"] == "RESOLVED" for e in errors.values())
        # No uncapsuled terminal state is silently accepted as complete.
        result["capsule_path"] = str(self.path / "capsules" / "final.cgcpack")
        if capsule_present is None:
            capsule_present = False
            if result["state"] == "PRESERVED" and Path(result["capsule_path"]).is_file():
                from .capsule import open_capsule
                try:
                    capsule = open_capsule(result["capsule_path"])
                    capsule_present = (capsule["timeline"][-1]["event_sha256"] == self._events[-1]["event_sha256"])
                except (OSError, ValueError):
                    pass
        result["preservation_complete"] = result["state"] == "PRESERVED" and capsule_present
        result["needs_recovery"] = bool(self._tail) or (result["state"] == "PRESERVED" and not result["preservation_complete"])
        return result

    def report(self, event_type, payload, actor="Codex", correlation_id=None):
        if type(event_type) is not str or event_type not in REPORT_TYPES or not isinstance(payload, dict):
            raise ValueError("REPORT_TYPE_REFUSED")
        # IDs are finite inert text. They cannot select provenance or controller transitions.
        if correlation_id is not None and (not isinstance(correlation_id, str) or len(correlation_id) > 128):
            raise ValueError("CORRELATION_ID_LIMIT")
        payload = dict(payload)
        payload.pop("transition", None)
        for key in ("error_id", "test_id", "path", "sha", "text"):
            if key in payload and (type(payload[key]) is not str or not payload[key] or len(payload[key]) > 2048):
                raise ValueError("INVALID_REPORT_FIELD")
        for key in ("paths", "dependencies", "preconditions"):
            if key in payload and (type(payload[key]) is not list or len(payload[key]) > 128
                                   or any(type(p) is not str or len(p) > 2048 for p in payload[key])):
                raise ValueError("INVALID_REPORT_FIELD")
        if event_type == "NEXT_ACTION_DECLARED":
            payload = dict(text=payload.get("text", ""), declared_by=actor, declared_at=now(),
                           dependencies=payload.get("dependencies", []), preconditions=payload.get("preconditions", []),
                           status="UNEXECUTED_FUTURE_ACTION", kind="AI_PROPOSED_NEXT_ACTION")
        with self._writer():
            self._running()
            event = self._emit(event_type, payload, grade="REPORTED", state="UNKNOWN", actor=actor,
                               source="CODEX_ADAPTER", correlation_id=correlation_id)
        return event

    def _observe(self, verify_remote=False):
        from .observers import FileObserver, git_snapshot
        previous_git = self._summary()["git"]
        try:
            git = _bounded(git_snapshot(self._project, verify_remote=verify_remote))
            self._emit("GIT_STATE_OBSERVED", git, source="GIT_OBSERVER")
            head = git.get("head")
            if head and head != previous_git.get("head"):
                self._emit("COMMIT_OBSERVED", {"sha": head, "scope": "CURRENT_HEAD"}, source="GIT_OBSERVER", state="SUPPORTED")
            if verify_remote:
                state = git.get("publication_state", "UNKNOWN")
                self._emit("PUSH_OBSERVED", {"local_head": head, "origin_main": git.get("origin_main"),
                           "live_remote": git.get("live_remote"), "verification": state}, source="GIT_OBSERVER")
                if state == "VERIFIED":
                    self._emit("PUSH_VERIFIED", {"sha": head, "scope": "REMOTE_REF_AT_OBSERVATION"},
                               source="GIT_OBSERVER", grade="VERIFIED", state="SUPPORTED")
                elif state == "CONTRADICTED":
                    self._emit("PUSH_CONTRADICTION", {"sha": head, "live_remote": git.get("live_remote")},
                               source="GIT_OBSERVER", state="CONTRADICTED")
        except (OSError, ValueError) as exc:
            git = {"status": "UNKNOWN", "error_class": type(exc).__name__, "publication_state": "UNKNOWN"}
            self._emit("GIT_STATE_OBSERVED", git, source="GIT_OBSERVER")
        changes = []
        try:
            baseline_path = self.path / "filesystem.json"
            baseline = None
            expected = next((e["payload"].get("snapshot_sha256") for e in reversed(self._events)
                             if e["event_type"] == "OBSERVER_COVERAGE"), None)
            if baseline_path.exists() and expected:
                candidate = _read_json(baseline_path)
                if sha(canonical(candidate)) == expected:
                    baseline = candidate
            observer = FileObserver(self._project, baseline=baseline)
            if baseline is None:
                snapshot = observer.snapshot()
                self._emit("FILESYSTEM_BASELINE_OBSERVED", {"scope": "METADATA_ONLY", "continuity": "BASELINE_RESET",
                           "files": len(snapshot.get("files", {}))}, source="WINDOWS_OBSERVER")
            else:
                changes = observer.poll()
                snapshot = observer.last_snapshot
                for change in changes:
                    payload = change.get("payload", change)
                    if payload.get("change") not in ("CREATED", "MODIFIED", "RENAMED", "REMOVED"):
                        self._emit("OBSERVER_COVERAGE", _bounded(payload), source="WINDOWS_OBSERVER")
                        continue
                    self._emit("FILESYSTEM_CHANGE_OBSERVED", payload, source="WINDOWS_OBSERVER", state="SUPPORTED")
            atomic_write(baseline_path, canonical(snapshot))
            self._emit("OBSERVER_COVERAGE", {"snapshot_sha256": sha(canonical(snapshot)),
                       "coverage": snapshot.get("coverage", "PARTIAL"), "polling_transient_events": "MAY_BE_MISSED",
                       "filesystem_exclusivity": "UNKNOWN", "excluded_reparse_count": snapshot.get("excluded_reparse_count", 0)},
                       source="WINDOWS_OBSERVER")
        except (OSError, ValueError) as exc:
            self._emit("OBSERVER_COVERAGE", {"coverage": "UNKNOWN", "error_class": type(exc).__name__,
                       "filesystem_exclusivity": "UNKNOWN"}, source="WINDOWS_OBSERVER")
        self._reconcile(git, changes)
        return {"git": git, "changes": changes}

    def _reconcile(self, git, changes):
        # Never edit a reported event. Retain each contradiction and its evidence references.
        paths = {c.get("payload", c).get("path") for c in changes}
        evaluated = {e["payload"].get("report_event_id") for e in self._events
                     if e["event_type"] in ("EVIDENCE_RECONCILED", "CONTRADICTION_DETECTED")}
        for event in list(self._events):
            if event["evidence_grade"] != "REPORTED" or event["event_id"] in evaluated:
                continue
            kind, payload, state = event["event_type"], event["payload"], "UNKNOWN"
            if kind == "FILE_EDIT_REPORTED":
                reported = payload.get("paths", [payload.get("path")])
                if isinstance(reported, list) and reported and all(isinstance(p, str) and p in paths for p in reported):
                    state = "SUPPORTED"
            if kind == "COMMAND_REPORTED" and payload.get("working_tree_clean") is True:
                if git.get("working_tree_clean") is True or git.get("clean") is True:
                    state = "SUPPORTED"
                elif git.get("working_tree_clean") is False or git.get("changed_paths"):
                    state = "CONTRADICTED"
            if kind == "COMMIT_REPORTED" and git.get("head"):
                state = "SUPPORTED" if payload.get("sha") == git["head"] else "UNKNOWN"
                if state == "SUPPORTED" and git.get("head_object_verified") is True:
                    self._emit("COMMIT_VERIFIED", {"sha": git["head"], "report_event_id": event["event_id"],
                               "scope": "LOCAL_HEAD_OBJECT"}, grade="VERIFIED", source="RECONCILER", state="SUPPORTED")
            if kind == "PUSH_REPORTED" and git.get("publication_state") in ("VERIFIED", "CONTRADICTED"):
                claimed = payload.get("sha")
                if claimed is None or claimed == git.get("head"):
                    state = "SUPPORTED" if git["publication_state"] == "VERIFIED" else "CONTRADICTED"
            if state != "UNKNOWN":
                self._emit("CONTRADICTION_DETECTED" if state == "CONTRADICTED" else "EVIDENCE_RECONCILED",
                           {"report_event_id": event["event_id"], "result": state,
                            "report_grade_unchanged": "REPORTED"}, source="RECONCILER", state=state)
        self._emit("RECONCILIATION_COMPLETED", {"scope": "OBSERVABLE_ENGINEERING_EVIDENCE",
                   "current_authority": "UNKNOWN", "production_mutation": False}, source="RECONCILER")

    def observe(self, verify_remote=False):
        with self._writer():
            self._running()
            result = self._observe(verify_remote)
        return result

    def checkpoint(self):
        with self._writer():
            self._running()
            self._transition("CHECKPOINTING", "CHECKPOINT_STARTED")
            self._observe()
            summary = self._summary()
            number = summary["checkpoint_count"] + 1
            target = self.path / "checkpoints" / f"checkpoint-{number:04d}.json"
            raw = canonical(dict(summary=summary, last_event_sha256=self._events[-1]["event_sha256"],
                                 evidence_only=True, source_preserved=False))
            atomic_write(target, raw)
            self._transition("RUNNING", "CHECKPOINT_PRESERVED", {"checkpoint": target.name, "sha256": sha(raw)})
        return self.summary()

    def interrupt(self, reason="CONTROLLER_CLOSED"):
        with self._writer():
            if self._validate_history() in ("PREPARING", "RUNNING", "CHECKPOINTING", "ENDING", "RECOVERING", "RECOVERABLE"):
                self._transition("INTERRUPTED", "SESSION_INTERRUPTED", {"reason": reason})
        return self.summary()

    def recover(self):
        with self._writer(recover=True):
            state = self._validate_history()
            if state == "CLOSED_WITH_UNKNOWN":
                raise ValueError("SESSION_CLOSED")
            if state == "PRESERVED" and self._summary()["preservation_complete"] and not self._tail:
                raise ValueError("SESSION_ALREADY_PRESERVED")
            repaired = self.journal.repair_tail(self._tail)
            self._tail = None
            if state == "IDLE":
                self._transition("PREPARING", "SESSION_PREPARING", {"reason": "INTERRUPTED_STARTUP"})
            if state != "INTERRUPTED":
                self._transition("INTERRUPTED", "SESSION_INTERRUPTED", {"reason": "EXPLICIT_FRESH_PROCESS_RECOVERY"})
            self._transition("RECOVERING", "SESSION_RECOVERING")
            prior_capsule = self.path / "capsules" / "final.cgcpack"
            if prior_capsule.exists():
                from .capsule import MAX_CAPSULE_BYTES
                safe_path(prior_capsule)
                with prior_capsule.open("rb") as stream:
                    retained = stream.read(MAX_CAPSULE_BYTES + 1)
                if len(retained) > MAX_CAPSULE_BYTES:
                    raise ValueError("CAPSULE_SIZE_LIMIT")
                backup = prior_capsule.with_name("interrupted-" + sha(retained) + ".cgcpack")
                if not backup.exists():
                    atomic_write(backup, retained)
            previous = self._summary()["git"].get("head")
            observation = self._observe()
            current = observation["git"].get("head")
            assessment = dict(previous_head=previous, current_head=current,
                              git_changed=previous != current if previous and current else "UNKNOWN",
                              torn_tail=repaired, mutation_authorized=False,
                              resume_scope="OBSERVATION_ONLY_NEW_GENERATION", source_recovery="NOT_PERFORMED",
                              interrupted_test_results="UNKNOWN", power_loss_durability="NOT_GUARANTEED")
            self._emit("RECOVERY_ASSESSED", assessment)
            self._transition("RECOVERABLE", "SESSION_RECOVERABLE")
        return assessment

    def resume(self):
        if self.summary()["state"] != "RECOVERABLE":
            self.recover()
        with self._writer():
            generation = self._summary()["generation"] + 1
            self._transition("RUNNING", "SESSION_RESUMED", {"generation": generation,
                             "previous_generation": generation - 1, "authority": "OBSERVATION_ONLY"})
        return self.summary()

    def run_test(self, command, framework="unittest", timeout=60):
        from .observers import run_test
        with self._writer():
            self._running()
            test_id = uuid.uuid4().hex
            self._emit("TEST_STARTED", {"test_id": test_id, "framework": framework}, source="TEST_OBSERVER")
            self._emit("COMMAND_STARTED", {"test_id": test_id, "classification": "EXPLICIT_TEST_WRAPPER"}, source="TEST_OBSERVER")
            try:
                result = run_test(self._project, command, framework=framework, timeout=timeout)
            except (ValueError, OSError) as exc:
                result = {"framework": framework, "verification_state": "UNKNOWN", "exit_code": None,
                          "error_class": type(exc).__name__, "counts": "UNKNOWN"}
            result["test_id"] = test_id
            self._emit("COMMAND_FINISHED", {"test_id": test_id, "exit_code": result.get("exit_code"),
                       "duration_seconds": result.get("duration_seconds"), "scope": "OWNED_TEST_PROCESS"}, source="TEST_OBSERVER")
            self._emit("TEST_FINISHED", _bounded(result), source="TEST_OBSERVER")
            if result.get("verification_state") in ("VERIFIED_PASS", "VERIFIED_FAIL"):
                self._emit("TEST_RESULT_VERIFIED", _bounded(result), source="TEST_OBSERVER", grade="VERIFIED", state="SUPPORTED")
        return result

    def preserve(self):
        from .capsule import build_capsule
        with self._writer():
            self._running()
            self._transition("ENDING", "SESSION_ENDING")
            self._observe()
            self._transition("PRESERVED", "SESSION_PRESERVED", {"scope": "EVIDENCE_ONLY",
                             "completion_requirement": "VALID_FINAL_CAPSULE_PRESENT"})
            target = self.path / "capsules" / "final.cgcpack"
            raw = build_capsule(self._summary(capsule_present=True), self._events)
            atomic_write(target, raw)
        return target


def discover_sessions(store=None):
    store = safe_path(store if store is not None else default_store())
    if not store.exists():
        return []
    result = []
    # Only CGC's own finite selected store, no project/user-directory discovery.
    with os.scandir(store) as entries:
        paths = []
        for count, entry in enumerate(entries):
            if count >= 1024 or len(paths) >= 256:
                result.append({"storage_path": str(store), "state": "UNKNOWN", "discovery": "STORE_SCAN_LIMIT"})
                break
            if entry.name.startswith("CGC-") and entry.is_dir(follow_symlinks=False):
                paths.append(Path(entry.path))
    for path in sorted(paths):
        if path.is_dir():
            try:
                summary = Session.open(path).summary()
                item = {k: summary[k] for k in ("session_id", "storage_path", "project_root", "state", "generation", "event_count", "journal_integrity", "needs_recovery")}
                item["recovery_candidate"] = summary["state"] not in ("PRESERVED", "CLOSED_WITH_UNKNOWN") or summary["needs_recovery"]
                result.append(item)
            except (ValueError, OSError):
                result.append({"storage_path": str(path), "state": "UNKNOWN", "journal_integrity": "INVALID", "recovery_candidate": True})
    return result
