"""Native finite owner/request correlation MODEL on inert D-Bus frames."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from m4_validate import frame
from child_protocol_validate import digest


def response(serial,value,sender='org.freedesktop.DBus',signature='s'):
    return frame(2,serial,[(5,'u',serial),(7,'s',sender),(8,'g',signature)],signature,[value])


def owner_signal(old,new):
    fields=[(1,'o','/org/freedesktop/DBus'),(2,'s','org.freedesktop.DBus'),
            (3,'s','NameOwnerChanged'),(7,'s','org.freedesktop.DBus'),(8,'g','sss')]
    return frame(4,1,fields,'sss',['org.freedesktop.systemd1',old,new])


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    def request(op,phase,good=1,generation=7):return (1,op,generation,b'',good,phase,op if good else 0)
    def message(raw,phase,pending=0,good=1,generation=7):return (2,0,generation,raw,good,phase,pending)
    fail=lambda raw:message(raw,3,good=0)
    hello=response(1,':1.100');owner=response(2,':1.42')
    handshake=[request(1,0),message(hello,1),request(2,1),message(owner,2)]
    version=lambda serial:response(serial,['s','259'],':1.42','v')
    valid=handshake+[request(3,2),message(version(3),2)]
    cases=[
        ('valid',valid,1),
        ('owner_no_change',handshake+[message(owner_signal(':1.42',':1.42'),2)],1),
        ('signal_during_pending',handshake+[request(3,2),message(owner_signal(':1.42',':1.42'),2,3),message(version(3),2)],1),
        ('owner_change',handshake+[fail(owner_signal(':1.42',':1.43'))],1),
        ('unrelated_equal_owner',handshake+[fail(owner_signal(':1.43',':1.43'))],1),
        ('duplicate_reply',valid+[fail(version(3))],1),
        ('wrong_generation',handshake+[request(3,3,0,8)],1),
        ('stale_frame_generation',handshake+[request(3,2),message(version(3),3,good=0,generation=8)],1),
        ('wrong_serial',handshake+[request(3,2),fail(version(2))],1),
        ('wrong_sender',handshake+[request(3,2),fail(response(3,['s','259'],':1.43','v'))],1),
        ('missing_pending',[fail(hello)],1),
        ('double_issue',[request(1,0),request(1,3,0)],1),
        ('wrong_order',[request(2,3,0)],1),
        ('bad_hello_name',[request(1,0),fail(response(1,'org.freedesktop.DBus'))],1),
        ('empty_component',[request(1,0),fail(response(1,':1..2'))],1),
        ('owner_is_client',handshake[:3]+[fail(response(2,':1.100'))],1),
        ('owner_signal_before_binding',handshake[:2]+[fail(owner_signal(':1.42',':1.42'))],1),
        ('disconnect',valid+[(3,1,7,b'',0,3,0),request(3,3,0)],1),
        ('suspected_reexec',valid+[(3,2,7,b'',0,3,0),message(version(3),3,good=0)],1),
        ('serial_exhaustion',[request(1,3,0)],0xffffffff),
        ('request_budget',handshake+sum(([request(3,2),message(version(i),2)] for i in range(3,9)),[])+[request(3,3,0)],1),
    ]
    # Every response was generated from fixed test constructors, not a live bus.
    output=[];rows=[];number=0
    for index,(_,steps,next_serial) in enumerate(cases):
        step_rows=[]
        for kind,op,generation,raw,good,phase,pending in steps:
            name='raw_'+str(number);number+=1
            output.append('static const unsigned char '+name+'[]={'+(','.join(map(str,raw)) or '0')+'};')
            step_rows.append('{%d,%d,%d,%s,%d,%d,%d,%d}'%(kind,op,generation,name,len(raw),good,phase,pending))
        output.append('static const struct step steps_%d[]={%s};'%(index,','.join(step_rows)))
        rows.append('{steps_%d,%d,%dUL}'%(index,len(steps),next_serial))
    output.append('static const struct scenario scenarios[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode()
    here=Path(__file__).resolve().parent;source=(here/'child_dbus_owner.c').read_bytes()
    decoder=(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0]
    with tempfile.TemporaryDirectory(prefix='cgcchild-owner-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('decoder.h',decoder),('owner_vectors.h',generated)]:(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      decoder_prefix_sha256=digest(decoder),generated_header_sha256=digest(generated),
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,scenarios=[c[0] for c in cases],steps=sum(len(c[1]) for c in cases),
                      input_buffers_overwritten=True,returncode=0,syscall_sites=1,
                      scope='native fixed request/owner MODEL; synthetic generation/events; no connection or live manager continuity proof')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
