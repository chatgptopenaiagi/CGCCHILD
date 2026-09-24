"""Bounded inert capsule data plane. Hash consistency is not authentication."""
import base64
import hashlib
import re
from . import capsule,snapshot_profiles as profiles

CHUNK_BYTES=32768
FIELDS={'offset','total_bytes','capsule_sha256','chunk_sha256','data','encoding','done'}


class ChunkError(ValueError):
    def __init__(self):super().__init__('INVALID_CAPSULE_CHUNK')


def chunk(value,offset):
    if type(offset) is not int or not 0<=offset<capsule.MAX_BYTES or offset%CHUNK_BYTES:raise ChunkError()
    return _slice(capsule.export_capsule(value),offset)


def _slice(raw,offset):
    """Internal only: bytes from this core's immutable accepted capsule export."""
    if type(raw) is not bytes or not 1<=len(raw)<=capsule.MAX_BYTES:raise ChunkError()
    if type(offset) is not int or not 0<=offset<len(raw) or offset%CHUNK_BYTES:raise ChunkError()
    piece=raw[offset:offset+CHUNK_BYTES]
    return dict(offset=offset,total_bytes=len(raw),capsule_sha256=hashlib.sha256(raw).hexdigest(),
                chunk_sha256=hashlib.sha256(piece).hexdigest(),encoding='base64',
                data=base64.b64encode(piece).decode('ascii'),done=offset+len(piece)==len(raw))


class Receiver:
    def __init__(self,expected_snapshot_digest):
        if type(expected_snapshot_digest) is not str or not re.fullmatch(r'[0-9a-f]{64}',expected_snapshot_digest):raise ChunkError()
        self._expected=expected_snapshot_digest
        self._pieces=[];self._offset=0;self._total=None;self._digest=None
        self._state='OPEN'

    def accept(self,value):
        try:
            if self._state!='OPEN' or type(value) is not dict or set(value)!=FIELDS:raise ChunkError()
            if type(value['offset']) is not int or value['offset']!=self._offset:raise ChunkError()
            total=value['total_bytes']
            if type(total) is not int or not 1<=total<=capsule.MAX_BYTES or self._offset>=total:raise ChunkError()
            for field in ('capsule_sha256','chunk_sha256'):
                if type(value[field]) is not str or not re.fullmatch(r'[0-9a-f]{64}',value[field]):raise ChunkError()
            if type(value['data']) is not str or len(value['data'])>4*((CHUNK_BYTES+2)//3) or value['encoding']!='base64':raise ChunkError()
            piece=base64.b64decode(value['data'],validate=True)
            if base64.b64encode(piece).decode('ascii')!=value['data']:raise ChunkError()
            if len(piece)!=min(CHUNK_BYTES,total-self._offset):raise ChunkError()
            if hashlib.sha256(piece).hexdigest()!=value['chunk_sha256']:raise ChunkError()
            if type(value['done']) is not bool or value['done']!=(self._offset+len(piece)==total):raise ChunkError()
            if self._total is not None and (self._total!=total or self._digest!=value['capsule_sha256']):raise ChunkError()
            self._total=total;self._digest=value['capsule_sha256']
            self._pieces.append(piece);self._offset+=len(piece)
            if value['done']:self._state='COMPLETE'
        except (ValueError,TypeError):
            self._pieces.clear();self._state='INVALIDATED'
            raise ChunkError() from None

    def finish(self):
        try:
            if self._state!='COMPLETE':raise ChunkError()
            raw=b''.join(self._pieces)
            if hashlib.sha256(raw).hexdigest()!=self._digest:raise ChunkError()
            view=capsule.import_capsule(raw)
            if profiles.digest(view.snapshot())!=self._expected:raise ChunkError()
            self._pieces.clear();self._state='CLOSED'
            return view
        except ValueError:
            self._pieces.clear();self._state='INVALIDATED'
            raise ChunkError() from None
