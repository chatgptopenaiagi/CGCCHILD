"""Two owned scalar launches and separate handle lifecycles; compiled in owned /tmp and removed."""
import hashlib,json,os,re,signal,subprocess,tempfile,struct
from m4_validate import eq,le,rule,union,generate,interpret,ALLOW,DENY,KILL
from pathlib import Path

def sha(raw):return hashlib.sha256(raw).hexdigest()

def filters():
    end=(rule(60,le(0,255)),)
    polls=tuple(rule(7,eq(1,1),eq(2,t)) for t in (0,2000))
    inventory=(rule(72,(0,3,63),eq(1,1)),)
    close=tuple(rule(3,eq(0,fd)) for fd in range(3,9))
    controller=union(end,polls,inventory,tuple(rule(3,eq(0,fd)) for fd in range(3,7)),(rule(0,eq(0,3),eq(2,1)),))
    worker=union(end,polls,inventory,tuple(rule(3,eq(0,fd)) for fd in range(3,8)),(rule(0,eq(0,5),eq(2,1)),))
    parent=union(end,polls,inventory,close,tuple(rule(1,eq(0,fd),eq(2,1)) for fd in (4,6)),
       tuple(rule(247,eq(0,3),eq(1,fd),eq(3,4),eq(4,0)) for fd in (7,8)))
    boot=union(controller,worker,parent,(rule(56,eq(0,0x1011),eq(1,0),eq(3,0),eq(4,0),eq(5,0)),rule(317,eq(0,1),eq(1,0))))
    assert all(set(x)<set(boot) for x in (controller,worker,parent))
    lines=[];evidence={}
    for name,rules in sorted(dict(boot=boot,controller=controller,worker=worker,parent=parent).items()):
        code=generate(rules);assert code==generate(tuple(reversed(rules))) and len(code)<=4096
        for nr,predicates in rules:
            args=[0]*6
            for i,low,high in predicates:args[i]=low
            assert interpret(code,nr,args)==ALLOW
        assert interpret(code,435)==DENY and interpret(code,0x40000001)==KILL
        assert interpret(code,60,arch=0x40000003)==KILL
        lines.append('static struct ins '+name+'_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};')
        lines.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        evidence[name]=dict(rules=rules,instructions=code,sha256=sha(b''.join(struct.pack('<HBBI',*row) for row in code)))
    return ('\n'.join(lines)+'\n').encode(),evidence

def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent;source=(here/'child_dual_launch.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-dual-launch-',dir='/tmp') as temp:
        root=Path(temp);(root/'fixture.c').write_bytes(source)
        header,tables=filters();(root/'filters.h').write_bytes(header)
        argv=['gcc','-DRELEASE_FIRST=0','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        subprocess.run(argv,cwd=root,check=True,capture_output=True,timeout=30)
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        codes=[];images=[]
        for order in (0,1):
            build=argv.copy();build[1]='-DRELEASE_FIRST='+str(order)
            subprocess.run(build,cwd=root,check=True,capture_output=True,timeout=30)
            images.append(sha((root/'fixture').read_bytes()))
            dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
            assert len(re.findall(r'\bsyscall\b',dis))==1
            start=dis.split('<_start>:',1)[1]
            assert re.search(r'and\s+\$0xfffffffffffffff0,%rsp',start) and 'entry>' in start
            for _ in range(3):
                proc=subprocess.Popen([str(root/'fixture')],cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
                try:out,err=proc.communicate(timeout=6)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=2);raise
                assert not out and not err and proc.returncode==0,(proc.returncode,out,err)
                codes.append(proc.returncode)
        assert len(set(codes))==1
        outcome={0:'OWNED_ATOMIC_PIDFD_LAUNCH_OBSERVED',77:'ENOSYS_UNAVAILABLE',78:'EPERM_UNAVAILABLE',79:'OTHER_LAUNCH_ERROR_UNRESOLVED'}[codes[0]]
        evidence=dict(source_sha256=sha(source),driver_sha256=sha(Path(__file__).read_bytes()),image_sha256=images,
          compiler=subprocess.check_output(['gcc','--version'],timeout=5).decode().splitlines()[0],kernel=os.uname().release,
          compile_argv=argv,runs=codes,result=outcome,syscalls=[0,1,3,7,56,60,72,102,157,247,293,317,436],
          clone_scalar=dict(flags=4113,stack=0,child_tid=0,tls=0,pidfd_parent_output=True),filter_tables=tables,filter_header_sha256=sha(header),filter_evidence=dict(generator_sha256=sha((here/'m4_validate.py').read_bytes())),
          raw_syscall_sites=1,static_elf=True,seccomp_installed=True,production_accepted=False,r6='NOT_EXECUTED')
    evidence['temporary_cleanup']='REMOVED'
    print(json.dumps(evidence,sort_keys=True,indent=2))

if __name__=='__main__':main()
