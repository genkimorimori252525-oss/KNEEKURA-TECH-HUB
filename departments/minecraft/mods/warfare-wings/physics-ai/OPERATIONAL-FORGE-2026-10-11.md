# Warfare Wings: simultaneous real-Forge operational acceptance, 2026-10-11

## Evidence boundaries

This report records the **local original-artifact Forge 1.20.1 GameTest** run
using the owner's hash-pinned Warfare Wings / Immersive Aircraft JARs. The
runtime traces live under the ignored
`runtime-probe/run-gametest/ww-physics-traces/` directory; no proprietary mod
JAR, save, or recorded binary is committed here. Compare this record against
the source-only V3 experiments in `COMBAT-SIMULATION-v1.md`, **not as the same
starting geometry**. The Forge scenarios intentionally add real multi-plane
actors and different starting formations.

Expected original Warfare Wings SHA-256:

`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`

Pinned Immersive Aircraft SHA-512:

`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`

## Actual local GameTest outcome

In the 2026-10-11 local Forge `runGameTestServer` log, the test server
reported **15 GAME TESTS COMPLETE** followed by **1 required tests failed**:
`twoescortsdefendb17againsttwoapproachinghostiles`. The other **14 GameTests
passed**, including the simultaneous 2v2 operation. The game server proceeded
to normal shutdown; the B-17 failure was not disguised as a successful escort
or converted into a cross-test orphan-plane crash.

The independently parsed real `ww.physics.forge-tactical-pilot.v1`
per-aircraft CSVs gave:

| Exact live scenario | Real entity ticks | Per-plane samples | Geometric result | Operational caveat |
|---|---:|---:|---|---|
| Two red A6M against two blue P-47N | 280 | 281 each | **PASS**: all six pairs remained at least **11.198347** blocks apart; opposing-pair minimum **27.331806** blocks; zero ticks under 6 | Movement/contact, **no real weapon fired, no kill** |
| B-17, two P-47N escorts against two A6M raiders | 340 | 341 each | **FAILED**: enemy inside the 95-block defended corridor for **101 ticks**, closest to B-17 **66.029299** blocks; all 10 aircraft pairs remained >=6 blocks apart | The aircraft and enemy attack approach actually moved and were measured; protection gate strictly failed |

Both were actually co-spawned, simultaneously controlled and matched to a
consecutive common server game-time series. Actual 2v2 passed collision
clearance and the GameTest's hostile-observation/engagement assertions; it is
**not** verified dogfight victory. The B-17 plane and its escort attempts
could not keep raiders outside the specified corridor; protection remains
**FAILED**. The original/source aft escort remains a separate scenario and
also **FAILED** under its unchanged radius.

Independent machine-checkable receipts are defined by:

- `scenarios/forge-operational-2v2.json`
- `scenarios/forge-operational-b17-escort.json`
- `tools/verify_live_aircombat_receipts.py`

With true locally collected traces present, execute from `physics-ai`:

```powershell
python tools/verify_live_aircombat_receipts.py scenarios/forge-operational-2v2.json runtime-probe/run-gametest/ww-physics-traces
python tools/verify_live_aircombat_receipts.py scenarios/forge-operational-b17-escort.json runtime-probe/run-gametest/ww-physics-traces
```

Expected at this known telemetry snapshot: the 2v2 verifier exits **0** and
the B-17 verifier exits **1** with
`ESCORT_PROTECTION_BREACHED:b17:ticks=101`. Do not alter radius, flight
horizon or starting conditions solely to change that exit code.

## Source-only control tests and reproducible baseline

Separately, the Java 17 offline/source simulator passed its deterministic
tests and all 24 corrected engine-reaction profiles. The unchanged original
aft V3 B-17 geometry improved from 92 to 63 intrusion ticks, but still
failed the 95-block corridor gate; forward-prepared V3 improved from 30 to
13 intrusion ticks, also FAILED. The corrected-source 2v2 all-six-pair
minimum remains 36.922230 blocks. None of these source-only numbers is a
live Forge aircraft measurement.

The Docker source verifier (Java 17, no network, read-only root, minimal
temporary filesystem) passed after independently comparing all 96 tactical
golden rows: **only 14 fighter `ROLE_MISSION=ESCORT` rows** changed as a
consequence of deliberate escort-controller updates; all non-escort rows,
24-aircraft Atlas V2/V3 reports and evidence-source labels were preserved.
The new independent operational CSV parser also passed 12 synthetic
tampering fixtures; these tests do not invent successful combat data.

## Unproven objectives

Actual machine-gun/bomb/torpedo release, damage, cooldown, ammunition,
friendly-fire/terrain harm, kill ownership, cross-environment trajectory
parity, a physically completed hostile-defeating escort, 24-plane
**simultaneous** battle, long-term mixed-mission fleet endurance and landing
are **NOT_ESTABLISHED**. Unsafe autonomous fire remains intentionally
disabled. A source-only attack waypoint or safe 2v2 proximity does not prove
combat effectiveness. Operational 2v2 and B-17 acceptance cases use real
actors, but are not a substitute for the full target mission suite.
