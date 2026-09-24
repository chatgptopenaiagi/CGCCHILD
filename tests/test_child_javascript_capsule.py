"""Independent Node/Python model-capsule parity; inert bytes only."""
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import unittest
import warnings
import zipfile
from cgc.experimental import capsule as cap,state_protocol as sp,continuity as co
from test_child_state_protocol import state
from test_child_continuity import source_state


@unittest.skipUnless(shutil.which('node'),'Node absent; no independent capsule acceptance')
class ChildJavaScriptCapsuleTests(unittest.TestCase):
    def node(self,cases):
        root=Path(__file__).resolve().parents[1]
        raw=json.dumps([x.hex() for x in cases]).encode('ascii')
        self.assertLessEqual(len(raw),8*1024*1024)
        run=subprocess.run(['node',str(root/'sdk/javascript/capsule_conformance.mjs')],
                           input=raw,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr)
        return json.loads(run.stdout)

    def parity(self,cases):
        expected=[]
        for raw in cases:
            try:
                view=cap.import_capsule(raw)
                expected.append(dict(accepted=True,hex=cap.export_capsule(view.snapshot()).hex(),
                                     state=sp.encode(view.snapshot()).decode('ascii'),integrity=view.integrity,
                                     freshness=view.freshness,authority=view.authority))
            except cap.CapsuleError:expected.append(dict(accepted=False))
        self.assertEqual(self.node(cases),expected)

    def rewrite(self,change):
        raw=cap.export_capsule(state());output=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(output,'w') as target:
            for info in source.infolist():
                info,data=change(info,source.read(info))
                target.writestr(info,data)
        return output.getvalue()

    def test_positive_profile_parity(self):
        values=[state()]
        for name in values[0]['model']['claims']:
            for truth in ('YES','NO','UNKNOWN'):
                value=state();value['model']['claims'][name]=truth;values.append(value)
        for field,value in [('source_instance','x'*128),('snapshot_id','id-1'),('captured_at','0001-01-01T00:00:00Z')]:
            item=state();item[field]=value;values.append(item)
        item=state();item['model'].update(observed_ns='9223372036854775806',expires_ns='9223372036854775807')
        values.append(item)
        self.parity([cap.export_capsule(value) for value in values])

    def test_hostile_archive_metadata(self):
        cases=[]
        for field,value in [('filename','../state.json'),('filename','/state.json'),
                            ('filename','C:\\state.json'),('filename','STATE.JSON'),
                            ('external_attr',(stat.S_IFLNK|0o777)<<16),('compress_type',zipfile.ZIP_DEFLATED),
                            ('comment',b'extra'),('extra',b'\x01\x00\x00\x00'),
                            ('date_time',(2026,1,1,0,0,0))]:
            def change(info,data):
                if info.filename=='state.json':setattr(info,field,value)
                return info,data
            cases.append(self.rewrite(change))
        for target in cap.NAMES:
            cases.append(self.rewrite(lambda info,data:(info,data+b'X' if info.filename==target else data)))
        raw=cap.export_capsule(state())
        for name in ('state.json','extra'):
            out=io.BytesIO(raw)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(out,'a') as archive:archive.writestr(name,b'{}')
            cases.append(out.getvalue())
        cases += [b'prefix'+raw,raw+b'suffix',raw+raw,b'x'*65537]
        self.parity(cases)

    def test_every_truncation_and_single_byte_corruption(self):
        raw=cap.export_capsule(state())
        cases=[raw[:i] for i in range(len(raw))]
        cases += [raw[:i]+bytes([raw[i]^128])+raw[i+1:] for i in range(len(raw))]
        self.parity(cases)

    def test_full_continuity_is_explicitly_unsupported(self):
        value=co.project(source_state(),portable_project_id='fixture')
        raw=cap.export_capsule(value)
        self.assertEqual(cap.import_capsule(raw).snapshot(),value)
        self.assertEqual(self.node([raw]),[dict(accepted=False)])

    def test_node_ownership_and_pinned_vector(self):
        root=Path(__file__).resolve().parents[1]
        run=subprocess.run(['node',str(root/'sdk/javascript/test_capsule.mjs')],capture_output=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        result=json.loads(run.stdout)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['cases'],3246)


if __name__=='__main__':unittest.main()
