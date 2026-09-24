import copy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from cgc.experimental import state_protocol as sp
from test_child_state_protocol import state


@unittest.skipUnless(shutil.which('node'),'Node not installed; no cross-language acceptance claimed')
class ChildJavaScriptTests(unittest.TestCase):
    def test_independent_codec_corpus(self):
        root=Path(__file__).resolve().parents[1]
        raw=sp.encode(state())
        cases=[raw]+[raw[:i] for i in range(len(raw))]
        for key in ('version','project','domain_empty'):
            needle=('"'+key+'":').encode()
            cases.append(raw.replace(needle,('"'+key+'":"forged","'+key+'":').encode()))
        for identifier in ('id\n','id\r','id\r\n','é','','a'*129,'valid-1'):
            v=state();v['source_instance']=identifier
            cases.append((json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode('ascii'))
        for value in ('01','-1','1.0','9223372036854775808',True,10,'1\n'):
            v=state();v['model']['observed_ns']=value
            cases.append((json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode('ascii'))
        for date in ('0001-01-01T00:00:00Z','9999-12-31T23:59:59Z','0000-01-01T00:00:00Z','2026-02-30T00:00:00Z'):
            v=state();v['captured_at']=date
            cases.append((json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode('ascii'))
        v=state();v['model'].update(observed_ns='9223372036854775806',expires_ns='9223372036854775807')
        cases.append(sp.encode(v))
        expected=[]
        for packet in cases:
            try:
                value=sp.decode(packet)
                expected.append(dict(accepted=True,hex=sp.encode(value).hex(),digest=sp.digest(value),human=sp.render_human(value)))
            except sp.ProtocolError:expected.append(dict(accepted=False))
        run=subprocess.run(['node',str(root/'sdk/javascript/conformance.mjs')],
                           input=json.dumps([x.hex() for x in cases]).encode('ascii'),capture_output=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout),expected)


if __name__=='__main__':unittest.main()
