"""Model-bound outgoing encoding composed with filtered private socket transport."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest
from child_dbus_owner_validate import response,owner_signal
from m4_validate import frame


from child_dbus_filtered_socket_validate import filters


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    bus='org.freedesktop.DBus'
    def request(serial,path,interface,member,destination,signature,body):
        fields=[(1,'o',path),(2,'s',interface),(3,'s',member),(6,'s',destination)]
        if signature:fields.append((8,'g',signature))
        return frame(1,serial,fields,signature,body,flags=2)
    values={
      'auth_request':b'\0AUTH EXTERNAL 3632303031\r\n',
      'auth_reply':b'OK 0123456789abcdef0123456789abcdef\r\n',
      'request_hello':request(1,'/org/freedesktop/DBus',bus,'Hello',bus,'',[]),
      'request_owner':request(2,'/org/freedesktop/DBus',bus,'GetNameOwner',bus,'s',['org.freedesktop.systemd1']),
      'reply_hello':response(1,':1.100')}
    owners=[':1.42',':1.777',':123.456',':1.'+'7'*252]
    cases=[];queries=[];bound_replies=[]
    for owner_index,owner in enumerate(owners):
        query=request(3,'/org/freedesktop/systemd1','org.freedesktop.DBus.Properties','Get',owner,'ss',['org.freedesktop.systemd1.Manager','Version'])
        bound=response(2,owner);version=response(3,['s','259'],owner,'v')
        variants=[('valid',version,1,0),('wrong_owner',response(3,['s','259'],':9.9','v'),0,0),
                  ('changed_owner',owner_signal(owner,':9.9'),0,0),('duplicate',version+version,0,0),
                  ('partial_eof',version[:-1],1,1),('complete_then_eof',version,1,1),
                  ('wrong_serial',response(2,['s','259'],owner,'v'),0,0)]
        for name,raw,accepted,eof in variants:
            cases.append(('owner%d_'%owner_index+name,raw,accepted,eof));queries.append(query);bound_replies.append(bound)
    output=[];rows=[]
    for name,raw in values.items():output.append('static const unsigned char '+name+'[]={'+','.join(map(str,raw))+'};')
    for i,(_,raw,accepted,eof) in enumerate(cases):
        output.append('static const unsigned char case_%d[]={%s};'%(i,','.join(map(str,raw))))
        output.append('static const unsigned char owner_%d[]={%s};'%(i,','.join(map(str,bound_replies[i]))))
        output.append('static const unsigned char query_%d[]={%s};'%(i,','.join(map(str,queries[i]))))
        rows.append('{owner_%d,%d,query_%d,%d,case_%d,%d,%d,%d}'%(i,len(bound_replies[i]),i,len(queries[i]),i,len(raw),accepted,eof))
    output.append('static const struct fixture fixtures[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode();here=Path(__file__).resolve().parent
    source=(here/'child_dbus_bound_socket.c').read_bytes()
    filter_header,filter_evidence=filters()
    encoder_source=(here/'child_dbus_model_queries.c').read_bytes()
    prefixes={
      'binding.h':(here/'child_dbus_query_binding.c').read_bytes().split(b'struct packet {',1)[0].replace(b'#include "owner.h"',b''),
      'encoder.h':(here/'child_dbus_encode.c').read_bytes().split(b'struct vector {',1)[0],
      'decoder.h':(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0],
      'owner.h':(here/'child_dbus_owner.c').read_bytes().split(b'struct step {',1)[0],
      'auth.h':(here/'child_dbus_auth.c').read_bytes().split(b'struct uid_vector {',1)[0],
      'connection.h':(here/'child_dbus_connection.c').read_bytes().split(b'struct step {',1)[0]}
    with tempfile.TemporaryDirectory(prefix='cgcchild-dbus-bound-' ,dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('queries.c',encoder_source),('socket_vectors.h',generated),('io_filter.h',filter_header),*prefixes.items()]:(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','queries.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'Advanced Micro Devices X86-64' in elf
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        for selector in range(56):
            run=subprocess.run([str(root/'fixture'),str(selector)],cwd=root,capture_output=True,timeout=5)
            assert run.returncode==0,(selector,run.returncode,run.stdout,run.stderr)
        for args in ([],['56'],['00'],['-1'],['x'],['0','extra']):
            run=subprocess.run([str(root/'fixture'),*args],cwd=root,capture_output=True,timeout=5)
            assert run.returncode==2 and not run.stdout and not run.stderr

        evidence=dict(source_sha256=digest(source),query_source_sha256=digest(encoder_source),
            filter_driver_sha256=digest((here/'child_dbus_filtered_socket_validate.py').read_bytes()),driver_sha256=digest(Path(__file__).read_bytes()),
            prefixes_sha256={k:digest(v) for k,v in prefixes.items()},generated_header_sha256=digest(generated),
            image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
            compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),kernel=os.uname().release,
            scenarios=[c[0] for c in cases],fragment_sizes=[1,17],scenario_runs=len(cases)*2,
            native_encoded_queries_per_run=3,owners=owners,capacity_refusals_total=2*sum(len(values['request_hello'])+len(values['request_owner'])+len(q) for q in queries),
            unknown_encoder_selectors_refused_per_run=3,canonical_version_query_digests=sorted(set(digest(q) for q in queries)),
            no_child_process=True,nonblocking=True,empty_read_eagain=True,fd_inventory_empty_after_each=True,
            filter_evidence=filter_evidence,filter_installs=56,denial_probes_per_install=18,invalid_selectors_refused=6,
            generated_filter_header_sha256=digest(filter_header),
            syscall_contract={'0':'owned endpoint read','3':'close owned endpoints','44':'sendto MSG_NOSIGNAL with no address',
              '53':'AF_UNIX STREAM NONBLOCK CLOEXEC socketpair','60':'exit','72':'FD/access flags and empty inventory',
              '102':'refuse root via getuid','436':'fixture prelude close inherited FDs3+',
              '157':'trusted setup NNP, denied afterward','317':'trusted setup filter install, denied afterward'},
            denial_probe_syscalls=[0,3,41,44,53,57,59,72,101,157,272,317,322,435,436],
            returncode=0,syscall_sites=1,scope='native model-bound encoder plus kernel-filtered private dummy byte transport; no live D-Bus, role separation, privileged controller or production acceptance')
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
