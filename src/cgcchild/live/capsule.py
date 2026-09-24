"""Bounded, nonextracting live session capsules. Imported history is never authority."""
import io
from pathlib import Path
import zipfile
import zlib
from .protocol import canonical, decode, sha, validate_event, ZERO_HASH
from .journal import safe_path, MAX_EVENTS

CAPSULE_VERSION = "cgc-live-capsule-0.1"
MAX_CAPSULE_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 32 * 1024 * 1024
SECTIONS = {"session.json", "timeline.json", "project-state-start.json", "project-state-end.json",
            "git-state.json", "tests.json", "errors.json", "decisions.json", "unfinished-work.json",
            "next-action.json", "evidence-index.json", "human-status.txt"}


def build_capsule(summary, events):
    session = dict(summary, current_authority="UNKNOWN", mutation_authorized=False,
                   import_semantics="HISTORICAL_ONLY")
    content = {"session.json": canonical(session), "timeline.json": canonical(events),
               "project-state-start.json": canonical(summary.get("initial_git_state")),
               "project-state-end.json": canonical(summary.get("final_git_state")),
               "git-state.json": canonical(summary.get("git")),
               "tests.json": canonical(summary["tests"]), "errors.json": canonical(summary["errors"]),
               "decisions.json": canonical(summary["decisions"]), "unfinished-work.json": canonical(summary["unfinished_work"]),
               "next-action.json": canonical(summary["next_action"]),
               "evidence-index.json": canonical({"events": len(events), "last_event_sha256": events[-1]["event_sha256"] if events else ZERO_HASH,
                                                 "contradictions": summary["contradictions"], "integrity_is_not_authenticity": True}),
               "human-status.txt": ("CREDID GUARDIAN CODEX\nHISTORICAL_ONLY — CURRENT AUTHORITY UNKNOWN\n"
                                    f"Session: {summary['session_id']}\nState: {summary['state']}\n"
                                    f"Events: {len(events)}\nSource tree: NOT INCLUDED\n"
                                    "AI_PROPOSED_NEXT_ACTION is not execution authority.\n").encode("utf-8")}
    manifest = dict(capsule_version=CAPSULE_VERSION, session_id=summary["session_id"],
                    authority="HISTORICAL_ONLY", mutation_authorized=False,
                    members={name: {"bytes": len(raw), "sha256": sha(raw)} for name, raw in content.items()})
    content["manifest.json"] = canonical(manifest)
    if any(len(raw) > MAX_MEMBER_BYTES for raw in content.values()) or sum(map(len, content.values())) > MAX_CAPSULE_BYTES:
        raise ValueError("CAPSULE_SIZE_LIMIT")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(content.items()):
            archive.writestr(name, raw)
    raw = buffer.getvalue()
    if len(raw) > MAX_CAPSULE_BYTES:
        raise ValueError("CAPSULE_SIZE_LIMIT")
    return raw


def open_capsule(path):
    if isinstance(path, bytes):
        raw = path
    else:
        with safe_path(path).open("rb") as stream:
            raw = stream.read(MAX_CAPSULE_BYTES + 1)
    if len(raw) > MAX_CAPSULE_BYTES:
        raise ValueError("CAPSULE_SIZE_LIMIT")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) != len(SECTIONS) + 1 or {i.filename for i in infos} != SECTIONS | {"manifest.json"}:
                raise ValueError("CAPSULE_MEMBERS_INVALID")
            if any(i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) for i in infos):
                raise ValueError("CAPSULE_COMPRESSION_REFUSED")
            if any(i.file_size > MAX_MEMBER_BYTES or i.flag_bits & 1 for i in infos) or sum(i.file_size for i in infos) > MAX_CAPSULE_BYTES:
                raise ValueError("CAPSULE_SIZE_LIMIT")
            content = {i.filename: archive.read(i.filename) for i in infos}
        manifest = decode(content.pop("manifest.json"))
        if (not isinstance(manifest, dict) or manifest.get("capsule_version") != CAPSULE_VERSION
                or manifest.get("authority") != "HISTORICAL_ONLY" or manifest.get("mutation_authorized") is not False
                or not isinstance(manifest.get("members"), dict) or set(manifest["members"]) != SECTIONS):
            raise ValueError("CAPSULE_MANIFEST_INVALID")
        for name, value in content.items():
            if manifest["members"][name] != {"bytes": len(value), "sha256": sha(value)}:
                raise ValueError("CAPSULE_DIGEST_MISMATCH")
        result = {name.removesuffix(".json").replace("-", "_"): decode(value)
                  for name, value in content.items() if name.endswith(".json")}
        events, session = result["timeline"], result["session"]
        if not isinstance(session, dict) or not isinstance(result["evidence_index"], dict):
            raise ValueError("CAPSULE_SESSION_INVALID")
        if not isinstance(events, list) or len(events) > MAX_EVENTS or not events:
            raise ValueError("CAPSULE_TIMELINE_INVALID")
        previous = ZERO_HASH
        for sequence, event in enumerate(events, 1):
            validate_event(event, previous, sequence, manifest["session_id"])
            if event["project_id"] != session["project_id"]:
                raise ValueError("CAPSULE_PROJECT_MISMATCH")
            previous = event["event_sha256"]
        if (result["evidence_index"]["last_event_sha256"] != previous or result["evidence_index"]["events"] != len(events)
                or session["session_id"] != manifest["session_id"] or session["event_count"] != len(events)):
            raise ValueError("CAPSULE_HISTORY_MISMATCH")
        # Rebuild all derived projections from the canonical timeline. Digests alone
        # cannot establish that an index or summary actually represents that history.
        from .session import Session, SESSION_VERSION
        manifest_keys = ("session_version", "session_id", "project_id", "project_root", "project_name",
                         "created_at", "worker_type", "worker_version", "mutation_authorized")
        if (session.get("session_version") != SESSION_VERSION or session.get("mutation_authorized") is not False
                or any(type(session.get(k)) is not str for k in ("session_id", "project_id", "project_root", "storage_path"))):
            raise ValueError("CAPSULE_SESSION_INVALID")
        projected = Session.__new__(Session)
        projected.manifest = {k: session[k] for k in manifest_keys}
        projected.path, projected._events, projected._tail = Path(session["storage_path"]), events, None
        derived = projected._summary(capsule_present=True)
        for key, value in derived.items():
            if session.get(key) != value:
                raise ValueError("CAPSULE_PROJECTION_MISMATCH")
        sections = {"git_state": "git", "tests": "tests", "errors": "errors", "decisions": "decisions",
                    "unfinished_work": "unfinished_work", "next_action": "next_action",
                    "project_state_start": "initial_git_state", "project_state_end": "final_git_state"}
        if any(result[key] != derived[field] for key, field in sections.items()):
            raise ValueError("CAPSULE_PROJECTION_MISMATCH")
        # Imported metadata cannot promote authority even in a self-consistent forged archive.
        result.update(authority="HISTORICAL_ONLY", mutation_authorized=False, current_authority="UNKNOWN", manifest=manifest)
        session.update(current_authority="UNKNOWN", mutation_authorized=False, import_semantics="HISTORICAL_ONLY")
        return result
    except (KeyError, TypeError, UnicodeError, zipfile.BadZipFile, zlib.error, RuntimeError, RecursionError):
        raise ValueError("INVALID_LIVE_CAPSULE") from None
