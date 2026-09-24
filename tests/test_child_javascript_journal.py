"""Independent Node/Python journal parity; expected anchors remain unsigned input."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from cgc.experimental import read_journal as journal,read_capabilities as grants,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_read_journal import records,anchor,rehash


@unittest.skipUnless(shutil.which('node'),'Node absent; no independent journal acceptance')
class ChildJavaScriptJournalTests(unittest.TestCase):
    def parity(self,cases):
        root=Path(__file__).resolve().parents[1]
        for at in range(0,len(cases),500):
            group=cases[at:at+500];expected=[]
            for raw,args in group:
                try:
                    view=journal.decode(raw,**args)
                    expected.append(dict(accepted=True,hex=journal.encode(view.events(),snapshot_digest=args['expected_snapshot_digest']).hex(),
                        authority=view.authority,freshness=view.freshness,integrity=view.integrity,completeness='EXPECTED_PREFIX_ONLY'))
                except journal.JournalError:expected.append(dict(accepted=False))
            payload=json.dumps([dict(hex=raw.hex(),expected=args) for raw,args in group]).encode('ascii')
            self.assertLessEqual(len(payload),8*1024*1024)
            run=subprocess.run(['node',str(root/'sdk/javascript/journal_conformance.mjs')],input=payload,capture_output=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout),expected)

    def test_all_prefix_lengths_kinds_and_large_clocks(self):
        value=state();digest=profiles.digest(value)
        lab=grants.ReadCapabilityLab(profiles.encode(value))
        handle=lab.issue('fixture',('status.get',),now_ns=0,expires_ns=100)
        for now in range(1,64):lab.read(handle,'fixture','status.get',now_ns=now,snapshot_digest=digest)
        events=lab.events();cases=[]
        for count in range(65):
            prefix=events[:count];cases.append((journal.encode(prefix,snapshot_digest=digest),anchor(prefix,digest)))
        for kind in journal.KINDS:
            one=copy.deepcopy(list(events[:1]));one[0]['kind']=kind;rehash(one)
            cases.append((journal.encode(one,snapshot_digest=digest),anchor(one,digest)))
        for clock in ('9007199254740993','9223372036854775807'):
            one=copy.deepcopy(list(events[:1]));one[0]['observed_ns']=clock;rehash(one)
            cases.append((journal.encode(one,snapshot_digest=digest),anchor(one,digest)))
        self.assertEqual(len(cases),73);self.parity(cases)

    def test_semantic_wire_and_anchor_refusals(self):
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest);args=anchor(events,digest)
        cases=[]
        for key,value in (('expected_tip','0'*64),('expected_count',0),('expected_count',True),
                          ('expected_count',1.5),('expected_count','5'),('expected_count',65),
                          ('expected_snapshot_digest','f'*64),('expected_tip','0'*64+'\n')):
            changed=dict(args);changed[key]=value;cases.append((raw,changed))
        for key,value in (('sequence',True),('sequence',0),('observed_ns','01'),('observed_ns','0'),
                          ('observed_ns','9223372036854775808'),('observed_ns','1\n'),('kind',[]),
                          ('kind','EXEC'),('snapshot_digest','f'*64),('version','other'),('extra','x')):
            obj=json.loads(raw);obj['events'][1][key]=value;rehash(obj['events'])
            cases.append(((json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode('ascii'),args))
        cases.extend((data,args) for data in [raw+b'x',b' '+raw,b'\xef\xbb\xbf'+raw,
            raw.replace(b'"sequence":1',b'"sequence":1,"sequence":1',1),
            raw.replace(b'"sequence":1',b'"sequence":1.0',1),
            raw.replace(b'"sequence":1',b'"sequence":NaN',1),
            raw.replace(b'"authority":"NONE"',b'"authority":"NONE","authority":"NONE"'),
            raw.replace(b'NONE',b'YES'),raw.replace(b'HISTORICAL_UNVERIFIED',b'CURRENT'),
            raw.replace(b'SOURCE_MONOTONIC_NOT_PORTABLE',b'LOCAL'),
            b'['*10000+b'0'+b']'*10000,b'x'*(journal.MAX_BYTES+1)])
        self.parity(cases)

    def test_every_truncation_and_single_byte_highbit(self):
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest);args=anchor(events,digest)
        cases=[(raw[:i],args) for i in range(len(raw))]
        cases += [(raw[:i]+bytes([raw[i]^128])+raw[i+1:],args) for i in range(len(raw))]
        self.assertEqual(len(cases),3940);self.parity(cases)

    def test_node_pinned_ownership_checks(self):
        root=Path(__file__).resolve().parents[1]
        run=subprocess.run(['node',str(root/'sdk/javascript/test_read_journal.mjs')],capture_output=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout),dict(status='PASS',cases=14))


if __name__=='__main__':unittest.main()
