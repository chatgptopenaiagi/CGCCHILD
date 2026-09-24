"""Independent Node preservation consistency mirrors the original pure Python validator."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from cgc import preservation as p
from test_preservation import record,verifying,handoff,STAMP,COMMIT

ROOT=Path(__file__).resolve().parents[1]
def wire(value):return (json.dumps(value,sort_keys=True,ensure_ascii=True)+'\n').encode('ascii')


@unittest.skipUnless(shutil.which('node'),'Node unavailable; independent record parity not executed')
class JavascriptPreservationTests(unittest.TestCase):
    def parity(self,rows):
        for start in range(0,len(rows),64):
            raw_rows=rows[start:start+64];expected=[]
            for raw in raw_rows:
                try:
                    value=p.validate_record(json.loads(raw.decode('ascii')))
                    if (p.render_json(value)+'\n').encode('ascii')!=raw:raise ValueError()
                    expected.append(dict(accepted=True,hex=raw.hex(),current_safe_to_resume='UNKNOWN',authority='NONE',receipts_authenticated=False))
                except (ValueError,UnicodeError,RecursionError):expected.append(dict(accepted=False))
            payload=json.dumps([raw.hex() for raw in raw_rows]).encode()
            self.assertLessEqual(len(payload),8*1024*1024)
            run=subprocess.run(['node',str(ROOT/'sdk/javascript/preservation_conformance.mjs')],input=payload,capture_output=True,timeout=20)
            self.assertEqual((run.returncode,run.stderr),(0,b''));self.assertEqual(json.loads(run.stdout),expected)

    def test_lifecycle_levels_receipts_and_derived_outcomes(self):
        values=[]
        for level in ('HANDOFF_ONLY','LOCAL_CHECKPOINT','REMOTE_VERIFIED'):
            for trigger in ('SYNTHETIC','MANUAL'):
                value=record(level,trigger);values.append(value)
                for phase in ('STABILIZING','TESTING','DOCUMENTING','CHECKPOINTING','PUBLISHING','VERIFYING'):
                    value=p.advance(value,phase,now=STAMP);values.append(value)
                for phase in ('BLOCKED','FAILED','CANCELLED','PARTIAL'):
                    values.append(p.advance(value,phase,now=STAMP))
                evidence=handoff()
                if level!='HANDOFF_ONLY':evidence['local_commit']=COMMIT
                if level=='REMOTE_VERIFIED':evidence.update(tracking_commit=COMMIT,remote_commit=COMMIT,push_attempted=True)
                values.append(p.advance(value,'PRESERVED',now=STAMP,evidence=evidence))
        for error in p.PUBLICATION_ERRORS:
            values.append(p.advance(verifying('REMOTE_VERIFIED',dict(handoff(),local_commit=COMMIT,publication_error=error)),'PARTIAL',now=STAMP))
        values.append(p.advance(record(),'BLOCKED',now=STAMP,evidence={'unsafe_target':True}))
        self.assertEqual(len(values),79);self.parity([wire(v) for v in values])

    def test_unicode_dates_and_text_bounds(self):
        values=[]
        for text in ('é','😀','\ufeff','\u0085','\u2000','\u0085x','x\u2028y','\ud800','\\quoted"', '😀'*2048,'😀'*2049,'x\x7f'):
            v=record();v['notes']['mission']=text;values.append(v)
        for stamp in ('0001-01-01T00:00:00Z','9999-12-31T23:59:59.999999Z',
                      '2024-02-29T00:00:00.000001Z','2026-09-24T12:00:00.001000Z',
                      '2026-09-24T12:00:00.000000Z','2026-09-24T12:00:00.1Z',
                      '2026-02-29T00:00:00Z','0000-01-01T00:00:00Z','2026-09-24T12:00:60Z'):
            v=record();v['events'][0]['at']=stamp;values.append(v)
        for first,last in [('2026-09-24T12:00:00Z','2026-09-24T12:00:00.000001Z'),
                           ('2026-09-24T12:00:00.000002Z','2026-09-24T12:00:00.000001Z')]:
            v=p.advance(record(),'DOCUMENTING',now=STAMP);v['events'][0]['at']=first;v['events'][1]['at']=last;values.append(v)
        self.parity([wire(v) for v in values])
        for count in (63,64):
            v=record();v['notes']['complete']=['x'*2048]*count;v['notes']['partial']=['x'*2048]*count
            self.parity([wire(v)])

    def test_all_fields_refuse_inconsistent_substitution(self):
        base=p.advance(verifying(evidence=handoff()),'PRESERVED',now=STAMP);values=[]
        for key in base:
            for bad in (None,True,0,[],{},'unrecognized'):
                v=copy.deepcopy(base);v[key]=bad;values.append(v)
        for section in ('evidence','notes'):
            for key in base[section]:
                for bad in (None,True,0,[],{},'unrecognized'):
                    v=copy.deepcopy(base);v[section][key]=bad;values.append(v)
        for key in base:
            v=copy.deepcopy(base);del v[key];values.append(v)
        v=copy.deepcopy(base);v['extra']='no';values.append(v)
        self.parity([wire(v) for v in values])

    def test_noncanonical_wire_and_bounded_mutations(self):
        raw=wire(record())
        cases=[raw[:-1],raw+b' ',b' '+raw,b'\xef\xbb\xbf'+raw,
               raw.replace(b'"trigger":',b'"trigger":"MANUAL","trigger":',1),b'['*1000+b'0'+b']'*1000]
        for offset in range(0,len(raw),max(1,len(raw)//120)):
            changed=bytearray(raw);changed[offset]^=128;cases.extend((bytes(changed),raw[:offset]))
        self.parity(cases)


if __name__=='__main__':unittest.main()
