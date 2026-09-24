"""Fixed owned stdio fault responder. No child processes, files, network or authority."""
import sys

MODES={'MALFORMED','OVERSIZE','TRUNCATED','STDERR','SILENT','EXTRA_FRAME','EARLY_EXIT'}
if len(sys.argv)!=2 or sys.argv[1] not in MODES:raise SystemExit(2)
# Consume only the explicit bounded startup line and first bounded request.
if not sys.stdin.buffer.readline(16385).endswith(b'\n'):raise SystemExit(2)
if not sys.stdin.buffer.readline(8193).endswith(b'\n'):raise SystemExit(2)
mode=sys.argv[1]
try:
    if mode=='MALFORMED':sys.stdout.buffer.write(b'{}\n')
    elif mode=='OVERSIZE':sys.stdout.buffer.write(b'x'*(96*1024+1))
    elif mode=='TRUNCATED':sys.stdout.buffer.write(b'{')
    elif mode=='STDERR':sys.stderr.buffer.write(b'owned synthetic diagnostic\n');sys.stderr.buffer.flush()
    elif mode=='EXTRA_FRAME':sys.stdout.buffer.write(b'{}\n{}\n')
    elif mode=='EARLY_EXIT':raise SystemExit(3)
    else:
        # Wait only on our parent's pipe. Harness deadline closes it/terminates us.
        sys.stdin.buffer.read(1)
    sys.stdout.buffer.flush()
except (BrokenPipeError,OSError):
    pass
