#!/usr/bin/env python3
import importlib,unittest
class StackGuardTests(unittest.TestCase):
 def setUp(self):
  try:self.m=importlib.import_module('native_candidate_stack_guard_ysm_265')
  except ModuleNotFoundError:self.fail('The fixed candidate-stack proof helper is not implemented')
 def test_known_rax_and_zero_rdx(self):
  r=self.m.known_stack_inputs();self.assertEqual((r['rax_after_cbw'],r['rdx_at_zero_store']),(1,0))
 def test_stack_guard_for_all_cl_values(self):
  self.assertTrue(callable(getattr(self.m,'stack_shift_word',None)),'Stack transfer proof is not implemented')
  for cl in range(256):
   for r10 in (0,0x8a,0xffff):
    r=self.m.stack_shift_word(cl,r10,0xffffffffffffffff,0)
    self.assertEqual((r['shift_word'],r['carry_after_shr15']),(0,0))
 def test_nonzero_store_changes_condition(self):
  self.assertTrue(callable(getattr(self.m,'stack_shift_word',None)),'Stack transfer proof is not implemented')
  self.assertEqual(self.m.stack_shift_word(0,0,0,1<<62)['carry_after_shr15'],1)
 def test_reject_out_of_byte_range(self):
  self.assertTrue(callable(getattr(self.m,'stack_shift_word',None)),'Stack transfer proof is not implemented')
  for cl in (-1,256):
   with self.assertRaises(ValueError):self.m.stack_shift_word(cl,0,0,0)
 def test_reject_changed_prefix(self):
  self.assertTrue(callable(getattr(self.m,'validate_parts',None)),'Prefix validation is not implemented')
  with self.assertRaises(ValueError):self.m.validate_parts([bytes(207),bytes(61)])
 def test_reject_missing_prefix(self):
  self.assertTrue(callable(getattr(self.m,'validate_parts',None)),'Prefix validation is not implemented')
  with self.assertRaises(ValueError):self.m.validate_parts([])
if __name__=='__main__':unittest.main()
