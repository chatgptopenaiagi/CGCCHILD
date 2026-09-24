"""Fixed owned Windows mapping/metadata witnesses, no live repository adapter."""
import ctypes as c
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib,json,os,platform,sys,tempfile
from pathlib import Path


def run():
    if os.name!='nt':raise RuntimeError('WINDOWS_FIXTURE_ONLY')
    k=c.WinDLL('kernel32',use_last_error=True)
    def api(name,args,result):
        f=getattr(k,name);f.argtypes=args;f.restype=result;return f
    create=api('CreateFileW',[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE],w.HANDLE)
    close=api('CloseHandle',[w.HANDLE],w.BOOL)
    mapping=api('CreateFileMappingW',[w.HANDLE,c.c_void_p,w.DWORD,w.DWORD,w.DWORD,w.LPCWSTR],w.HANDLE)
    view=api('MapViewOfFile',[w.HANDLE,w.DWORD,w.DWORD,w.DWORD,c.c_size_t],c.c_void_p)
    unmap=api('UnmapViewOfFile',[c.c_void_p],w.BOOL)
    flush=api('FlushViewOfFile',[c.c_void_p,c.c_size_t],w.BOOL)
    set_time=api('SetFileTime',[w.HANDLE,c.POINTER(w.FILETIME),c.POINTER(w.FILETIME),c.POINTER(w.FILETIME)],w.BOOL)
    get_time=api('GetFileTime',[w.HANDLE,c.POINTER(w.FILETIME),c.POINTER(w.FILETIME),c.POINTER(w.FILETIME)],w.BOOL)
    invalid=c.c_void_p(-1).value;handles=set();views=set();facts=[]
    def checked(result):
        if not result:raise c.WinError(c.get_last_error())
        return result
    @contextmanager
    def owned(h):
        if h is None or h==invalid:raise c.WinError(c.get_last_error())
        handles.add(h)
        try:yield h
        finally:checked(close(h));handles.remove(h)
    def opening(path,access,share):return create(str(path),access,share,None,3,0x80,None)
    def stamp(h):
        t=w.FILETIME();checked(get_time(h,None,None,c.byref(t)));return t.dwHighDateTime<<32|t.dwLowDateTime
    parent=Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix='cgcchild-map-',dir=parent) as td:
        root=Path(td).resolve()
        if root.parent!=parent or not root.name.startswith('cgcchild-map-'):raise RuntimeError('TEMP_BOUNDARY')
        path=root/'owned.bin';path.write_bytes(b'0'*4096)
        ptr=None
        try:
            with owned(opening(path,0xc0000000,7)) as f:
                with owned(mapping(f,None,4,0,0,None)) as m:
                    ptr=checked(view(m,2,0,0,4096));views.add(ptr)
            if handles:raise AssertionError('FILE_OR_MAPPING_HANDLE_RETAINED')
            h=opening(path,0x80000000,1)
            if h==invalid:
                error=c.get_last_error()
                facts.append(dict(case='guard_with_retained_writable_view',opened=False,error=error))
                c.memmove(ptr,b'mapped!!',8);checked(flush(ptr,8))
            else:
                with owned(h):
                    c.memmove(ptr,b'mapped!!',8);checked(flush(ptr,8))
                    facts.append(dict(case='guard_with_retained_writable_view',opened=True,mapped_write_during_guard=True))
        finally:
            if ptr:checked(unmap(ptr));views.remove(ptr)
        if path.read_bytes()[:8]!=b'mapped!!':raise AssertionError('MAPPED_WRITE_NOT_VISIBLE_AFTER_UNMAP')
        facts.append(dict(case='retained_view_write_after_file_and_mapping_handle_close',bytes_verified_after_unmap=True))
        with owned(opening(path,0x80000000,1)):
            facts.append(dict(case='guard_after_unmap',opened=True))
        with owned(opening(path,0x80000000,1)) as guard:
            before=stamp(guard)
            target=132000000000000000
            if before==target:target+=10000000
            t=w.FILETIME(target&0xffffffff,target>>32)
            with owned(opening(path,0x100,7)) as metadata:
                checked(set_time(metadata,None,None,c.byref(t)))
            if stamp(guard)!=target or before==target:raise AssertionError('METADATA_WITNESS')
            facts.append(dict(case='metadata_write_during_guard',write_attributes_opened=True,last_write_time_changed=True))
        if handles or views:raise AssertionError('OWNED_RESOURCE_LEAK')
    if root.exists():raise AssertionError('TEMP_REMAINS')
    return dict(profile='OWNED_WINDOWS_MAPPING_METADATA_V1',classification='OBSERVED_FACT',platform=platform.system(),version=platform.version(),python=platform.python_version(),source_digest_basis='UTF8_LF_NORMALIZED',source_sha256=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),facts=facts,owned_handles_remaining=0,owned_views_remaining=0,temporary_directory_removed=True,production_filesystem='UNKNOWN',production_p3='UNKNOWN',mutation_authorized=False,limitations=['single owned process','one local file','flush success is not power-loss durability','no complete pending-I/O proof','no cross-OS or deputy coverage','no repository exclusion'])

if __name__=='__main__':
    if len(sys.argv)!=1:raise SystemExit('NO_ARGUMENTS_ACCEPTED')
    print(json.dumps(run(),sort_keys=True,indent=2))
