import dataclasses
import unittest
from unittest.mock import patch
from cgc.experimental import filesystem_model as fs
from cgc.experimental.quiescence import Truth


def model(action='CREATE_CHECKPOINT',status=Truth.YES):
    return fs.Model('fixture','epoch',action,10,20,
                    tuple(fs.Cell(d,c,status) for d,c in fs.required_cells(action)))


def assess(value,**overrides):
    args=dict(project='fixture',generation='epoch',action=value.action,now_ns=15);args.update(overrides)
    return fs.assess(value,**args)


class ChildFilesystemModelTests(unittest.TestCase):
    def test_every_action_scope_never_produces_live_proof(self):
        with patch('builtins.open',side_effect=AssertionError('file')),patch('subprocess.Popen',side_effect=AssertionError('process')):
            for action in fs.SCOPES:
                result=assess(model(action))
                expected='NOT_APPLICABLE' if action=='READ_ONLY_ANALYSIS' else 'UNKNOWN' if action=='REPAIR_KNOWN_FAILURE' else 'YES'
                self.assertEqual(result.model_filesystem,expected)
                self.assertIs(result.production_filesystem,Truth.UNKNOWN)
                self.assertIs(result.production_p3,Truth.UNKNOWN)
                self.assertFalse(result.mutation_authorized)

    def test_each_missing_or_unknown_route_blocks(self):
        value=model('PUBLISH_CHECKPOINT')
        for index,cell in enumerate(value.cells):
            cells=value.cells[:index]+value.cells[index+1:]
            result=assess(dataclasses.replace(value,cells=cells))
            self.assertEqual(result.model_filesystem,'UNKNOWN')
            self.assertIn((cell.domain,cell.channel),result.missing)
            cells=value.cells[:index]+(dataclasses.replace(cell,status=Truth.UNKNOWN),)+value.cells[index+1:]
            self.assertEqual(assess(dataclasses.replace(value,cells=cells)).model_filesystem,'UNKNOWN')

    def test_each_contradiction_is_preserved(self):
        value=model()
        for index,cell in enumerate(value.cells):
            cells=value.cells[:index]+(dataclasses.replace(cell,status=Truth.NO),)+value.cells[index+1:]
            result=assess(dataclasses.replace(value,cells=cells))
            self.assertEqual(result.model_filesystem,'NO')
            self.assertEqual(result.contradicted,((cell.domain,cell.channel),))

    def test_linux_only_cannot_close_windows_alias_or_descriptor_routes(self):
        value=model()
        cells=tuple(c for c in value.cells if c.channel=='LINUX_DOMAIN')
        result=assess(dataclasses.replace(value,cells=cells))
        self.assertEqual(result.model_filesystem,'UNKNOWN')
        for channel in ('WINDOWS_HOST','ALIASES','PREOPENED_DESCRIPTORS','DEPUTIES','QUEUED_IO'):
            self.assertIn(('WORKTREE',channel),result.missing)

    def test_binding_freshness_and_imported_evidence(self):
        value=model()
        for overrides in ({'project':'other'},{'generation':'other'},{'action':'RUN_TESTS'},
                          {'now_ns':9},{'now_ns':20}):
            self.assertEqual(assess(value,**overrides).model_filesystem,'UNKNOWN')
        self.assertEqual(assess(dataclasses.replace(value,provenance='IMPORTED')).model_filesystem,'UNKNOWN')

    def test_bounds_duplicates_order_and_no_live_label(self):
        value=model()
        for changes in ({'cells':value.cells+(value.cells[0],)},
                        {'cells':tuple(reversed(value.cells))},{'cells':list(value.cells)},
                        {'cells':(fs.Cell('DESTINATION_REFS','WINDOWS_HOST',Truth.YES),)},
                        {'provenance':'LIVE'},{'project':'/path'},{'expires_ns':True},
                        {'expires_ns':10+fs.MAX_TTL_NS+1},{'action':'ARBITRARY_EXEC'}):
            with self.subTest(changes=tuple(changes)),self.assertRaises(ValueError):dataclasses.replace(value,**changes)
        with self.assertRaises(ValueError):fs.Cell('WORKTREE','LINUX_DOMAIN','YES')


if __name__=='__main__':unittest.main()
