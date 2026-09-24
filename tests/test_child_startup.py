import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from cgc.experimental import startup_snapshot as startup,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state
from test_child_mcp import init,req


class ChildStartupPlatformTests(unittest.TestCase):
    def test_unsupported_platform_does_not_touch_descriptor(self):
        with patch.object(startup.os,'name','nt'),patch.object(startup.os,'read') as read:
            with self.assertRaises(startup.StartupError):startup.read_owned_fd(3,'0'*64)
            read.assert_not_called()


@unittest.skipUnless(os.name=='posix','POSIX descriptor startup only')
class ChildStartupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='cgcchild-startup-',dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.file=Path(self.temp.name)/'snapshot.json'
        self.raw=profiles.encode(state())
        self.file.write_bytes(self.raw);self.file.chmod(0o600)
        self.digest=profiles.digest(state())

    def fd(self,flags=os.O_RDONLY):
        return os.open(self.file,flags)

    def test_owned_readonly_fd_consumed(self):
        fd=self.fd()
        self.assertEqual(startup.read_owned_fd(fd,self.digest),self.raw)
        with self.assertRaises(OSError):os.fstat(fd)

    def test_permissions_write_access_offset_digest_and_links_refuse(self):
        cases=('permissions','writable','offset','digest','hardlink')
        for case in cases:
            self.file.chmod(0o600)
            link=self.file.with_name('alias')
            if link.exists():link.unlink()
            if case=='permissions':self.file.chmod(0o644)
            if case=='hardlink':os.link(self.file,link)
            fd=self.fd(os.O_RDWR if case=='writable' else os.O_RDONLY)
            if case=='offset':os.read(fd,1)
            with self.subTest(case=case),self.assertRaises(startup.StartupError):
                startup.read_owned_fd(fd,'0'*64 if case=='digest' else self.digest)
            with self.assertRaises(OSError):os.fstat(fd)

    def test_pipe_refused_without_blocking(self):
        read,write=os.pipe()
        try:
            with self.assertRaises(startup.StartupError):startup.read_owned_fd(read,self.digest)
        finally:os.close(write)

    def test_content_change_rejected(self):
        fd=self.fd();self.file.write_bytes(self.raw+b'x')
        with self.assertRaises(startup.StartupError):startup.read_owned_fd(fd,self.digest)

    def test_large_actual_mcp_startup(self):
        value=large_state();raw=profiles.encode(value);digest=profiles.digest(value)
        self.file.write_bytes(raw);fd=self.fd()
        try:
            env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
            run=subprocess.run([sys.executable,'-B','-m','cgc.experimental.mcp_stdio',
                '--snapshot-fd',str(fd),'--snapshot-digest',digest],
                pass_fds=(fd,),input=init()+req('notifications/initialized',identifier=None)+
                req('tools/call',{'name':'cgcchild_status','arguments':{'snapshot_digest':digest}},identifier=2),
                capture_output=True,env=env,timeout=5)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(run.stderr,b'')
            response=json.loads(run.stdout.splitlines()[-1])
            self.assertIn('Latest attempt: FAILED',response['result']['structuredContent']['result']['text'])
            self.assertEqual(self.file.read_bytes(),raw)
        finally:os.close(fd)


if __name__=='__main__':unittest.main()
