"""Versioned bounded SDK facade over the independently tested historical codecs."""
from cgc.experimental import snapshot_profiles as profiles, capsule, offline_surface
from cgc.experimental.read_router import ReadRouter as LocalAgentRouter
from . import __version__

API_VERSION = "cgcchild-sdk-1"


def negotiate(version):
    if version != API_VERSION:
        raise ValueError("UNSUPPORTED_SDK_VERSION")
    return {"api_version": API_VERSION, "package_version": __version__,
            "profiles": [profiles.MODEL, profiles.CONTINUITY], "mutation_authorized": False}


def decode(raw):
    try:
        return profiles.decode(raw)
    except ValueError:
        raise ValueError("INVALID_SNAPSHOT") from None


def encode(value):
    try:
        return profiles.encode(value)
    except ValueError:
        raise ValueError("INVALID_SNAPSHOT") from None


def import_capsule(raw):
    try:
        return decode(capsule.import_capsule(raw).state_bytes)
    except ValueError:
        raise ValueError("INVALID_CAPSULE") from None


def export_capsule(value):
    return capsule.export_capsule(decode(encode(value)))


def report(value):
    return offline_surface.render_html(encode(value))


def live_start(project, *, store=None, worker_type="Codex", worker_version=None):
    """Start a user-selected project session; storage is external by default."""
    from .live import Session
    return Session.start(project, store=store, worker_type=worker_type, worker_version=worker_version)


def live_open(session_directory):
    """Replay one explicit session; replay grants no mutation authority."""
    from .live import Session
    return Session.open(session_directory)


def live_capsule_open(path):
    """Read and validate a live session capsule as historical evidence."""
    from .live import open_capsule
    return open_capsule(path)


def live_sessions(store=None):
    """Discover bounded session summaries only in CGC's own store."""
    from .live import discover_sessions
    return discover_sessions(store)
