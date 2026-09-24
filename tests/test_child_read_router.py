"""Local route labels never substitute for opaque scoped read handles."""
import copy,json,unittest
from unittest.mock import patch
from cgc.experimental import read_router as router,snapshot_profiles as profiles
import test_child_state_protocol as models
import test_child_chunks as fixtures

def request(route,value,method='status.get',**extra):return router._wire(dict(version=router.VERSION,route=route,method=method,snapshot_digest=profiles.digest(value),**extra))
class RouterTests(unittest.TestCase):
 def setup_router(self):
  r=router.ReadRouter();a=models.state();b=fixtures.large_state();r.register('model',profiles.encode(a),now_ns=0);r.register('continuity',profiles.encode(b),now_ns=0)
  return r,a,b
 def test_two_routes_scope_and_no_io(self):
  with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
   r,a,b=self.setup_router();h=r.issue('model','alice',('status.get',),now_ns=1,expires_ns=100);g=r.issue('continuity','bob',('capsule.chunk',),now_ns=1,expires_ns=100)
   x=json.loads(r.dispatch(h,'alice',request('model',a),now_ns=2));self.assertEqual(x['snapshot_digest'],profiles.digest(a));self.assertFalse(x['mutation_authorized'])
   y=json.loads(r.dispatch(g,'bob',request('continuity',b,'capsule.chunk',offset=0),now_ns=2));self.assertEqual(y['result']['offset'],0);self.assertFalse(y['mutation_authorized'])
  events=r.events('model');events[0]['kind']='changed';self.assertNotEqual(r.events('model')[0]['kind'],'changed')
 def test_cross_route_principal_and_forged_handles_refuse(self):
  r,a,b=self.setup_router();h=r.issue('model','alice',('status.get',),now_ns=1,expires_ns=100)
  other,_,_=self.setup_router();foreign=other.issue('model','alice',('status.get',),now_ns=1,expires_ns=100)
  for handle,principal,raw in [(foreign,'alice',request('model',a)),(h,'alice',request('continuity',b)),(h,'bob',request('model',a)),(router.RoutedGrant(),'alice',request('model',a)),('model','alice',request('model',a)),(h,'alice',request('model',b)),(h,'alice',request('model',a,'capsule.export'))]:
   with self.assertRaises(router.RouteDenied):r.dispatch(handle,principal,raw,now_ns=2)
 def test_revocation_expiry_and_clock_rollback(self):
  r,a,b=self.setup_router();h=r.issue('model','alice',('status.get',),now_ns=1,expires_ns=3)
  with self.assertRaises(router.RouteDenied):r.dispatch(h,'alice',request('model',a),now_ns=3)
  g=r.issue('continuity','bob',('status.get',),now_ns=3,expires_ns=10);r.revoke(g,now_ns=4)
  with self.assertRaises(router.RouteDenied):r.dispatch(g,'bob',request('continuity',b),now_ns=4)
  with self.assertRaises(router.RouteDenied):r.dispatch(h,'alice',request('model',a),now_ns=2)
  with self.assertRaises(router.RouteDenied):r.register('later',profiles.encode(a),now_ns=5)
  r.close();r.close()
 def test_wire_generic_authority_and_duplicates_refuse(self):
  r,a,b=self.setup_router();h=r.issue('model','alice',('status.get',),now_ns=1,expires_ns=100);raw=request('model',a)
  for bad in [raw+b' ',raw[:-1],raw.replace(b'"route":"model"',b'"route":"model","route":"model"'),b'X'*(router.MAX_REQUEST+1),request('model',a,'execute'),request('model',a,path='/arbitrary'),request('model',a,'capsule.chunk',offset=True)]:
   with self.assertRaises(router.RouteDenied):r.dispatch(h,'alice',bad,now_ns=2)
 def test_underlying_source_budget_cannot_be_reset(self):
  r,a,b=self.setup_router();h=r.issue('model','alice',('status.get',),now_ns=1,expires_ns=100)
  for i in range(63):r.dispatch(h,'alice',request('model',a),now_ns=2)
  with self.assertRaises(router.RouteDenied):r.dispatch(h,'alice',request('model',a),now_ns=2)
  with self.assertRaises(router.RouteDenied):r.issue('model','alice',('status.get',),now_ns=2,expires_ns=100)
  g=r.issue('continuity','bob',('status.get',),now_ns=2,expires_ns=100);self.assertFalse(json.loads(r.dispatch(g,'bob',request('continuity',b),now_ns=3))['mutation_authorized'])
 def test_registration_and_call_bounds(self):
  r=router.ReadRouter();a=models.state()
  for i in range(router.MAX_ROUTES):r.register('r'+str(i),profiles.encode(a),now_ns=0)
  for name in ['extra','r0']:
   with self.assertRaises(router.RouteDenied):r.register(name,profiles.encode(a),now_ns=0)
  for i in range(router.MAX_CALLS):
   with self.assertRaises(router.RouteDenied):r.dispatch(None,'nobody',b'{}',now_ns=0)
  with self.assertRaises(router.RouteDenied):r.issue('r0','alice',('status.get',),now_ns=0,expires_ns=1)
if __name__=='__main__':unittest.main()
