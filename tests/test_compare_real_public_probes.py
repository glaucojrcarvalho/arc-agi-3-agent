"""Ensure public Qwen Phase-A comparisons do not mix incompatible runs."""
import copy
import unittest
from scripts.compare_real_public_probes import compare


def fixture(calls=10, seconds=20):
    return {'model':'Qwen3.8-27B FP8','probe_complete':True,'completed_games':2,
      'results':[{'game':g,'actions':3,'max_levels_completed':1,'model_calls':calls,
                  'elapsed_seconds':seconds,'action_trace':[
                    {'levels_completed':0},{'levels_completed':1},
                    {'levels_completed':1}]} for g in ('a','b')]}



def seeded_fixture(seed=101, environment=0):
    sample = fixture()
    sample['probe_protocol'] = {
        'controller_seed':seed, 'environment_seed':environment,
        'verified_progress':'levels_completed', 'official_submission':False,
    }
    for row in sample['results']:
        row['controller_seed'] = seed
        row['environment_seed'] = environment
        row['level_completion_actions'] = [{'level':1,'after_action':2}]
    return sample

class PublicQwenComparisonTests(unittest.TestCase):
    def test_levels_calls_time_and_steps(self):
        result=compare(fixture(),fixture(calls=6,seconds=12))
        self.assertEqual(result['baseline_levels'],2)
        self.assertEqual(result['candidate_levels'],2)
        self.assertEqual(result['qwen_call_reduction_pct'],40)
        self.assertEqual(result['wallclock_reduction_pct'],40)
        self.assertEqual(result['by_public_game']['a']['candidate_first_level_step'],2)

    def test_incomplete_and_fake_not_comparable(self):
        a=fixture();a['probe_complete']=False
        with self.assertRaisesRegex(ValueError,'incomplete'):
            compare(a,fixture())
        a=fixture();a['model']='fake'
        with self.assertRaisesRegex(ValueError,'Qwen'):
            compare(a,fixture())

    def test_unpaired_or_mismatched_runs(self):
        a,b=fixture(),fixture();b['results'][1]['game']='c'
        with self.assertRaisesRegex(ValueError,'inventory'):
            compare(a,b)
        b=fixture();b['model']='Qwen2.5-0.5B'
        with self.assertRaisesRegex(ValueError,'model mismatch'):
            compare(a,b)
        b=fixture();b['results'][0]['actions']=4
        with self.assertRaisesRegex(ValueError,'trace/actions mismatch'):
            compare(a,b)

    def test_corrupt_trace_and_duplicate_games(self):
        a,b=fixture(),fixture();b['results'][1]['game']='a'
        with self.assertRaisesRegex(ValueError,'duplicate'):
            compare(a,b)
        b=fixture();b['results'][1]['max_levels_completed']=2
        with self.assertRaisesRegex(ValueError,'trace/level mismatch'):
            compare(a,b)
        b=fixture();b['results'][1]['model_calls']=True
        with self.assertRaisesRegex(ValueError,'invalid'):
            compare(a,b)
        b=fixture();b['results'][1]['elapsed_seconds']=float('nan')
        with self.assertRaisesRegex(ValueError,'invalid'):
            compare(a,b)


    def test_seed_101_validated_and_aggregated_without_raw_trace(self):
        report = compare(seeded_fixture(), seeded_fixture())
        self.assertEqual(report['controller_seed'], 101)
        self.assertEqual(report['environment_seed'], 0)
        self.assertEqual(report['pairing_provenance'], 'explicit-public-protocol')
        self.assertNotIn('action_trace', str(report))
        self.assertEqual(report['baseline_levels'], 2)

    def test_controller_and_environment_seed_mismatches_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unpaired'):
            compare(seeded_fixture(101), seeded_fixture(102))
        with self.assertRaisesRegex(ValueError, 'unpaired'):
            compare(seeded_fixture(101, 0), seeded_fixture(101, 1))

    def test_per_game_seed_mixing_rejected_even_when_probe_matches(self):
        after = seeded_fixture()
        after['results'][1]['controller_seed'] = 102
        with self.assertRaisesRegex(ValueError, 'controller_seed'):
            compare(seeded_fixture(), after)
        after = seeded_fixture()
        after['results'][0]['environment_seed'] = 2
        with self.assertRaisesRegex(ValueError, 'environment_seed'):
            compare(seeded_fixture(), after)
        after = seeded_fixture()
        del after['results'][0]['controller_seed']
        with self.assertRaisesRegex(ValueError, 'controller_seed'):
            compare(seeded_fixture(), after)

    def test_authoritative_milestones_must_match_trace_not_pixels(self):
        after = seeded_fixture()
        after['results'][0]['action_trace'][0]['changed_cells'] = 123456
        compare(seeded_fixture(), after)
        after['results'][0]['level_completion_actions'][0]['after_action'] = 3
        with self.assertRaisesRegex(ValueError, 'milestone'):
            compare(seeded_fixture(), after)
        after = seeded_fixture()
        del after['results'][1]['level_completion_actions']
        with self.assertRaisesRegex(ValueError, 'milestones'):
            compare(seeded_fixture(), after)

    def test_protocol_requires_public_only_counter_and_explicit_seeds(self):
        for key, value in (('official_submission', True),
                           ('verified_progress', 'pixel-delta'),
                           ('environment_seed', False),
                           ('controller_seed', -1)):
            after = seeded_fixture()
            after['probe_protocol'][key] = value
            with self.assertRaises(ValueError, msg=key):
                compare(seeded_fixture(), after)
        after = seeded_fixture()
        del after['probe_protocol']['environment_seed']
        with self.assertRaisesRegex(ValueError, 'environment_seed'):
            compare(seeded_fixture(), after)

    def test_legacy_and_seeded_probes_may_not_be_paired(self):
        with self.assertRaisesRegex(ValueError, 'unpaired'):
            compare(fixture(), seeded_fixture())
        legacy = compare(fixture(), fixture())
        self.assertEqual(legacy['pairing_provenance'],
                         'legacy-unseeded-not-independently-paired')

    def test_malformed_trace_record_rejected_with_value_error(self):
        after = seeded_fixture()
        after['results'][0]['action_trace'][1] = None
        with self.assertRaisesRegex(ValueError, 'trace levels'):
            compare(seeded_fixture(), after)

if __name__=='__main__':unittest.main()
