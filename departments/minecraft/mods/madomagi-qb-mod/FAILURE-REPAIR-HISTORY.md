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