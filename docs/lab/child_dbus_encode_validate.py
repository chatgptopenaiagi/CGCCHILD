"""Execute closed native D-Bus encoder against retained exact inert frames."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from m4_validate import load_vectors,decode,rebuild
from child_protocol_validate import digest


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    here=Path(__file__).resolve().parent
    vectors,_=load_vectors(here.parent/'V3_QUIESCENCE_LAB_VECTORS.md')
    assert sorted(vectors)==['V-D%02d'%i for i in range(1,12)]
    output=[];rows=[]
    for i,(key,(logical,raw)) in enumerate(sorted(vectors.items())):
        assert decode(raw,logical)==logical
        assert rebuild(logical,i+1)==raw
        output.append('static const unsigned char data_%d[]={%s};'%(i,','.join(map(str,raw))))
        rows.append('{data_%d,%d}'%(i,len(raw)))
    output.append('static const struct vector vectors[]={'+','.join(rows)+'};')
    generated=('\n'.join(output)+'\n').encode();source=(here/'child_dbus_encode.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-encode-',dir='/tmp') as temp:
        root=Path(temp);(root/'fixture.c').write_bytes(source);(root/'encode_vectors.h').write_bytes(generated)
        argv=['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fno-stack-protector',
              '-fno-pie','-mno-red-zone','-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack','fixture.c','-o','fixture']
        result=subprocess.run(argv,cwd=root,capture_output=True,timeout=30)
        if result.returncode:raise RuntimeError(result.stderr.decode())
        elf=subprocess.check_output(['readelf','-hldWs',str(root/'fixture')],timeout=5).decode()
        dis=subprocess.check_output(['objdump','-d',str(root/'fixture')],timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf and not re.search(r'\bUND[ \t]+\S',elf)
        assert len(re.findall(r'\bsyscall\b',dis))==1
        run=subprocess.run([str(root/'fixture')],cwd=root,capture_output=True,timeout=10)
        assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
        evidence=dict(source_sha256=digest(source),driver_sha256=digest(Path(__file__).read_bytes()),
                      generated_header_sha256=digest(generated),image_sha256=digest((root/'fixture').read_bytes()),
                      argv=argv,compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,positive=11,capacity_refusals=sum(len(raw) for _,raw in vectors.values()),
                      unknown_selector_refusals=3,output_untouched_on_refusal=True,returncode=0,syscall_sites=1,
                      vectors=[dict(id=key,bytes=len(raw),sha256=digest(raw)) for key,(_,raw) in sorted(vectors.items())],
                      scope='fixed dummy outgoing encoding; exact retained frame match; no runtime manifest, transport, manager operation or authorization')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
