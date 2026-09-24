"""Independent native incoming decoder against fixed inert frames, no bus."""
import json,os,re,struct,subprocess,tempfile
from pathlib import Path
from m4_validate import frame,decode,Reject
from child_protocol_validate import digest

PROPS={'ControlGroup':1,'InvocationID':2,'MainPID':3,'Version':4,'Features':5}
BASE=dict(sender=':1.42',reply_serial=1,signature='',test='T7')


def reply(sig,body,extra=(),kind=2):
    return frame(kind,1,[(5,'u',1),(7,'s',':1.42')]+list(extra)+([(8,'g',sig)] if sig else []),sig,body)


def corpus():
    cases=[]
    def add(name,raw,ctx=BASE,good=True):
        try: logical=decode(raw,ctx,True)
        except Reject:
            assert not good,name
            logical=None
        else: assert good,name
        cases.append((name,raw,dict(ctx),logical))
    for sig,body in [('',[]),('s',[':1.42']),('o',['/org/freedesktop/systemd1'])]:
        add('return_'+(sig or 'empty'),reply(sig,body),dict(BASE,signature=sig))
    for prop,value in [('ControlGroup',['s','/system.slice/cgc-lab.service']),
                       ('InvocationID',['ay',list(range(16))]),('MainPID',['u',4242]),
                       ('Version',['s','259']),('Features',['s','+PAM'])]:
        add('property_'+prop,reply('v',[value]),dict(BASE,signature='v',property=prop))
    for error,test in [('AccessDenied','T7'),('InteractiveAuthorizationRequired','T8')]:
        add('error_'+error,reply('s',['discard this text'],[(4,'s','org.freedesktop.DBus.Error.'+error)],3),
            dict(BASE,test=test))
    signal=[(1,'o','/org/freedesktop/DBus'),(2,'s','org.freedesktop.DBus'),
            (3,'s','NameOwnerChanged'),(7,'s','org.freedesktop.DBus'),(8,'g','sss')]
    ctx=dict(BASE,sender='org.freedesktop.DBus')
    add('owner_unchanged',frame(4,1,signal,'sss',['org.freedesktop.systemd1',':1.42',':1.42']),ctx)
    # Incoming field order is not required to be canonical.
    add('reordered_headers',frame(2,1,[(7,'s',':1.42'),(5,'u',1)],'',[]))
    base=cases[0][1]
    def patch(raw,offset,value):return raw[:offset]+value+raw[offset+len(value):]
    for name,offset,value in [('endian',0,b'B'),('kind',1,b'\1'),('version',3,b'\2'),
                             ('flags',2,b'\x80'),('serial_zero',8,b'\0'*4),
                             ('body_overflow',4,b'\xff'*4),('header_overflow',12,b'\xff'*4),
                             ('padding',38,b'\1')]:
        add(name,patch(base,offset,value),good=False)
    for name,extra in [('duplicate',[(5,'u',1)]),('rights',[(9,'u',0)]),
                       ('unknown_header',[(10,'u',0)]),('wrong_header_variant',[(8,'s','')])]:
        add(name,reply('',[],extra),good=False)
    add('wrong_reply',patch(base,20,struct.pack('<I',2)),good=False)
    add('wrong_sender',base.replace(b':1.42',b':1.43'),good=False)
    add('wrong_signature',reply('s',['x']),good=False)
    add('invalid_path',reply('o',['/bad//path']),dict(BASE,signature='o'),False)
    add('owner_changed',frame(4,1,signal,'sss',['org.freedesktop.systemd1',':1.42',':1.43']),ctx,False)
    add('unknown_signal',frame(4,1,[(k,t,'Unknown' if k==3 else v) for k,t,v in signal],
                              'sss',['org.freedesktop.systemd1',':1.42',':1.42']),ctx,False)
    reload_fields=[(1,'o','/org/freedesktop/systemd1'),(2,'s','org.freedesktop.systemd1.Manager'),
                   (3,'s','Reloading'),(7,'s',':1.42'),(8,'g','b')]
    add('reloading',frame(4,1,reload_fields,'b',[1]),BASE,False)
    add('generic_error',reply('s',['private text'],[(4,'s','org.freedesktop.DBus.Error.Failed')],3),good=False)
    add('denial_wrong_test',cases[8][1],dict(BASE,test='T6'),False)
    ivctx=dict(BASE,signature='v',property='InvocationID')
    add('wrong_variant',reply('v',[['s','x']]),ivctx,False)
    add('short_invocation',reply('v',[['ay',list(range(15))]]),ivctx,False)
    add('nested_variant',reply('v',[['v',['s','x']]]),ivctx,False)
    iv=cases[4][1]
    add('array_overflow',patch(iv,len(iv)-20,b'\xff'*4),ivctx,False)
    add('string_overflow',patch(cases[1][1],len(cases[1][1])-10,b'\xff'*4),dict(BASE,signature='s'),False)
    add('trailing',base+b'\0',good=False)
    add('truncated',base[:-1],good=False)
    # Original incoming witnesses, not outgoing frames rejected merely for direction.
    original=json.loads((Path(__file__).parent/'m4_evidence.json').read_text())
    for item in original['dbus']['negative']:
        if item['id'] in ('V-D30','V-D31','V-D32','V-D35'):
            add('retained_'+item['id'],bytes.fromhex(item['bytes']),ctx if item['id']=='V-D32' else BASE,False)
    originals=list(cases[:12])
    mutations=0
    for name,raw,context,_ in originals:
        for offset in (0,1,3,4,7,12,15):
            add('mut_'+name+'_'+str(offset),patch(raw,offset,bytes([raw[offset]^128])),context,False);mutations+=1
        for end in range(0,len(raw),8):
            add('cut_'+name+'_'+str(end),raw[:end],context,False);mutations+=1
    assert mutations<=2000
    return cases,mutations


def generate(cases):
    output=[];rows=[];serial=0
    def data(raw):
        nonlocal serial
        name='data_'+str(serial);serial+=1
        output.append('static const unsigned char '+name+'[]={'+(','.join(map(str,raw)) or '0')+'};')
        return name
    def span(raw):return '{%s,%d}'%(data(raw),len(raw))
    for _,raw,ctx,logical in cases:
        texts=[b'',b'',b''];number=variant=error=0;blob=b''
        if logical is not None:
            if logical.get('outcome')=='DENIED':
                error=1 if logical['error'].endswith('.AccessDenied') else 2
            else:
                sig=logical['signature'];body=logical['body']
                if sig in ('s','o','sss'):texts[:len(body)]=[x.encode() for x in body]
                elif sig=='v':
                    typ,value=body[0];variant={'s':1,'ay':2,'u':3}[typ]
                    if typ=='s':texts[0]=value.encode()
                    elif typ=='ay':blob=bytes(value)
                    else:number=value
        expected='{%d,%d,%d,{%s},%d,%s}'%(raw[1] if logical is not None else 0,error,variant,
                    ','.join(span(x) for x in texts),number,span(blob))
        context='{%s,%s,%d,%d,%d}'%(json.dumps(ctx['sender']),json.dumps(ctx['signature']),
                    ctx['reply_serial'],PROPS.get(ctx.get('property'),0),int(ctx['test'][1:]))
        rows.append('{%s,%d,%s,%d,%s}'%(data(raw),len(raw),context,logical is not None,expected))
    output.append('static const struct vector vectors[]={'+','.join(rows)+'};')
    return ('\n'.join(output)+'\n').encode()


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    cases,mutations=corpus();generated=generate(cases)
    here=Path(__file__).resolve().parent;source=(here/'child_dbus.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-dbus-',dir='/tmp') as temp:
        root=Path(temp);(root/'fixture.c').write_bytes(source);(root/'dbus_vectors.h').write_bytes(generated)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        if run.returncode:
            failed=int.from_bytes(run.stdout,'little')
            raise AssertionError((run.returncode,failed,cases[failed][0] if failed<len(cases) else '?'))
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      generated_header_sha256=digest(generated),image_sha256=digest((root/'fixture').read_bytes()),
                      argv=argv,compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,cases=len(cases),positive=sum(x[3] is not None for x in cases),
                      negative=sum(x[3] is None for x in cases),mutations=mutations,returncode=0,syscall_sites=1,
                      vectors=[dict(id=name,bytes=raw.hex(),context=ctx,expected=logical) for name,raw,ctx,logical in cases if not name.startswith(('mut_','cut_'))],
                      scope='native finite incoming parser against inert bytes; no bus, encoder, syscall filter or authority')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
