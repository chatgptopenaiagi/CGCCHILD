"""Finite synthetic owner/serial binding; never connects to a bus."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest
from child_dbus_owner_validate import response
from m4_validate import frame


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    owners=[':1.42',':1.777',':123.456',':1.'+'7'*252]
    output=[];rows=[];capacity_cases=0
    def packet(name,raw):
        output.append('static const unsigned char '+name+'[]={'+','.join(map(str,raw))+'};')
        return '{'+name+','+str(len(raw))+'}'
    for i,owner in enumerate(owners):
        hello=packet('h'+str(i),response(1,':1.100'));bound=packet('o'+str(i),response(2,owner))
        requests=[];replies=[]
        for serial in range(3,9):
            fields=[(1,'o','/org/freedesktop/systemd1'),(2,'s','org.freedesktop.DBus.Properties'),
                    (3,'s','Get'),(6,'s',owner),(8,'g','ss')]
            raw=frame(1,serial,fields,'ss',['org.freedesktop.systemd1.Manager','Version'],flags=2)
            capacity_cases+=len(raw)
            requests.append(packet('q%d_%d'%(i,serial),raw))
            replies.append(packet('r%d_%d'%(i,serial),response(serial,['s','259'],owner,'v')))
        rows.append('{'+hello+','+bound+',{'+','.join(requests)+'},{'+','.join(replies)+'}}')
    output.append('static const struct fixture fixtures[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode()
    files={name:(here/name).read_bytes() for name in ('child_dbus_query_binding.c','child_dbus_model_queries.c')}
    prefixes={'decoder.h':(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0],
              'owner.h':(here/'child_dbus_owner.c').read_bytes().split(b'struct step {',1)[0],
              'encoder.h':(here/'child_dbus_encode.c').read_bytes().split(b'struct vector {',1)[0]}
    with tempfile.TemporaryDirectory(prefix='cgcchild-query-binding-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in {**files,**prefixes,'binding_vectors.h':generated}.items():(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack',*files,'-o','fixture']
        built=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if built.returncode:raise RuntimeError(built.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'Advanced Micro Devices X86-64' in elf
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0 and not run.stdout and not run.stderr,run.returncode
        evidence=dict(sources_sha256={k:digest(v) for k,v in files.items()},driver_sha256=digest(Path(__file__).read_bytes()),
            prefixes_sha256={k:digest(v) for k,v in prefixes.items()},generated_header_sha256=digest(generated),
            image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
            compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),kernel=os.uname().release,
            owners=owners,query_serials=list(range(3,9)),positive_queries=24,capacity_refusals=capacity_cases,
            invalid_model_cases=18,request_limit_refusals=4,returncode=0,syscall_sites=1,
            syscall_contract={'102':'refuse root','60':'exit'},
            scope='inert native model owner/serial binding; no socket, live manager, caller authentication or production acceptance')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
