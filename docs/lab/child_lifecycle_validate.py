"""Generate deterministic admission MODEL/reply vectors; no privileged effects."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest,OPS

EPOCH='5'*32


def packet(op,seq,epoch='0',**overrides):
    v=dict(BROKER_GENERATION='1'*32,CONTROLLER_GENERATION='2'*32,DOMAIN_ID='3'*32,
           LAB_ID='cgcq-'+'0'*31+'1',OP=op,REQUEST_SEQUENCE=seq,SEAL_EPOCH=epoch)
    v.update(overrides)
    return json.dumps(v,sort_keys=True,separators=(',',':')).encode()


def reply(raw,invalid=False):
    v=json.loads(raw);v['RESULT']='INVALIDATED' if invalid else 'OK'
    if v['OP']=='SEAL' and not invalid:v['SEAL_EPOCH']=EPOCH
    return json.dumps(v,sort_keys=True,separators=(',',':')).encode()


def step(raw,state,accepted=True,auth=1,continuity=1,empty=0):
    return (raw,auth,continuity,empty,int(accepted),state,reply(raw) if accepted else b'')


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    first=[step(packet(OPS[0],1),1),step(packet(OPS[1],2),2),step(packet(OPS[2],3),3)]
    closed=first+[step(packet(OPS[3],4,EPOCH),3),step(packet(OPS[4],5,EPOCH),4,empty=1)]
    scenarios=[
        ('valid',closed,1,(1,1,1)),
        ('wrong_generation',[step(packet(OPS[0],1,BROKER_GENERATION='9'*32),5,False)],1,(0,0,0)),
        ('wrong_sequence',[step(packet(OPS[0],2),5,False)],1,(0,0,0)),
        ('late_epoch',first+[step(packet(OPS[3],4),5,False)],1,(1,1,0)),
        ('late_attach',first+[step(packet(OPS[1],4,EPOCH),5,False)],1,(1,1,0)),
        ('populated_remove',first+[step(packet(OPS[4],4,EPOCH),5,False,empty=2)],1,(1,1,0)),
        ('unknown_remove',first+[step(packet(OPS[4],4,EPOCH),5,False)],1,(1,1,0)),
        ('continuity_loss',first+[step(packet(OPS[3],4,EPOCH),5,False,continuity=0)],1,(1,1,0)),
        ('unauthenticated',[step(packet(OPS[0],1),5,False,auth=0)],1,(0,0,0)),
        ('wrap',[step(packet(OPS[0],(1<<64)-1),5,False)],(1<<64)-1,(0,0,0)),
        ('duplicate',[first[0],step(packet(OPS[0],1),5,False)],1,(1,0,0)),
        ('malformed',[step(packet(OPS[0],1)+b' ',5,False)],1,(0,0,0)),
        ('closed_no_reopen',closed+[step(packet(OPS[0],6,EPOCH),4,False)],1,(1,1,1)),
        ('invalid_no_reopen',[step(packet(OPS[0],1),5,False,auth=0),step(packet(OPS[0],1),5,False)],1,(0,0,0)),
        ('budget',first+[step(packet(OPS[3],n,EPOCH),3) for n in range(4,9)]+[step(packet(OPS[3],9,EPOCH),5,False)],1,(1,1,0)),
    ]
    positive=[reply(packet(OPS[3],4,EPOCH)),reply(packet(OPS[3],4,EPOCH),True)]
    replies=[(raw,True,index) for index,raw in enumerate(positive)]
    base=positive[0]
    replies += [(base.replace(b'"RESULT":"OK"',b'"RESULT":"YES"'),False,0),
                (base.replace(b'"RESULT":"OK"',b'"RESULT":"OK","RESULT":"OK"'),False,0),
                (base+b'\n',False,0)]
    for raw in positive:
        for i in range(len(raw)):replies.append((raw[:i]+bytes([raw[i]^128])+raw[i+1:],False,0))
        for i in (0,1,len(raw)//2,len(raw)-1):replies.append((raw[:i],False,0))
    header=[];rows=[];serial=0
    def data(raw):
        nonlocal serial
        name='bytes_'+str(serial);serial+=1
        header.append('static const unsigned char '+name+'[]={'+(','.join(map(str,raw)) or '0')+'};')
        return name
    for index,(_,steps,next_seq,effects) in enumerate(scenarios):
        values=[]
        for raw,auth,continuity,empty,accepted,state,response in steps:
            a=data(raw);b=data(response)
            values.append('{'+','.join(map(str,(a,len(raw),auth,continuity,empty,accepted,state,b,len(response))))+'}')
        header.append('static const struct step steps_%d[]={'%index+','.join(values)+'};')
        rows.append('{steps_%d,%d,%dUL,%d,%d,%d}'%(index,len(steps),next_seq,*effects))
    header.append('static const struct scenario scenarios[]={'+','.join(rows)+'};')
    rows=[]
    for raw,good,invalid in replies:rows.append('{'+','.join(map(str,(data(raw),len(raw),int(good),invalid)))+'}')
    header.append('static const struct reply_vector reply_vectors[]={'+','.join(rows)+'};')
    generated=('\n'.join(header)+'\n').encode()
    here=Path(__file__).resolve().parent;payload=(here/'child_protocol.c').read_bytes().split(b'struct vector {',1)[0]
    source=(here/'child_lifecycle.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-lifecycle-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in (('fixture.c',source),('payload.h',payload),('lifecycle_vectors.h',generated)):(root/name).write_bytes(raw)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=5)
        assert run.returncode==0,(run.returncode,run.stderr)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      payload_prefix_sha256=digest(payload),generated_header_sha256=digest(generated),
                      image_sha256=digest((root/'fixture').read_bytes()),argv=argv,
                      compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,scenarios=[s[0] for s in scenarios],
                      transition_steps=sum(len(s[1]) for s in scenarios),reply_cases=len(replies),
                      reply_positive=2,reply_negative=len(replies)-2,returncode=0,syscall_sites=1,
                      scope='pure native admission MODEL; synthetic authentication/continuity/empty inputs and fixed epoch; no broker effects')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
