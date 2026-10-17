import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import inspect_member_evidence_ysm_265 as viewer

class ViewerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.row = dict(owner='example/Owner', name='run', descriptor='()V', access=1,
                        instructions=[dict(offset=0, opcode='0xb1')], exception_handlers=[], code_sha256='snapshot')
        self.write(dict(artifact=dict(sha256='declared'), members=[self.row]))

    def write(self, data):
        (self.root/'e.json').write_text(json.dumps(data))

    def call(self, **kw):
        return viewer.inspect(self.root, 'e.json', 'example.Owner', **kw)

    def test_summary_does_not_return_instruction_payload(self):
        out = self.call()
        self.assertEqual(out['total_matches'], 1)
        self.assertEqual(out['members'][0]['instruction_count'], 1)
        self.assertNotIn('instructions', out['members'][0])
        self.assertFalse(out['artifact_rechecked'])

    def test_full_preserves_complete_selected_record(self):
        self.assertEqual(self.call(name='run', descriptor='()V', full=True)['member'], self.row)

    def test_full_requires_exact_identity_and_match(self):
        for kw in [dict(full=True),dict(name='run',full=True),dict(name='absent',descriptor='()V',full=True)]:
            with self.subTest(kw=kw), self.assertRaises(ValueError): self.call(**kw)

    def test_abstract_native_and_support_collections(self):
        for key in viewer.COLLECTIONS:
            for flag in [0x400,0x100]:
                row=dict(owner='example/Owner',name='noCode',descriptor='()V',access=flag)
                self.write({key:[row]})
                out=self.call(name='noCode',descriptor='()V',full=True)
                self.assertEqual(out['member'],row)
                self.assertNotIn('instructions',out['member'])

    def test_duplicate_same_record_deduplicates_and_conflict_rejects(self):
        self.write(dict(members=[self.row],caller_methods=[self.row]))
        self.assertEqual(self.call()['total_matches'],1)
        other=copy.deepcopy(self.row);other['instructions'][0]['opcode']='0x00'
        self.write(dict(members=[self.row],caller_methods=[other]))
        with self.assertRaises(ValueError):self.call()

    def test_paging_and_limits(self):
        self.write(dict(members=[dict(self.row,name='m'+str(i)) for i in range(25)]))
        self.assertTrue(self.call()['truncated'])
        self.assertEqual(len(self.call(offset=20)['members']),5)
        for kw in [dict(offset=-1),dict(limit=0),dict(limit=101)]:
            with self.assertRaises(ValueError):self.call(**kw)

    def test_unsafe_names_and_symlink_escape(self):
        for name in ['../e.json','/tmp/e.json','sub/e.json','sub\\e.json','e.txt']:
            with self.assertRaises(ValueError):viewer.inspect(self.root,name,'example/Owner')
        with tempfile.TemporaryDirectory() as outside:
            target=Path(outside)/'external.json';target.write_text('{}')
            (self.root/'link.json').symlink_to(target)
            with self.assertRaises(ValueError):viewer.inspect(self.root,'link.json','example/Owner')

    def test_unknown_or_malformed_schema_not_guessed(self):
        for data in [[],{},dict(members={}),dict(members=[{}])]:
            self.write(data)
            with self.assertRaises(ValueError):self.call()

    def test_overloads_are_not_conflated(self):
        second=dict(self.row,descriptor='(F)V')
        self.write(dict(members=[self.row,second]))
        self.assertEqual(self.call(name='run')['total_matches'],2)
        self.assertEqual(self.call(name='run',descriptor='(F)V',full=True)['member'],second)

    def test_missing_owner_is_empty_summary(self):
        out=viewer.inspect(self.root,'e.json','missing/Owner')
        self.assertEqual(out['members'],[])
        self.assertEqual(out['total_matches'],0)

    def test_malformed_artifact_metadata_rejected(self):
        self.write(dict(artifact=None,members=[self.row]))
        with self.assertRaises(ValueError):self.call()

    def test_reads_only_selected_file(self):
        original=Path.read_bytes;reads=[]
        def track(path):
            reads.append(path)
            return original(path)
        with patch.object(Path,'read_bytes',track):self.call()
        self.assertEqual(reads,[(self.root/'e.json').resolve()])

if __name__=='__main__':unittest.main()
