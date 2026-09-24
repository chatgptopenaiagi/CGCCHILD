"""Deterministic inert in-memory ZIP profile; never extracts or executes content."""
from dataclasses import dataclass
import hashlib
import io
import json
import stat
import zipfile
from . import state_protocol as sp

VERSION = 'cgcchild-capsule-0.1-experimental'
MAX_BYTES = 65536
NAMES = ('manifest.json', 'state.json', 'HUMAN-STATUS.txt')


class CapsuleError(ValueError):
    def __init__(self):super().__init__('INVALID_CAPSULE')


def _manifest(state, human):
    return (json.dumps({'version':VERSION,'signature':'UNSIGNED',
        'members':{'state.json':hashlib.sha256(state).hexdigest(),
                   'HUMAN-STATUS.txt':hashlib.sha256(human).hexdigest()}},
        sort_keys=True,separators=(',',':'))+'\n').encode('ascii')


def export_capsule(value):
    state=sp.encode(value)
    human=sp.render_human(value).encode('ascii')
    values=(_manifest(state,human),state,human)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED,allowZip64=False) as archive:
        for name,data in zip(NAMES,values):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.create_system=3
            info.external_attr=(stat.S_IFREG|0o600)<<16
            archive.writestr(info,data)
    raw=stream.getvalue()
    if len(raw)>MAX_BYTES:raise CapsuleError()
    return raw


@dataclass(frozen=True)
class HistoricalView:
    state_bytes: bytes
    integrity: str = 'CONSISTENT_UNSIGNED_BYTES'
    freshness: str = 'HISTORICAL_UNVERIFIED'
    authority: str = 'NONE'

    def snapshot(self):
        return sp.decode(self.state_bytes)


def import_capsule(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise CapsuleError()
    try:
        with zipfile.ZipFile(io.BytesIO(raw),'r',allowZip64=False) as archive:
            infos=archive.infolist()
            if tuple(x.filename for x in infos)!=NAMES or archive.comment:raise CapsuleError()
            for info in infos:
                if (info.compress_type!=zipfile.ZIP_STORED or info.flag_bits!=0 or info.extra or info.comment
                        or info.create_system!=3 or info.external_attr!=(stat.S_IFREG|0o600)<<16
                        or info.date_time!=(1980,1,1,0,0,0) or info.file_size!=info.compress_size
                        or not 0<info.file_size<=sp.MAX_BYTES):
                    raise CapsuleError()
            members={info.filename:archive.read(info) for info in infos}
        state=sp.decode(members['state.json'])
        human=sp.render_human(state).encode('ascii')
        if members['HUMAN-STATUS.txt']!=human or members['manifest.json']!=_manifest(members['state.json'],human):
            raise CapsuleError()
        # Reject noncanonical local headers, prefixes, trailing bytes, duplicated
        # records and other ambiguities even if the ZIP parser tolerates them.
        if export_capsule(state)!=raw:raise CapsuleError()
        return HistoricalView(members['state.json'])
    except (ValueError,zipfile.BadZipFile,RuntimeError,NotImplementedError,OverflowError,EOFError):
        raise CapsuleError() from None
