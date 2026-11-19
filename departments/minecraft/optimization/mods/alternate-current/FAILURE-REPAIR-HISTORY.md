# Alternate Current — scoped upstream failure/repair, Minecraft tracks separated

## AC-27 — dropped redstone duplicated when support broken, repair in 1.7.0

- **Issue** [#27](https://github.com/SpaceWalkerRS/alternate-current/issues/27): reported on 2023-06-24, **Minecraft 1.19.2 Forge 43.2.14**, Alternate Current **1.6.0**; a comment also reports Fabric MC 1.20.1 v1.6.0. Breaking support sometimes yielded two dust items. User video exists but **not timestamp-reviewed**.
- **Cause/repair** [commit 815fac14e103ce5defcf98578acdd55da0b0cd63](https://github.com/SpaceWalkerRS/alternate-current/commit/815fac14e103ce5defcf98578acdd55da0b0cd63) 2023-06-25; parent `a9edb5c9b978bfc4b66835e6c80dfd62228af01c`. Direct diff changes onPlace/onRemove injection offset and neighborChanged call to cancel vanilla handler *only when* `WireHandler.onWireUpdated(pos)` sees a valid wire. Before callback did not cancel, enabling duplicate vanilla/mixin paths.
- **Validation:** developer [confirmed “fixed in v1.7.0”](https://github.com/SpaceWalkerRS/alternate-current/issues/27#issuecomment-1606258150). ANCHOR Forge 1.20.1 1.7.0 [`RedStoneWireBlockMixin`](https://github.com/SpaceWalkerRS/alternate-current/blob/ab87061f1d04c44bfd42ba219ca567f8709c2acc/src/main/java/alternate/current/mixin/RedStoneWireBlockMixin.java) contains fix. **No KNEEKURA in-game validation**, no official JAR class parity.
- **Lesson:** intercept order + cancel policy and cleanup effects must be treated atomically when overwriting world update flow. Guard by present block identity, avoid reentrant duplicate drop.

## AC-13 — vanilla update order differs, explicit by design

[Issue #13](https://github.com/SpaceWalkerRS/alternate-current/issues/13) developer states that vanilla's location-dependent redstone wire update order **intentionally differs** from AC. Consequently some quasi-connectivity/piston circuits that rely on vanilla order may fail in AC while wire power stabilizes correctly. This is **documented semantic deviation**, not an upstream bug/fix chain. Later [#55](https://github.com/SpaceWalkerRS/alternate-current/issues/55) reports an affected door in **2026**, with newer 1.8+/1.9 update-order config, not proof the same circuit breaks in 1.7.0.

## Evidence and bounds

History window: 2022–2026 selected #13/#27/#55 and specific fix diff. Findings: DIRECT_OBSERVATION code delta, AUTHOR_CLAIM issue behavior, INFERENCE root and no runtime PASS. Full upstream issue/PR history, original video transcript, exact JAR SHA, adapter CAS record **NOT_ACQUIRED**.
