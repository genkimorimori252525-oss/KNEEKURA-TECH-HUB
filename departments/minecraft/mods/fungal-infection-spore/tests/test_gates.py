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

class AiGoalLayerUnitTest(unittest.TestCase):
    """Portable tests only: no copyrighted Spore JAR on CI runners."""

    def test_wrong_jar_is_blocked_before_bytecode_read(self):
        from audit_ai_goal_layer import inspect
        with TemporaryDirectory() as temp:
            wrong=Path(temp)/'synthetic-wrong.jar'
            wrong.write_bytes(b'not the owned Spore binary')
            report=inspect(wrong)
            self.assertEqual(report['status'], 'BLOCKED_HASH_MISMATCH')
            self.assertNotIn('ai_classes', report)

    def test_javap_method_extraction_does_not_absorb_following_method(self):
        from audit_ai_goal_layer import extract_method
        text=('  public boolean m_8036_();\n'
              '    Code:\n'
              '       0: iconst_1\n'
              '  public void m_8037_();\n'
              '    Code:\n'
              '       0: athrow\n')
        method=extract_method(text, 'm_8036_')
        self.assertIn('iconst_1', method)
        self.assertNotIn('athrow', method)

    def test_exact_binary_pins_and_scope(self):
        from audit_ai_goal_layer import PREFIX, PINS, ORIGINAL_SHA
        self.assertEqual(PREFIX, 'com/Harbinger/Spore/Sentities/AI/')
        self.assertEqual(len(PINS), 7)
        self.assertEqual(len(ORIGINAL_SHA), 64)
        self.assertEqual(len(set(PINS)), 7)
        self.assertTrue(all(len(h)==64 for h in PINS.values()))

class GargoylHardnessUnitTest(unittest.TestCase):
    """Original binary is kept private; CI exercises narrow negative behavior."""

    def test_wrong_jar_refused_without_javap(self):
        from check_gargoyl_hardness import analyze
        with TemporaryDirectory() as tmp:
            wrong=Path(tmp)/'not-spore.jar'
            wrong.write_bytes(b'test fixture that is not the original JAR')
            outcome=analyze(wrong)
            self.assertEqual(outcome['status'],'BLOCKED_HASH_MISMATCH')
            self.assertNotIn('checks',outcome)

    def test_exact_original_gargoyl_fingerprint(self):
        from check_gargoyl_hardness import JAR_SHA,CLS,CLS_SHA
        self.assertEqual(JAR_SHA,'d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489')
        self.assertEqual(CLS,'com/Harbinger/Spore/Sentities/EvolvedInfected/Gargoyl.class')
        self.assertEqual(len(CLS_SHA),64)

class SporeGoalRegistrationUnitTest(unittest.TestCase):
    """Portable synthetic parser regressions; original Spore JAR is not in CI."""

    def test_owner_goal_and_target_call_sites(self):
        from audit_spore_goal_registrations import parse_javap
        body='''  protected void m_8099_();
    Code:
       0: aload_0
       1: getfield #2 // Field f_21345_:Lnet/minecraft/world/entity/ai/goal/GoalSelector;
       4: iconst_1
       5: new #3 // class com/Harbinger/Spore/Sentities/AI/TransportInfected
       9: invokevirtual #4 // Method net/minecraft/world/entity/ai/goal/GoalSelector.m_25352_:(ILnet/minecraft/world/entity/ai/goal/Goal;)V
      12: aload_0
      13: getfield #5 // Field f_21346_:Lnet/minecraft/world/entity/ai/goal/GoalSelector;
      16: bipush 7
      18: new #6 // class net/minecraft/world/entity/ai/goal/target/NearestAttackableTargetGoal
      21: invokevirtual #4 // Method net/minecraft/world/entity/ai/goal/GoalSelector.m_25352_:(ILnet/minecraft/world/entity/ai/goal/Goal;)V
  public void anotherMethod();
    Code:
       0: return'''
        rows=parse_javap(body,'synthetic.class')
        self.assertEqual(len(rows),2)
        self.assertEqual((rows[0]['selector'],rows[0]['priority'],rows[0]['goal_class'].split('/')[-1]),('goal',1,'TransportInfected'))
        self.assertEqual((rows[1]['selector'],rows[1]['priority']),('target',7))

    def test_goal_new_distinguishes_nested_item(self):
        from audit_spore_goal_registrations import is_goal_alloc
        self.assertFalse(is_goal_alloc('net/minecraft/world/item/ItemStack'))
        self.assertTrue(is_goal_alloc('com/Harbinger/Spore/Sentities/BasicInfected/InfectedWitch$3'))

    def test_other_jar_rejected_before_javap(self):
        from audit_spore_goal_registrations import analyze
        with TemporaryDirectory() as directory:
            wrong=Path(directory)/'wrong.jar'
            wrong.write_bytes(b'incorrect')
            self.assertEqual(analyze(wrong)['status'],'BLOCKED_HASH_MISMATCH')

    def test_constant_priority_parsing(self):
        from audit_spore_goal_registrations import priority_value
        for op,arg,expected in [
            ('iconst_5','',5),('iconst_m1','',-1),
            ('bipush',' 40',40),('sipush',' 128',128),
            ('ldc',' #4 // int 23',23)
        ]:
            self.assertEqual(priority_value((1,op,arg,'')),expected)

    def test_partial_inventory_cannot_pass_372_contract(self):
        from audit_spore_goal_registrations import summarize
        example=[{'owner':'synthetic','selector':'goal','priority':1,'goal_class':'net/minecraft/world/entity/ai/goal/FloatGoal'}]
        _,contracts=summarize(example)
        self.assertFalse(contracts['original_direct_registration_invokes_372'])
        self.assertFalse(contracts['original_unique_direct_registration_owners_86'])

class SporeGoalSnapshotReviewTest(unittest.TestCase):
    """Candidate overlaps are inventory observations, never proof of runtime bugs."""

    @staticmethod
    def sample_goals():
        return [
            dict(selector='goal', priority=4,
                 goal_class='com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$3',
                 flags=['MOVE', 'LOOK'], running=True),
            dict(selector='goal', priority=4,
                 goal_class='com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$4',
                 flags=['MOVE', 'LOOK'], running=False),
            dict(selector='goal', priority=4,
                 goal_class='com.Harbinger.Spore.Sentities.AI.LocHiv.SearchAreaGoal',
                 flags=['MOVE'], running=False)
        ]

    def review(self, scenario='G12', data=None, origin='synthetic_fixture',
               ending='completed'):
        from analyze_spore_goal_snapshots import analyze
        with TemporaryDirectory() as temp:
            p=Path(temp)/'fixture.jsonl'
            if data is None:
                data={'entity_uuid':'fake-witch-uuid',
                      'registered_goal_count':3,'registered_running_count':1,
                      'truncated':False,'goals':self.sample_goals()}
            fixture=make_trace(scenario, [('goal_registry_snapshot',data)],
                               origin=origin, end=ending)
            p.write_text('\n'.join(json.dumps(x) for x in fixture)+'\n',encoding='utf-8')
            return analyze(p)

    def test_witch_same_priority_move_lock_candidates(self):
        report=self.review()
        self.assertEqual(report['status'],'SYNTHETIC_FIXTURE_ONLY')
        self.assertEqual(report['potential_shared_flag_pairs_sum'],3)
        self.assertEqual(report['same_priority_shared_flag_pairs_sum'],3)
        self.assertEqual(report['co_running_shared_flag_pairs_sum'],0)
        self.assertFalse(report['runtime_pass'])

    def test_target_goal_selectors_not_compared(self):
        goals=self.sample_goals()[:1]
        other=dict(goals[0])
        other['selector']='target'
        data={'entity_uuid':'fake-unit','registered_goal_count':2,
              'registered_running_count':1,'truncated':False,
              'goals':goals+[other]}
        report=self.review(data=data)
        self.assertEqual(report['potential_shared_flag_pairs_sum'],0)

    def test_invalid_flag_rejected_without_goal_claim(self):
        data={'entity_uuid':'fake-unit','registered_goal_count':1,
              'registered_running_count':0,'truncated':False,
              'goals':[dict(selector='goal',priority=4,flags=['FLY'],
                            running=False,goal_class='TestGoal')]}
        report=self.review(data=data)
        self.assertEqual(report['status'],'INCONCLUSIVE_INVALID_OR_ABSENT_GOAL_SNAPSHOTS')
        self.assertEqual(report['parsed_snapshot_rows'],0)
        self.assertFalse(report['runtime_pass'])

    def test_wrong_scenario_blocked(self):
        self.assertEqual(self.review(scenario='G09')['status'],'BLOCKED_WRONG_SCENARIO')

    def test_unattested_claim_is_not_runtime_pass(self):
        report=self.review(origin='runtime_claim_unattested')
        self.assertEqual(report['status'],'IMPORTED_UNATTESTED_GOAL_REGISTRY')
        self.assertFalse(report['runtime_pass'])

    def test_partial_or_aborted_run_not_accepted(self):
        report=self.review(ending='aborted')
        self.assertEqual(report['status'],'INCONCLUSIVE_INCOMPLETE_RUN')
        self.assertFalse(report['runtime_pass'])


class SporeGoalStateDeltaReviewTest(unittest.TestCase):
    """End-of-tick state changes are not exact Goal.start/stop callbacks."""

    @staticmethod
    def goal_data():
        return dict(entity_uuid='synthetic-witch',registered_goal_count=1,
                    registered_running_count=0,truncated=False,
                    goals=[dict(goal_instance_id=101,selector='goal',priority=4,
                                goal_class='synthetic.WitchBuffGoal',running=False,
                                flags=['MOVE','LOOK'])])

    @staticmethod
    def delta_data():
        return dict(entity_uuid='synthetic-witch',
                    observed_state_changes=1,changes_truncated=False,
                    snapshot_goal_entries=1,snapshot_truncated=False,
                    capture_scope='END_TICK_RUNNING_STATE_DIFF_NOT_GOAL_CALLBACK',
                    changes=[dict(goal_instance_id=101,selector='goal',
                                  priority=4,goal_class='synthetic.WitchBuffGoal',
                                  previous_running=False,current_running=True)])

    def evaluate(self, delta=None, origin='synthetic_fixture', end='completed'):
        from analyze_spore_goal_snapshots import analyze
        with TemporaryDirectory() as temp:
            p=Path(temp)/'g12.jsonl'
            rows=make_trace('G12',[
                ('goal_registry_snapshot',self.goal_data()),
                ('goal_running_state_delta_snapshot',delta if delta is not None else self.delta_data()),
            ], origin=origin, end=end)
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n',encoding='utf-8')
            return analyze(p)

    def test_synthetic_one_tick_state_transition(self):
        result=self.evaluate()
        self.assertEqual(result['status'],'SYNTHETIC_FIXTURE_ONLY')
        self.assertEqual(result['delta_snapshot_events'],1)
        self.assertEqual(result['delta_snapshot_valid'],1)
        self.assertEqual(result['delta_changes_false_to_true'],1)
        self.assertEqual(result['delta_changes_true_to_false'],0)
        self.assertFalse(result['runtime_pass'])
        self.assertIn('not Goal.start/stop',result['interpretation'])

    def test_fake_unchanged_transition_rejected(self):
        data=self.delta_data()
        data['changes'][0]['current_running']=False
        result=self.evaluate(delta=data)
        self.assertEqual(result['status'],'INCONCLUSIVE_INVALID_DELTA_SNAPSHOTS')
        self.assertEqual(result['delta_snapshot_invalid'],1)

    def test_forged_direct_callback_claim_rejected(self):
        data=self.delta_data()
        data['capture_scope']='GOAL_START_CALLBACK_DIRECT'
        self.assertEqual(self.evaluate(delta=data)['status'],'INCONCLUSIVE_INVALID_DELTA_SNAPSHOTS')

    def test_duplicate_goal_ids_cannot_be_counted_twice(self):
        data=self.delta_data()
        data['changes'].append(dict(data['changes'][0]))
        data['observed_state_changes']=2
        self.assertEqual(self.evaluate(delta=data)['delta_snapshot_invalid'],1)

    def test_out_of_scope_runtime_claim_still_not_attested(self):
        r=self.evaluate(origin='runtime_claim_unattested')
        self.assertEqual(r['status'],'IMPORTED_UNATTESTED_GOAL_REGISTRY')
        self.assertFalse(r['runtime_pass'])

    def test_unfinished_delta_trace_not_promoted(self):
        r=self.evaluate(end='aborted')
        self.assertEqual(r['status'],'INCONCLUSIVE_INCOMPLETE_RUN')

if __name__=='__main__':unittest.main()
