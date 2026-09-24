# Offline Guardian surface foundation

[Renderer](../src/cgc/experimental/offline_surface.py),
[tests](../tests/test_child_surface.py),
[synthetic example](lab/child_status_example.html).

This V4.5 foundation renders either closed historical snapshot profile to deterministic UTF-8
HTML. It is an offline view, not a desktop/mobile application, daemon, live monitor or source of
proof. It shows historical summary, canonical snapshot digest, UNKNOWN current safety/P3 and
NONE mutation authority. No arbitrary stored next-action instructions are rendered as controls.

All variable summary text is HTML-escaped. There is no script, external asset, link, form,
button, refresh, URL input or network request in the document. The fixed stylesheet is permitted
by its exact SHA256 in a default-deny CSP; policy text is defense in depth, not a claim about
every browser's security enforcement. The output ceiling is32768 bytes. Invalid snapshots,
forged authority or extra CLI options refuse.

The optional foreground CLI accepts one bounded canonical snapshot on stdin until EOF and
writes HTML to stdout. It opens no path, captures no live state and owns no persistence:

```text
python -B -m cgc.experimental.offline_surface
```

An owner-controlled caller decides whether/where to save that output. The parent owns timeout
and stream lifecycle. The committed example is synthetic historical data only.

Four tests cover both profiles, deterministic/digest-bound output, forbidden tags/attributes,
CSP, escaping, size refusal, malformed/forged inputs and actual subprocess rendering. A fresh
disposable Windows Edge headless profile rendered the example at1280x1100; visual inspection
confirmed readable cards and the preserved FAILED/last-known-good distinction. Browser profile
and screenshot were removed. No browser credentials or existing profile were accessed.
