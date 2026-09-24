"""Inert imported-report status over explicit stdin/stdout; no collection."""
import hashlib
import sys
from . import session_report as reports
MAX_OUTPUT=8192


def transform(raw,mode):
    if mode not in ('json','text'):raise reports.ReportError()
    value=reports.decode(raw);proof=value['verification']
    rows=[{k:row[k] for k in ('id','plane','required','status')} for row in proof['proof_obligations']]
    result=dict(version='cgcchild-session-status-0.1-experimental',scope='IMPORTED_ANALYSIS_REVIEW',
        report_sha256=hashlib.sha256(raw).hexdigest(),verification_sha256=value['verification_sha256'],
        imported_verdict=proof['safe_to_resume'],current_repository_safety='UNKNOWN',
        authority='NONE',mutation_authorized=False,execution_state='NO_ACCEPTED_EXECUTION_ADAPTER',
        freshness='HISTORICAL_UNVERIFIED',source_authenticated=False,
        obligations=rows,blockers=proof['blockers'],unknowns=proof['unknowns'])
    if mode=='json':out=reports._bytes(result)
    else:
        text=('CGCCHILD imported analysis report\n'
              'Saved proof re-evaluated as IMPORTED; source authenticated: false\n'
              'Imported verdict: '+proof['safe_to_resume']+'\n'
              'Current repository safety: UNKNOWN; authority: NONE; mutation authorized: false\n'
              'Execution: NO_ACCEPTED_EXECUTION_ADAPTER\n'+
              ''.join(row['id']+': '+row['status']+' ('+row['plane']+')\n' for row in rows))
        out=text.encode('ascii')
    if len(out)>MAX_OUTPUT:raise reports.ReportError()
    return out


def serve(reader,writer,mode):
    try:
        raw=reader.read(reports.MAX_BYTES+1)
        if type(raw) is not bytes or len(raw)>reports.MAX_BYTES:raise reports.ReportError()
        out=transform(raw,mode)
        if writer.write(out)!=len(out):return 2
        writer.flush();return 0
    except RuntimeError as error:
        return 3 if str(error)=='UNSUPPORTED_REPORT_VERIFIER_PLATFORM' else 2
    except (ValueError,TypeError,OSError):return 2


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=1 or args[0] not in ('json','text'):code=2
    else:code=serve(sys.stdin.buffer,sys.stdout.buffer,args[0])
    if code:
        try:
            sys.stderr.buffer.write(b'CGCCHILD_REPORT_PLATFORM_UNAVAILABLE\n' if code==3 else b'CGCCHILD_REPORT_STATUS_REFUSED\n')
            sys.stderr.buffer.flush()
        except OSError:pass
    return code


if __name__=='__main__':raise SystemExit(main())
