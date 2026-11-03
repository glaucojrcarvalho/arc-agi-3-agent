"""Compare paired PUBLIC real-Qwen Kaggle probes; not official RHAE."""
import argparse
import json
from pathlib import Path



def _probe_seeds(probe):
    """Return explicit public-only pairing metadata; never infer missing seeds."""
    if 'probe_protocol' not in probe:
        return None  # Historical unseeded probes lack an auditable seed pair.
    protocol = probe['probe_protocol']
    if not isinstance(protocol, dict):
        raise ValueError('invalid public probe protocol')
    if protocol.get('official_submission') is not False:
        raise ValueError('probe must be labeled non-submission')
    if protocol.get('verified_progress') != 'levels_completed':
        raise ValueError('probe lacks authoritative level-counter provenance')
    for key in ('controller_seed', 'environment_seed'):
        if key not in protocol:
            raise ValueError('missing '+key)
        seed = protocol[key]
        if key == 'controller_seed' and seed is None:
            continue  # Explicitly unseeded, not an independent RNG trial.
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError('invalid '+key)
    return protocol['controller_seed'], protocol['environment_seed']


def _milestones(trace):
    """Derive verified completions from increasing max(levels_completed)."""
    highest = 0
    events = []
    for action, frame in enumerate(trace, 1):
        level = frame['levels_completed']
        if level > highest:
            events.extend({'level': n, 'after_action': action}
                          for n in range(highest + 1, level + 1))
            highest = level
    return events


def _rows(probe):
    if probe.get('probe_complete') is not True:
        raise ValueError('incomplete public probe')
    if 'qwen' not in str(probe.get('model', '')).lower():
        raise ValueError('not a real Qwen probe')
    seeds = _probe_seeds(probe)
    rows = probe.get('results')
    if not isinstance(rows, list) or not rows or probe.get('completed_games') != len(rows):
        raise ValueError('malformed public probe inventory')
    results = {}
    for row in rows:
        name = row.get('game')
        if not isinstance(name, str) or not name:
            raise ValueError('invalid game')
        if name in results:
            raise ValueError('duplicate game')
        if seeds is not None:
            for field, expected in zip(('controller_seed', 'environment_seed'), seeds):
                if field not in row or isinstance(row[field], bool) or row[field] != expected:
                    raise ValueError('game '+field+' disagrees with probe protocol')
        for key in ('actions', 'max_levels_completed', 'model_calls'):
            val = row.get(key)
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise ValueError('invalid '+key)
        sec = row.get('elapsed_seconds')
        if isinstance(sec, bool) or not isinstance(sec,(int,float)) or not 0<=sec<float('inf'):
            raise ValueError('invalid elapsed_seconds')
        trace = row.get('action_trace')
        if not isinstance(trace, list) or len(trace) != row['actions']:
            raise ValueError('trace/actions mismatch')
        if any(not isinstance(t,dict) or not isinstance(t.get('levels_completed'),int) or isinstance(t.get('levels_completed'),bool) or t['levels_completed']<0 for t in trace):
            raise ValueError('invalid trace levels')
        if trace and max(t['levels_completed'] for t in trace) != row['max_levels_completed']:
            raise ValueError('trace/level mismatch')
        reported = row.get('level_completion_actions')
        if seeds is not None and reported is None:
            raise ValueError('missing authoritative level milestones')
        if reported is not None and reported != _milestones(trace):
            raise ValueError('milestone/trace mismatch')
        results[name] = row
    return results


def compare(baseline, candidate):
    before_seeds, after_seeds = _probe_seeds(baseline), _probe_seeds(candidate)
    if before_seeds != after_seeds:
        raise ValueError('unpaired controller/environment seeds')
    b,c = _rows(baseline),_rows(candidate)
    if baseline['model']!=candidate['model']:
        raise ValueError('model mismatch')
    if b.keys()!=c.keys():
        raise ValueError('game inventory mismatch')
    per_game={}
    for game in sorted(b):
        old,new=b[game],c[game]
        if old['actions']!=new['actions']:
            raise ValueError('action budget mismatch')
        def first_level(row):
            return next((i for i,t in enumerate(row['action_trace'],1) if t['levels_completed']>0),None)
        per_game[game]={
            'actions':old['actions'],
            'baseline_levels':old['max_levels_completed'],
            'candidate_levels':new['max_levels_completed'],
            'baseline_qwen_calls':old['model_calls'],
            'candidate_qwen_calls':new['model_calls'],
            'baseline_wallclock_s':old['elapsed_seconds'],
            'candidate_wallclock_s':new['elapsed_seconds'],
            'baseline_first_level_step':first_level(old),
            'candidate_first_level_step':first_level(new),
        }
    def sum_field(rows,k):return sum(r[k] for r in rows.values())
    old_calls,new_calls=sum_field(b,'model_calls'),sum_field(c,'model_calls')
    old_secs,new_secs=sum_field(b,'elapsed_seconds'),sum_field(c,'elapsed_seconds')
    return {
        'protocol':'real-Qwen/public-only/same-games-actions/not-official-RHAE',
        'model':baseline['model'],'games':len(b),'actions':sum_field(b,'actions'),
        'controller_seed':before_seeds[0] if before_seeds else None,
        'environment_seed':before_seeds[1] if before_seeds else None,
        'pairing_provenance':('explicit-public-protocol' if before_seeds is not None
                              else 'legacy-unseeded-not-independently-paired'),
        'baseline_levels':sum_field(b,'max_levels_completed'),
        'candidate_levels':sum_field(c,'max_levels_completed'),
        'baseline_qwen_calls':old_calls,'candidate_qwen_calls':new_calls,
        'qwen_call_reduction_pct':round(100*(old_calls-new_calls)/old_calls,2) if old_calls else None,
        'baseline_wallclock_s':round(old_secs,2),'candidate_wallclock_s':round(new_secs,2),
        'wallclock_reduction_pct':round(100*(old_secs-new_secs)/old_secs,2) if old_secs else None,
        'by_public_game':per_game,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=compare(json.loads(a.baseline.read_text()),json.loads(a.candidate.read_text()))
    report=json.dumps(result,indent=2,sort_keys=True)+'\n'
    print(report)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(report)

if __name__=='__main__':main()
