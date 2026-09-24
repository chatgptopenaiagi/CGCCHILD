import io
import hashlib
import json
from pathlib import Path
import stat
import unittest
import zipfile
from cgc.experimental import capsule as cap
from cgc.experimental import state_protocol as sp
from cgc.experimental.quiescence import assess,Truth
from cgc.experimental.orchestration import plan_attempt,Action,execute
from test_child_state_protocol import state


class ChildCapsuleTests(unittest.TestCase):
    def test_pinned_wire_vector(self):
        vector=json.loads((Path(__file__).resolve().parents[1]/'docs/lab/child_state_vectors.json').read_text(encoding='utf-8'))
        self.assertEqual(sp.encode(state()),vector['state_ascii'].encode('ascii'))
        self.assertEqual(sp.digest(state()),vector['state_sha256'])
        self.assertEqual(hashlib.sha256(cap.export_capsule(state())).hexdigest(),vector['capsule_sha256'])

    def test_deterministic_and_inert_roundtrip(self):
        raw=cap.export_capsule(state())
        self.assertEqual(raw,cap.export_capsule(state()))
        view=cap.import_capsule(raw)
        self.assertEqual(view.snapshot(),state())
        self.assertEqual(view.authority,'NONE')
        self.assertEqual(view.freshness,'HISTORICAL_UNVERIFIED')
        self.assertEqual(view.integrity,'CONSISTENT_UNSIGNED_BYTES')
        self.assertEqual(cap.export_capsule(view.snapshot()),raw)
        p=sp.imported_profile(view.snapshot())
        self.assertIs(assess(p,project='fixture',generation='g1',now_ns=11).model_result,Truth.UNKNOWN)
        plan=plan_attempt(Action.REPAIR,p,project='fixture',generation='g1',now_ns=11,previous_attempt='UNCERTAIN')
        with self.assertRaises(RuntimeError):execute(plan)

    def rewrite(self,transform):
        source=zipfile.ZipFile(io.BytesIO(cap.export_capsule(state())))
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as out:
            for info in source.infolist():
                data=source.read(info)
                info,data=transform(info,data)
                out.writestr(info,data)
        source.close()
        return stream.getvalue()

    def test_paths_links_compression_and_metadata_refuse(self):
        def change(field,value):
            def apply(info,data):
                if info.filename=='state.json':setattr(info,field,value)
                return info,data
            return apply
        for field,value in (('filename','../state.json'),('filename','/state.json'),
                            ('filename','C:\\state.json'),('filename','STATE.JSON'),
                            ('external_attr',(stat.S_IFLNK|0o777)<<16),
                            ('compress_type',zipfile.ZIP_DEFLATED),('comment',b'extra'),
                            ('date_time',(2026,1,1,0,0,0))):
            with self.subTest(field=field),self.assertRaises(cap.CapsuleError):
                cap.import_capsule(self.rewrite(change(field,value)))

    def test_manifest_human_and_state_tamper(self):
        for target in cap.NAMES:
            def change(info,data):return info,data+b'X' if info.filename==target else data
            with self.assertRaises(cap.CapsuleError):cap.import_capsule(self.rewrite(change))

    def test_duplicate_and_extra_member(self):
        raw=cap.export_capsule(state())
        for name in ('extra','state.json'):
            stream=io.BytesIO(raw)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(stream,'a') as z:z.writestr(name,b'{}')
            with self.assertRaises(cap.CapsuleError):cap.import_capsule(stream.getvalue())

    def test_truncations_prefix_suffix_and_size(self):
        raw=cap.export_capsule(state())
        for bad in (b'',b'x'*65537,b'prefix'+raw,raw+b'trailer'):
            with self.assertRaises(cap.CapsuleError):cap.import_capsule(bad)
        for i in range(len(raw)):
            with self.assertRaises(cap.CapsuleError):cap.import_capsule(raw[:i])


if __name__=='__main__':unittest.main()
