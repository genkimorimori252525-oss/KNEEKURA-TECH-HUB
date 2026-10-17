import unittest
from unittest.mock import patch
import validate_member_targets_ysm_265 as validator

class TargetValidationTest(unittest.TestCase):
    def setUp(self):
        self.owner='example/Owner'
        self.method=(self.owner,'run','()V')
        self.field=(self.owner,'count','I')
        self.data=dict(methods={self.method,(self.owner,'<init>','(I)V')},fields={self.field},classes={self.owner},class_count=1)

    def test_exact_method_and_field(self):
        rows=validator.validate_targets([self.method,self.field],self.data)
        self.assertEqual({r['kind'] for r in rows},{'methods','fields'})
        self.assertTrue(all(r['declaration_present'] for r in rows))

    def test_one_character_owner_error_rejected(self):
        with self.assertRaises(ValueError):validator.validate_targets([('example/Ownr','run','()V')],self.data)

    def test_wrong_name_descriptor_and_kind_rejected(self):
        for t in [(self.owner,'other','()V'),(self.owner,'run','(I)V'),(self.owner,'count','()I')]:
            with self.subTest(t=t),self.assertRaises(ValueError):validator.validate_targets([t],self.data)

    def test_empty_and_malformed_rejected(self):
        for targets in [[],[self.owner],[('x','y')],[(self.owner,None,'()V')]]:
            with self.subTest(targets=targets),self.assertRaises(ValueError):validator.validate_targets(targets,self.data)

    def test_declared_constructor(self):
        self.assertEqual(validator.validate_targets([(self.owner,'<init>','(I)V')],self.data)[0]['kind'],'methods')

    def test_class_inventory_is_explicit_separate_schema(self):
        self.assertEqual(validator.validate_inventory_targets([self.owner],self.data)[0]['kind'],'classes')
        with self.assertRaises(ValueError):validator.validate_inventory_targets(['example/Missing'],self.data)
        with self.assertRaises(ValueError):validator.validate_inventory_targets(None,self.data)

    def test_deduplicate_exact_members(self):
        self.assertEqual(len(validator.validate_targets([self.method,list(self.method)],self.data)),1)

    def test_index_reads_class_declarations_not_resources(self):
        class Archive:
            def namelist(self):return ['example/Owner.class','readme.txt']
            def read(self,name):
                if name!='example/Owner.class':raise AssertionError('resource read')
                return b'snapshot'
        declaration=dict(methods=[dict(name='run',descriptor='()V')],fields=[dict(name='count',descriptor='I')])
        with patch.object(validator,'parse_class',return_value=declaration):result=validator.declaration_index(Archive())
        self.assertEqual(result['class_count'],1)
        self.assertEqual(result['classes'],{self.owner})
        self.assertIn(self.method,result['methods'])
        self.assertIn(self.field,result['fields'])

if __name__=='__main__':unittest.main()
