"""Nonroot Linux inert bootstrap fixture; never an R6 or production launcher."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from m4_validate import eq, le, rule, union, generate, interpret, ALLOW, DENY, KILL

BOUND = 0x12345678  # generated relocation marker, never a launch target


def main():
    if os.name != 'posix' or os.getuid() == 0 or os.uname().machine != 'x86_64':
        raise SystemExit('requires nonroot x86-64 Linux')
    end = (rule(60, le(0, 255)),)
    sealed = union(end, (rule(1, eq(0, 6), eq(2, 1)),
                        rule(61, eq(0, BOUND), eq(2, 0)),
                        rule(7, eq(1, 1), eq(2, 0))),
                   tuple(rule(3, eq(0, fd)) for fd in (3, 5, 6, 7)))
    boot = union(sealed, (rule(434, eq(0, BOUND), eq(1, 0)),
                         rule(0, eq(0, 7), eq(2, 1)),
                         rule(1, eq(0, 4), le(2, 20)),
                         rule(17, eq(0, 4), le(2, 20), eq(3, 0)),
                         rule(3, eq(0, 4)), rule(317, eq(0, 1), eq(1, 0))))
    worker = union(end, (rule(1, eq(0, 8), eq(2, 1)), rule(0, eq(0, 5), eq(2, 1)),
                        rule(3, eq(0, 5)), rule(3, eq(0, 8))))
    assert set(sealed) < set(boot)
    tables = {'b_boot': boot, 'b_sealed': sealed, 'w_filter': worker}
    header, bindings, evidence = [], [], {}
    for name in sorted(tables):
        code = generate(tables[name])
        assert code == generate(tuple(reversed(tables[name])))
        assert len(code) <= 4096
        assert interpret(code, 59) == DENY
        assert interpret(code, 0x40000001) == KILL
        assert interpret(code, 1, arch=0x40000003) == KILL
        for nr, predicates in tables[name]:
            args = [0]*6
            for index, low, high in predicates:
                args[index] = low
            assert interpret(code, nr, args) == ALLOW
        # The inherited generator returns raw cBPF instruction arrays.
        header.append('static struct ins '+name+'_code[]={'+','.join(
            '{%d,%d,%d,%d}' % tuple(x) for x in code)+'};')
        header.append('static struct prog '+name+'={'+str(len(code))+','+name+'_code};')
        positions = [i for i, x in enumerate(code) if x[0] == 0x15 and x[3] == BOUND]
        for pid in (1, 4242, 0x7fffffff):
            patched = [list(row) for row in code]
            for index in positions:
                patched[index][3] = pid
            if name.startswith('b_'):
                assert interpret(patched, 61, (pid, 0, 0)) == ALLOW
                assert interpret(patched, 61, (pid+1, 0, 0)) == DENY
                assert interpret(patched, 434, (pid, 0)) == (ALLOW if name == 'b_boot' else DENY)
        bindings += ['{'+name+'_code,'+str(i)+'}' for i in positions]
        import struct
        raw = b''.join(struct.pack('<HBBI', *x) for x in code)
        evidence[name] = {'sha256_template': hashlib.sha256(raw).hexdigest(),
                          'instructions': code, 'pid_relocations': positions}
    assert len(bindings) == 3
    header.append('static struct {struct ins *code;unsigned int index;} bindings[]={'+','.join(bindings)+'};')
    source = Path(__file__).with_name('child_bootstrap.c').read_bytes()
    with tempfile.TemporaryDirectory(prefix='cgcchild-bootstrap-', dir='/tmp') as temp:
        root = Path(temp)
        (root/'fixture.c').write_bytes(source)
        (root/'child_filters.h').write_text('\n'.join(header))
        argv = ['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-ffreestanding',
                '-fno-builtin','-fno-stack-protector','-fno-pie','-mno-red-zone',
                '-nostdlib','-static','-no-pie','-Wl,--build-id=none','-Wl,-z,noexecstack',
                'fixture.c','-o','fixture']
        subprocess.run(argv, cwd=root, check=True, capture_output=True, timeout=30)
        elf = subprocess.check_output(['readelf','-hldWs',str(root/'fixture')], timeout=5).decode()
        dis = subprocess.check_output(['objdump','-d',str(root/'fixture')], timeout=5).decode()
        assert 'INTERP' not in elf and '(NEEDED)' not in elf
        assert not re.search(r'\bUND[ \t]+\S', elf)
        assert len(re.findall(r'\bsyscall\b', dis)) == 1
        run = subprocess.run([str(root/'fixture')], cwd=root, stdin=subprocess.DEVNULL,
                             capture_output=True, timeout=5)
        assert run.returncode == 0, (run.returncode, run.stderr)
        pid_text = (root/'domain/membership.inert').read_text()
        assert pid_text.isascii() and pid_text.isdecimal()
        evidence.update(source_sha256=hashlib.sha256(source).hexdigest(),
                        image_sha256=hashlib.sha256((root/'fixture').read_bytes()).hexdigest(),
                        compiler=subprocess.check_output(['gcc','-dumpfullversion']).decode().strip(),
                        argv=argv, returncode=run.returncode, syscall_sites=1,
                        kernel=os.uname().release, monotonic_edge='b_boot -> b_sealed',
                        scope='inert regular file; no cgroup, credential drop, IPC authentication or R6')
        evidence['model_checks'] = 'determinism, 4096 bound, arch/x32, all clauses, 3 PID specializations'
    evidence['temporary_directory_removed'] = not root.exists()
    print(json.dumps(evidence, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
