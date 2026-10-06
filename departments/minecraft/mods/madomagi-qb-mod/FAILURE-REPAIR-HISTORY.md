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
