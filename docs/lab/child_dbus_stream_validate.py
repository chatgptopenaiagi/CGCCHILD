"""Compose native finite incoming decoder with bounded inert stream framing."""
import json,os,re,subprocess,tempfile
from pathlib import Path
from child_protocol_validate import digest
from child_dbus_validate import corpus,generate


def main():
    if os.name!='posix' or os.getuid()==0 or os.uname().machine!='x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    cases,_=corpus();generated=generate(cases)
    assert all(c[3] is not None for c in cases[:12]) and all(c[3] is None for c in cases[12:])
    stream=b''.join(c[1] for c in cases[:12]);assert len(stream)<65536
    here=Path(__file__).resolve().parent;source=(here/'child_dbus_stream.c').read_bytes()
    decoder=(here/'child_dbus.c').read_bytes().split(b'struct vector {',1)[0]
    with tempfile.TemporaryDirectory(prefix='cgcchild-stream-',dir='/tmp') as temp:
        root=Path(temp)
        for name,raw in [('fixture.c',source),('decoder.h',decoder),('dbus_vectors.h',generated),
                         ('stream_bytes.h',','.join(map(str,stream)).encode())]:(root/name).write_bytes(raw)
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
                      decoder_prefix_sha256=digest(decoder),generated_header_sha256=digest(generated),
                      stream_sha256=digest(stream),image_sha256=digest((root/'fixture').read_bytes()),
                      argv=argv,compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                      kernel=os.uname().release,stream_bytes=len(stream),stream_frames=12,
                      every_split_positive=len(stream)+1,fixed_chunk_positive=[1,17],
                      every_incomplete_prefix_refused=len(stream),negative_frame_cases=len(cases)-12,
                      input_after_finish_refused=True,extra_frame_refused=True,zero_feed_refused=True,
                      invalid_frame_budget_refused=True,returncode=0,syscall_sites=1,
                      scope='native bounded inert stream framing and typed decoder composition; fixed expected contexts, no transport or manager binding')
    evidence['temporary_directory_removed']=not root.exists()
    print(json.dumps(evidence,sort_keys=True,indent=2))


if __name__=='__main__':main()
