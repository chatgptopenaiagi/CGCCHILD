"""Two fixed Windows/WSL owned-file witnesses; not Linux containment or R6."""
import ctypes as c
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib,json,os,platform,queue,subprocess,sys,tempfile,threading
from pathlib import Path

LINUX=r"""
import fcntl,json,os,platform,select,signal,sys
signal.alarm(12)
mode,path=sys.argv[1:]
if mode not in ('writer','flock') or not path.startswith('/mnt/c/') or '/cgcchild-cross-' not in path or not path.endswith('/owned.bin'):raise SystemExit(20)
if os.geteuid()==0:raise SystemExit(21)
base=dict(kernel=platform.release(),uid=os.geteuid(),mode=mode)
if mode=='writer':
 try:f=os.open(path,os.O_WRONLY)
 except OSError as e:base.update(opened=False,errno=e.errno)
 else:
  try:
   n=os.write(f,b'linux!!!')
   if n!=8:raise RuntimeError('SHORT_WRITE')
   base.update(opened=True,written=8)
  finally:os.close(f)
 print(json.dumps(base,sort_keys=True),flush=True)
else:
 f=os.open(path,os.O_RDWR)
 try:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except OSError as e:print(json.dumps(dict(base,locked=False,errno=e.errno),sort_keys=True),flush=True)
  else:
   print(json.dumps(dict(base,locked=True),sort_keys=True),flush=True)
   ready,_,_=select.select([sys.stdin],[],[],8)
   if not ready or sys.stdin.buffer.read(1)!=b'R':raise SystemExit(22)
   print(json.dumps(dict(release_received=True),sort_keys=True),flush=True)
 finally:os.close(f)
"""


def run():
 if os.name!='nt':raise RuntimeError('WINDOWS_CONTROLLER_ONLY')
 k=c.WinDLL('kernel32',use_last_error=True)
 create=k.CreateFileW;create.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];create.restype=w.HANDLE
 close=k.CloseHandle;close.argtypes=[w.HANDLE];close.restype=w.BOOL
 write=k.WriteFile;write.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p];write.restype=w.BOOL
 invalid=c.c_void_p(-1).value;active=set();facts=[]
 @contextmanager
 def owned(h):
  if h==invalid:raise c.WinError(c.get_last_error())
  active.add(h)
  try:yield h
  finally:
   if not close(h):raise c.WinError(c.get_last_error())
   active.remove(h)
 def open_file(p,access,share):return create(str(p),access,share,None,3,0x80,None)
 def argv(mode,path):return ['wsl.exe','-d','FedoraLinux-44','--','python3','-B','-c',LINUX,mode,path]
 parent=Path(tempfile.gettempdir()).resolve()
 with tempfile.TemporaryDirectory(prefix='cgcchild-cross-',dir=parent) as td:
  root=Path(td).resolve()
  if root.parent!=parent or not root.name.startswith('cgcchild-cross-'):raise RuntimeError('TEMP_BOUNDARY')
  p=root/'owned.bin';p.write_bytes(b'initial!')
  converted=subprocess.run(['wsl.exe','-d','FedoraLinux-44','--','wslpath','-u',p.as_posix()],capture_output=True,timeout=15,check=True)
  if converted.stderr or len(converted.stdout)>4096:raise RuntimeError('PATH_TRANSLATION')
  lp=converted.stdout.decode('utf-8').strip()
  with owned(open_file(p,0x80000000,1)):
   attempt=subprocess.run(argv('writer',lp),capture_output=True,timeout=15,check=True)
   if attempt.stderr or len(attempt.stdout)>1024:raise RuntimeError('WRITER_OUTPUT')
   row=json.loads(attempt.stdout);facts.append(dict(case='windows_guard_linux_writer',**row))
  expected=b'linux!!!' if row['opened'] else b'initial!'
  if p.read_bytes()!=expected:raise AssertionError('LINUX_WRITE_WITNESS')
  control=subprocess.run(argv('writer',lp),capture_output=True,timeout=15,check=True)
  if control.stderr or len(control.stdout)>1024:raise RuntimeError('CONTROL_OUTPUT')
  baseline=json.loads(control.stdout)
  if not baseline['opened'] or p.read_bytes()!=b'linux!!!':raise AssertionError('LINUX_WRITER_CONTROL')
  facts.append(dict(case='linux_writer_after_windows_guard_close',**baseline))
  child=subprocess.Popen(argv('flock',lp),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  q=queue.Queue(maxsize=1)
  reader=threading.Thread(target=lambda:q.put(child.stdout.readline(1025)),daemon=True);reader.start()
  try:
   line=q.get(timeout=15);reader.join(timeout=1)
   if len(line)>1024:raise RuntimeError('LOCK_OUTPUT_BOUND')
   row=json.loads(line);facts.append(dict(case='linux_flock',**row))
   if row['locked']:
    h=open_file(p,0x40000000,7)
    if h==invalid:facts.append(dict(case='windows_writer_during_linux_flock',opened=False,error=c.get_last_error()))
    else:
     with owned(h):
      count=w.DWORD();buf=c.create_string_buffer(b'windows!')
      if not write(h,buf,8,c.byref(count),None) or count.value!=8:raise c.WinError(c.get_last_error())
     facts.append(dict(case='windows_writer_during_linux_flock',opened=True,written=8))
    out,err=child.communicate(input=b'R',timeout=15)
    if json.loads(out)!={'release_received':True}:raise AssertionError('RELEASE_ACK')
   else:out,err=child.communicate(timeout=15)
   if child.returncode or err or len(out)>1024:raise RuntimeError('LOCK_CHILD_EXIT')
  finally:
   if child.poll() is None:
    # Linux's own alarm bounds its lifetime; EOF also aborts the release wait.
    if child.stdin and not child.stdin.closed:child.stdin.close();child.stdin=None
    try:child.wait(timeout=15)
    except subprocess.TimeoutExpired:
     child.kill();child.wait(timeout=5);raise RuntimeError('WSL_LAUNCHER_TIMEOUT')
   for stream in (child.stdin,child.stdout,child.stderr):
    if stream and not stream.closed:stream.close()
   reader.join(timeout=1)
  if facts[-1].get('opened') and p.read_bytes()!=b'windows!':raise AssertionError('WINDOWS_WRITE_WITNESS')
  if active:raise AssertionError('HANDLE_LEAK')
 if root.exists():raise AssertionError('TEMP_REMAINS')
 return dict(profile='OWNED_WINDOWS_FEDORA_SHARE_V1',classification='OBSERVED_FACT',windows_version=platform.version(),distro='FedoraLinux-44',path_class='WINDOWS_TEMP_VIA_MNT_C',facts=facts,source_sha256=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),source_digest_basis='UTF8_LF_NORMALIZED',owned_processes_exited=True,owned_handles_remaining=0,temporary_directory_removed=True,production_filesystem='UNKNOWN',production_p3='UNKNOWN',mutation_authorized=False,limitations=['two fixed mechanisms and one positive control','not Linux-native containment','not every DrvFS mount or distro','no alias/deputy/queued-I/O closure','no real repository writer proof'])

if __name__=='__main__':
 if len(sys.argv)!=1:raise SystemExit('NO_ARGUMENTS_ACCEPTED')
 print(json.dumps(run(),sort_keys=True,indent=2))
