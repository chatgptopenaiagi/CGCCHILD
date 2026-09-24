"""Post-setup scalar I/O policy on an owned private socketpair."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest
from child_dbus_owner_validate import response,owner_signal
from m4_validate import frame


def filters():
    import struct
    from m4_validate import eq,rule,union,generate,interpret,ALLOW,DENY,KILL
    tables=union((rule(60,(0,0,255)),rule(72,(0,3,63),eq(1,1),eq(2,0))),
      tuple(rule(0,eq(0,fd),(2,1,17)) for fd in (3,4)),
      tuple(rule(44,eq(0,fd),(2,1,17),eq(3,0x4000),eq(4,0),eq(5,0)) for fd in (3,4)),
      tuple(rule(3,eq(0,fd)) for fd in (3,4)),
      tuple(rule(72,eq(0,fd),eq(1,3),eq(2,0)) for fd in (3,4)))
    code=generate(tables)
    assert code==generate(tuple(reversed(tables))) and len(code)<=4096
    for index,(op,jt,jf,k) in enumerate(code):
        if op==5:assert index+1+k<len(code)
        elif op in (0x15,0x25,0x35,0x45):assert index+1+max(jt,jf)<len(code)
        elif op==6:assert k in (ALLOW,DENY,KILL)
        else:assert op==0x20 and k%4==0 and 0<=k<=60
    assert code[-1]==[6,0,0,DENY]
    assert interpret(code,0,arch=0x40000003)==KILL
    assert interpret(code,0x40000000)==KILL
    for nr in (41,53,57,59,101,157,272,317,322,435,436):assert interpret(code,nr)==DENY
    for nr,preds in tables:
        args=[0]*6
        for index,low,high in preds:args[index]=low
        assert interpret(code,nr,args)==ALLOW
        for index,low,high in preds:
            test=args.copy();test[index]=(1<<32)+low
            assert interpret(code,nr,test)==DENY
    for args in ((0,0,1),(3,0,0),(3,0,18)):assert interpret(code,0,args)==DENY
    for args in ((3,0,1,0,0,0),(1,0,1,0x4000,0,0),(3,0,1,0x4000,1,1)):
        assert interpret(code,44,args)==DENY
    assert interpret(code,3,(0,))==DENY
    assert interpret(code,72,(3,2,0))==DENY
    raw=b''.join(struct.pack('<HBBI',*x) for x in code)
    header='static struct ins io_code[]={'+','.join('{%d,%d,%d,%d}'%tuple(x) for x in code)+'};\n'
    header+='static struct prog io_filter={'+str(len(code))+',io_code};\n'
    return header.encode(),dict(rules=tables,instructions=code,instruction_count=len(code),
        bytes_hex=raw.hex(),sha256=digest(raw),architecture='x86_64 native only',default='ERRNO_EPERM',
        wrong_arch_x32='KILL_PROCESS_MODEL_TESTED',generator_sha256=digest(Path(__file__).with_name('m4_validate.py').read_bytes()))


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':raise SystemExit('requires nonroot x86-64 Linux')
    bus='org.freedesktop.DBus'
    def request(serial,path,interface,member,destination,signature,body):
        fields=[(1,'o',path),(2,'s',interface),(3,'s',member),(6,'s',destination)]
        if signature:fields.append((8,'g',signature))
        return frame(1,serial,fields,signature,body)
    values={
      'auth_request':b'\0AUTH EXTERNAL 3632303031\r\n',
      'auth_reply':b'OK 0123456789abcdef0123456789abcdef\r\n',
      'request_hello':request(1,'/org/freedesktop/DBus',bus,'Hello',bus,'',[]),
      'request_owner':request(2,'/org/freedesktop/DBus',bus,'GetNameOwner',bus,'s',['org.freedesktop.systemd1']),
      'request_version':request(3,'/org/freedesktop/systemd1','org.freedesktop.DBus.Properties','Get',':1.42','ss',['org.freedesktop.systemd1.Manager','Version']),
      'reply_hello':response(1,':1.100'),'reply_owner':response(2,':1.42')}
    version=response(3,['s','259'],':1.42','v')
    cases=[('valid',version,1,0),('wrong_owner',response(3,['s','259'],':1.43','v'),0,0),
           ('changed_owner',owner_signal(':1.42',':1.43'),0,0),('duplicate',version+version,0,0),
           ('partial_eof',version[:-1],1,1),('complete_then_eof',version,1,1),
           ('wrong_serial',response(2,['s','259'],':1.42','v'),0,0)]
    output=[];rows=[]
    for name,raw in values.items():output.append('static const unsigned char '+name+'[]={'+','.join(map(str,raw))+'};')
    for i,(_,raw,accepted,eof) in enumerate(cases):
        output.append('static const unsigned char case_%d[]={%s};'%(i,','.join(map(str,raw))))
        rows.append('{case_%d,%d,%d,%d}'%(i,len(raw),accepted,eof))
    output.append('static const struct fixture fixtures[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode();here=Path(__file__).resolve().parent
    source=(here/'child_dbus_filtered_socket.c').read_bytes()
    filter_header,filter_evidence=filters()
    prefixes={
      'decoder.h':(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0],
      'owner.h':(here/'child_dbus_owner.c').read_bytes().split(b'struct step {',1)[0],
      'auth.h':(here/'child_dbus_auth.c').read_bytes().split(b'struct uid_vector {',1)[0],
      'connection.h':(here/'child_dbus_connection.c').read_bytes().split(b'struct step {',1)[0]}
    with tempfile.TemporaryDirectory(prefix='cgcchild-dbus-filter-' ,dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('socket_vectors.h',generated),('io_filter.h',filter_header),*prefixes.items()]:(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'Advanced Micro Devices X86-64' in elf
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        for selector in range(14):
            run=subprocess.run([str(root/'fixture'),str(selector)],cwd=root,capture_output=True,timeout=5)
            assert run.returncode==0,(selector,run.returncode,run.stdout,run.stderr)
        for args in ([],['14'],['00'],['-1'],['x'],['0','extra']):
            run=subprocess.run([str(root/'fixture'),*args],cwd=root,capture_output=True,timeout=5)
            assert run.returncode==2 and not run.stdout and not run.stderr

        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
            prefixes_sha256={k:digest(v) for k,v in prefixes.items()},generated_header_sha256=digest(generated),
            image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
            compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),kernel=os.uname().release,
            scenarios=[c[0] for c in cases],fragment_sizes=[1,17],scenario_runs=len(cases)*2,
            no_child_process=True,nonblocking=True,empty_read_eagain=True,fd_inventory_empty_after_each=True,
            filter_evidence=filter_evidence,filter_installs=14,denial_probes_per_install=18,invalid_selectors_refused=6,
            generated_filter_header_sha256=digest(filter_header),
            syscall_contract={'0':'owned endpoint read','3':'close owned endpoints','44':'sendto MSG_NOSIGNAL with no address',
              '53':'AF_UNIX STREAM NONBLOCK CLOEXEC socketpair','60':'exit','72':'FD/access flags and empty inventory',
              '102':'refuse root via getuid','436':'fixture prelude close inherited FDs3+',
              '157':'trusted setup NNP, denied afterward','317':'trusted setup filter install, denied afterward'},
            denial_probe_syscalls=[0,3,41,44,53,57,59,72,101,157,272,317,322,435,436],
            returncode=0,syscall_sites=1,scope='kernel-filtered private dummy byte transport; no live D-Bus, role separation, privileged controller or production acceptance')
    evidence['temporary_directory_removed']=not root.exists()
    text=json.dumps(evidence,sort_keys=True,indent=2)
    text=re.sub(r'\[\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\]',lambda m:'['+','.join(m.groups())+']',text)
    print(text)


if __name__=='__main__':main()
