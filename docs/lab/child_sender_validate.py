"""Owned fork-launched sender/pidfd mechanical binding, no privileged/R6 boundary."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    ancillary=(here/'child_ancillary.c').read_bytes()
    for marker in (b'struct iov {',b'static int inventory(',b'static int ancillary(',b'static int exchange('):
        assert ancillary.count(marker)==1
    receive=ancillary.split(b'struct iov {',1)[1].split(b'static int inventory(',1)[0]
    receive=b'struct iov {'+receive+ b'static int ancillary('+ancillary.split(b'static int ancillary(',1)[1].split(b'static int exchange(',1)[0]
    source=(here/'child_sender.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-sender-',dir='/tmp') as temp:
        root=Path(temp)
        for name,data in (('payload.h',payload),('receive.h',receive),('fixture.c',source)):(root/name).write_bytes(data)
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
        assert len(run.stdout)==32
        values=[int.from_bytes(run.stdout[i:i+8],'little') for i in (0,8,16,24)]
        assert values==[2,1,1,1],values
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),receive_prefix_sha256=digest(receive),
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,returncode=0,messages=2,
                      live_sender_accepted=1,connection_identity_differs=1,dead_queued_message_refused=1,
                      exact_child_reaped=True,closed_pidfd_poll_refused=True,final_fds_3_to_63_empty=True,syscall_sites=1,
                      scope='owned gated nonroot fork child; no protected identity, atomic authorization or R6')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
