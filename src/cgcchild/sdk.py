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
