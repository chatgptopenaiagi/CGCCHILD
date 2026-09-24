import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cgcchild import sdk
from cgcchild.core import Workbench, read_input, save_new, security_debt, resource
from cgcchild.execution import (Mode, ACTIONS, plan, NullExecutor, DryRunExecutor,
    SimulationExecutor, LocalExperimentalExecutor, ProductionExecutorPlaceholder)
from cgcchild.evidence import FilesystemClosureAssessment, WriterInventory, Truth
from cgcchild.cli import main


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.value = sdk.decode(resource('example.json'))

    def test_default_has_no_implicit_observation(self):
        with patch('subprocess.Popen', side_effect=AssertionError('process forbidden')):
            app = Workbench()
            self.assertEqual(app.status()['mode'], 'READ_ONLY_SAFE')
            self.assertFalse(app.status()['snapshot_loaded'])
            self.assertFalse(app.status()['mutation_authorized'])

    def test_every_mode_refuses_real_execution(self):
        for mode in Mode:
            for action in ACTIONS:
                for executor in (NullExecutor(), LocalExperimentalExecutor(), ProductionExecutorPlaceholder()):
                    result = executor.execute(action, mode)
                    self.assertEqual(result['state'], 'REFUSED')
                    self.assertFalse(result['mutation_authorized'])
                self.assertEqual(DryRunExecutor().execute(action, mode)['effects'], [])

    def test_simulation_requires_explicit_mode_and_never_promotes(self):
        self.assertEqual(SimulationExecutor().execute('CHECKPOINT')['state'], 'REFUSED')
        for mode in (Mode.SIMULATION, Mode.DEVELOPER_LAB):
            result = SimulationExecutor().execute('CHECKPOINT', mode)
            self.assertEqual(result['state'], 'SIMULATED')
            self.assertEqual(result['production_p3'], 'UNKNOWN')
            self.assertFalse(result['mutation_authorized'])
        for action in ('shell', {}, None):
            with self.assertRaises(ValueError): plan(action)
        with self.assertRaises(ValueError): plan('CHECKPOINT', 'SIMULATION')

    def test_input_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'test.cgcpack'
            raw = sdk.export_capsule(self.value)
            save_new(path, raw)
            self.assertEqual(read_input(path), self.value)
            with self.assertRaises(FileExistsError): save_new(path, b'bad')
            self.assertEqual(path.read_bytes(), raw)
            for name in ('auth.json', 'credentials.json', 'test.exe'):
                p = Path(folder)/name
                p.write_bytes(b'not read')
                with self.assertRaises(ValueError): read_input(p)

    def test_invalid_and_oversized_input(self):
        from cgc.experimental.capsule import MAX_BYTES
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'data.json'
            for raw in (b'{}', b'x'*(MAX_BYTES+1), resource('example.json').replace(b'UNKNOWN', b'YES')):
                path.write_bytes(raw)
                with self.assertRaises(ValueError): read_input(path)

    def test_detached_state_and_historical_review(self):
        app = Workbench()
        app.load(self.value)
        self.value['safe_to_resume'] = 'YES'
        self.assertEqual(app.snapshot()['safe_to_resume'], 'UNKNOWN')
        self.assertFalse(app.review()['current_repository_checked'])
        self.assertFalse(app.review()['mutation_authorized'])

    def test_debt_contract(self):
        required = {'debt_id','claim','current_status','missing_evidence','affected_features',
                    'runtime_consequence','safe_fallback','future_acceptance_test','blocking_or_nonblocking'}
        items = security_debt()
        self.assertEqual(len({x['debt_id'] for x in items}), len(items))
        for item in items:
            self.assertEqual(set(item), required)
            self.assertEqual(item['blocking_or_nonblocking']['product_build'], 'NONBLOCKING')

    def test_provider_labels_do_not_close_production(self):
        report = FilesystemClosureAssessment(writers=WriterInventory(Truth.YES)).report()
        self.assertEqual(report['production_status'], 'UNKNOWN')

    def test_cli_safe_defaults_and_refusal(self):
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main(['status']), 0)
            self.assertFalse(json.loads(out.getvalue())['mutation_authorized'])
        with patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(main(['simulate', 'CHECKPOINT']), 1)
            self.assertEqual(main(['--mode','SIMULATION','simulate','CHECKPOINT']), 0)

    def test_sdk_errors_and_byte_parity(self):
        with self.assertRaisesRegex(ValueError, '^UNSUPPORTED_SDK_VERSION$'): sdk.negotiate('future')
        with self.assertRaisesRegex(ValueError, '^INVALID_SNAPSHOT$'): sdk.decode(b'{}')
        with self.assertRaisesRegex(ValueError, '^INVALID_CAPSULE$'): sdk.import_capsule(b'bad')
        code = "import fs from 'node:fs'; import * as m from './sdk/javascript/index.mjs'; const v=m.decode(fs.readFileSync(0)); process.stdout.write(m.capsuleExport(v));"
        result = subprocess.run(['node','--input-type=module','-e',code],input=sdk.encode(self.value),capture_output=True,timeout=10,check=True)
        self.assertEqual(result.stdout, sdk.export_capsule(self.value))
        self.assertEqual(sdk.import_capsule(result.stdout), self.value)

    def test_service_real_process(self):
        request = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'snapshot.json'
            path.write_bytes(sdk.encode(self.value))
            result = subprocess.run([sys.executable,'-m','cgcchild','serve','--input',str(path)],input=request,capture_output=True,timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['id'], 1)
            self.assertIn('result', json.loads(result.stdout))


if __name__ == '__main__': unittest.main()
