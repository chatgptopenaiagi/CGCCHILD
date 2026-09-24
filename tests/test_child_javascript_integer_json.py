"""Lossless bounded integer JSON parity; intentionally not schema acceptance."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
def wire(value,compact):return (json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':') if compact else None)+'\n').encode('ascii')


@unittest.skipUnless(shutil.which('node'),'Node unavailable; integer codec parity not executed')
class IntegerJsonTests(unittest.TestCase):
    def check(self,rows):
        for start in range(0,len(rows),64):
            group=rows[start:start+64]
            request=[dict(hex=raw.hex(),compact=compact) for raw,compact,valid in group]
            run=subprocess.run(['node',str(ROOT/'sdk/javascript/integer_json_conformance.mjs')],input=json.dumps(request).encode(),capture_output=True,timeout=15)
            self.assertEqual((run.returncode,run.stderr),(0,b''))
            self.assertEqual(json.loads(run.stdout),[dict(accepted=True,hex=raw.hex()) if valid else dict(accepted=False) for raw,compact,valid in group])

    def test_large_signed_integers_and_unicode_key_order(self):
        values=[0,1,-1,2**53-1,2**53,2**53+1,2**64-1,-2**64,10**4299,
                {'inode':2**64-1,'small':42,'nested':[True,None,'😀','\ud800']},
                {'\ue000':1,'😀':2,'\ud800':3,'a':4,'\u007f':5},
                {'__proto__':{'polluted':True},'constructor':0}]
        self.check([(wire(value,compact),compact,True) for value in values for compact in (True,False)])

    def test_noncanonical_numbers_duplicates_and_structure(self):
        bad=[b'1.0\n',b'1e0\n',b'-0\n',b'01\n',b'+1\n',b'NaN\n',b'Infinity\n',b'{"a":1,"a":1}\n',
             b'{"b":0,"a":1}\n',b'[1,]\n',b'{"a":1,}\n',b'"\\u0061"\n',b'"\\/"\n',b'"\xff"\n',
             b'1\n0\n',b'1',b' 1\n',b'1\r\n',b'1'+b'0'*4300+b'\n',b'['*33+b'0'+b']'*33+b'\n']
        self.check([(raw,compact,False) for raw in bad for compact in (True,False)])
        self.check([(b'{"a": 1}\n',True,False),(b'{"a":1}\n',False,False)])

    def test_exact_wire_truncations_and_highbit_corruption(self):
        raw=wire({'dev':18446744073709551615,'inode':9007199254740993,'note':'é😀'},True);rows=[]
        for i in range(len(raw)):
            changed=bytearray(raw);changed[i]^=128;rows.extend(((bytes(changed),True,False),(raw[:i],True,False)))
        self.check(rows)

    def test_encode_bounds_ownership_and_no_getter_execution(self):
        run=subprocess.run(['node',str(ROOT/'sdk/javascript/test_integer_json.mjs')],capture_output=True,timeout=15)
        self.assertEqual((run.returncode,run.stderr),(0,b''));self.assertEqual(json.loads(run.stdout),dict(status='PASS',cases=20))


if __name__=='__main__':unittest.main()
