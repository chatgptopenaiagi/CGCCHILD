"""Inert offline historical status HTML; no scripts, network or executable controls."""
import base64
import hashlib
from html import escape
import sys
from . import snapshot_profiles as profiles, capsule

MAX_HTML=32768
STYLE="""body{margin:0;background:#f5f3ee;color:#202a33;font:16px/1.6 system-ui,sans-serif}
main{max-width:880px;margin:48px auto;padding:0 24px}h1{font-size:36px;line-height:1.15}
.kicker{letter-spacing:.12em;font-size:12px;font-weight:700;color:#566b75}
.notice{border-left:5px solid #a16a13;background:#fff3d9;padding:16px 20px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.card{flex:1;min-width:180px;background:white;padding:16px;border:1px solid #deddd7}
.card strong{display:block;font-size:22px}dl{overflow-wrap:anywhere}dt{font-weight:700}dd{margin:0 0 12px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #deddd7;padding:20px;font:14px/1.7 ui-monospace,monospace}
footer{color:#566b75;font-size:13px;margin:32px 0}"""


def render_html(snapshot_bytes):
    value=profiles.decode(snapshot_bytes)
    digest=profiles.digest(value)
    style_hash=base64.b64encode(hashlib.sha256(STYLE.encode('utf-8')).digest()).decode('ascii')
    csp="default-src 'none'; style-src 'sha256-"+style_hash+"'; base-uri 'none'; form-action 'none'"
    text=profiles.render_human(value)
    out=('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width, initial-scale=1">'
         '<meta http-equiv="Content-Security-Policy" content="'+escape(csp,quote=True)+'">'
         '<title>CGCCHILD | Historical status</title><style>'+STYLE+'</style></head><body><main>'
         '<p class="kicker">CGCCHILD / EXPERIMENTAL OFFLINE VIEW</p>'
         '<h1>Saved state. Current safety unknown.</h1>'
         '<p class="notice">This is a historical snapshot. No repository, filesystem or remote was checked '
         'by this page. Snapshot integrity does not grant authority.</p>'
         '<section class="cards" aria-label="Current proof limits">'
         '<div class="card">Safe to resume<strong>UNKNOWN</strong></div>'
         '<div class="card">Filesystem / P3<strong>UNKNOWN</strong></div>'
         '<div class="card">Mutation authority<strong>NONE</strong></div></section>'
         '<h2>Snapshot identity</h2><dl><dt>Profile</dt><dd>'+escape(profiles.kind(value))+'</dd>'
         '<dt>Canonical snapshot SHA256</dt><dd>'+digest+'</dd>'
         '<dt>Freshness</dt><dd>HISTORICAL_UNVERIFIED</dd></dl>'
         '<h2>Saved evidence summary</h2><pre>'+escape(text)+'</pre>'
         '<footer>No scripts, refresh, network, imported instructions or execution controls. '
         'Source files and Git objects are not included. Obtain fresh scoped evidence before acting.'
         '</footer></main></body></html>\n').encode('utf-8')
    if len(out)>MAX_HTML:raise ValueError('SURFACE_LIMIT')
    return out


def render_capsule(raw):
    """Validate inert capsule bytes in memory before rendering the saved snapshot.

    No member is extracted or trusted as markup. The existing canonical importer
    checks archive/member integrity; the surface retains UNKNOWN/NONE semantics.
    """
    view=capsule.import_capsule(raw)
    return render_html(view.state_bytes)


def main():
    if sys.argv[1:] not in ([],['--capsule-stdin']):return 2
    try:
        is_capsule=bool(sys.argv[1:])
        limit=capsule.MAX_BYTES if is_capsule else profiles.MAX_BYTES
        raw=sys.stdin.buffer.read(limit+1)
        output=render_capsule(raw) if is_capsule else render_html(raw)
        sys.stdout.buffer.write(output)
        return 0
    except (ValueError,OSError):return 2


if __name__=='__main__':raise SystemExit(main())
