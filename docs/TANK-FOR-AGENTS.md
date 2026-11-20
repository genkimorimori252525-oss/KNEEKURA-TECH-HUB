# Tank for AI agents: test a MOD in one command

2026-11-20. Start here when you are asked to check a Minecraft **1.20.1 Forge** MOD in the real game. This page is the task order; [native-host/README.md](../departments/minecraft/lab/native-host/README.md) is the full reference and [TANK-OPERATING-GUIDE.md](TANK-OPERATING-GUIDE.md) holds the older, deeper observation routes.

The Tank launches a real client on a private copy of a small pre-generated world, runs a finite window, closes it with verified exit and evidence, and prints one PASS/FAIL JSON summary. You do not build a client, edit run configs, or patch refmaps.

## Rules (keep them)

- **One trial at a time.** The host holds a shared lock; a second `run` waits or is refused.
- **No automatic retry.** A FAIL is a result: read its summary, fix the cause, then run again on purpose.
- **Never delete `host-lock.json` or any lock by hand.** Interrupted `warm`/`prepare`: `tank.mjs release-stale-lock --installation INSTALLED` (it refuses while an owner or user process exists, and never touches a trial lock). A trial: `stop --trial` / `abort --trial`.
- **Never open the original world with RegionFile tools.** Every trial runs on its own copy; scenario commands also act only on that copy.
- Do not touch a trial another agent is running.

## 1. Find the installed host

```powershell
$tank = (Get-Content (Join-Path $env:LOCALAPPDATA 'Kneekura/TechHub/Tank/active-host.json') -Raw | ConvertFrom-Json).installed
node "$tank/native-host/tank.mjs" doctor --installation $tank
```

No `active-host.json`? Install and warm once from this repository's `departments/minecraft/lab` (see the reference's "One-time installation"; `warm --online` only when dependencies are missing). A changed host source needs `install` + `warm` again; the new host becomes active only after a successful warm.

## 2. Put `tank.json` in the MOD project

```json
{
  "schema": "kneekura.tank-project/v1",
  "id": "my-mod",
  "mods": [{"id": "mymod", "jar": "build/libs/mymod-*.jar", "kind": "mapped-dev"}],
  "world": "@swap",
  "selfTest": true
}
```

- `kind`: `mapped-dev` for a normal `gradlew build` dev JAR (refmap remapping is automatic), `forge-distribution` for a reobfuscated release JAR. `*` picks the newest matching file.
- `world: "@swap"` is the ready 52×52×24 test tank (fixture under `%LOCALAPPDATA%/Kneekura/TechHub/Tank/fixtures/`). It supplies Player and subject UUIDs. A raw world path instead needs `subjectUuid` (a living entity in that world).
- Defaults you usually keep: `view: "tank"` (small render/simulation distance), `trails: true`, `ai: true`, `maxTicks: 600` (server ticks, 30 s), `maxWallMs: 30000`. Raise `maxWallMs` (≤120000) for longer scenarios.

## 3. Run and read the summary

```powershell
node "$tank/native-host/tank.mjs" run --project C:/path/to/mod
```

The last JSON line is the summary. Read in this order:

| Field | Meaning | If wrong |
| --- | --- | --- |
| `status` | PASS only if launch, closure, self-test and scenario all pass | look at the blocks below |
| `failure` | crash-report excerpt, last error lines, launch/cleanup/ready-wait facts | fix the MOD or `tank.json`; do not just rerun |
| `selfTest` | your MOD's own checks (below) | `failed` lists the rows |
| `scenario` | failed steps/expectations, load `segments`, `screenshots` | `scenario-judgement.json` has every row |
| `ai` | path of `ai.jsonl`, `explainedClasses`, `next` hint | |

READY typically takes 25–30 s; a whole 600-tick trial about 1–2 min.

## 4. Observe without writing per-MOD code

On by default, generic for every MOD:

- **Trails:** sampled paths of every Mob/Projectile near the Player (`trails-result.json`).
- **AI lens:** WHAT each nearby Mob's AI is doing: running goals, target goals, Brain activity, target, path, and state-like fields your entity classes declare (enum fields, `EntityDataAccessor` values, phase/state/mode fields). `ai.jsonl` records only changes: `{"tick","event":"CHANGE"|"GONE","type","goals","targetGoals","target","state","why","pathTo"}`. Read it instead of guessing from screenshots.

## 5. Explain WHY (MOD-owned, improves over time)

Copy [`templates/TankWhy.java`](../departments/minecraft/lab/native-host/templates/TankWhy.java) into the MOD, then:

```java
final TankWhy why = new TankWhy();
public java.util.Map<String, Object> tankWhy() { return why.snapshot(); }   // on the entity or a custom Goal
// at the deciding line:
if (cooldown > 0) { why.note("attack", "skip: cooldown " + cooldown); return false; }
```

The lens finds `tankWhy()` by reflection; notes appear above the mob and as `"why"` in `ai.jsonl`. Outside the Tank it is one boolean check. Loop: run → read `why` → if a question is not answered, add or sharpen a note at the deciding line (one stable key per decision, the deciding value, no narration, no side effects) → run again. Leave the notes in the MOD.

## 6. Set up situations and judge them (`scenario`, `expect`)

```json
"maxWallMs": 60000,
"scenario": [
  {"at": 0,   "try": "difficulty normal"},
  {"at": 0,   "run": "gamemode survival @p"},
  {"at": 0,   "run": "effect give @p minecraft:resistance 120 4 true"},
  {"at": 0,   "run": "effect give @p minecraft:night_vision 120 0 true"},
  {"at": 20,  "mark": "idle"},
  {"at": 100, "run": "execute at @p run summon mymod:boss ^ ^ ^8"},
  {"at": 140, "mark": "boss"},
  {"at": 200, "screenshot": "fight"},
  {"at": 400, "check": "execute if entity @e[type=mymod:boss]"}
],
"expect": [
  {"entity": "mymod:boss", "target": "minecraft:player", "by": 200},
  {"entity": "mymod:boss", "goal": "BossChargeGoal", "between": [100, 500]},
  {"entity": "mymod:boss", "state": {"phase": "ENRAGED"}, "after": 150},
  {"seen": "mymod:fireball"},
  {"tickMs": {"segment": "boss", "p95": 50}}
]
```

- Steps run at server ticks from the bound Player (tick 0), as the Player with permission 4. `run` must succeed; `try` is recorded only (vanilla errors on no-op setup such as `difficulty normal`); `check` must succeed with result > 0; `screenshot` is for eyes, never judged; `mark` starts a load segment.
- Keep the Player alive in survival (resistance) or the window ends early. Use `^ ^ ^N` (in front of the Player).
- `expect` is judged after closure from recorded facts: `target`, `goal` (`between`), `state` (state fields or `tankWhy` notes), `gone` (`REMOVED`/`OUT_OF_SELECTION`/`ANY`), `seen`, `tickMs`. Goal names are class names (`ZombieAttackGoal`, inner classes by their own name).
- **Load:** every server tick is timed; each `mark` segment reports `ms` and `tankExcludedMs` (mean/p50/p95/max), plus entity counts at the mark. Compare segments of the same run; budgets should be generous (one run, client renders on the same machine). Measured reference: 1 → 161 Husks raised mean tick 8.5 → 10.9 ms.
- Not automated: Player walking/using items. Use `/damage`, `/give`, `/item`, `/effect`, `/tp`.

## 7. MOD self-test (optional)

With `"selfTest": true` the MOD sees `System.getProperty("kneekura.tank.selfTest")` (a nonce). Only then, log `KNEEKURA_TANK_SELFTEST <nonce> PASS|FAIL <name>` lines and one `KNEEKURA_TANK_SELFTEST <nonce> DONE pass=N fail=M`. Missing DONE or a mismatch is FAIL.

## Troubleshooting

| Symptom | Do |
| --- | --- |
| `SUBJECT_NOT_LOADED` after ~20 s | wrong `subjectUuid` for a raw world; use `@swap` or a real entity UUID |
| `TANK_REFMAP_REMAPPING_FILE_MISSING` | host not warmed: run `warm` |
| warm silent for minutes | run it under a watchdog (`guard.mjs --idle`); if stopped, `release-stale-lock`, then warm again (seen twice, cause unknown) |
| `run` refused by lock | someone else's trial; wait. Never delete the lock |
| scenario step `NOT_REACHED` | window ended first: raise `maxWallMs`/`maxTicks` or keep the Player alive |
| labels/trails missing on screen | they are presentation only; trust `ai.jsonl`, `trails-result.json` |
