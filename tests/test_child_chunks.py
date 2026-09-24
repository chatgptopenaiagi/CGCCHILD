import base64
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
from cgc.experimental import capsule_chunks as chunks,capsule,snapshot_profiles as profiles,continuity
from cgc.experimental import readonly_service as svc,mcp_stdio as mcp,read_capabilities as grants
from test_child_state_protocol import state
from test_child_continuity import source_state
from test_child_mcp import init,req


def large_state():
    source=source_state();slot=source['last_known_good']
    slot['record']['notes']['complete']=['inert-'+str(i)+'-'+'x'*1800 for i in range(60)]
    del slot['digest']
    slot['digest']=hashlib.sha256((json.dumps(slot,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
    return continuity.project(source,portable_project_id='fixture')


class ChildChunkTests(unittest.TestCase):
    def test_large_end_to_end_mcp_receiver(self):
        value=large_state();digest=profiles.digest(value)
        adapter=mcp.MCPAdapter(profiles.encode(value));adapter.handle(init())
        adapter.handle(req('notifications/initialized',identifier=None))
        receiver=chunks.Receiver(digest)
        offset=0;count=0
        while True:
            raw=adapter.handle(req('tools/call',{'name':'cgcchild_capsule_chunk',
                'arguments':{'snapshot_digest':digest,'offset':offset}},identifier=count+2))
            self.assertLessEqual(len(raw),mcp.MAX_RESPONSE)
            result=json.loads(raw)['result'];self.assertFalse(result['isError'])
            piece=result['structuredContent']['result'];receiver.accept(piece);count+=1
            if piece['done']:break
            offset+=chunks.CHUNK_BYTES
        self.assertGreater(count,1);self.assertLess(count,mcp.MAX_MESSAGES-2)
        self.assertEqual(receiver.finish().snapshot(),value)

    def test_tamper_reorder_duplicates_and_cross_snapshot(self):
        value=large_state();first=chunks.chunk(value,0);second=chunks.chunk(value,chunks.CHUNK_BYTES)
        for key,bad in (('data','AAAA'),('chunk_sha256','0'*64),('total_bytes',capsule.MAX_BYTES+1),
                        ('offset',True),('done',True),('encoding','hex'),('extra','x')):
            receiver=chunks.Receiver(profiles.digest(value));v=dict(first);v[key]=bad
            with self.assertRaises(chunks.ChunkError):receiver.accept(v)
            with self.assertRaises(chunks.ChunkError):receiver.accept(first)
        receiver=chunks.Receiver(profiles.digest(value))
        with self.assertRaises(chunks.ChunkError):receiver.accept(second)
        receiver=chunks.Receiver(profiles.digest(value));receiver.accept(first)
        with self.assertRaises(chunks.ChunkError):receiver.accept(first)
        receiver=chunks.Receiver(profiles.digest(value));receiver.accept(first)
        bad=dict(second,capsule_sha256='0'*64)
        with self.assertRaises(chunks.ChunkError):receiver.accept(bad)
        receiver=chunks.Receiver('0'*64);receiver.accept(chunks.chunk(state(),0))
        with self.assertRaises(chunks.ChunkError):receiver.finish()

    def test_incomplete_final_digest_and_closed_receiver(self):
        value=state();piece=chunks.chunk(value,0)
        receiver=chunks.Receiver(profiles.digest(value))
        with self.assertRaises(chunks.ChunkError):receiver.finish()
        receiver=chunks.Receiver(profiles.digest(value));receiver.accept(dict(piece,capsule_sha256='0'*64))
        with self.assertRaises(chunks.ChunkError):receiver.finish()
        receiver=chunks.Receiver(profiles.digest(value));receiver.accept(piece);receiver.finish()
        with self.assertRaises(chunks.ChunkError):receiver.finish()

    def test_offsets_refuse_without_generic_byte_range(self):
        for offset in (-1,True,1,1.0,2**63):
            with self.assertRaises(chunks.ChunkError):chunks.chunk(state(),offset)

    def test_export_uses_one_detached_object(self):
        value=state();before=copy.deepcopy(value);real=profiles.encode
        def encode_then_mutate(v):
            raw=real(v);value['model']['project']='changed-after-copy';return raw
        with patch('cgc.experimental.capsule.profiles.encode',side_effect=encode_then_mutate):
            raw=capsule.export_capsule(value)
        self.assertEqual(capsule.import_capsule(raw).snapshot(),before)

    def test_core_refusal_is_not_logged_as_completed_read(self):
        value=large_state();lab=grants.ReadCapabilityLab(profiles.encode(value))
        handle=lab.issue('p',('state.get',),now_ns=10,expires_ns=20)
        out=json.loads(lab.read(handle,'p','state.get',now_ns=11,snapshot_digest=profiles.digest(value)))
        self.assertEqual(out['error'],'RESPONSE_LIMIT')
        self.assertEqual(lab.events()[-1]['kind'],'CORE_REFUSED')
        # Chunk access now exists only under a separate explicit grant/offset API.
        with self.assertRaises(grants.ReadDenied):lab.read_chunk(handle,'p',0,now_ns=12,snapshot_digest=profiles.digest(value))
        chunk_handle=lab.issue('p',('capsule.chunk',),now_ns=13,expires_ns=20)
        with self.assertRaises(grants.ReadDenied):lab.read(chunk_handle,'p','capsule.chunk',now_ns=14,snapshot_digest=profiles.digest(value))
        self.assertEqual(lab.events()[-1]['kind'],'READ_DENIED')

    def test_one_archive_generation_per_immutable_core(self):
        value=large_state();core=svc.ReadOnlyCore(profiles.encode(value));digest=profiles.digest(value)
        receiver=chunks.Receiver(digest);offset=0
        with patch('cgc.experimental.readonly_service.export_capsule',wraps=capsule.export_capsule) as export:
            while True:
                request=dict(id='once',method='capsule.chunk',snapshot_digest=digest,offset=offset)
                piece=json.loads(core.dispatch((json.dumps(request)+'\n').encode()))['result']
                receiver.accept(piece)
                if piece['done']:break
                offset+=chunks.CHUNK_BYTES
            self.assertEqual(export.call_count,1)
        self.assertEqual(receiver.finish().snapshot(),value)


if __name__=='__main__':unittest.main()
