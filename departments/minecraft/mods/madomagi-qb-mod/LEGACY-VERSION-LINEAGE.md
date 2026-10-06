# QB-MOD / Garnet-MOD — Legacy version lineage and archive reconnaissance

Date: 2026-10-07

This document is a bounded historical-reconnaissance record. Community/archive references establish discovery leads and chronology; they do not override the pinned 1.6.4.082 source/binary snapshot.

## Confirmed / strongly bounded points

### 2013-11-04 — 1.6.4.080-era update

A contemporary Bahamut guide, edited 2013-11-05, labels the change as "11/4 update" and identifies the then-current download text as:

- `ver.1.6.4.080ダウンロード（9.11.1.916）` for QB-MOD;
- matching 1.6.4.080 Garnet-MOD;
- older versions under a separate `旧ver.` link.

Source:
- https://forum.gamer.com.tw/Co.php?bsn=18673&sn=404365
- retrieved 2026-10-07.

The same page reports that this update included small bug fixes plus two Ultimate Form inventory rules:
1. inventory contents are ejected when entering UF;
2. the NPC inventory cannot be opened in UF.

These are useful version-history claims but not a repair diff.

A separate Minecraft Forum crash log from late 2013 shows a live 1.6.4 Forge installation containing:
- `QB-MOD.v.1.6.4.080.zip`;
- `Garnet-MOD.v.1.6.4.080.zip`.

This independently corroborates that .080 was distributed and used in the wild.

### 1.6.4.082 — recovered final/current archived distribution

The project-owner supplied archives identify themselves in their readmes as:
- `QB-MOD 1.6.4.082`;
- `Garnet-MOD 1.6.4.082`.

Archive hashes are pinned in `SOURCE-SNAPSHOT.md`.

A 2022 Reddit recovery thread reports that the 2019 Wayback snapshot of the original Japanese forum exposes the red download line beginning `ver.1.6.4.082`. The same thread later identifies the archived Garnet-MOD forum page as the required dependency.

Discovery references:
- https://www.reddit.com/r/MadokaMagica/comments/t0iusb
- archived QB topic: https://web.archive.org/web/20190715132938/https://forum.minecraftuser.jp/viewtopic.php?f=13&t=8468
- archived Garnet topic: https://web.archive.org/web/20190715134048/https://forum.minecraftuser.jp/viewtopic.php?f=13&t=6128

The Wayback page itself was not fetchable through the current retrieval environment, so this remains a secondary report about the archived page rather than a direct capture.

### 1.6.4.082 archive-internal time bound

The supplied ZIP directory timestamps provide an internal build-content bound:

QB-MOD:
- earliest member timestamp: 2012-11-15;
- latest member timestamp: **2014-01-04 15:10:32**;
- 166 entries share **2014-01-04 15:04:38**.

Garnet-MOD:
- earliest member timestamp: 2012-12-06;
- latest member timestamp: **2014-01-04 15:19:58**;
- 45 entries share **2014-01-04 15:04:38**.

Interpretation:
- .082 contains files written/packed on 2014-01-04;
- therefore this exact content snapshot cannot predate those member timestamps;
- ZIP DOS timestamps are **not** proof of the public release time, timezone or upload time.

Combined with the confirmed 2013-11-04 .080 reference, this establishes continued development from .080 into the supplied .082 snapshot across roughly the following two months without inventing an exact .082 release date.

## Behavioral delta lead: .080 guide vs .082 source

The .080-era guide describes Homura UF as losing time magic while gaining flight plus continuous spread homing arrows.

The pinned .082 source's `EntityHomuraAIUltimate` instead contains a close pursuit / repeated melee / percentage-health and eventual execution escalation path, while the oscillatory homing-arrow flight pattern exists in `EntityHomuraAIRebellion`.

This is a concrete version-delta lead:
- it may reflect post-.080 redesign associated with Rebellion-era content;
- it may also reflect guide staleness or terminology drift.

No old .080 source archive has yet been pinned, so the exact introducing revision/change cannot be claimed.

## Project lifetime evidence

The creator introduction video metadata identifies the original download topic and the creator's Twitter handle `@Ganetto0314`. A later annotation dated 2018-03-04 states that video/MOD production was being suspended indefinitely due to loss of motivation.

Discovery reference:
- creator introduction mirror/index for Nico video `sm19563098`;
- original distribution topic `t=8468`.

This only establishes a later suspension notice. It does not prove that .082 was the final code ever produced.

## FRONTIER search performed

GitHub repository search on 2026-10-07:
- `QB-MOD Madoka Minecraft` → no matching repository;
- `Garnet-MOD Minecraft` → no matching repository;
- `Ganetto0314 Minecraft` → no matching repository;
- `puellamagi mods EntityWalpurgisnacht Minecraft` → no matching repository;
- `EntityMahoShojo Minecraft` → no matching repository.

GitHub public code search:
- `EntityMahoShojo` → 0;
- `EntityWalpurgisnacht puellamagi` → 0;
- `mod_QB Garnet-MOD` → 0;
- `Ganetto0314` → 0.

General web searches also failed to establish a supported 1.7.x+ lineage for this exact QB/Garnet implementation.

Interpretation:
- **FRONTIER remains UNPINNED / NOT_ANALYZED**;
- this is not a claim that no later/private/deleted source ever existed;
- deleted, private, non-indexed and non-GitHub material remain possible.

## Historical artifacts still worth recovering

Highest-value missing artifacts:
1. direct capture of the archived original QB forum page;
2. direct capture of the archived Garnet forum page;
3. QB/Garnet 1.6.4.080 archives;
4. any .081 archive;
5. any post-.082 release archive or changelog;
6. creator update posts/Twitter captures around 2013-11 through 2014-01.

If .080 or .081 binaries/sources are recovered, compare full archive hashes/tree inventories first, then perform source/bytecode deltas. Do not infer a chronological code change solely from community prose.
