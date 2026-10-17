import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import evidence_locator_ysm_265 as locator


class LocatorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write('A-EVIDENCE.json', {'members': [
            {'owner': 'com.example.A', 'name': 'x', 'descriptor': '()V'},
            {'owner': 'com.example.A', 'name': 'y', 'descriptor': '()V'}]})
        self.write('B-EVIDENCE.json', {'bounded_dependency_support': [
            {'owner': 'com/example/A', 'name': 'x', 'descriptor': '()V'}]})
        self.write('UNSUPPORTED-EVIDENCE.json', {'references': [{'owner': 'invented'}]})
        self.write(locator.MAP, {'mappings': [{'kind': 'class', 'obfuscated_owner': 'com.example.A',
            'semantic_owner': 'role.Animation', 'confidence': 'HIGH'}]})
        (self.root / locator.LOOKUP).write_text(json.dumps({'query': 'ysm.test', 'target': {'owner': 'com/example/A'}})+'\n')
        (self.root / 'TEST-RECOVERY.md').write_text('A bounded document')

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def invoke(self, *args):
        out = io.StringIO()
        with patch('sys.argv', ['locator', '--root', str(self.root), *args]), contextlib.redirect_stdout(out):
            locator.main()
        return json.loads(out.getvalue())

    def test_build_deterministic_and_no_reference_promotion(self):
        a = locator.build(self.root)
        self.assertEqual(a, locator.build(self.root))
        self.assertEqual(a['owners'], {'com/example/A': ['A-EVIDENCE.json', 'B-EVIDENCE.json']})
        self.assertEqual(a['unindexed_evidence_schemas'], ['UNSUPPORTED-EVIDENCE.json'])

    def test_short_owner_role_and_case_search(self):
        index = locator.build(self.root)
        self.assertEqual(locator.search(index, owner='ANIMATION')['total_matches'], 1)
        self.assertEqual(locator.search(index, owner='com.example.A')['total_matches'], 1)
        self.assertEqual(locator.search(index, owner='no-such-role')['results'], [])

    def test_query_and_topic(self):
        index = locator.build(self.root)
        self.assertEqual(locator.search(index, query='YSM.TEST')['results'][0]['evidence'], ['A-EVIDENCE.json', 'B-EVIDENCE.json'])
        self.assertEqual(locator.search(index, topic='test')['results'], [{'document': 'TEST-RECOVERY.md'}])

    def test_bounded_results(self):
        index = locator.build(self.root)
        index['documents'] += ['TEST-SECOND-RECOVERY.md']
        result = locator.search(index, topic='test', limit=1)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['total_matches'], 2)
        self.assertEqual(len(result['results']), 1)

    def test_default_search_does_not_rebuild_or_check(self):
        self.invoke('--build')
        (self.root / 'A-EVIDENCE.json').unlink()
        result = self.invoke('--owner', 'A')
        self.assertEqual(result['freshness'], 'UNCHECKED_SNAPSHOT')
        self.assertEqual(result['total_matches'], 1)

    def test_selected_hash_missing_or_stale(self):
        self.invoke('--build')
        self.assertEqual(self.invoke('--query', 'ysm.test', '--check-selected')['freshness'], 'SELECTED_FILES_MATCH')
        self.write('A-EVIDENCE.json', {'changed': True})
        with self.assertRaises(SystemExit) as ex:
            self.invoke('--query', 'ysm.test', '--check-selected')
        self.assertEqual(ex.exception.code, 1)

    def test_topic_hash_is_checked(self):
        self.invoke('--build')
        (self.root / 'TEST-RECOVERY.md').write_text('changed')
        with self.assertRaises(SystemExit):
            self.invoke('--topic', 'test', '--check-selected')

    def test_unrelated_changes_do_not_run_global_check(self):
        self.invoke('--build')
        self.write('UNSUPPORTED-EVIDENCE.json', {'changed': True})
        self.assertEqual(self.invoke('--query', 'ysm.test', '--check-selected')['freshness'], 'SELECTED_FILES_MATCH')

    def test_extra_catalog_keeps_both_branch_sites(self):
        rows = [{'query': 'ctrl.test', 'target': {'kind': 'registration-site', 'owner': 'com/example/A', 'name': name},
                 'scope': 'branch not evaluated'} for name in ('real', 'fallback')]
        (self.root / locator.EXTRA_LOOKUP).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.invoke('--build')
        result = self.invoke('--query', 'ctrl.test', '--check-selected')
        self.assertEqual(result['total_matches'], 2)
        self.assertEqual({r['target']['name'] for r in result['results']}, {'real', 'fallback'})
        self.assertEqual({r['scope'] for r in result['results']}, {'branch not evaluated'})
        self.assertTrue(result['selected_hashes'][locator.EXTRA_LOOKUP])

    def test_index_is_not_its_own_evidence(self):
        self.invoke('--build')
        self.write('EVIDENCE-LOCATOR-VERIFICATION-2026-10-17.json', {'receipt': True})
        index = locator.build(self.root)
        self.assertNotIn(locator.INDEX, index['unindexed_evidence_schemas'])
        self.assertNotIn('EVIDENCE-LOCATOR-VERIFICATION-2026-10-17.json', index['unindexed_evidence_schemas'])


if __name__ == '__main__':
    unittest.main()
