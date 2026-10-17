#!/usr/bin/env python3
"""Opt-in fixed-artifact inventory corruption tests; never loads target classes."""
import argparse,json,tempfile,unittest
from pathlib import Path
from native_boundary_inventory_ysm_265 import inventory,ANCHORS
P=argparse.ArgumentParser();P.add_argument('--jar',required=True);A=P.parse_args();JAR=Path(A.jar);ROOT=Path(__file__).resolve().parent.parent
class InventoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for x in ANCHORS:
   name=x+'-EVIDENCE-2026-10-17.json';(self.root/name).write_bytes((ROOT/name).read_bytes())
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,fn):
  p=self.root/'COMMON-NATIVE-LIFECYCLE-EVIDENCE-2026-10-17.json';e=json.loads(p.read_text());fn(e);p.write_text(json.dumps(e))
 def test_fixed_inventory(self):
  r=inventory(JAR,self.root);self.assertEqual((r['class_files_scanned'],r['native_declaration_count'],r['owner_count']),(955,17,8))
 def test_missing_native(self):
  self.mutate(lambda e:e.update(members=[m for m in e['members'] if not m['access']&256]))
  with self.assertRaises(ValueError):inventory(JAR,self.root)
 def test_invented_native_code(self):
  self.mutate(lambda e:next(m for m in e['members'] if m['access']&256).update(instructions=[]))
  with self.assertRaises(ValueError):inventory(JAR,self.root)
 def test_changed_access(self):
  self.mutate(lambda e:next(m for m in e['members'] if m['access']&256).update(access=257))
  with self.assertRaises(ValueError):inventory(JAR,self.root)
 def test_wrong_anchor_artifact(self):
  self.mutate(lambda e:e['artifact'].update(sha256='0'*64))
  with self.assertRaises(ValueError):inventory(JAR,self.root)
 def test_changed_native_descriptor(self):
  self.mutate(lambda e:next(m for m in e['members'] if m['access']&256).update(descriptor='()I'))
  with self.assertRaises(ValueError):inventory(JAR,self.root)
if __name__=='__main__':unittest.main(argv=[__file__])
