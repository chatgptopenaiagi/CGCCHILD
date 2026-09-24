"""Static evidence audit never runs a fixture or grants current acceptance."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'docs'/'lab'
spec=importlib.util.spec_from_file_location('child_native_audit',ROOT/'child_evidence_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def read(self,name):return (ROOT/name).read_bytes()

    def test_actual_bindings_and_no_execution(self):
        with patch('subprocess.Popen',side_effect=AssertionError('execute')):
            result=audit.audit(ROOT)
        self.assertEqual(len(result['fixtures']),30)
        self.assertEqual(result['files_read'],92)
        self.assertFalse(result['production_accepted'])
        bootstrap=next(x for x in result['fixtures'] if x['fixture']=='child_bootstrap')
        self.assertEqual(bootstrap['driver_binding'],'UNRECORDED')
        for row in result['fixtures']:
            self.assertEqual(row['current_execution'],'NOT_EXECUTED')
            self.assertEqual(row['generated_and_binary_artifacts'],'NOT_REBUILT')

    def test_changed_missing_and_oversized_sources_refuse(self):
        target='child_protocol.c'
        for raw in (b'changed',b'',b'x'*(audit.MAX_BYTES+1)):
            def read(name):return raw if name==target else self.read(name)
            with self.assertRaises(audit.AuditError):audit.audit_reader(read)
        def missing(name):
            if name==target:raise FileNotFoundError('do not expose arbitrary path')
            return self.read(name)
        with self.assertRaisesRegex(audit.AuditError,'INVALID_OR_MISSING_ARTIFACT'):audit.audit_reader(missing)

    def test_binding_omission_and_extra_header_refuse(self):
        target='child_dbus_bound_socket_evidence.json'
        for mutation in ('missing','header','shape'):
            value=json.loads(self.read(target))
            if mutation=='missing':del value['prefixes_sha256']
            elif mutation=='header':value['prefixes_sha256']['evil.h']='0'*64
            else:value['prefixes_sha256']=[]
            raw=json.dumps(value).encode()
            with self.assertRaises(audit.AuditError):audit.audit_reader(lambda n:raw if n==target else self.read(n))

    def test_duplicate_json_and_changed_driver_refuse(self):
        target='child_ancillary_evidence.json'
        raw=self.read(target).replace(b'{',b'{"source_sha256":"0",',1)
        with self.assertRaisesRegex(audit.AuditError,'DUPLICATE_EVIDENCE_KEY'):
            audit.audit_reader(lambda n:raw if n==target else self.read(n))
        with self.assertRaisesRegex(audit.AuditError,'DIGEST_MISMATCH'):
            audit.audit_reader(lambda n:b'changed' if n=='child_ancillary_validate.py' else self.read(n))

    def test_consistency_is_not_source_authentication(self):
        # Replacing BOTH a covered artifact and its expected hash is consistent, not authenticated.
        target='child_bootstrap.c';evidence='child_bootstrap_evidence.json';raw=self.read(target)+b'\n'
        value=json.loads(self.read(evidence));value['source_sha256']=audit.sha(raw)
        def read(name):return raw if name==target else json.dumps(value).encode() if name==evidence else self.read(name)
        result=audit.audit_reader(read)
        self.assertFalse(result['production_accepted']);self.assertEqual(result['live_proof'],'UNKNOWN')


if __name__=='__main__':unittest.main()
