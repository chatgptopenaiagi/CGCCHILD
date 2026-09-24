"""Experimental inert capsule pipe adapter. No paths, extraction, network or execution."""
import hashlib
import json
import sys
from . import capsule,snapshot_profiles as profiles

MODES=('export','import','inspect')
ERROR=b'CGCCHILD_CAPSULE_REFUSED\n'


class CapsuleCommandError(ValueError):
    def __init__(self):super().__init__('CGCCHILD_CAPSULE_REFUSED')


def transform(mode,raw):
    """Validate completely before returning output; integrity never grants authority."""
    if type(mode) is not str or mode not in MODES:raise CapsuleCommandError()
    try:
        if mode=='export':return capsule.export_capsule(profiles.decode(raw))
        view=capsule.import_capsule(raw)
        value=view.snapshot()
        if mode=='import':return profiles.encode(value)
        report=dict(version='cgcchild-capsule-inspection-0.1',profile=profiles.kind(value),
                    capsule_sha256=hashlib.sha256(raw).hexdigest(),snapshot_digest=profiles.digest(value),
                    capsule_bytes=len(raw),integrity=view.integrity,freshness=view.freshness,
                    authority=view.authority,current_safe_to_resume='UNKNOWN',
                    mutation_authorized=False,filesystem_exclusivity='UNKNOWN',
                    extraction_performed=False,source_authenticated=False)
        return (json.dumps(report,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
    except (ValueError,TypeError,OverflowError,RecursionError):raise CapsuleCommandError() from None


def serve(mode,source,destination):
    """One bounded binary input and output. Caller owns pipe deadline/lifecycle.

    Invalid input produces no output. Output I/O failure may leave partial bytes;
    callers must require exit0 and validate the received artifact independently.
    """
    if type(mode) is not str or mode not in MODES:return 2
    bound=profiles.MAX_BYTES if mode=='export' else capsule.MAX_BYTES
    try:
        raw=source.read(bound+1)
        result=transform(mode,raw)
        written=destination.write(result)
        if type(written) is not int or written!=len(result):return 2
        destination.flush()
        return 0
    except (CapsuleCommandError,OSError):return 2


def main():
    if len(sys.argv)!=2 or sys.argv[1] not in MODES:
        code=2
    else:code=serve(sys.argv[1],sys.stdin.buffer,sys.stdout.buffer)
    if code:
        try:sys.stderr.buffer.write(ERROR);sys.stderr.buffer.flush()
        except OSError:pass
    return code


if __name__=='__main__':raise SystemExit(main())
