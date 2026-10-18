"""Checkpoint state equivalence and rejection tests using authored instructions only."""
import io,json,unittest,copy
from native_shadow_image_ysm_265 import ShadowGuardedCPU
from native_guarded_checkpoint_ysm_265 import capture,restore,pack,unpack,ContextHeader,sanitize_context
from native_unicorn_guarded_ysm_265 import SP,STACK,STACK_SIZE,LEGACY_STACK,LEGACY_STACK_SIZE,HEAP,X,REGS
CODE=0x100000;DATA=0x200000
class CheckpointTests(unittest.TestCase):
 def cpu(self,limit=1):
  c=ShadowGuardedCPU(io.StringIO(),'heap',limit,5);c.add_image(CODE,bytes.fromhex('488903488b0b4883c101')+b'\x90');c.add_image(DATA,bytes(4096),False);c.protect_image();c.reg('RAX',0x123456789abc);c.reg('RBX',DATA);return c
 def stopped(self):
  c=self.cpu();c.grant_shadow_range(DATA,16,7);c.allocate(24);c.write_private(SP+32,b'abc');c.opaque[SP+64]=SP+128;c.uc.reg_write(X.UC_X86_REG_XMM15,0x123456789abcdef0123456789abcdef0);c.run(CODE);return c
 def test_full_cpu_private_and_image_state_roundtrip(self):
  c=self.stopped();state=json.loads(json.dumps(capture(c)));r=self.cpu();restore(r,state)
  self.assertEqual({x:c.reg(x) for x in REGS},{x:r.reg(x) for x in REGS});self.assertEqual(c.uc.reg_read(X.UC_X86_REG_EFLAGS),r.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(c.uc.reg_read(X.UC_X86_REG_XMM15),r.uc.reg_read(X.UC_X86_REG_XMM15));self.assertEqual(c.known,r.known);self.assertEqual(c.opaque,r.opaque);self.assertEqual(c.read_known(SP+32,3),r.read_known(SP+32,3));self.assertTrue(r.expected_image_matches());self.assertEqual(r.shadow_events,1);self.assertEqual(r.origin_completed,1);self.assertEqual(r.attempted,0)
 def test_resumed_execution_equals_uninterrupted(self):
  c=self.stopped();r=self.cpu(limit=2);restore(r,capture(c));r.run(r.reg('RIP'));full=self.cpu(limit=3);full.grant_shadow_range(DATA,16,7);full.run(CODE)
  self.assertEqual({x:full.reg(x) for x in REGS},{x:r.reg(x) for x in REGS});self.assertEqual(full.uc.reg_read(X.UC_X86_REG_EFLAGS),r.uc.reg_read(X.UC_X86_REG_EFLAGS));self.assertEqual(full.read_known(DATA,8),r.read_known(DATA,8));self.assertEqual(r.completed,2)
 def test_image_mismatch_rejected(self):
  state=capture(self.stopped());state['images'][0]=(CODE,CODE+10,'bad');r=self.cpu()
  with self.assertRaises(ValueError):restore(r,state)
 def test_engine_mismatch_rejected(self):
  state=capture(self.stopped());state['engine']='other'
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_context_size_mismatch_rejected(self):
  state=capture(self.stopped());state['context']['size']+=1
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_bad_known_mask_rejected(self):
  state=capture(self.stopped());state['private'][str(STACK)]['known']=pack(bytes([2])*STACK_SIZE)
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_patch_outside_image_rejected(self):
  state=capture(self.stopped());state['patches']=[[SP,'01']]
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_patch_without_writable_history_rejected(self):
  state=capture(self.stopped());state['shadow_ranges']=[]
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_bounded_decompression(self):
  with self.assertRaises(ValueError):unpack(pack(bytes(4096)),8)
 def test_serialized_context_has_no_memory_snapshot_pointers(self):
  state=capture(self.stopped());m=state['context'];raw=unpack(m['bytes'],m['size']);h=ContextHeader.from_buffer_copy(raw);self.assertIsNone(h.last_block);self.assertIsNone(h.fv);self.assertEqual(h.snapshot_level,0)
 def test_bad_cpu_header_rejected(self):
  state=capture(self.stopped());m=state['context'];raw=bytearray(unpack(m['bytes'],m['size']));raw[0]^=1;m['bytes']=pack(raw)
  with self.assertRaises(ValueError):restore(self.cpu(),state)
 def test_crc_diagnostic_counters_roundtrip(self):
  c=self.stopped();c.crc_blocks=15;c.crc_iterations=23591981;c.crc_logical_steps=528156776;r=self.cpu();restore(r,capture(c));self.assertEqual((r.crc_blocks,r.crc_iterations,r.crc_logical_steps),(15,23591981,528156776));self.assertTrue(r.crc_counters_complete)
 def test_legacy_missing_crc_diagnostics_are_marked_incomplete(self):
  state=capture(self.stopped())
  for key in ('crc_blocks','crc_iterations','crc_logical_steps','crc_counters_complete'):state['fields'].pop(key)
  r=self.cpu();restore(r,state);self.assertFalse(r.crc_counters_complete);self.assertEqual(r.crc_blocks,0)
 def test_locale_fixture_and_readonly_state_roundtrip(self):
  from native_c_locale_fixture_ysm_265 import ensure_c_locale
  from native_unicorn_guarded_ysm_265 import ModelHalt
  c=self.stopped();p=ensure_c_locale(c);state=capture(c);r=self.cpu();restore(r,state);self.assertEqual(r.c_locale_handle,p);self.assertEqual(r.fixture_reserved,8192);self.assertEqual(r.read_known(p+104,24),c.read_known(p+104,24));self.assertIsNotNone(r.unknown(p,104))
  with self.assertRaises(ModelHalt):r.write_private(p+104,bytes(8))
 def test_capture_requires_stopped_state(self):
  with self.assertRaises(ValueError):capture(self.cpu())
 def test_host_tcg_retaddr_normalized_without_masking_guest_registers(self):
  from native_guarded_checkpoint_ysm_265 import sanitize_context
  c=self.stopped();s=capture(c);m=s['context'];raw=bytearray(unpack(m['bytes'],m['size']));self.assertEqual(len(raw),5608);raw[-8:]=bytes.fromhex('8877665544332211');raw[40]^=0x55;result=sanitize_context(bytes(raw),m['size'],m['arch'],m['mode']);self.assertEqual(result[-8:],bytes(8));self.assertEqual(result[40],raw[40])
 def test_acceleration_comparison_explicitly_normalizes_only_diagnostics(self):
  import copy
  from compare_native_guarded_checkpoints_ysm_265 import compare
  a=capture(self.stopped());b=copy.deepcopy(a);a['origin_completed']=31;b['origin_completed']=1;b['fields']['accelerate_crc']=True;b['fields']['crc_blocks']=1;b['fields']['crc_iterations']=1;b['fields']['crc_logical_steps']=31
  self.assertFalse(compare(a,b)['all_checks_pass']);self.assertTrue(compare(a,b,True)['all_checks_pass']);m=b['context'];raw=bytearray(unpack(m['bytes'],m['size']));raw[40]^=1;m['bytes']=pack(raw);self.assertFalse(compare(a,b,True)['all_checks_pass'])
 def legacy_state(self):
  c=self.stopped();state=capture(c);record=state['private'].pop(str(STACK));offset=LEGACY_STACK-STACK
  state['private'][str(LEGACY_STACK)]={key:pack(unpack(record[key],STACK_SIZE)[offset:]) for key in ('bytes','known')}
  state.pop('stack_layout');state.pop('scenario_extensions');return c,state
 def test_legacy_restore_requires_explicit_scenario_extension(self):
  c,state=self.legacy_state();r=self.cpu()
  with self.assertRaisesRegex(ValueError,'explicit allow_stack_extension'):restore(r,state)
  self.assertEqual(r.read_known(SP,8),c.read_known(SP,8));self.assertEqual(r.shadow_ranges,[])
 def test_legacy_extension_preserves_cpu_old_bytes_and_unknownness(self):
  c,state=self.legacy_state();r=self.cpu();restore(r,state,allow_stack_extension=True)
  self.assertEqual({x:c.reg(x) for x in REGS},{x:r.reg(x) for x in REGS});self.assertEqual(c.opaque,r.opaque)
  self.assertEqual(bytes(r.uc.mem_read(LEGACY_STACK,LEGACY_STACK_SIZE)),bytes(c.uc.mem_read(LEGACY_STACK,LEGACY_STACK_SIZE)))
  self.assertEqual(r.known[STACK][LEGACY_STACK-STACK:],c.known[STACK][LEGACY_STACK-STACK:])
  self.assertEqual(r.known[STACK][:LEGACY_STACK-STACK],bytes(LEGACY_STACK-STACK));self.assertEqual(r.unknown(STACK,1),STACK)
  self.assertIn('equivalent_scenario=false',r.out.getvalue());self.assertEqual(len(r.scenario_extensions),1)
 def test_migration_history_survives_next_checkpoint_without_duplicate(self):
  c,state=self.legacy_state();r=self.cpu();restore(r,state,allow_stack_extension=True);r.run(r.reg('RIP'));new=capture(r);again=self.cpu();restore(again,new)
  self.assertEqual(again.scenario_extensions,r.scenario_extensions);self.assertEqual(again.known,r.known);self.assertEqual(new['stack_layout']['size'],0x100000)
 def test_legacy_wrong_private_layout_rejected_before_restore(self):
  c,state=self.legacy_state();state['private'][str(STACK)]={'bytes':pack(b''),'known':pack(b'')};r=self.cpu()
  with self.assertRaisesRegex(ValueError,'private layout'):restore(r,state,allow_stack_extension=True)
  self.assertEqual(r.shadow_ranges,[])
 def test_legacy_wrong_byte_length_or_mask_rejected(self):
  for key,payload in (('bytes',bytes(LEGACY_STACK_SIZE-1)),('known',bytes([2])*LEGACY_STACK_SIZE)):
   c,state=self.legacy_state();state['private'][str(LEGACY_STACK)][key]=pack(payload);r=self.cpu()
   with self.assertRaises(ValueError):restore(r,state,allow_stack_extension=True)
   self.assertEqual(r.shadow_ranges,[])
 def test_legacy_opaque_cannot_claim_new_stack_region(self):
  for entry in ((STACK,SP),(SP,STACK)):
   c,state=self.legacy_state();state['opaque']=[entry]
   with self.assertRaisesRegex(ValueError,'opaque address'):restore(self.cpu(),state,allow_stack_extension=True)
 def test_new_layout_and_extension_history_cannot_be_forged(self):
  for key,value in (('stack_layout',{'base':STACK,'size':STACK_SIZE*2,'initial_sp':SP}),('scenario_extensions',[{'kind':'anything'}])):
   state=capture(self.stopped());state[key]=value
   with self.assertRaises(ValueError):restore(self.cpu(),state,allow_stack_extension=True)
 def test_layout_metadata_cannot_be_removed_from_new_payload(self):
  state=capture(self.stopped());state.pop('stack_layout')
  with self.assertRaisesRegex(ValueError,'private layout'):restore(self.cpu(),state,allow_stack_extension=True)
 def test_comparison_rejects_migration_as_equivalent_scenario(self):
  from compare_native_guarded_checkpoints_ysm_265 import compare
  c,old=self.legacy_state();new=capture(c)
  self.assertTrue(compare(old,copy.deepcopy(old))['all_checks_pass'])
  for a,b in ((old,new),(new,old)):
   result=compare(a,b);self.assertFalse(result['all_checks_pass']);self.assertFalse(result['checks']['stack_layout_equal'])
  r=self.cpu();restore(r,old,allow_stack_extension=True);new['scenario_extensions']=copy.deepcopy(r.scenario_extensions)
  clean=copy.deepcopy(new);clean['scenario_extensions']=[];result=compare(new,clean)
  self.assertFalse(result['all_checks_pass']);self.assertFalse(result['checks']['scenario_extensions_equal'])
 def test_read_checkpoint_requires_explicit_migration_flag(self):
  import tempfile
  from pathlib import Path
  from native_guarded_checkpoint_ysm_265 import read_checkpoint
  c,state=self.legacy_state()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'old.json';p.write_text(json.dumps(state))
   with self.assertRaisesRegex(ValueError,'explicit allow_stack_extension'):read_checkpoint(self.cpu(),p)
   r=self.cpu();digest=read_checkpoint(r,p,allow_stack_extension=True);self.assertEqual(len(digest),64);self.assertEqual(len(r.scenario_extensions),1)
if __name__=='__main__':unittest.main()
