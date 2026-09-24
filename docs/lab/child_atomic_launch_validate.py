"""Nonroot clone3 capability only; compiled in owned /tmp and removed."""
import hashlib,json,os,re,signal,subprocess,tempfile
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent;source=(here/'child_atomic_launch.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-atomic-launch-',dir='/tmp') as temp:
        root=Path(temp);(root/'fixture.c').write_bytes(source)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        subprocess.run(argv,cwd=root,check=True,capture_output=True,timeout=30)
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        codes=[]
        for _ in range(3):
            proc=subprocess.Popen([str(root/'fixture')],cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:out,err=proc.communicate(timeout=6)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=2);raise
            assert not out and not err and proc.returncode in (0,77,78,79),(proc.returncode,out,err)
            codes.append(proc.returncode)
        assert len(set(codes))==1
        outcome={0:'OWNED_ATOMIC_PIDFD_LAUNCH_OBSERVED',77:'ENOSYS_UNAVAILABLE',78:'EPERM_UNAVAILABLE',79:'OTHER_LAUNCH_ERROR_UNRESOLVED'}[codes[0]]
        evidence=dict(source_sha256=sha(source),driver_sha256=sha(Path(__file__).read_bytes()),image_sha256=sha((root/'fixture').read_bytes()),
          compiler=subprocess.check_output(['gcc','--version'],timeout=5).decode().splitlines()[0],kernel=os.uname().release,
          compile_argv=argv,runs=codes,result=outcome,syscalls=[0,1,3,7,60,61,72,102,157,293,435,436],
          clone_args=dict(flags=4096,exit_signal=17,all_other_fields_zero_except_pidfd_output=True),
          raw_syscall_sites=1,static_elf=True,seccomp_installed=False,production_accepted=False,r6='NOT_EXECUTED')
    evidence['temporary_cleanup']='REMOVED'
    print(json.dumps(evidence,sort_keys=True,indent=2))

if __name__=='__main__':main()
