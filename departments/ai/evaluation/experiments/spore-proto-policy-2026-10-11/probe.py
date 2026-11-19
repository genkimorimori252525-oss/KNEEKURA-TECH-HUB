#!/usr/bin/env python3
"""Independent Spore Proto arithmetic probe; NOT a Minecraft/JAR runtime test.

Synthetic labels are invented for an ablation test. The implemented equations
mirror the narrowly inspected 2.2.0j scorer and row-wide delta update; no
copyrighted source, assets, save files or third-party algorithms are copied.
"""
import argparse
import json
import random
import statistics

JAR_SHA = 'd20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489'
CONTEXTS = tuple(tuple(float(i == j) for i in range(4)) for j in range(4))
MODES = ('frozen', 'proto_row', 'feature_gated', 'proto_row_plus_morale')


def choose(weights, x):
    scores = [sum(weights[j*4+i]*x[i] for i in range(4)) for j in range(4)]
    return max(range(4), key=lambda j: scores[j])  # first wins ties


def update(weights, action, x, success, feature_gated=False):
    delta = 0.05 if success else -0.10
    for i in range(4):
        if feature_gated and not x[i]:
            continue
        p = action*4+i
        weights[p] = max(-1., min(1., weights[p] + delta))


def boost(weights, rng):
    if sum(w < 0 for w in weights) > 8:
        for i in range(16):
            weights[i] += rng.random()  # original special path has no clamp


def trial(seed, mode, scenario, episodes):
    initial_rng = random.Random(seed)
    w = [initial_rng.random() for _ in range(16)]
    cases_rng = random.Random(seed+1_000_003)
    boost_rng = random.Random(seed+2_000_003)
    def accuracy():
        return sum(choose(w, x) == (i if scenario == 'conditional' else 2)
                   for i, x in enumerate(CONTEXTS))/4
    before = accuracy()
    history = []
    for ep in range(episodes):
        context_index = cases_rng.randrange(4)
        x = CONTEXTS[context_index]
        action = choose(w, x)
        success = action == (context_index if scenario == 'conditional' else 2)
        history.append(success)
        if mode != 'frozen':
            update(w, action, x, success, feature_gated=mode == 'feature_gated')
        if mode == 'proto_row_plus_morale' and (ep+1) % 6 == 0:
            boost(w, boost_rng)  # synthetic 200-tick episodes assumption
    return {'initial': before, 'final': accuracy(), 'last300': sum(history[-300:])/300,
            'all': sum(history)/episodes, 'neg': sum(z < 0 for z in w)}


def assert_contracts():
    w = [0.]*16
    assert choose(w, (0, 0, 0, 0)) == 0
    update(w, 1, (1, 0, 0, 0), True)
    assert w[4:8] == [0.05]*4
    update(w, 1, (1, 0, 0, 0), False)
    assert all(abs(z+0.05) < 1e-12 for z in w[4:8])
    w = [0.]*16
    update(w, 2, (0, 1, 0, 0), True, feature_gated=True)
    assert w[8:12] == [0., 0.05, 0., 0.]
    w = [-0.01]*9 + [0.99]*7
    boost(w, type('FixedRng', (), {'random': lambda self: 0.9})())
    assert w[-1] > 1.0
    assert 3-5*2 == -7
    # With four alternatives per team, P(real member == decision index) = 1/4
    assert sum(k == j for j in range(4) for k in range(4)) == 4


def run(seeds, episodes):
    assert_contracts()
    results = {}
    for scenario in ('conditional', 'global_best'):
        results[scenario] = {}
        for mode in MODES:
            rows = [trial(i, mode, scenario, episodes) for i in range(seeds)]
            results[scenario][mode] = {
                k: round(statistics.mean(row[k] for row in rows), 6)
                for k in ('initial', 'final', 'last300', 'all', 'neg')}
            results[scenario][mode]['perfect_at_end'] = sum(row['final'] == 1 for row in rows)
    return {
        'schema': 'kneekura.synthetic-policy-probe.v1',
        'source_jar_sha256_for_arithmetic_contract_only': JAR_SHA,
        'assertions': 'PASS', 'runtime': 'SYNTHETIC_NOT_MINECRAFT',
        'seeds': {'start': 0, 'stop_exclusive': seeds},
        'episodes_per_seed': episodes,
        'context': '4 uniformly sampled one-hot binary features',
        'conditional': 'synthetic optimal action equals active input feature index',
        'global_best': 'synthetic optimal action is always 2',
        'proto_row_plus_morale': 'MORALE PERIOD ARTIFICIALLY every 6 episodes (200 ticks per episode); not an original runtime trace',
        'feature_gated': 'PROPOSED COMPARATOR, not original Spore',
        'results': results,
        'limits': ['Invented task/rewards and seeded Python RNG, not Mojang RNG or combat events',
                   'No pathfinding, tick-time cost, physics, Mob spawning, attribution feedback or resource lifecycle simulated',
                   'The synthetic outcome is conditional on scenario/seed/horizon, NOT measured Spore combat intelligence']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=256)
    parser.add_argument('--episodes', type=int, default=1200)
    args = parser.parse_args()
    assert args.seeds > 0 and args.episodes >= 300
    print(json.dumps(run(args.seeds, args.episodes), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
