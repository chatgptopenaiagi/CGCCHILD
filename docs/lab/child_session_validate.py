"""Fixed native two-process admission MODEL session; no privileged effects."""
import json,os,re,struct,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest,OPS
from child_lifecycle_validate import packet,reply,EPOCH
from m4_validate import eq,le,rule,union,generate,interpret,ALLOW,DENY,KILL


def filters():
    bound=0x12345678;end=(rule(60,le(0,255)),)
    common=union(end,tuple(rule(3,eq(0,fd)) for fd in range(3,64)),
                 tuple(rule(7,eq(1,1),eq(2,t)) for t in (0,2000)))
    controller=union(common,(rule(46,eq(0,3),eq(2,0)),rule(47,eq(0,3),eq(2,0x40000040)),
                            rule(0,eq(0,5),eq(2,1))))
    sealed=union(common,(rule(46,eq(0,4),eq(2,0)),rule(47,eq(0,4),eq(2,0x40000040)),
                         rule(61,eq(0,bound),eq(2,0)),rule(72,(0,3,63),eq(1,1)),
                         rule(1,eq(0,1),eq(2,32))))
    opened=union(sealed,(rule(1,eq(0,6),eq(2,1)),rule(317,eq(0,1),eq(1,0))))
    assert set(sealed)<set(opened)
    tables={'controller_filter':controller,'broker_open':opened,'broker_sealed':sealed}
    header=[];bindings=[];evidence={}
    for name,rules in sorted(tables.items()):
        code=generate(rules);assert code==generate(tuple(reversed(rules))) and len(code)<=4096
        assert interpret(code,1,arch=0x40000003)==KILL and interpret(code,0x40000001)==KILL
        for nr in (59,41,57,101):assert interpret(code,nr)==DENY
        for nr,predicates in rules:
            args=[0]*6
            for index,low,high in predicates:args[index]=low
            assert interpret(code,nr,args)==ALLOW
        positions=[i for i,x in enumerate(code) if x[0]==0x15 and x[3]==bound]
        header.append('static struct ins '+name+'_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};')
        header.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        bindings+=['{'+name+'_code,'+str(i)+'}' for i in positions]
        evidence[name]=dict(rules=rules,instructions=code,pid_relocations=positions,
                           template_sha256=digest(b''.join(struct.pack('<HBBI',*x) for x in code)))
    assert len(bindings)==2
    header.append('static struct {struct ins *code;unsigned int index;} bindings[]={'+','.join(bindings)+'};')
    return ('\n'.join(header)+'\n').encode(),evidence


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    lifecycle=(here/'child_lifecycle.c').read_bytes().split(b'struct step {',1)[0]
    ancillary=(here/'child_ancillary.c').read_bytes()
    socket_types=b'struct iov {'+ancillary.split(b'struct iov {',1)[1].split(b'static const char packet[]',1)[0]
    header=[];rows=[]
    for i in range(6):
        raw=packet(OPS[i] if i<5 else OPS[0],i+1,EPOCH if i>=3 else '0')
        response=reply(raw) if i<5 else b''
        for name,data in [('request',raw),('reply',response)]:
            header.append('static const unsigned char %s_%d[]={%s};'%(name,i,','.join(map(str,data)) or '0'))
        rows.append('{request_%d,reply_%d,%d,%d}'%(i,i,len(raw),len(response)))
    header.append('static const struct packet_vector packets[]={'+','.join(rows)+'};')
    vectors=('\n'.join(header)+'\n').encode();generated,filter_evidence=filters()
    source=(here/'child_session.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-session-',dir='/tmp') as temp:
        root=Path(temp)
        for name,data in [('payload.h',payload),('lifecycle.h',lifecycle),('socket_types.h',socket_types),
                          ('session_vectors.h',vectors),('session_filters.h',generated),('fixture.c',source)]:
            (root/name).write_bytes(data)
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
        assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
        assert len(run.stdout)==32
        values=[int.from_bytes(run.stdout[i:i+8],'little') for i in (0,8,16,24)]
        assert values==[6,5,1,1],values
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),lifecycle_prefix_sha256=digest(lifecycle),
                      socket_types_sha256=digest(socket_types),vectors_sha256=digest(vectors),
                      filter_header_sha256=digest(generated),filter_tables=filter_evidence,
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,returncode=0,requests=6,canonical_replies=5,
                      closed_state_refusal=1,exact_child_reaped=True,final_fds_3_to_63_empty=True,
                      monotonic_edge='broker_open -> broker_sealed',syscall_sites=1,
                      scope='owned nonroot native admission MODEL session; real socket credentials/pidfds, synthetic generations/continuity/empty; effects only counters')
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
