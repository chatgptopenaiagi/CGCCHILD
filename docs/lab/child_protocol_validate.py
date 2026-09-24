"""Disposable nonroot x86-64 native protocol fixture; no sockets or broker actions."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

OPS=('CREATE_OWN_DOMAIN','ATTACH_OWN_GATED_CHILD','SEAL','QUERY','REMOVE_OWN_EMPTY_DOMAIN')
GOOD=[1,0,0,0,4242,62001,62001]


def digest(raw):return hashlib.sha256(raw).hexdigest()


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    text=(here.parent/'V3_QUIESCENCE_LAB_VECTORS.md').read_text(encoding='utf-8')
    blocks=re.split(r'(?=### V-P\d+ )',text)[1:]
    positive={}
    cases=[]
    for block in blocks:
        key=block.split()[1]
        raw=re.search(r'~~~text\n(.*?)\n~~~',block,re.S)[1].encode('ascii')
        ancillary=re.search(r'Ancillary: (.*?)\. Expected:',block)[1]
        good='**ACCEPT_CANONICAL_ONLY**' in block
        if good:positive[key]=raw
        expected=positive[key] if key in positive else positive['V-P01'] if key=='V-P20' else positive['V-P04']
        if key=='V-P23':expected=expected.replace(b'"SEAL_EPOCH":"0"',b'"SEAL_EPOCH":"'+b'5'*32+b'"')
        a=GOOD.copy()
        if ancillary=='SCM_RIGHTS present':a[1]=1
        elif ancillary=='duplicate SCM_CREDENTIALS':a[0]=2
        elif ancillary=='wrong PID 4243':a[4]=4243
        elif ancillary=='wrong UID 62002':a[5]=62002
        elif ancillary=='wrong GID 62002':a[6]=62002
        elif ancillary=='MSG_TRUNC':a[3]=32
        elif ancillary=='MSG_CTRUNC':a[3]=8
        elif ancillary!='one ucred(pid=4242,uid=62001,gid=62001)':raise AssertionError(ancillary)
        cases.append((key,raw,expected,a,good))
    assert len(cases)==19 and len(positive)==6
    base=positive['V-P04']
    for number in (b'0',b'03',b'-1',b'3.0',b'3e0',b'18446744073709551616'):
        cases.append(('NUM-'+number.decode(),base.replace(b'"REQUEST_SEQUENCE":3',b'"REQUEST_SEQUENCE":'+number),base,GOOD,False))
    maximum=base.replace(b'"REQUEST_SEQUENCE":3',b'"REQUEST_SEQUENCE":18446744073709551615')
    cases.append(('MAX64',maximum,maximum,GOOD,True))
    for index in (0,2):
        a=GOOD.copy();a[index]=0 if index==0 else 1
        cases.append(('ANC-'+str(index),base,base,a,False))
    for key,raw in sorted(positive.items()):
        for index in range(len(raw)):
            changed=raw[:index]+bytes([raw[index]^128])+raw[index+1:]
            cases.append((key+'-ASCII-'+str(index),changed,raw,GOOD,False))
        for index in (0,1,len(raw)//2,len(raw)-1):
            cases.append((key+'-TRUNC-'+str(index),raw[:index],raw,GOOD,False))
    assert len(cases)<=2048,len(cases)
    header=[];records=[]
    for index,(key,raw,expected,a,good) in enumerate(cases):
        e=json.loads(expected)
        fields={'kind':1 if 'NONCE' in e else 2}
        if 'NONCE' in e:fields['nonce']=json.dumps(e['NONCE'])
        else:
            fields.update(op=OPS.index(e['OP']),seq=str(e['REQUEST_SEQUENCE'])+'UL',
                          b=json.dumps(e['BROKER_GENERATION']),c=json.dumps(e['CONTROLLER_GENERATION']),
                          domain=json.dumps(e['DOMAIN_ID']),lab=json.dumps(e['LAB_ID'][5:]),epoch=json.dumps(e['SEAL_EPOCH']))
        header.append('static const struct message e%d={'%index+','.join('.'+k+'='+str(v) for k,v in sorted(fields.items()))+'};')
        header.append('static const unsigned char r%d[]={'%index+(','.join(str(b) for b in raw) or '0')+'};')
        records.append('{r%d,%d,&e%d,{'%(index,len(raw),index)+','.join(map(str,a))+'},'+str(int(good))+'}')
    header.append('static const struct vector vectors[]={'+','.join(records)+'};')
    generated=('\n'.join(header)+'\n').encode('ascii')
    source=(here/'child_protocol.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-protocol-',dir='/tmp') as temp:
        root=Path(temp)
        (root/'fixture.c').write_bytes(source);(root/'protocol_vectors.h').write_bytes(generated)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
              '-fno-stack-protector','-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie',
              '-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        build=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if build.returncode:raise RuntimeError(build.stderr.decode())
        first=(root/'fixture').read_bytes()
        subprocess.run(argv,cwd=root,check=True,capture_output=True,timeout=30)
        assert first==(root/'fixture').read_bytes()
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        failed=int.from_bytes(run.stdout,'little') if run.stdout else None
        assert run.returncode==0,(run.returncode,failed,cases[failed][0] if failed is not None else None)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      generated_header_sha256=digest(generated),image_sha256=digest(first),
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,argv=argv,cases=len(cases),positive=sum(c[-1] for c in cases),
                      negative=sum(not c[-1] for c in cases),returncode=0,identical_rebuild=True,
                      syscall_sites=1,original_vectors=19,
                      scope='native payload grammar/re-encoding and normalized ancillary model; no IPC, live identity, state dispatch or R6')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
