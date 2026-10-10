#!/usr/bin/env python3
"""Independent arithmetic probe for original Spore Proto Signal dispatch choice.

Synthesizes the narrow code branch identified in `Proto.checkForCalamities`:
for each eligible, idle Calamity, a 50% random trial; on the first success,
set a search destination. If all eligible candidates fail, attempt Womb.
No Minecraft runtime, actual Mob, AI scheduling or real terrain is emulated.
"""
from __future__ import annotations
import argparse
import json
import random
from math import sqrt


def proto_signal_branch(rng: random.Random, eligible_count: int) -> str:
    for _ in range(eligible_count):
        if rng.random() < 0.5:
            return 'redirect'
    return 'womb_attempt'


def commander_prefer_available(eligible_count: int) -> str:
    return 'redirect' if eligible_count else 'womb_attempt'


def run(trials: int, seed: int) -> dict:
    out=[]
    for n in range(6):
        rng=random.Random(seed+1009*n)
        fallback=sum(proto_signal_branch(rng,n)=='womb_attempt' for _ in range(trials))
        exact=2.0**(-n)
        observed=fallback/trials
        tolerance=5*sqrt(exact*(1-exact)/trials) + 0.005
        assert abs(observed-exact)<tolerance,(n,observed,exact,tolerance)
        independent=commander_prefer_available(n)
        assert independent==('redirect' if n>0 else 'womb_attempt')
        out.append({
            'eligible_unassigned_calamities':n,
            'exact_original_attempt_womb_probability':exact,
            'observed_original_womb_attempt_rate':round(observed,6),
            'observed_womb_attempts':fallback,
            'independent_prefer_available_rate':0.0 if n>0 else 1.0,
            'approximate_expected_goal_evaluations': 'NOT_MODELED',
        })
    return {
        'schema':'kneekura.spore.signal-branch-synthetic.v1',
        'status':'PASS_SYNTHETIC_MODEL',
        'input_scope':'Conditional original Proto.checkForCalamities 50% per idle Calamity; assumed independent draws and valid placement',
        'not_modeled':['Forge GoalSelector and tick rate','actual terrain placement','Mob availability across chunks','Womb spawn success/cost','live performance/tps','branch caller state'],
        'trials_per_scenario':trials,'rng_seed':seed,
        'comparison':'independent deterministic alternative prefers an eligible existing unit; NOT original Spore AI',
        'results':out,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--trials',type=int,default=30000)
    p.add_argument('--seed',type=int,default=20261011)
    opts=p.parse_args()
    if opts.trials<10000:p.error('At least 10000 trials for this statistical assertion')
    print(json.dumps(run(opts.trials,opts.seed),ensure_ascii=False,indent=2,sort_keys=True))

if __name__=='__main__':main()
