"""POSIX-only adopted read-only descriptor for an inert historical snapshot."""
import hashlib
import os
import re
import stat
from . import snapshot_profiles as profiles


class StartupError(ValueError):
    def __init__(self):super().__init__('INVALID_STARTUP_SNAPSHOT')


def read_owned_fd(fd,expected_digest):
    """Consume this process's inherited fd; no pathname lookup or ownership change.

    The caller owns process timeout and must provide an explicit reviewed digest.
    Shared file-description offset advances. No filesystem-exclusivity claim.
    """
    if os.name!='posix' or type(fd) is not int or not 3<=fd<=63:raise StartupError()
    try:
        if type(expected_digest) is not str or not re.fullmatch(r'[0-9a-f]{64}',expected_digest):raise StartupError()
        import fcntl
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=os.geteuid()
                or before.st_nlink!=1 or before.st_mode & 0o077
                or not 1<=before.st_size<=profiles.MAX_BYTES
                or fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE!=os.O_RDONLY
                or os.lseek(fd,0,os.SEEK_CUR)!=0):raise StartupError()
        parts=[];remaining=before.st_size
        while remaining:
            piece=os.read(fd,min(65536,remaining))
            if not piece:raise StartupError()
            parts.append(piece);remaining-=len(piece)
        if os.read(fd,1):raise StartupError()
        after=os.fstat(fd)
        fields=('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
        if any(getattr(before,k)!=getattr(after,k) for k in fields):raise StartupError()
        raw=b''.join(parts)
        if hashlib.sha256(raw).hexdigest()!=expected_digest:raise StartupError()
        profiles.decode(raw)
        return raw
    except (OSError,ValueError):raise StartupError() from None
    finally:
        try:os.close(fd)
        except OSError:pass
