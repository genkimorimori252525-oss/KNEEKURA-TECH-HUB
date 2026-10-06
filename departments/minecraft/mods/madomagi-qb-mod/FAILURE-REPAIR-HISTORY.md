# QB-MOD / Garnet-MOD 1.6.4.082 — Failure / Repair History status

## Window and sources checked

Analysis date: 2026-10-07.

Target snapshot: supplied QB-MOD/Garnet-MOD 1.6.4.082 archives.

History reconnaissance:
- original distribution topic: http://forum.minecraftuser.jp/viewtopic.php?f=13&t=8468
- creator introduction: https://www.nicovideo.jp/watch/sm19563098
- contemporary Bahamut update: https://forum.gamer.com.tw/Co.php?bsn=18673&sn=404365
- general web/GitHub discovery for a matching source repository

## Result

No supported upstream Git repository has been pinned, so no Issues → PR → fix commit → before/after chain is available in the current evidence set.

The Bahamut 2013 update describes small bug fixes and two UF behavior changes (dropping stored items on UF entry and refusing inventory open in UF), but it contains no repair diff or introducing/fixing commit. It is secondary change-history reconnaissance, not a completed Failure/Repair record.

The historical Minecraft Japan Forum topic is repeatedly corroborated but currently inaccessible through the fetcher. It remains DISCOVERED_NOT_REVIEWED.

## Source-level anomalies for future history matching

1. Walpurgis airborne fallback applies poison to theHost rather than theTarget.
2. EntityMahoShojo.setSoulGemDamage is additive despite setter naming.
3. MadomagiGuiHandler stores mutable shared container state.
4. Walpurgis mutates attacking player creative/flying capability flags.
5. Walpurgis repeatedly mutates global overworld weather/time.

These are candidate failure leads, not historically proven bugs until matching reports or revisions are found.

## Facet status

NOT_ANALYZED / HISTORICAL_VCS_UNAVAILABLE_WITH_CURRENT_EVIDENCE

This does not mean the MOD had no bugs; it means the mandatory repair-history facet cannot be promoted with the evidence currently available.

## Additional source-level anomaly leads from the deep-dive pass

6. **Oktavia wheel spawn stdout spam** — `EntityMajoAIOktavia.spawnWheel` prints `false` for failed candidate positions and `true` on success. Combat can execute many candidate attempts per volley.
7. **Homulilly unreachable apparent attack selection** — `getRNG().nextInt(1)` always evaluates to 0, so the surrounding switch/selection shape cannot select a second mode.
8. **Grief Seed unreachable Walpurgis default** — `chooseMajo` uses `nextInt(5)`, yielding 0–4; its switch default constructs Walpurgisnacht but cannot be reached through that random call.
9. **Repeated up-to-64 teleport attempts** — Homulilly and Homura-family logic can test many random destinations synchronously in one action/update.
10. **Large synchronous collision block destruction** — Homulilly Nutcracker and Charlotte second form iterate collision regions and remove blocks during living updates.
11. **Kriemhild large-volume pulse / terminal explosion** — large AABB living-entity scan can process roughly one hundred targets per 40-tick pulse, and death explosion strength is 80.
12. **Creative/flying capability mutation is duplicated** — the unsafe anti-cheese pattern exists outside Walpurgisnacht in Homulilly Nutcracker.

These remain static anomaly candidates. Without a historical report, repair diff or bounded runtime reproduction they are not promoted to proven failures.


## Additional architecture / persistence / asset anomaly leads

13. **Garnet reverse dependency on QB** — `EntityGarnetAINearestAttackableTarget` directly references `puellamagi.mods.entity.monster.EntityHomulillyNutcracker`, and the reference is present in the distributed Garnet class constant pool. The nominal lower-level framework therefore contains a concrete upper-layer QB dependency.
14. **Source-only stale external imports** — two Garnet Java files import Korezon/Kuko classes from unrelated packages even though their method bodies do not use them and the compiled class files do not contain those references. A clean source build can therefore have dependency friction not represented by the shipped binary.
15. **Repeated target reacquisition** — Garnet nearest-target `continueExecuting()` calls `shouldExecute()`, potentially repeating multi-AABB scans/sorts while already tracking a target. Static performance lead only.
16. **TexturePack Madoka UF resource-path mismatch** — the intended `madokaUF.png` entry begins with full-width U+FF4D `ｍ`, not ASCII `m`. Nineteen other overrides map to exact base paths; this one does not.
17. **Homulilly ritual flag not persisted** — `EntityGriefSeed.isHomulilly` selects Nutcracker hatching but is absent from custom NBT read/write. Save/load should therefore lose the special ritual identity unless an unobserved engine path restores it.
18. **Charlotte second-form flag not persisted** — DataWatcher 19 controls second-form behavior/rendering, but NBT stores only `Revivable`. Default load state is first form unless another path resets it.
19. **Witch ecological age not persisted** — `EntityMajo.age` and `summonServant` drive evolution/summoning and are plain fields with no NBT persistence. Save/load resets the growth clock by construction.
20. **Parent/encounter object references are runtime-only** — Ophelia master, Shadow→Walpurgis and Homulilly-servant→Nutcracker links are not persisted as stable IDs in the inspected classes, so callbacks/lifetime coupling can be lost across serialization boundaries.
21. **Walpurgis singleton gate is process-local** — `mod_QB.canWalpurgisSpawn` is a static runtime/config boolean flipped false at spawn and true on death/removal; it is not world-persisted. Server restart with an existing encounter is a duplicate-admission candidate.
22. **GarnetGun packet indexes byte zero without visible length validation** — malformed/empty legacy custom payload is a packet-boundary robustness lead.
23. **Lotte/Luiselotte hostile hit upgrades weak armor to diamond** — source explicitly replaces sub-diamond armor with diamond equivalents. This may be intentional oddity or inverted logic; historical intent is unavailable.
24. **Kriemhild possible duplicate Grief Seed path** — health<=0 living-update code explicitly drops one Seed before `setDead()`, while `dropFewItems` separately drops one. Exact superclass death lifecycle must be traced/runtime-tested before claiming two drops.
25. **EntityGriefSeed bypasses superclass custom NBT hooks** — its overrides do not call `super.writeEntityToNBT/readEntityFromNBT`. Base Entity serialization still handles common outer fields, but inherited EntityLiving/Creature-specific state impact is unresolved.
26. **Reserved Oriko/Yuma configuration without implementation** — config/entity/item ID fields exist, but the supplied tree contains no corresponding entities and no usable registration/instantiation. Treat as dead/reserved code, not a feature.

These are deliberately kept as **static leads**. Promotion to a failure/repair case still requires bounded runtime evidence or historical report+repair provenance.
