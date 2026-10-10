from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_spore_metadata import inspect_toml, range_contains
from evaluate_spore_trace import evaluate

SHA='d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'

def make_trace(scenario, cases=None, origin='synthetic_fixture', end='completed'):
    cases=cases or []
    meta={'ch':'spore_meta','schema':'kneekura.spore.observation.v1','run_id':'fixture-20261011-G',
      'scenario':scenario,'jar_sha256':SHA,'minecraft':'1.20.1','loader':'Forge',
      'seed':42,'world_id':'disposable-fixture-world','dimension':'minecraft:overworld',
      'world_disposable':True,'origin':origin,'physical_side':'DEDICATED_SERVER',
      'observer_identity':'selftest-fixture-not-runtime'}
    ev=[]
    for i,(kind, data) in enumerate(cases):
        ev.append({'ch':'spore_observation','run_id':meta['run_id'],'scenario':scenario,
            'world_id':meta['world_id'],'dimension':meta['dimension'],
            'seq':i+1,'tick':i+100,'kind':kind,'data':data})
    finish={'ch':'spore_end','run_id':meta['run_id'],'scenario':scenario,'reason':end,'observation_count':len(ev),
         'cleanup':'NOT_VERIFIED_SYNTHETIC'}
    return [meta]+ev+[finish]

class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.path=Path(self.tmp.name)/'fixture.jsonl'
    def tearDown(self):self.tmp.cleanup()
    def run_check(self,rows):
        self.path.write_text('\n'.join(json.dumps(x,sort_keys=True) for x in rows)+'\n',encoding='utf-8')
        return evaluate(self.path)

    def test_no_events_inconclusive(self):
        result=self.run_check(make_trace('G09'))
        self.assertEqual(result['status'],'SYNTHETIC_FIXTURE_ONLY')
        self.assertEqual(result['observation_coverage']['state'],'INCONCLUSIVE')
        self.assertFalse(result['runtime_pass'])

    def test_non_synthetic_unauthenticated(self):
        rows=make_trace('G09', [('signal_dispatch', {'candidates':[{'uuid':'a','distance_sq':4.0},{'uuid':'b','distance_sq':1.0}], 'recipient_uuid':'a','signal_id':'X'})],origin='runtime_claim_unattested')
        r=self.run_check(rows)
        self.assertEqual(r['status'],'IMPORTED_UNATTESTED_OBSERVATIONS')
        self.assertEqual(r['observation_coverage']['state'],'OBSERVED_CONTRAST')
        self.assertTrue(r['observation_coverage']['examples'][0]['chosen_first'])
        self.assertFalse(r['runtime_pass'])

    def test_nearest_and_first_same_is_inconclusive(self):
        rows=make_trace('G09',[('signal_dispatch',{'candidates':[{'uuid':'a','distance_sq':1},{'uuid':'b','distance_sq':4}], 'recipient_uuid':'a'})])
        self.assertEqual(self.run_check(rows)['observation_coverage']['state'],'INCONCLUSIVE')

    def test_mismatched_run_rejected(self):
        rows=make_trace('G10',[('signal_resolution',{'eligible':0,'decision':'womb_attempt'})]);rows[1]['run_id']='another-run'
        self.assertEqual(self.run_check(rows)['status'],'BLOCKED_INVALID_TRACE')

    def test_cross_world_rejected(self):
        rows=make_trace('G10',[('signal_resolution',{'eligible':0,'decision':'womb_attempt'})]);rows[1]['world_id']='private-world'
        self.assertEqual(self.run_check(rows)['status'],'BLOCKED_INVALID_TRACE')

    def test_wrong_sha_rejected(self):
        rows=make_trace('G09'); rows[0]['jar_sha256']='0'*64
        self.assertEqual(self.run_check(rows)['status'],'BLOCKED_INVALID_TRACE')

    def test_missing_end_rejected(self):
        rows=make_trace('G09')[:-1]
        self.assertEqual(self.run_check(rows)['status'],'BLOCKED_INVALID_TRACE')

    def test_duplicate_seq_rejected(self):
        rows=make_trace('G10',[('signal_resolution',{'eligible':0,'decision':'womb_attempt'}),('signal_resolution',{'eligible':1,'decision':'redirect'})]);rows[2]['seq']=1
        self.assertEqual(self.run_check(rows)['status'],'BLOCKED_INVALID_TRACE')

    def test_unfinished_trace_cannot_pass(self):
        rows=make_trace('G09',[('signal_dispatch',{'candidates':[{'uuid':'a','distance_sq':4},{'uuid':'b','distance_sq':1}], 'recipient_uuid':'a'})],origin='runtime_claim_unattested',end='aborted')
        self.assertEqual(self.run_check(rows)['status'],'INCONCLUSIVE_INCOMPLETE_RUN')

    def test_g10_required_cohorts(self):
        cases=[('signal_resolution',{'eligible':n,'decision':'womb_attempt' if n==0 else 'redirect','spawn_success':False}) for n in (0,1,2,4)]
        r=self.run_check(make_trace('G10',cases))
        self.assertEqual(r['observation_coverage']['state'],'OBSERVED_CONTRAST')
        self.assertEqual(r['observation_coverage']['covered_groups'],[0,1,2,4])

    def test_g10_partial(self):
        r=self.run_check(make_trace('G10',[('signal_resolution',{'eligible':0,'decision':'womb_attempt'})]))
        self.assertEqual(r['observation_coverage']['state'],'INCONCLUSIVE')

    def test_g11_order_chain(self):
        uid='VIGIL-1';seq=[(e,{'vigil_uuid':uid}) for e in ['wave_award','wave_spawn_attempt','wave_spawn_result','vigil_retire','vigil_penalty']]
        r=self.run_check(make_trace('G11',seq))
        self.assertEqual(r['observation_coverage']['state'],'OBSERVED_CHAIN')
        bad=self.run_check(make_trace('G11',list(reversed(seq))))
        self.assertEqual(bad['observation_coverage']['state'],'INCONCLUSIVE')

    def test_g12_boundary(self):
        cases=[('search_goal_step',{'distance_to_block_center':8.9,'search_pos_cleared':True}),
            ('search_goal_step',{'distance_to_block_center':9.1,'search_pos_cleared':False}),
            ('follow_goal_step',{'distance_sq':8.99,'navigation_stopped':True}),
            ('follow_goal_step',{'distance_sq':10,'navigation_stopped':False})]
        r=self.run_check(make_trace('G12',cases))
        self.assertEqual(r['observation_coverage']['state'],'OBSERVED_BOUNDARIES')

    def test_g13_requires_min_samples_each_cohort(self):
        cases=[('server_tick_sample',{'proto_count':n,'signal_count':0,'infected_count':0,'tick_ms':1+n/10}) for n in (1,4,16) for _ in range(200)]
        r=self.run_check(make_trace('G13',cases))
        self.assertEqual(r['observation_coverage']['state'],'OBSERVED_BASELINE_COMPARISON')
        self.assertEqual(len(r['observation_coverage']['summaries']),3)
        self.assertFalse(r['runtime_pass'])
        cases=cases[:199]+cases[200:]
        self.assertEqual(self.run_check(make_trace('G13',cases))['observation_coverage']['state'],'INCONCLUSIVE')

    def test_metadata_toml_dependency_mapping(self):
        raw=b'''modLoader="javafml"\n[[mods]]\nmodId="spore"\n[[dependencies.examplemod]]\nmodId="minecraft"\nmandatory=true\nversionRange="[1.20,1.20.1)"\n'''
        r=inspect_toml(raw)
        self.assertEqual(r['dependencies_for_declared_mod_ids']['spore'],[])
        self.assertEqual(len(r['findings']),2)
        self.assertFalse(range_contains('[1.20,1.20.1)','1.20.1'))
        self.assertTrue(range_contains('[1.20.1,1.21)','1.20.1'))
        self.assertFalse(range_contains('[1.20.1,1.21)','1.21'))

if __name__=='__main__':unittest.main()
