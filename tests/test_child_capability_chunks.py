"""Chunk reads keep per-call local grant checks and finite historical event semantics."""
import json
import unittest
from unittest.mock import patch
from cgc.experimental import read_capabilities as cap,capsule_chunks as chunks,snapshot_profiles as profiles
from test_child_chunks import large_state


class CapabilityChunkTests(unittest.TestCase):
    def setUp(self):
        self.value=large_state();self.digest=profiles.digest(self.value)
        self.lab=cap.ReadCapabilityLab(profiles.encode(self.value))

    def issue(self,methods=('capsule.chunk',),end=1000):
        return self.lab.issue('consumer',methods,now_ns=0,expires_ns=end)

    def read(self,handle,offset,now=1):
        return json.loads(self.lab.read_chunk(handle,'consumer',offset,now_ns=now,snapshot_digest=self.digest))

    def test_large_snapshot_with_explicit_scope_and_core_receiver(self):
        handle=self.issue();receiver=chunks.Receiver(self.digest);offset=0
        while True:
            response=self.read(handle,offset,1+offset//chunks.CHUNK_BYTES)
            self.assertFalse(response['mutation_authorized']);packet=response['result'];receiver.accept(packet)
            if packet['done']:break
            offset+=chunks.CHUNK_BYTES
        self.assertGreater(offset,0);view=receiver.finish()
        self.assertEqual(view.snapshot(),self.value);self.assertEqual(view.authority,'NONE')
        self.assertEqual(len(self.lab.events()),2+offset//chunks.CHUNK_BYTES)

    def test_export_grant_does_not_imply_chunk_grant(self):
        handle=self.issue(('capsule.export',))
        response=json.loads(self.lab.read(handle,'consumer','capsule.export',now_ns=1,snapshot_digest=self.digest))
        self.assertEqual(response['error'],'RESPONSE_LIMIT')
        with patch.object(self.lab._core,'dispatch',side_effect=AssertionError('scope bypass')):
            with self.assertRaises(cap.ReadDenied):self.read(handle,0,2)
        self.assertEqual(self.lab.events()[-1]['kind'],'READ_DENIED')

    def test_no_generic_offset_or_other_method_promotion(self):
        handle=self.issue()
        for method in ('state.get','capsule.export','capsule.chunk'):
            with self.assertRaises(cap.ReadDenied):self.lab.read(handle,'consumer',method,now_ns=1,snapshot_digest=self.digest)
        for offset in (None,True,-1,1,chunks.CHUNK_BYTES-1,cap.MAX_CAPSULE_BYTES,1.0,'0'):
            with self.assertRaises(cap.ReadDenied):self.read(handle,offset,2)
        self.assertEqual(self.read(handle,chunks.CHUNK_BYTES*60,3)['error'],'CHUNK_RANGE')
        self.assertEqual(self.lab.events()[-1]['kind'],'CORE_REFUSED')

    def test_revocation_expiry_and_cross_snapshot_mid_transfer(self):
        for mode in ('revoke','expire','snapshot','principal'):
            lab=cap.ReadCapabilityLab(profiles.encode(self.value));h=lab.issue('consumer',('capsule.chunk',),now_ns=0,expires_ns=3)
            first=json.loads(lab.read_chunk(h,'consumer',0,now_ns=1,snapshot_digest=self.digest))['result']
            receiver=chunks.Receiver(self.digest);receiver.accept(first)
            if mode=='revoke':lab.revoke(h,now_ns=2)
            with self.assertRaises(cap.ReadDenied):lab.read_chunk(h,'wrong' if mode=='principal' else 'consumer',chunks.CHUNK_BYTES,
                now_ns=3 if mode=='expire' else 2,snapshot_digest='0'*64 if mode=='snapshot' else self.digest)
            with self.assertRaises(chunks.ChunkError):receiver.finish()

    def test_budget_cannot_be_bypassed_by_chunks(self):
        handle=self.issue()
        for now in range(1,64):self.assertIn('result',self.read(handle,0,now))
        self.assertEqual(len(self.lab.events()),64)
        with patch.object(self.lab._core,'dispatch',side_effect=AssertionError('budget bypass')):
            with self.assertRaises(cap.ReadDenied):self.read(handle,chunks.CHUNK_BYTES,64)
        self.assertEqual(len(self.lab.events()),64)


if __name__=='__main__':unittest.main()
