# Wave System Deep Dive — authored siege rhythm to persistent budget phases

## Legacy Wave 1–11

The original 1.1.2 waves are handcrafted encounter scripts. Each `WaveEntry` independently defines time window, planned amount, spawn granularity, mob pool, optional angular sector and minimum spawn points.

| Wave | Defined mobs | Duration | Rest | Role progression |
|---:|---:|---:|---:|---|
| 1 | 11 | 110 s | 15 s | Zombie/Spider + Engineer burst |
| 2 | 14 | 120 s | 15 s | Skeleton/Pigman/rare Creeper |
| 3 | 17 | 120 s | 18 s | T2 Spider/T2 Zombie burst |
| 4 | 17 | 120 s | 18 s | intended Pigman T2 burst |
| 5 | 30 defined | 130 s | 80 s | Thrower introduction; unreachable finale defect |
| 6 | 19 | 110 s | 25 s | denser T2 pressure |
| 7 | 19 | 120 s | 36 s | Thrower specialist + two bursts |
| 8 | 21 | 110 s | 30 s | concentrated 25° burst |
| 9 | 22 | 120 s | 35 s | T3 Zombie introduction |
| 10 | 38 | 172 s | 60 s | largest authored wave |
| 11 | 23 | 120 s | 35 s | stronger general pool |

“Defined mobs” is the sum of entry amounts, not proof every entity successfully spawns.

## Distributed defect — Wave 5 finale cannot begin

Wave 5 defines a seven-mob finale at **135000–165000 ms**, but creates the enclosing Wave with total time **130000 ms**.

Legacy `Wave.isComplete()` becomes true once total elapsed exceeds 130000 ms, while `Wave.doNextSpawns` invokes an entry only inside its own scheduling window.

The uploaded JAR bytecode contains the same constants. Therefore the finale cannot enter its window through normal Wave-5 scheduling before the Wave is already complete.

## Legacy blocked-spawn boundary

A failed spawn remains queued in `WaveEntry.spawnList`, but after the entry time window closes the old `Wave` stops calling that entry. Old `Wave.isComplete` ignores pending constructs.

Modern history explicitly repairs this.

## Legacy >11 scaling

For `N > 11`:

```text
mobScale  = 1.09^(N - 11)
timeScale = 1 + 0.04*(N - 11)
```

The system reuses a Wave-11-like base/specialist/burst structure and introduces Imp / Thrower T2. Intended higher Pigman tiers are undermined by the distributed T2/T3 pattern initialization bug.

Burrower is not in the legacy extended pool.

## Legacy continuous mode

Stable Nexus uses a separate procedural 240-second builder rather than simply replaying authored waves:

- base rate roughly `0.12 * difficulty` mobs/sec;
- seven regular group/steady cycles;
- one larger group;
- finale and cleanup pressure.

Difficulty/tier scale from Nexus power level. This already separates authored campaign waves from procedural endless pressure.

## Modern scheduler repair chain

- `bd28a994`: keep retrying pending constructs after their formal scheduling window and require entry spawn completion.
- `6bea029c`: add 1000 ms blocked-spawn retry backoff.
- `1589c88f`: abort/discard pending obligations when Nexus truly stops.
- ANCHOR `aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10`: bounded spawn-failure grace and explicit skipped-spawn accounting without awarding kills.

The important lifecycle is:

```text
planned -> spawned -> alive/defeated
       \-> explicitly skipped/cancelled
```

Do not collapse these counters.

## Modern standard driver — BudgetWavePlan

The pinned 1.20.1 Nexus normal driver generates a persistent `BudgetWavePlan` rather than relying on the retained legacy-style WaveBuilder.

A normal wave normally has four phases. Each phase:

- selects a tactical theme;
- receives budget `wave * 10`;
- buys individual units or occasional predefined teams;
- fills remaining pressure;
- guarantees an Engineer-role purchase;
- persists the exact purchase list.

Reload restores the plan rather than rerolling it.

### Themes

SWARM, ARMORED, RANGED, UNDERGROUND, SPIDER, FLYING, NETHER, SIEGE, FAST, MIXED, RANDOM, RANDOMHELL.

### Team purchases

Supported groups include ZOMBIE_RUSH, WITHER_GANG, SPIDER_GANG, SPIDER_FAMILY, SKELETON_FAMILY and ENDER_SWARM.

This preserves tactical relationships inside procedural composition.

### Soft adaptation

Forge events record player block placements and whether player kills are projectile-based.

At the next plan, the choice pool is softly biased:

- >20 placed blocks -> more SIEGE probability;
- strongly melee-dominated kills -> more RANGED probability;
- strongly ranged-dominated kills -> more SWARM probability;
- strong nearby fire/lava presence -> more NETHER probability.

Bias changes probability; it does not force a hard counter.

### Phase completion

The modern lifecycle considers purchase counts, actual loaded surviving phase mobs, spawn completion and a no-progress timeout. Timeout can close impossible spawn obligations rather than pretending they were kills.

## KNEEKURA design lesson

A strong hybrid is:

1. authored early waves that deliberately teach roles;
2. authored milestone/boss waves;
3. budget/theme generation for long-term replayability;
4. soft adaptation based on demonstrated defenses;
5. persisted exact plans across save/load;
6. separate planned/spawned/alive/defeated/skipped counters.
