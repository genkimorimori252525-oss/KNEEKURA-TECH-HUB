"""Source metadata and opaque JNI references; all classes are authored byte fixtures."""
import io,struct,unittest
from native_jni_fixture_ysm_265 import JniGuardedCPU,TRAPS
from native_guarded_checkpoint_ysm_265 import capture,restore
from native_unicorn_guarded_ysm_265 import ModelHalt,SP
import test_native_java_metadata_ysm_265 as fixtures
RET=0x100000
class MetadataBridgeTests(unittest.TestCase):
 def metadata(self):
  return fixtures.fixture({'example/Root.class':fixtures.class_bytes('example/Root',methods=[(1,'<init>','()V'),(1,'run','(I)Z'),(9,'create','()I')]),'example/Child.class':fixtures.class_bytes('example/Child','example/Root')})
 def cpu(self):
  c=JniGuardedCPU(io.StringIO(),'heap',limit=1);c.add_image(RET,b'\x90'*16);c.protect_image();c.configure_jni();c.configure_java_metadata(self.metadata());return c
 def string(self,c,s):
  a=c.reserve_fixture(len(s)+1);c.write_private(a,s.encode()+b'\0');return a
 def call(self,c,index,*args):
  c.pc=TRAPS+(8+index)*16;c.reg('RSP',SP);c.write_private(SP,struct.pack('<Q',RET));c.reg('RDI',c.jni_state['env'])
  for r,v in zip(('RSI','RDX','RCX','R8','R9'),args):c.reg(r,v)
  c.model('jni-import');return c.reg('RAX')
 def cls(self,c,name='example/Root'):return self.call(c,6,self.string(c,name))
 def test_artifact_class_proof_and_missing_class(self):
  c=self.cpu();h=self.cls(c);self.assertEqual(c.jni_state['classes'][str(h)],'example/Root');self.assertIn('example/Root',c.jni_state['class_proofs'])
  with self.assertRaises(ModelHalt):self.cls(c,'example/Missing')
 def test_global_reference_survives_local_deletion(self):
  c=self.cpu();h=self.cls(c);g=self.call(c,21,h);self.assertNotEqual(g,h);self.call(c,23,h);m=self.call(c,33,g,self.string(c,'run'),self.string(c,'(I)Z'));self.assertEqual(c.jni_state['methods'][str(m)]['declaring_class'],'example/Root');self.call(c,22,g)
  with self.assertRaises(ModelHalt):self.call(c,21,g)
 def test_null_global_and_delete(self):
  c=self.cpu();self.assertEqual(self.call(c,21,0),0);self.call(c,22,0);self.assertEqual(c.jni_state['global_refs'],[])
 def test_global_cannot_be_deleted_as_local(self):
  c=self.cpu();g=self.call(c,21,self.cls(c))
  with self.assertRaises(ModelHalt):self.call(c,23,g)
 def test_exact_static_and_inherited_method_metadata(self):
  c=self.cpu();h=self.cls(c,'example/Child');m=self.call(c,33,h,self.string(c,'run'),self.string(c,'(I)Z'));self.assertEqual(c.jni_state['methods'][str(m)]['declaring_class'],'example/Root');s=self.call(c,113,h,self.string(c,'create'),self.string(c,'()I'));self.assertTrue(c.jni_state['methods'][str(s)]['static']);self.assertEqual(c.read_known(RET,1),b'\x90')
 def test_missing_or_invalid_method_never_invented(self):
  for name,descriptor in [('missing','()V'),('run','(J)Z'),('run','bad'),('<init>','()V')]:
   c=self.cpu();h=self.cls(c,'example/Child')
   with self.assertRaises(ModelHalt):self.call(c,33,h,self.string(c,name),self.string(c,descriptor))
   self.assertEqual(c.jni_state['methods'],{})
 def test_checkpoint_requires_same_metadata(self):
  c=self.cpu();h=self.cls(c);g=self.call(c,21,h);self.call(c,33,g,self.string(c,'run'),self.string(c,'(I)Z'));c.stop={'reason':'TEST'};s=capture(c);d=JniGuardedCPU(io.StringIO(),'heap',limit=1);d.add_image(RET,b'\x90'*16);d.protect_image();restore(d,s);d.configure_java_metadata(self.metadata());self.assertEqual(d.jni_state,c.jni_state)
  changed=fixtures.fixture({'example/Other.class':fixtures.class_bytes('example/Other')})
  with self.assertRaises(ValueError):d.configure_java_metadata(changed)
 def test_exception_check_without_side_effects(self):
  c=self.cpu();self.assertEqual(self.call(c,228),0);c.jni_state['pending_exception']={'class':'java/lang/RuntimeException','message':'owned'};self.assertEqual(self.call(c,228),1);self.assertEqual(c.jni_state['pending_exception']['message'],'owned')
if __name__=='__main__':unittest.main()
