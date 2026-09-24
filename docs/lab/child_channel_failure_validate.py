"""Fixed native three-process channel/effect fixture; no privileged effects."""
import json,os,re,struct,subprocess,tempfile,signal
from pathlib import Path
from child_protocol_validate import digest,OPS
from child_lifecycle_validate import packet,reply,EPOCH
from m4_validate import eq,le,rule,union,generate,interpret,ALLOW,DENY,KILL


def filters():
    common=union((rule(60,le(0,255)),rule(72,(0,3,63),eq(1,1)),rule(72,(0,3,12),eq(1,3)),rule(5,(0,3,12))),
       tuple(rule(3,eq(0,fd)) for fd in range(3,64)),tuple(rule(7,eq(1,1),eq(2,t)) for t in (0,2000)))
    controller=union(common,(rule(46,eq(0,3),eq(2,0)),rule(47,eq(0,3),eq(2,0x40000040))))
    worker=union(common,(rule(0,eq(0,6),eq(2,1)),))
    sealed=union(common,(rule(46,eq(0,4),eq(2,0)),rule(47,eq(0,4),eq(2,0x40000040)),rule(1,eq(0,7),eq(2,1)),
       rule(263,eq(0,10),eq(2,0)),rule(263,eq(0,8),eq(2,512))),
       tuple(rule(247,eq(0,3),eq(1,fd),eq(3,4),eq(4,0)) for fd in (9,12)))
    boot=union(controller,worker,sealed,(rule(56,eq(0,0x1011),eq(1,0),eq(3,0),eq(4,0),eq(5,0)),rule(317,eq(0,1),eq(1,0)),
       rule(258,eq(0,8),eq(2,0o700)),rule(257,eq(0,8),eq(2,0xb0000),eq(3,0)),
       rule(257,eq(0,10),eq(2,0xa00c2),eq(3,0o600)),rule(1,eq(0,11),(2,1,20)),rule(17,eq(0,11),(2,1,20),eq(3,0))))
    assert all(set(x)<set(boot) for x in (controller,worker,sealed))
    header=[];evidence={}
    for name,rules in sorted(dict(controller_filter=controller,worker_filter=worker,broker_boot=boot,broker_sealed=sealed).items()):
        code=generate(rules);assert code==generate(tuple(reversed(rules))) and len(code)<=4096
        assert interpret(code,1,arch=0x40000003)==KILL and interpret(code,0x40000001)==KILL
        for nr in (59,41,57,101,434,435):assert interpret(code,nr)==DENY
        for nr,predicates in rules:
            args=[0]*6
            for index,low,high in predicates:args[index]=low
            assert interpret(code,nr,args)==ALLOW
        header.append('static struct ins '+name+'_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};')
        header.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        evidence[name]=dict(rules=rules,instructions=code,sha256=digest(b''.join(struct.pack('<HBBI',*x) for x in code)))
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
    source=(here/'child_channel_failure.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-channel-failure-',dir='/tmp') as temp:
        root=Path(temp)
        for name,data in [('payload.h',payload),('lifecycle.h',lifecycle),('socket_types.h',socket_types),
                          ('session_vectors.h',vectors),('session_filters.h',generated),('fixture.c',source)]:
            (root/name).write_bytes(data)
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
        runs=[]
        for selected in range(3):
            cwd=root/str(selected);cwd.mkdir()
            if selected==0:(cwd/'domain').mkdir();(cwd/'domain'/'owner-material').write_bytes(b'untouched')
            proc=subprocess.Popen([str(root/'fixture'),str(selected)],cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:out,err=proc.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.communicate(timeout=2);raise
            assert proc.returncode==0 and not out and not err,(proc.returncode,out,err)
            if selected==0:
                assert sorted(p.name for p in (cwd/'domain').iterdir())==['owner-material']
                assert (cwd/'domain'/'owner-material').read_bytes()==b'untouched'
            else:assert not (cwd/'domain').exists()
            runs.append(proc.returncode)
        evidence=dict(preprocessed_sha256=digest(preprocessed),fd_identity_preflight=True,runs=runs,source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),lifecycle_prefix_sha256=digest(lifecycle),
                      socket_types_sha256=digest(socket_types),vectors_sha256=digest(vectors),
                      filter_header_sha256=digest(generated),filter_tables=filter_evidence,
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,returncode=0,positive_requests=6,positive_canonical_replies=5,failure_cases=['create_collision','attach_ebadf'],
                      closed_state_refusal=1,exact_child_reaped=True,final_fds_3_to_63_empty=True,
                      monotonic_edge='broker_boot -> broker_sealed/controller_filter/worker_filter',syscall_sites=1,
                      scope='owned FD-bound filtered channel plus inert regular-file effects; synthetic generations/continuity, no cgroup authority',filter_evidence=dict(generator_sha256=digest((here/'m4_validate.py').read_bytes())))
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
