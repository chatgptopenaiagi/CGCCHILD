"""Compose native AUTH, frame assembly and owner/request models without transport."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest
from child_dbus_owner_validate import response,owner_signal


def corpus():
    def step(kind,raw=b'',op=0,generation=7,good=1):return (kind,op,raw,generation,good)
    auth=b'OK 0123456789abcdef0123456789abcdef\r\n'
    hello=response(1,':1.100');owner=response(2,':1.42')
    version=response(3,['s','259'],':1.42','v')
    ready=[step(1),step(2,auth),step(3)]
    bound=ready+[step(4,op=1),step(5,hello),step(4,op=2),step(5,owner)]
    complete=bound+[step(4,op=3),step(5,version),step(6)]
    fail=lambda raw:step(5,raw,good=0)
    return [
      ('valid',complete,1),
      ('coalesced_signal',bound+[step(4,op=3),step(5,version+owner_signal(':1.42',':1.42')),step(6)],1),
      ('before_auth',[fail(hello)],0),
      ('before_begin',ready[:2]+[fail(hello)],0),
      ('early_request',ready[:1]+[step(4,op=1,good=0)],0),
      ('wrong_auth',[step(1),step(2,b'REJECTED EXTERNAL\r\n',good=0)],0),
      ('auth_binary_smuggling',[step(1),step(2,auth+hello,good=0)],0),
      ('unsolicited_owner',ready+[step(4,op=1),fail(hello+owner)],0),
      ('duplicate_reply',bound+[step(4,op=3),fail(version+version)],0),
      ('owner_change',bound+[fail(owner_signal(':1.42',':1.43'))],0),
      ('wrong_sender',bound+[step(4,op=3),fail(response(3,['s','259'],':1.43','v'))],0),
      ('wrong_serial',bound+[step(4,op=3),fail(response(2,['s','259'],':1.42','v'))],0),
      ('stale_generation',bound+[step(4,op=3),step(5,version,generation=8,good=0)],0),
      ('truncated',bound+[step(4,op=3),step(5,version[:-1]),step(6,good=0)],0),
      ('partial_request',bound+[step(4,op=3),step(5,version[:10]),step(4,op=3,good=0)],0),
      ('zero_feed',bound+[step(5,good=0)],0),
      ('disconnect',bound+[step(7,good=0)],0),
      ('suspected_reexec',bound+[step(8,good=0)],0),
      ('unknown_selector',bound+[step(99,good=0)],0),
      ('premature_finish',bound+[step(6,good=0)],0),
      ('wrong_endian',bound+[step(4,op=3),fail(b'B'+version[1:])],0),
      ('oversized_header',bound+[step(4,op=3),fail(version[:12]+b'\xff'*4+version[16:])],0),
    ]


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    cases=corpus();output=[];rows=[];number=0
    for index,(_,steps,good) in enumerate(cases):
        entries=[]
        for kind,op,raw,generation,accepted in steps:
            name='raw_'+str(number);number+=1
            output.append('static const unsigned char '+name+'[]={'+(','.join(map(str,raw)) or '0')+'};')
            entries.append('{%d,%d,%s,%d,%d,%d}'%(kind,op,name,len(raw),generation,accepted))
        output.append('static const struct step steps_%d[]={%s};'%(index,','.join(entries)))
        rows.append('{steps_%d,%d,%d}'%(index,len(steps),good))
    output.append('static const struct scenario scenarios[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode()
    here=Path(__file__).resolve().parent;source=(here/'child_dbus_connection.c').read_bytes()
    decoder=(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0]
    owner=(here/'child_dbus_owner.c').read_bytes().split(b'struct step {',1)[0]
    auth=(here/'child_dbus_auth.c').read_bytes().split(b'struct uid_vector {',1)[0]
    with tempfile.TemporaryDirectory(prefix='cgcchild-connection-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('decoder.h',decoder),('owner.h',owner),('auth.h',auth),('connection_vectors.h',generated)]:
            (root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'Advanced Micro Devices X86-64' in elf
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
            decoder_prefix_sha256=digest(decoder),owner_prefix_sha256=digest(owner),auth_prefix_sha256=digest(auth),
            generated_header_sha256=digest(generated),image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
            compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),kernel=os.uname().release,
            scenarios=[c[0] for c in cases],fragment_sizes=[1,17,65536],scenario_runs=len(cases)*3,
            scripted_steps=sum(len(c[1]) for c in cases)*3,returncode=0,syscall_sites=1,
            syscall_contract={'102':'refuse root via getuid','1':'failure diagnostic stdout only','60':'exit'},
            scope='inert composed native authentication/framing/owner MODEL; encoded not sent; no connection or manager operation')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
