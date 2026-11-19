# ERA-CONTEXT — contemporary usage and reports

Temporal role: **ERA_CONTEXT / LATER_RETROSPECTIVE**

Primary surviving forum thread:
https://www.civa.jp/viewtopic.php?t=25

Page 2:
https://forum.civa.jp/viewtopic.php?start=20&t=25

These sources are player/author context. They do not override the distributed binary/source.

## 2019-07-03 — frou01 distribution post

The thread describes the supplied ecosystem around 五つの難題MOD+.

Relevant author claims:

- `EntityModeTOHOU MAIDs 2.61.zip` targets **Minecraft 1.7.10 + LMMX 0.1.3**.
- The maid mode uses knives and basic danmaku.
- Ordinary danmaku is fired rapidly toward enemy mobs.
- Knife-like weapons switch between melee and throwing depending on distance; the author says ballistic calculation exists but accuracy is low because of special movement.
- Spell cards can activate immediately after encounter while the maid continues other danmaku.
- Some item-angle detection used body orientation instead of head orientation.
- `Add_Battler_Sakuya.jar` adds a combat Sakuya that can spawn at night in Plains, uses two normal attacks plus two spell cards, and unlocks Sakuya's watch trade after the encounter is cleared.
- The X1 distribution is described as adding bug fixes plus changes to invulnerability removal, damage speed and rendering, and supporting multiplayer / Forge **10.13.4.1614**.
- Illusion Laser adds a right-click beam that follows the player's facing direction. The author explicitly describes the visibly choppy motion as specification/expected behavior.

## 2019-08-13 — redistribution/use boundary

frou01 says use should follow the original MOD's terms and asks users to state that the version used is the redistributed/modified version rather than the original.

This is not enough to derive a software license. The Tech Hub license state remains **UNKNOWN**.

## 2019-09-15 — maid mode ID collision report

A user reports that configuring the automatic value `-1` still appears to overwrite/conflict with Fencer.

The binary's automatic mode ID is based on `maidEntityModeList.size()+1`. This contemporary report is consistent with the conclusion that list size is not a proof of unused numeric ID.

## 2019-12-27 — original-version Forge limitation

frou01 says the original Five Difficult Problems build would not start after Forge build suffix 1448.

This is kept as historical context for the original upstream, not applied to the X1 binary, because the X1 author explicitly claims Forge 1614 support.

## 2020-03-17 / 2020-05-05 — hidden Illusion Laser dependency

A crash report shows:

```text
java.lang.NoClassDefFoundError: illusion_Laser/Item_LaserCore
at TOHOmaid.New_EntityMode_Toho.onUpdate(New_EntityMode_Toho.java:286)
```

A follow-up identifies missing Illusion Laser as the cause.

This directly matches the supplied TOHOU MAIDs bytecode, which references `illusion_Laser.Item_LaserCore` without declaring Illusion Laser in its `@Mod` dependency string.

## 2021-09-20 — Illusion Laser source loss

frou01 says the Illusion Laser source code was lost and maintenance had become difficult enough that decompilation was effectively required.

This makes exact binary preservation/hash + bytecode analysis particularly important for that addon.

## 2021-12-10 — dedicated-server Sakuya watch crash

A multiplayer server report shows:

```text
java.lang.NoSuchMethodError:
net.minecraft.entity.player.EntityPlayer.func_71052_bv()I
at thKaguyaMod.item.ItemSakuyaWatch.func_77654_b(ItemSakuyaWatch.java:92)
```

The supplied X1 binary calls that exact symbol.

This is evidence that old mapping/runtime symbol compatibility is part of the historical environment; a method that works in one 1.7.10 runtime can fail in another modded/dedicated environment.

## Evidence policy

- forum descriptions = AUTHOR_CLAIM or community report;
- supplied source/class behavior = DIRECT_OBSERVATION;
- a matching forum crash + matching binary reference strengthens a failure claim but still does not substitute for a reproduced runtime test.
