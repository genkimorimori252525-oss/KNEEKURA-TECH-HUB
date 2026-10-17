import unittest
from inherited_call_candidates_ysm_265 import ancestry,classify,validate_instance_target

def cls(parent=None,interfaces=(),methods=()):return dict(super=parent,interfaces=list(interfaces),methods=list(methods))
def method(name='run',descriptor='()V',access=1):return dict(name=name,descriptor=descriptor,access=access)
class CandidatesTest(unittest.TestCase):
    def setUp(self):
        self.target=('I','run','()V');self.classes={'I':cls(methods=[method()]),'Base':cls('External',['I']),'Child':cls('Base'),'Other':cls()};self.ref=dict(owner='Child',name='run',descriptor='()V')
    def test_exact_owner_still_not_dispatch(self):
        r=classify(dict(self.ref,owner='I'),self.target,self.classes);self.assertEqual(r['category'],'EXACT_SYMBOLIC_OWNER');self.assertFalse(r['dispatch_resolved'])
    def test_inherited_interface_path(self):
        r=classify(self.ref,self.target,self.classes);self.assertEqual(r['ancestry_path'],['Child','Base','I']);self.assertEqual(r['category'],'NOMINAL_DESCENDANT_CANDIDATE')
    def test_override_does_not_become_proven_target_call(self):
        self.classes['Child']['methods']=[method()];r=classify(self.ref,self.target,self.classes);self.assertEqual(r['same_signature_declarations_on_path'],[dict(owner='Child',access=1)]);self.assertFalse(r['dispatch_resolved'])
    def test_external_unknown_not_absence_proof(self):
        r=classify(dict(self.ref,owner='Unknown'),self.target,self.classes);self.assertEqual(r['missing_ancestor_declarations'],['Unknown']);self.assertEqual(r['category'],'SAME_SIGNATURE_NO_PROVEN_ANCESTRY')
    def test_unrelated_signature_matches_are_not_descendants(self):
        self.assertEqual(classify(dict(self.ref,owner='Other'),self.target,self.classes)['category'],'SAME_SIGNATURE_NO_PROVEN_ANCESTRY')
    def test_overload_and_name_mismatch_ignored(self):
        self.assertIsNone(classify(dict(self.ref,descriptor='(I)V'),self.target,self.classes));self.assertIsNone(classify(dict(self.ref,name='other'),self.target,self.classes))
    def test_cycles_terminate(self):
        self.classes.update(A=cls('B'),B=cls('A'));self.assertEqual(ancestry('A','I',self.classes),(None,[]))
    def test_diamond_interface(self):
        self.classes.update(J=cls(interfaces=['I']),K=cls(interfaces=['I']),D=cls(interfaces=['J','K']));self.assertEqual(ancestry('D','I',self.classes)[0],['D','J','I'])
    def test_missing_target_rejected(self):
        with self.assertRaises(ValueError):validate_instance_target(('I','rn','()V'),self.classes)
    def test_static_private_constructor_rejected(self):
        for m in [method(access=9),method(access=2),method(name='<init>')]:
            self.classes['I']['methods']=[m]
            with self.subTest(m=m),self.assertRaises(ValueError):validate_instance_target(('I',m['name'],m['descriptor']),self.classes)
    def test_abstract_instance_supported(self):
        self.classes['I']['methods']=[method(access=1025)];self.assertEqual(validate_instance_target(self.target,self.classes)['access'],1025)
if __name__=='__main__':unittest.main()
