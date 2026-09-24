import io
import hashlib
import json
import unittest
from cgc.experimental import snapshot_profiles as profiles,continuity,capsule,readonly_service,mcp_stdio
from cgc.experimental.state_protocol import encode as model_encode
from test_child_state_protocol import state
from test_child_continuity import source_state
from test_child_mcp import init,req


class ChildProfilesTests(unittest.TestCase):
    def setUp(self):self.continuity=continuity.project(source_state(),portable_project_id='fixture')

    def test_both_profiles_lossless_capsules(self):
        for value,kind in ((state(),profiles.MODEL),(self.continuity,profiles.CONTINUITY)):
            raw=profiles.encode(value)
            self.assertEqual(profiles.kind(profiles.decode(raw)),kind)
            archive=capsule.export_capsule(value)
            self.assertEqual(capsule.import_capsule(archive).snapshot(),value)
            self.assertEqual(capsule.export_capsule(capsule.import_capsule(archive).snapshot()),archive)

    def test_fixed_registry_and_cross_profile_confusion(self):
        for value in ({'version':'remote-schema','schema':'https://invalid.test/schema'},
                      dict(self.continuity,version=state()['version']),dict(state(),version=continuity.VERSION)):
            with self.assertRaises(profiles.ProfileError):profiles.encode(value)
        with self.assertRaises(profiles.ProfileError):profiles.decode(b'{"version":"x","version":"y"}\n')

    def test_core_continuity_projection(self):
        core=readonly_service.ReadOnlyCore(profiles.encode(self.continuity))
        for method in readonly_service.METHODS:
            request=dict(id='x',method=method,snapshot_digest=profiles.digest(self.continuity))
            if method=='capsule.chunk':request['offset']=0
            wire=(json.dumps(request)+'\n').encode()
            out=json.loads(core.dispatch(wire));self.assertFalse(out['mutation_authorized'])
            self.assertNotIn('error',out)
            if method=='state.get':self.assertEqual(out['result'],self.continuity)
            if method=='status.get':
                self.assertIn('Latest attempt: FAILED',out['result']['text'])
                self.assertIn('Current safe to resume: UNKNOWN',out['result']['text'])

    def test_mcp_continuity_calls_core(self):
        adapter=mcp_stdio.MCPAdapter(profiles.encode(self.continuity))
        adapter.handle(init());adapter.handle(req('notifications/initialized',identifier=None))
        out=json.loads(adapter.handle(req('tools/call',dict(name='cgcchild_state',arguments={'snapshot_digest':profiles.digest(self.continuity)}))))
        self.assertEqual(out['result']['structuredContent']['result'],self.continuity)
        self.assertFalse(out['result']['structuredContent']['mutation_authorized'])

    def test_existing_model_bytes_unchanged(self):
        self.assertEqual(profiles.encode(state()),model_encode(state()))

    def test_large_valid_continuity_archive_but_transport_refuses(self):
        source=source_state();slot=source['last_known_good']
        slot['record']['notes']['complete']=['inert-'+str(n)+'-'+'x'*1800 for n in range(60)]
        del slot['digest']
        slot['digest']=hashlib.sha256((json.dumps(slot,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
        value=continuity.project(source,portable_project_id='fixture')
        self.assertGreater(len(profiles.encode(value)),readonly_service.MAX_RESPONSE)
        self.assertEqual(capsule.import_capsule(capsule.export_capsule(value)).snapshot(),value)
        core=readonly_service.ReadOnlyCore(profiles.encode(value))
        request=(json.dumps(dict(id='x',method='state.get',snapshot_digest=profiles.digest(value)))+'\n').encode()
        self.assertEqual(json.loads(core.dispatch(request))['error'],'RESPONSE_LIMIT')


if __name__=='__main__':unittest.main()
