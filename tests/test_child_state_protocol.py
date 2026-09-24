import copy
import json
import unittest
from cgc.experimental import state_protocol as sp
from cgc.experimental.quiescence import assess, Truth
from test_child_quiescence import profile


def state():
    return sp.snapshot(profile(),source_instance='producer-1',snapshot_id='snapshot-1',captured_at='2026-09-24T12:00:00Z')


class ChildStateProtocolTests(unittest.TestCase):
    def test_roundtrip_and_nonmutation(self):
        value=state();before=copy.deepcopy(value)
        data=sp.encode(value)
        self.assertEqual(sp.decode(data),value)
        self.assertEqual(sp.encode(sp.decode(data)),data)
        self.assertEqual(value,before)
        self.assertEqual(len(sp.digest(value)),64)

    def test_import_never_current(self):
        p=sp.imported_profile(state())
        a=assess(p,project='fixture',generation='g1',now_ns=11)
        self.assertIs(a.model_result,Truth.UNKNOWN)
        self.assertFalse(a.mutation_authorized)
        self.assertEqual(p.observed_ns,10)
        self.assertIn('NOT CHECKED',sp.render_human(state()))

    def test_duplicate_keys_at_every_level(self):
        b=sp.encode(state())
        for old,new in ((b'"version":',b'"version":"forged","version":'),
                        (b'"project":',b'"project":"forged","project":'),
                        (b'"domain_empty":',b'"domain_empty":"NO","domain_empty":')):
            with self.assertRaisesRegex(sp.ProtocolError,'DUPLICATE_KEY'):sp.decode(b.replace(old,new))

    def test_unknown_versions_fields_and_promotion(self):
        for key,value in (('version','v9'),('safe_to_resume','YES'),('production_p3','YES'),
                          ('mutation_authorized',True),('mutation_authorized',0),('extra',None),
                          ('omissions',[]),('snapshot_id','../x'),('captured_at','2026-02-30T12:00:00Z')):
            v=state();v[key]=value
            with self.subTest(key=key),self.assertRaises(sp.ProtocolError):sp.encode(v)
        for key in state():
            v=state();del v[key]
            with self.assertRaises(sp.ProtocolError):sp.encode(v)

    def test_bad_wire_forms(self):
        raw=sp.encode(state())
        for b in (raw+b' ',b' '+raw,raw.replace(b'10',b'10.0'),raw.replace(b'10',b'NaN'),
                  raw.replace(b'10',b'1e1'),raw.replace(b'10',b'99999999999999999999'),
                  b'\xef\xbb\xbf'+raw,raw+b'{}',b'['*1000+b']'*1000,b'x'*16385):
            with self.subTest(raw=b[:40]),self.assertRaises(sp.ProtocolError):sp.decode(b)

    def test_all_truncations_refuse(self):
        raw=sp.encode(state())
        for i in range(len(raw)):
            with self.assertRaises(sp.ProtocolError):sp.decode(raw[:i])

    def test_status_preservation(self):
        for status in Truth:
            v=state();v['model']['claims']['domain_empty']=status.value
            self.assertEqual(sp.decode(sp.encode(v))['model']['claims']['domain_empty'],status.value)
        v=state();v['model']['claims']['domain_empty']=None
        with self.assertRaises(sp.ProtocolError):sp.encode(v)


if __name__=='__main__':unittest.main()
