"""Native owned-socketpair ancillary validation, never privileged broker/R6 execution."""
import hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    source=(here/'child_ancillary.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-ancillary-',dir='/tmp') as temp:
        root=Path(temp);(root/'payload.h').write_bytes(payload);(root/'fixture.c').write_bytes(source)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
              '-fno-stack-protector','-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie',
              '-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        build=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if build.returncode:raise RuntimeError(build.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stderr)
        assert len(run.stdout)==24
        values=[int.from_bytes(run.stdout[i:i+8],'little') for i in (0,8,16)]
        assert values==[38,513,22],values
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),image_sha256=digest((root/'fixture').read_bytes()),
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,argv=argv,returncode=0,
                      received_messages=values[0],explicitly_closed_received_fds=values[1],
                      maximum_received_fd=values[2],syscall_sites=1,
                      cases=['valid own credentials and payload','wrong expected PID','one received FD closed',
                             'payload truncation','ancillary truncation','missing credentials',
                             '32 iterations of16 received FDs closed with CLOEXEC'],
                      scope='same-process owned unnamed socketpair; no independent caller authentication or R6')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
