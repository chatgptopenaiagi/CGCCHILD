"""Owned fork-launched sender/pidfd mechanical binding, no privileged/R6 boundary."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest



def filters():
    from m4_validate import eq,le,rule,union,generate,interpret,ALLOW,DENY,KILL
    import struct
    bound=0x12345678
    end=(rule(60,le(0,255)),)
    sender=union(end,(rule(46,eq(0,3),eq(2,0)),rule(0,eq(0,5),eq(2,1))),
                 tuple(rule(3,eq(0,fd)) for fd in (3,5)))
    drain=union(end,(rule(47,eq(0,4),eq(2,0x40000040)),
                    rule(1,eq(0,1),eq(2,32)),rule(72,(0,3,63),eq(1,1))),
                tuple(rule(7,eq(1,1),eq(2,t)) for t in (0,2000)),
                tuple(rule(3,eq(0,fd)) for fd in range(3,64)))
    live=union(drain,(rule(1,eq(0,6),eq(2,1)),rule(3,eq(0,6)),
                      rule(61,eq(0,bound),eq(2,0)),rule(317,eq(0,1),eq(1,0))))
    assert set(drain)<set(live)
    sender=union(sender,tuple(rule(5,eq(0,fd)) for fd in (3,5)),tuple(rule(72,eq(0,fd),eq(1,op)) for fd in (3,5) for op in (1,3)))
    observations=union(tuple(rule(5,eq(0,fd)) for fd in (3,4,6)),tuple(rule(72,eq(0,fd),eq(1,3)) for fd in (3,4,6)))
    drain=union(drain,observations);live=union(live,observations)
    assert set(drain)<set(live)
    tables={'receiver_drain':drain,'receiver_live':live,'sender_filter':sender}
    header=[];bindings=[];evidence={}
    for name,rules in sorted(tables.items()):
        code=generate(rules)
        assert code==generate(tuple(reversed(rules))) and len(code)<=4096
        assert interpret(code,1,arch=0x40000003)==KILL
        assert interpret(code,0x40000001)==KILL
        for nr in (59,41,435,272,101,57,322):assert interpret(code,nr)==DENY
        for nr,preds in rules:
            args=[0]*6
            for index,low,high in preds:args[index]=low
            assert interpret(code,nr,args)==ALLOW
        positions=[i for i,x in enumerate(code) if x[0]==0x15 and x[3]==bound]
        for pid in (1,4242,0x7fffffff):
            patched=[list(row) for row in code]
            for index in positions:patched[index][3]=pid
            if name=='receiver_live':
                assert interpret(patched,61,(pid,0,0))==ALLOW
                assert interpret(patched,61,(pid+1,0,0))==DENY
        header.append('static struct ins '+name+'_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};')
        header.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        bindings+=['{'+name+'_code,'+str(i)+'}' for i in positions]
        evidence[name]=dict(rules=rules,instructions=code,pid_relocations=positions,
                           template_sha256=digest(b''.join(struct.pack('<HBBI',*x) for x in code)))
    assert len(bindings)==1
    header.append('static struct {struct ins *code;unsigned int index;} bindings[]={'+','.join(bindings)+'};')
    return ('\n'.join(header)+'\n').encode(),evidence


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    ancillary=(here/'child_ancillary.c').read_bytes()
    for marker in (b'struct iov {',b'static int inventory(',b'static int ancillary(',b'static int exchange('):
        assert ancillary.count(marker)==1
    receive=ancillary.split(b'struct iov {',1)[1].split(b'static int inventory(',1)[0]
    receive=b'struct iov {'+receive
    source=(here/'child_fd_identity.c').read_bytes()
    generated,filter_evidence=filters()
    with tempfile.TemporaryDirectory(prefix='cgcchild-fd-identity-',dir='/tmp') as temp:
        root=Path(temp)
        for name,data in (('payload.h',payload),('receive.h',receive),('fixture.c',source),('sender_filters.h',generated)):(root/name).write_bytes(data)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
              '-fno-stack-protector','-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie',
              '-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        build=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if build.returncode:raise RuntimeError(build.stderr.decode())
        preprocessed=subprocess.check_output(['gcc','-std=c11','-E','-P','fixture.c'],cwd=root,timeout=10)
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stderr)
        assert len(run.stdout)==32
        values=[int.from_bytes(run.stdout[i:i+8],'little') for i in (0,8,16,24)]
        assert values==[5,48,21,64],values
        evidence=dict(preprocessed_sha256=digest(preprocessed),fd_identity_checks=True,substitution_refusals=5,source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),receive_prefix_sha256=digest(receive),
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,returncode=0,messages=5,received_rights_closed=48,maximum_received_fd=21,owned_nofile_limit=64,
                      live_sender_accepted=1,connection_identity_differs=1,dead_queued_message_refused=1,
                      exact_child_reaped=True,closed_pidfd_poll_refused=True,final_fds_3_to_63_empty=True,syscall_sites=1,
                      filter_tables=filter_evidence,generated_filter_header_sha256=digest(generated),
                      monotonic_edge='receiver_live -> receiver_drain',
                      scope='owned filtered type/access/dev-inode binding and substitution refusal; creation-bound pidfd; no filesystem exclusivity or R6')
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
