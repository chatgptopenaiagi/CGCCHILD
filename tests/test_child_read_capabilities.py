import hashlib
import json
import unittest
from cgc.experimental import read_capabilities as cap,state_protocol as sp
from test_child_state_protocol import state


class ChildReadCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.lab=cap.ReadCapabilityLab(sp.encode(state()))
        self.digest=sp.digest(state())

    def test_scope_and_handle_identity(self):
        handle=self.lab.issue('consumer',('status.get',),now_ns=10,expires_ns=20)
        out=json.loads(self.lab.read(handle,'consumer','status.get',now_ns=11,snapshot_digest=self.digest))
        self.assertFalse(out['mutation_authorized'])
        for h,p,m,d in ((cap.GrantHandle(),'consumer','status.get',self.digest),
                        ({'grant':'forged'},'consumer','status.get',self.digest),
                        (handle,'other','status.get',self.digest),(handle,'consumer','state.get',self.digest),
                        (handle,'consumer','status.get','0'*64),(handle,'consumer','execute',self.digest)):
            with self.assertRaises(cap.ReadDenied):self.lab.read(h,p,m,now_ns=12,snapshot_digest=d)

    def test_expiry_revocation_and_generation(self):
        h=self.lab.issue('p',('state.get',),now_ns=10,expires_ns=20)
        with self.assertRaises(cap.ReadDenied):self.lab.read(h,'p','state.get',now_ns=20,snapshot_digest=self.digest)
        self.lab.revoke(h,now_ns=21)
        with self.assertRaises(cap.ReadDenied):self.lab.read(h,'p','state.get',now_ns=22,snapshot_digest=self.digest)
        h=self.lab.issue('p',('state.get',),now_ns=23,expires_ns=30)
        self.lab.invalidate(now_ns=24)
        with self.assertRaises(cap.ReadDenied):self.lab.read(h,'p','state.get',now_ns=25,snapshot_digest=self.digest)
        with self.assertRaises(cap.ReadDenied):self.lab.issue('p',('state.get',),now_ns=25,expires_ns=30)

    def test_backwards_clock_permanently_closes(self):
        h=self.lab.issue('p',('state.get',),now_ns=10,expires_ns=20)
        for now in (9,11):
            with self.assertRaises(cap.ReadDenied):self.lab.read(h,'p','state.get',now_ns=now,snapshot_digest=self.digest)

    def test_no_cross_router_or_serialized_grants(self):
        h=self.lab.issue('p',('state.get',),now_ns=10,expires_ns=20)
        other=cap.ReadCapabilityLab(sp.encode(state()))
        with self.assertRaises(cap.ReadDenied):other.read(h,'p','state.get',now_ns=11,snapshot_digest=self.digest)
        with self.assertRaises(TypeError):json.dumps(h)

    def test_bounds_and_event_chain(self):
        h=self.lab.issue('p',('state.get',),now_ns=10,expires_ns=100)
        for n in range(63):self.lab.read(h,'p','state.get',now_ns=11+n,snapshot_digest=self.digest)
        with self.assertRaises(cap.ReadDenied):self.lab.read(h,'p','state.get',now_ns=80,snapshot_digest=self.digest)
        previous='0'*64
        for sequence,event in enumerate(self.lab.events(),1):
            self.assertEqual(event['sequence'],sequence);self.assertEqual(event['previous'],previous)
            digest=event.pop('digest')
            self.assertEqual(digest,hashlib.sha256(json.dumps(event,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest())
            previous=digest
        self.assertIn('digest',self.lab.events()[0])

    def test_bad_grant_requests(self):
        for methods,now,end in ((('execute',),10,20),(('state.get','state.get'),10,20),
                                ((),10,20),(('state.get',),True,20),(('state.get',),10,10),
                                (('state.get',),10,10+cap.MAX_TTL_NS+1)):
            with self.assertRaises(cap.ReadDenied):self.lab.issue('p',methods,now_ns=now,expires_ns=end)


if __name__=='__main__':unittest.main()
