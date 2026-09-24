"""Native fixed EXTERNAL transcript vectors; no authentication or bus connection."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    uids=[0,1,62001,4294967294]
    positive=[b'OK 0123456789abcdef0123456789abcdef\r\n',b'OK ABCDEF0123456789ABCDEF0123456789\r\n']
    lines=list(positive)
    lines += [b'',b'REJECTED EXTERNAL\r\n',b'DATA 00\r\n',b'AGREE_UNIX_FD\r\n',b'OK '+b'0'*33+b'\r\n',
              positive[0]+b'\0',positive[0]+positive[1],b'OK '+b'g'*32+b'\r\n',b'x'*65]
    lines += [positive[0][:i] for i in range(37)]
    lines += [positive[0][:i]+bytes([positive[0][i]^128])+positive[0][i+1:] for i in range(37)]
    assert len(lines)==85
    header=[];rows=[]
    for i,uid in enumerate(uids):
        raw=b'\0AUTH EXTERNAL '+str(uid).encode().hex().encode()+b'\r\n'
        header.append('static const unsigned char uid_%d[]={%s};'%(i,','.join(map(str,raw))))
        rows.append('{%dUL,uid_%d,%d}'%(uid,i,len(raw)))
    header.append('static const struct uid_vector uids[]={'+','.join(rows)+'};')
    rows=[]
    for i,raw in enumerate(lines):
        good=re.fullmatch(rb'OK [0-9a-fA-F]{32}\r\n',raw) is not None
        assert good==(i<2)
        header.append('static const unsigned char line_%d[]={%s};'%(i,','.join(map(str,raw)) or '0'))
        rows.append('{line_%d,%d,%d}'%(i,len(raw),good))
    header.append('static const struct line_vector lines[]={'+','.join(rows)+'};')
    generated=('\n'.join(header)+'\n').encode()
    here=Path(__file__).resolve().parent;source=(here/'child_dbus_auth.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-auth-',dir='/tmp') as temp:
        root=Path(temp);(root/'fixture.c').write_bytes(source);(root/'auth_vectors.h').write_bytes(generated)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      generated_header_sha256=digest(generated),image_sha256=digest((root/'fixture').read_bytes()),
                      argv=argv,compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,line_vectors=len(lines),positive=2,negative=len(lines)-2,
                      split_runs=sum(len(raw)+1 for raw in lines),bytewise_positive=True,
                      uid_vectors=uids,uid_capacity_cases=sum(18+2*len(str(uid)) for uid in uids),
                      terminal_refusals=True,returncode=0,syscall_sites=1,
                      corpus=[dict(bytes=raw.hex(),accepted=i<2) for i,raw in enumerate(lines)],
                      scope='inert native transcript codec; encoded is not sent, GUID not identity, no transport or authentication acceptance')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
