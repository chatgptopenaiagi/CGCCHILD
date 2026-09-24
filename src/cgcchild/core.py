"""Shared desktop/CLI application model. Explicit files only; no implicit project scan."""
import json
import os
import stat
from importlib.resources import files
from pathlib import Path
from . import __version__, sdk
from .execution import Mode, plan
from .evidence import WindowsEvidenceProvider
from cgc.experimental import snapshot_profiles as profiles, capsule, continuity


def resource(name):
    return files("cgcchild").joinpath("resources", name).read_bytes()


def security_debt():
    return json.loads(resource("security-debt.json"))


def read_input(path):
    target = Path(path)
    if target.suffix.lower() not in (".json", ".cgcpack"):
        raise ValueError("EXPECTED_JSON_OR_CGCPACK")
    # Selected inert documents only. Refuse reparse points/devices and credential names.
    if target.name.lower() in ("auth.json", "credentials.json"):
        raise ValueError("PROHIBITED_INPUT")
    for part in (target, *target.parents):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("REPARSE_POINT_REFUSED")
    with target.open("rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("REGULAR_FILE_REQUIRED")
        raw = stream.read(capsule.MAX_BYTES + 1)
    if len(raw) > capsule.MAX_BYTES:
        raise ValueError("INPUT_LIMIT")
    return sdk.import_capsule(raw) if target.suffix.lower() == ".cgcpack" else sdk.decode(raw)


def save_new(path, raw):
    # Explicit exports never replace an existing file or extract archive members.
    with Path(path).open("xb") as stream:
        stream.write(raw)


class Workbench:
    def __init__(self, mode=Mode.READ_ONLY_SAFE):
        if type(mode) is not Mode:
            raise ValueError("INVALID_MODE")
        self.mode = mode
        self._snapshot = None

    def load(self, value):
        self._snapshot = sdk.encode(value)

    def snapshot(self):
        if self._snapshot is None:
            raise ValueError("NO_SNAPSHOT_SELECTED")
        return sdk.decode(self._snapshot)

    def status(self):
        value = dict(project="CGCCHILD", product="CREDID GUARDIAN CODEX", version=__version__,
                     mode=self.mode.value, release_state="EXPERIMENTAL", mutation_authorized=False,
                     safe_to_resume="UNKNOWN", production_p3="UNKNOWN",
                     snapshot_loaded=self._snapshot is not None)
        if self._snapshot is not None:
            data = self.snapshot()
            value.update(profile=profiles.kind(data), snapshot_digest=profiles.digest(data),
                         freshness="HISTORICAL_UNVERIFIED", summary=profiles.render_human(data))
        return value

    def review(self):
        value = self.snapshot()
        result = dict(scope="HISTORICAL_OFFLINE_REVIEW", safe_to_resume="UNKNOWN",
                      mutation_authorized=False, current_repository_checked=False,
                      recovery_plan=plan("RECOVERY_PLAN", self.mode))
        if profiles.kind(value) == profiles.CONTINUITY:
            result["continuity"] = continuity.summary(value)
        else:
            result["model_claims"] = value["model"]["claims"]
        result["next_steps"] = ["Retain saved evidence", "Collect fresh scoped evidence",
                                "Review unresolved acceptance debt before repository actions"]
        return result

    def evidence(self):
        return WindowsEvidenceProvider().assess().report()
