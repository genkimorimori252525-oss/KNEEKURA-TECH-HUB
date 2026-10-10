#!/usr/bin/env python3
"""Review passive Forge GoalSelector snapshots without asserting runtime correctness.

Requires an existing G12 companion JSONL accepted by evaluate_spore_trace.
Class names / flags come from observation files and remain untrusted until LAB
run + world + original JAR + build + cleanup are independently attested.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path
import sys

from evaluate_spore_trace import InvalidTrace, read_trace

ALLOWED_FLAGS = frozenset(('MOVE', 'LOOK', 'JUMP', 'TARGET'))
MAX_CAPTURED = 12
MAX_EVENTS_REVIEWED = 10000
MAX_PAIRS_REPORTED = 36


def _valid_int(value, low=0, high=100000):
    return type(value) is int and low <= value <= high


def _goal(value):
    if not isinstance(value, dict):
        return None
    if value.get('selector') not in ('goal', 'target'):
        return None
    if not _valid_int(value.get('priority'), 0, 1000):
        return None
    clazz = value.get('goal_class')
    flags = value.get('flags')
    if not isinstance(clazz, str) or not (1 <= len(clazz) <= 300):
        return None
    if type(value.get('running')) is not bool:
        return None
    if not isinstance(flags, list) or len(flags) > 4 or any(
            type(f) is not str or f not in ALLOWED_FLAGS for f in flags):
        return None
    if len(set(flags)) != len(flags):
        return None
    return dict(selector=value['selector'], priority=value['priority'],
                goal_class=clazz, flags=tuple(sorted(flags)),
                running=value['running'])


def _snapshot(value):
    if not isinstance(value, dict):
        return None
    uid = value.get('entity_uuid')
    if not isinstance(uid, str) or not 1 <= len(uid) <= 128:
        return None
    n = value.get('registered_goal_count')
    running = value.get('registered_running_count')
    raw = value.get('goals')
    truncated = value.get('truncated')
    if not _valid_int(n, 0, 1000) or not _valid_int(running, 0, n):
        return None
    if type(truncated) is not bool or not isinstance(raw, list) or len(raw) > MAX_CAPTURED:
        return None
    if n < len(raw) or (n > len(raw)) != truncated:
        return None
    parsed = [_goal(g) for g in raw]
    if any(g is None for g in parsed):
        return None
    if sum(g['running'] for g in parsed) > running:
        return None
    # A one-shot partial snapshot cannot support absolute negative conclusions.
    return dict(entity_uuid=uid, total=n, captured=len(parsed), running=running,
                truncated=truncated, goals=parsed)


def _pairs(snapshot):
    potential, co_running = [], []
    for a, b in combinations(snapshot['goals'], 2):
        # Goal and target selectors have independent priority / scheduling.
        if a['selector'] != b['selector']:
            continue
        shared = sorted(set(a['flags']) & set(b['flags']))
        if not shared:
            continue
        pair = {
            'selector': a['selector'],
            'shared_flags': shared,
            'same_priority': a['priority'] == b['priority'],
            'a': {'goal_class': a['goal_class'], 'priority': a['priority'], 'running': a['running']},
            'b': {'goal_class': b['goal_class'], 'priority': b['priority'], 'running': b['running']},
        }
        potential.append(pair)
        if a['running'] and b['running']:
            co_running.append(pair)
    return potential, co_running




def _delta(value):
    """Validate state-diff observations; never interpret these as Goal callbacks."""
    if not isinstance(value, dict):
        return None
    if value.get('capture_scope') != 'END_TICK_RUNNING_STATE_DIFF_NOT_GOAL_CALLBACK':
        return None
    uuid = value.get('entity_uuid')
    count = value.get('observed_state_changes')
    rows = value.get('changes')
    trimmed = value.get('changes_truncated')
    snap_trimmed = value.get('snapshot_truncated')
    snap_count = value.get('snapshot_goal_entries')
    if not isinstance(uuid, str) or not 1 <= len(uuid) <= 128:
        return None
    if not _valid_int(count, 1, 12) or not isinstance(rows, list) or len(rows) > 12:
        return None
    if type(trimmed) is not bool or type(snap_trimmed) is not bool:
        return None
    if not _valid_int(snap_count, 0, 12):
        return None
    if len(rows) > count or (count > len(rows)) != trimmed:
        return None
    ids = set()
    started, ended = 0, 0
    for row in rows:
        if not isinstance(row, dict):
            return None
        instance = row.get('goal_instance_id')
        priority = row.get('priority')
        clazz = row.get('goal_class')
        if not _valid_int(instance, 1, 2048) or instance in ids:
            return None
        ids.add(instance)
        if row.get('selector') not in ('goal', 'target') or not _valid_int(priority, 0, 1000):
            return None
        if not isinstance(clazz, str) or not 1 <= len(clazz) <= 300:
            return None
        before = row.get('previous_running')
        after = row.get('current_running')
        if type(before) is not bool or type(after) is not bool or before == after:
            return None
        started += int(not before and after)
        ended += int(before and not after)
    return {'entity_uuid': uuid, 'observed_changes': count,
            'reported_changes': len(rows), 'truncated': trimmed,
            'sample_truncated': snap_trimmed, 'observed_false_to_true': started,
            'observed_true_to_false': ended}

def analyze(path):
    try:
        meta, records, end = read_trace(path)
    except (InvalidTrace, KeyError, ValueError, TypeError, OSError, UnicodeError) as exc:
        return {'schema': 'kneekura.spore.goal-snapshot-review.v1',
                'status': 'BLOCKED_INVALID_TRACE', 'reason': str(exc),
                'runtime_pass': False}
    if meta['scenario'] != 'G12':
        return {'schema': 'kneekura.spore.goal-snapshot-review.v1',
                'status': 'BLOCKED_WRONG_SCENARIO', 'actual_scenario': meta['scenario'],
                'runtime_pass': False}
    summaries = []
    invalid = 0
    n_snapshots = 0
    truncated = 0
    sampled = 0
    potential_count = 0
    same_priority_count = 0
    co_running_count = 0
    n_goal_only = 0
    n_target_only = 0
    deltas_total = 0
    deltas_valid = 0
    deltas_invalid = 0
    deltas_start_like = 0
    deltas_stop_like = 0
    deltas_with_truncation = 0
    delta_examples = []
    for event in records[:MAX_EVENTS_REVIEWED]:
        if event['kind'] == 'goal_running_state_delta_snapshot':
            deltas_total += 1
            delta = _delta(event['data'])
            if delta is None:
                deltas_invalid += 1
                continue
            deltas_valid += 1
            deltas_start_like += delta['observed_false_to_true']
            deltas_stop_like += delta['observed_true_to_false']
            deltas_with_truncation += int(delta['truncated'] or delta['sample_truncated'])
            if len(delta_examples) < 8:
                delta_examples.append({'tick': event['tick'], **delta})
            continue
        if event['kind'] != 'goal_registry_snapshot':
            continue
        n_snapshots += 1
        info = _snapshot(event['data'])
        if info is None:
            invalid += 1
            continue
        sampled += 1
        truncated += int(info['truncated'])
        potential, concurrent = _pairs(info)
        potential_count += len(potential)
        same_priority_count += sum(p['same_priority'] for p in potential)
        co_running_count += len(concurrent)
        n_goal_only += sum(1 for g in info['goals'] if g['selector'] == 'goal')
        n_target_only += sum(1 for g in info['goals'] if g['selector'] == 'target')
        if len(summaries) < MAX_PAIRS_REPORTED:
            summaries.append({
                'tick': event['tick'],
                'entity_uuid': info['entity_uuid'],
                'registered_count': info['total'],
                'captured_count': info['captured'],
                'running_count': info['running'],
                'truncated': info['truncated'],
                'potential_shared_flag_pairs': potential[:6],
                'co_running_shared_flag_pairs': concurrent[:6],
            })
    # Even if a supported trace looks like a real run, it carries no cryptographic
    # attestation and cannot promote actual Forge behavior to runtime PASS.
    status = ('SYNTHETIC_FIXTURE_ONLY' if meta['origin'] == 'synthetic_fixture'
              else 'IMPORTED_UNATTESTED_GOAL_REGISTRY')
    if end['reason'] != 'completed':
        status = 'INCONCLUSIVE_INCOMPLETE_RUN'
    if invalid or not sampled:
        status = 'INCONCLUSIVE_INVALID_OR_ABSENT_GOAL_SNAPSHOTS'
    elif deltas_invalid:
        status = 'INCONCLUSIVE_INVALID_DELTA_SNAPSHOTS'
    return {
        'schema': 'kneekura.spore.goal-snapshot-review.v1',
        'status': status, 'run_id': meta['run_id'], 'scenario': 'G12',
        'origin': meta['origin'], 'end_reason': end['reason'],
        'observed_snapshot_rows': n_snapshots, 'parsed_snapshot_rows': sampled,
        'invalid_snapshot_rows': invalid, 'truncated_snapshot_rows': truncated,
        'captured_goal_entries_sum': n_goal_only + n_target_only,
        'goal_selector_entries_sum': n_goal_only,
        'target_selector_entries_sum': n_target_only,
        'potential_shared_flag_pairs_sum': potential_count,
        'same_priority_shared_flag_pairs_sum': same_priority_count,
        'co_running_shared_flag_pairs_sum': co_running_count,
        'delta_snapshot_events': deltas_total,
        'delta_snapshot_valid': deltas_valid,
        'delta_snapshot_invalid': deltas_invalid,
        'delta_changes_false_to_true': deltas_start_like,
        'delta_changes_true_to_false': deltas_stop_like,
        'delta_events_with_truncation': deltas_with_truncation,
        'delta_examples': delta_examples,
        'examples': summaries,
        'runtime_pass': False,
        'interpretation': 'Shared flag and same priority is a resource-contention CANDIDATE; delta events are end-of-tick state differences, not Goal.start/stop or interrupt callbacks. No runtime conflict, failure or TPS benefit is established.',
        'requirements_for_conclusion': 'Authenticated LAB run, loaded exact Spore jar and observer build, targeted goal method transitions and cleanup evidence, completed Forge GameTest assertions.',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('jsonl', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    report = analyze(args.jsonl)
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    if args.out:
        args.out.write_text(encoded, encoding='utf-8')
    else:
        print(encoded, end='')
    return 2 if report['status'].startswith('BLOCKED') else 0


if __name__ == '__main__':
    sys.exit(main())
