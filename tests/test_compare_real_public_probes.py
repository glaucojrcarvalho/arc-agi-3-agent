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

if __name__=='__main__':unittest.main()
