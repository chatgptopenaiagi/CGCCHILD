# Fixed native lab-protocol payload validation

[Native source](lab/child_protocol.c), [driver](lab/child_protocol_validate.py),
[evidence](lab/child_protocol_evidence.json).

M17 closes a previously unprivileged mechanical gap, not a privileged acceptance gate.
The freestanding C11/x86-64 image has one raw-syscall site and no interpreter, dynamic dependency
or undefined import. It refuses root, reads no argv/input/path, opens no sockets and performs
no broker operation. Embedded immutable vectors exercise a finite parser and encoder.

The parser accepts only canonical READY and the five fixed request operations from
[Protocol V1](V3_QUIESCENCE_LAB_ABI.md#4-cgc_lab_proto_v1). It validates literal key order,
lowercase32-hex fields, fixed cgcq- prefix, operation enum, uint64 decimal overflow/no leading zero,
epoch grammar, exact end and1024-byte ceiling. No general JSON engine or arbitrary method
dispatch exists. Parsed fields must equal the fixture's expected structure; native re-encoding
must reproduce the exact input bytes.

Normalized ancillary facts are explicit test inputs. Wrong credential counts/tuple, rights,
unknown control or truncation flags refuse in that model. They are not recvmsg observations,
live-instance binding or kernel authentication. Native CMSG walking, received-FD disposal,
reply encoding and lifecycle dispatch remain incomplete and block full M4/R6 readiness.

The generated corpus contains all19 inherited V-P vectors, six additional invalid sequence
forms, uint64 maximum, two ancillary model negatives, every high-bit single-byte mutation of
the six positive packets, and bounded truncations:1541 cases,7 positive/1534 negative.
No corpus bytes are supplied to a privileged process. The native fixture exited0 and both
same-environment builds were byte-identical. Source/driver/generated-header/image hashes,
flags and compiler/kernel identity are recorded. This is one measured build reproducibility
result, not a toolchain-independent guarantee.

First driver execution exposed eager evaluation of a missing default vector; explicit branch
selection fixed it. The next compile refused misleading indentation under -Werror; braces
fixed it without changing warning policy. The complete corpus then passed. Temporary build
directories were removed on failed and successful paths by the driver context manager.

Repeat only from Windows-controlled child cwd through Fedora:

```text
wsl.exe -d FedoraLinux-44 -- python3 -B /mnt/c/Codex-Projects/CGCCHILD/docs/lab/child_protocol_validate.py
```

Production source and inherited lab sources remain unchanged. No RO/R6, account, unit,
manager operation, cgroup, credential transition or production producer was executed.
