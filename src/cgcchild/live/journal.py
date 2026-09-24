"""Finite Windows single-writer, fsync-backed canonical segmented journal."""
from contextlib import contextmanager
from itertools import islice
import os
from pathlib import Path
import stat
import uuid
from .protocol import canonical, decode, make_event, validate_event, MAX_EVENT_BYTES, ZERO_HASH, sha

MAX_SEGMENT_BYTES = 1024 * 1024
MAX_SEGMENTS = 64
MAX_EVENTS = 20000


def safe_path(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("REPARSE_POINT_REFUSED")
    return path


def atomic_write(path, raw):
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


class Journal:
    def __init__(self, path, session_id, project_id):
        self.path = safe_path(path)
        self.session_id, self.project_id = session_id, project_id

    @contextmanager
    def writer(self):
        if os.name != "nt":
            raise ValueError("WINDOWS_NATIVE_REQUIRED")
        import msvcrt
        safe_path(self.path)
        target = safe_path(self.path / "writer.lock")
        with target.open("a+b") as stream:
            if stream.seek(0, 2) == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise ValueError("SESSION_WRITER_BUSY") from None
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def replay(self, allow_tail=False):
        paths = sorted(islice(self.path.glob("events-*.jsonl"), MAX_SEGMENTS + 1))
        if len(paths) > MAX_SEGMENTS:
            raise ValueError("SEGMENT_LIMIT")
        events, previous, tail = [], ZERO_HASH, None
        for index, path in enumerate(paths, 1):
            safe_path(path)
            if path.name != f"events-{index:04d}.jsonl" or path.stat().st_size > MAX_SEGMENT_BYTES + MAX_EVENT_BYTES:
                raise ValueError("INVALID_SEGMENT")
            with path.open("rb") as stream:
                while True:
                    offset = stream.tell()
                    line = stream.readline(MAX_EVENT_BYTES + 2)
                    if not line:
                        break
                    if len(line) > MAX_EVENT_BYTES + 1:
                        raise ValueError("EVENT_SIZE_LIMIT")
                    if not line.endswith(b"\n"):
                        if path != paths[-1] or not allow_tail:
                            raise ValueError("TORN_JOURNAL_TAIL")
                        tail = {"path": path, "offset": offset, "raw": line, "sha256": sha(line)}
                        break
                    event = decode(line)
                    validate_event(event, previous, len(events) + 1, self.session_id)
                    if event["project_id"] != self.project_id or canonical(event) + b"\n" != line:
                        raise ValueError("NONCANONICAL_EVENT")
                    events.append(event)
                    if len(events) > MAX_EVENTS:
                        raise ValueError("EVENT_COUNT_LIMIT")
                    previous = event["event_sha256"]
        return events, tail

    def append(self, events, event_type, payload, **kwargs):
        if len(events) >= MAX_EVENTS:
            raise ValueError("SESSION_CAPACITY_REACHED")
        previous = events[-1]["event_sha256"] if events else ZERO_HASH
        event = make_event(self.session_id, self.project_id, len(events) + 1, previous, event_type, payload, **kwargs)
        raw = canonical(event) + b"\n"
        paths = sorted(islice(self.path.glob("events-*.jsonl"), MAX_SEGMENTS + 1))
        index = len(paths) or 1
        target = self.path / f"events-{index:04d}.jsonl"
        if target.exists() and target.stat().st_size + len(raw) > MAX_SEGMENT_BYTES:
            index += 1
            target = self.path / f"events-{index:04d}.jsonl"
        if index > MAX_SEGMENTS:
            raise ValueError("SESSION_CAPACITY_REACHED")
        safe_path(target)
        with target.open("ab") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        events.append(event)
        return event

    def repair_tail(self, tail):
        if tail is None:
            return None
        # Only an incomplete, never-committed final line can be removed. Preserve its bytes.
        backup = self.path / ("torn-tail-" + tail["sha256"] + ".bin")
        if not backup.exists():
            atomic_write(backup, tail["raw"])
        safe_path(tail["path"])
        with tail["path"].open("r+b") as stream:
            stream.truncate(tail["offset"])
            stream.flush()
            os.fsync(stream.fileno())
        return {"sha256": tail["sha256"], "bytes": len(tail["raw"]), "retained": backup.name}
