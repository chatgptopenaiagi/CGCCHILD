"""Central bounded data minimization. Patterns are defense in depth, not proof."""
import re

_KEY = re.compile(r"(?i)(password|passwd|secret|token|api.?key|authorization|cookie|private.?key|chain.?of.?thought|hidden.?reason|reasoning|environment|transcript)")
_PATTERNS = (
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|$)", re.S),
    re.compile(r"(?i)\b(?:sk-(?:proj-)?|gh[pousr]_|github_pat_)[A-Za-z0-9_-]{6,}"),
    re.compile(r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_.=-]+"),
    re.compile(r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|secret|authorization|cookie)\s*[=:]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"),
    re.compile(r"(?i)https?://[^\s/@]+:[^\s/@]+@"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
)


def redact_text(text):
    if not isinstance(text, str):
        raise ValueError("TEXT_REQUIRED")
    # Bound input before expensive patterns; over-limit input is never retained.
    if len(text) > 65536:
        return "[OMITTED:TEXT_LIMIT]"
    for pattern in _PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:2048] + ("[TRUNCATED]" if len(text) > 2048 else "")


def redact(value, _depth=0):
    if _depth > 8:
        raise ValueError("PAYLOAD_DEPTH_LIMIT")
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        if len(value) > 128 or any(type(k) is not str or len(k) > 128 for k in value):
            raise ValueError("PAYLOAD_KEYS_LIMIT")
        return {redact_text(k): "[REDACTED]" if _KEY.search(k) else redact(v, _depth + 1)
                for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 256:
            raise ValueError("PAYLOAD_LIST_LIMIT")
        return [redact(v, _depth + 1) for v in value]
    if value is None or type(value) in (bool, int, float):
        return value
    raise ValueError("JSON_VALUE_REQUIRED")
