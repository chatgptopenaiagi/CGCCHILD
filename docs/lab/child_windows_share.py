"""Owned Windows temporary-file share checks; never a repository exclusion adapter."""
import ctypes as c
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib,json,os,platform,sys,tempfile
from pathlib import Path

READ=0x80000000
WRITE=0x40000000
SHARE_READ=1
SHARE_ALL=7
EXISTING=3
NEW=1
NORMAL=0x80
DIRECTORY=0x02000000
INVALID=c.c_void_p(-1).value


def run():
    if os.name!='nt':raise RuntimeError('WINDOWS_FIXTURE_ONLY')
    k=c.WinDLL('kernel32',use_last_error=True)
    def api(name,args,result):
        f=getattr(k,name);f.argtypes=args;f.restype=result;return f
    create=api('CreateFileW',[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE],w.HANDLE)
    close=api('CloseHandle',[w.HANDLE],w.BOOL)
    write=api('WriteFile',[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p],w.BOOL)
    volume_path=api('GetVolumePathNameW',[w.LPCWSTR,w.LPWSTR,w.DWORD],w.BOOL)
    volume_info=api('GetVolumeInformationW',[w.LPCWSTR,w.LPWSTR,w.DWORD,c.POINTER(w.DWORD),c.POINTER(w.DWORD),c.POINTER(w.DWORD),w.LPWSTR,w.DWORD],w.BOOL)
    class Info(c.Structure):
        _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),('volume',w.DWORD),('size_hi',w.DWORD),('size_lo',w.DWORD),('links',w.DWORD),('index_hi',w.DWORD),('index_lo',w.DWORD)]
    info=api('GetFileInformationByHandle',[w.HANDLE,c.POINTER(Info)],w.BOOL)
    active=set();facts=[]
    @contextmanager
    def opened(path,access,sharing,disposition=EXISTING,flags=NORMAL):
        h=create(str(path),access,sharing,None,disposition,flags,None)
        if h==INVALID:raise c.WinError(c.get_last_error())
        active.add(h)
        try:yield h
        finally:
            if not close(h):raise c.WinError(c.get_last_error())
            active.remove(h)
    def denied(path,access,sharing):
        h=create(str(path),access,sharing,None,EXISTING,NORMAL,None)
        if h!=INVALID:
            close(h);raise AssertionError('EXPECTED_SHARING_DENIAL')
        error=c.get_last_error()
        if error!=32:raise AssertionError('UNEXPECTED_OPEN_ERROR_'+str(error))
        return error
    def write_exact(h,data):
        count=w.DWORD();buf=c.create_string_buffer(data)
        if not write(h,buf,len(data),c.byref(count),None):raise c.WinError(c.get_last_error())
        if count.value!=len(data):raise AssertionError('SHORT_WRITE')
    def identity(h):
        x=Info()
        if not info(h,c.byref(x)):raise c.WinError(c.get_last_error())
        return x.volume,x.index_hi,x.index_lo
    parent=Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix='cgcchild-share-',dir=parent) as td:
        root=Path(td).resolve()
        if root.parent!=parent or not root.name.startswith('cgcchild-share-'):raise RuntimeError('TEMP_BOUNDARY')
        f=root/'owned.bin';f.write_bytes(b'initial')
        vp=c.create_unicode_buffer(512);fs=c.create_unicode_buffer(64)
        serial=w.DWORD();max_component=w.DWORD();flags=w.DWORD()
        if not volume_path(str(root),vp,len(vp)):raise c.WinError(c.get_last_error())
        if not volume_info(vp.value,None,0,c.byref(serial),c.byref(max_component),c.byref(flags),fs,len(fs)):raise c.WinError(c.get_last_error())
        with opened(f,WRITE,SHARE_ALL):
            facts.append(dict(case='preexisting_writer_blocks_guard',error=denied(f,READ,SHARE_READ)))
        with opened(f,READ,SHARE_READ) as guard:
            guard_id=identity(guard)
            facts.append(dict(case='guard_blocks_new_writer',error=denied(f,WRITE,SHARE_ALL)))
            with opened(f,READ,SHARE_READ) as reader:
                if identity(reader)!=guard_id:raise AssertionError('OBJECT_CHANGED')
            facts.append(dict(case='compatible_reader',same_object=True))
        with opened(f,WRITE,SHARE_ALL) as writer:write_exact(writer,b'after!!')
        if f.read_bytes()!=b'after!!':raise AssertionError('POST_CLOSE_CONTENT')
        facts.append(dict(case='writer_after_guard_close',write_verified=True))
        # A directory handle is deliberately challenged with child data and creation.
        with opened(root,READ,SHARE_READ,flags=DIRECTORY):
            with opened(f,WRITE,SHARE_ALL) as writer:write_exact(writer,b'child!!')
            with opened(root/'new.bin',WRITE,SHARE_ALL,disposition=NEW) as writer:write_exact(writer,b'new')
        if f.read_bytes()!=b'child!!' or (root/'new.bin').read_bytes()!=b'new':raise AssertionError('DIRECTORY_WITNESS')
        facts.append(dict(case='directory_guard_child_write',write_verified=True))
        facts.append(dict(case='directory_guard_child_create',write_verified=True))
        alias=root/'alias.bin'
        try:os.link(f,alias)
        except OSError as e:facts.append(dict(case='hardlink_alias',status='UNAVAILABLE_CAPABILITY',winerror=e.winerror))
        else:
            with opened(f,READ,SHARE_READ) as guard:
                with opened(alias,READ,SHARE_READ) as other:
                    if identity(guard)!=identity(other):raise AssertionError('ALIAS_OBJECT')
                facts.append(dict(case='hardlink_alias',same_object=True,error=denied(alias,WRITE,SHARE_ALL),status='OBSERVED_FACT'))
        if active:raise AssertionError('HANDLE_LEAK')
    if root.exists():raise AssertionError('TEMP_REMAINS')
    return dict(profile='OWNED_WINDOWS_SHARE_V1',platform=platform.system(),release=platform.release(),version=platform.version(),python=platform.python_version(),filesystem=fs.value,source_sha256=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),source_digest_basis='UTF8_LF_NORMALIZED',facts=facts,classification='OBSERVED_FACT',open_handles_at_cleanup=0,temporary_directory_removed=True,production_filesystem='UNKNOWN',production_p3='UNKNOWN',mutation_authorized=False,limitations=['same-process handle operations only','no metadata-writer exclusion','no queued I/O completion proof','no mapped-writer test','no cross-OS or other-distro test','no complete alias enumeration','no controller crash test'])

if __name__=='__main__':
    if len(sys.argv)!=1:raise SystemExit('NO_ARGUMENTS_ACCEPTED')
    print(json.dumps(run(),sort_keys=True,indent=2))
