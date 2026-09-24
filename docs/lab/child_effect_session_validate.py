"""Protocol/effect ordering on owned inert files; no cgroup or privileged operation."""
import json,os,re,signal,struct,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest,OPS
from child_lifecycle_validate import packet,reply,EPOCH
from m4_validate import eq,le,rule,union,generate,interpret,ALLOW,DENY,KILL


def filters():
    bound=0x12345678;end=(rule(60,le(0,255)),)
    sealed=union(end,(rule(1,eq(0,6),eq(2,1)),rule(61,eq(0,bound),eq(2,0)),
                      rule(263,eq(0,3),eq(2,0)),rule(84)),
                 tuple(rule(7,eq(1,1),eq(2,t)) for t in (0,2000)),
                 tuple(rule(3,eq(0,fd)) for fd in (3,5,6,7)))
    boot=union(sealed,(rule(434,eq(0,bound),eq(1,0)),rule(0,eq(0,7),eq(2,1)),
                      rule(1,eq(0,4),(2,1,20)),rule(17,eq(0,4),(2,1,20),eq(3,0)),
                      rule(3,eq(0,4)),rule(317,eq(0,1),eq(1,0))))
    worker=union(end,(rule(1,eq(0,8),eq(2,1)),rule(0,eq(0,5),eq(2,1)),
                       rule(7,eq(1,1),eq(2,2000)),rule(3,eq(0,5)),rule(3,eq(0,8))))
    assert set(sealed)<set(boot)
    header=[];bindings=[];evidence={}
    for name,rules in sorted({'b_boot':boot,'b_sealed':sealed,'w_filter':worker}.items()):
        code=generate(rules);assert code==generate(tuple(reversed(rules))) and len(code)<=4096
        assert interpret(code,59)==DENY and interpret(code,0x40000001)==KILL
        assert interpret(code,1,arch=0x40000003)==KILL
        for nr,predicates in rules:
            args=[0]*6
            for index,low,high in predicates:args[index]=low
            assert interpret(code,nr,args)==ALLOW
        positions=[i for i,x in enumerate(code) if x[0]==0x15 and x[3]==bound]
        for pid in (1,4242,0x7fffffff):
            patched=[list(row) for row in code]
            for index in positions:patched[index][3]=pid
            if name.startswith('b_'):
                assert interpret(patched,61,(pid,0,0))==ALLOW and interpret(patched,61,(pid+1,0,0))==DENY
        header.append('static struct ins '+name+'_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};')
        header.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        bindings+=['{'+name+'_code,'+str(i)+'}' for i in positions]
        evidence[name]=dict(rules=rules,instructions=code,pid_relocations=positions,
                           template_sha256=digest(b''.join(struct.pack('<HBBI',*x) for x in code)))
    assert len(bindings)==3
    header.append('static struct {struct ins *code;unsigned int index;} bindings[]={'+','.join(bindings)+'};')
    return ('\n'.join(header)+'\n').encode(),evidence


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent;output=[];rows=[]
    for i in range(5):
        raw=packet(OPS[i],i+1,EPOCH if i>=3 else '0');answer=reply(raw)
        for name,data in [('request',raw),('reply',answer)]:output.append('static const unsigned char %s_%d[]={%s};'%(name,i,','.join(map(str,data))))
        rows.append('{request_%d,reply_%d,%d,%d}'%(i,i,len(raw),len(answer)))
    output.append('static const struct packet_vector packets[]={'+','.join(rows)+'};')
    vectors=('\n'.join(output)+'\n').encode();filter_header,filter_evidence=filters()
    source=(here/'child_effect_session.c').read_bytes()
    payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    lifecycle=(here/'child_lifecycle.c').read_bytes().split(b'struct step {',1)[0]
    with tempfile.TemporaryDirectory(prefix='cgcchild-effects-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('payload.h',payload),('lifecycle.h',lifecycle),('effect_vectors.h',vectors),('effect_filters.h',filter_header)]:(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        built=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if built.returncode:raise RuntimeError(built.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        for selector in range(3):
            cwd=root/str(selector);cwd.mkdir()
            if selector==1:(cwd/'domain').mkdir();(cwd/'domain'/'owner-material').write_bytes(b'untouched')
            proc=subprocess.Popen([str(root/'fixture'),str(selector)],cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:out,err=proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=2);raise
            assert proc.returncode==0 and not out and not err,(selector,proc.returncode,out,err)
            if selector==1:
                assert sorted(p.name for p in (cwd/'domain').iterdir())==['owner-material']
                assert (cwd/'domain'/'owner-material').read_bytes()==b'untouched'
            else:assert not (cwd/'domain').exists()
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
            payload_prefix_sha256=digest(payload),lifecycle_prefix_sha256=digest(lifecycle),vectors_sha256=digest(vectors),
            filter_header_sha256=digest(filter_header),filter_tables=filter_evidence,image_sha256=digest((root/'fixture').read_bytes()),
            argv=argv,compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),kernel=os.uname().release,
            cases=['positive_effects_before_five_model_acks','create_collision_no_ack_no_owner_material_change','attach_closed_fd_one_ack_only'],
            exact_owned_children_reaped=2,monotonic_edge='b_boot -> b_sealed',returncode=0,syscall_sites=1,
            scope='owned inert filesystem effects and gated child, synthetic packet authentication/continuity; no cgroup or production acceptance',
            poll_errors_distinct_from_not_ready=True,
            pointer_policy='fixed trusted native literal paths; seccomp does not inspect pathname/poll-pointer contents')
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
