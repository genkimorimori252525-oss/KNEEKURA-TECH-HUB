# ServerCore — bounded source repair / behavior incident

Scope: historical `inactiveTick` chicken reproduction 2022 and 1.21.1 issue #118. *Tracks not silently merged with 1.20.1 Forge.*

## SC-2022-CHICKEN-INACTIVE

Source diff: [commit 09ffb1b7d1c958b4bb2723d4ef1f3ce09af59a4b](https://github.com/Wesley1808/ServerCore/commit/09ffb1b7d1c958b4bb2723d4ef1f3ce09af59a4b) vs parent `c153266fb982a8f197b93437f9e7a365959141b0`, source file `ChickenMixin`.
- Before: `inactiveTick()` only decremented `eggTime`.
- After: it decrements egg timer **and spawns egg**, plays sound, emits game event and reseeds timer on expiry.
- Root cause: INFERENCE from diff that reducing ticks without reproducing scheduled side effects can suppress chicken laying eggs; no isolated bug report or live reproduction read.
- Lesson: a tick-skipping optimization requires explicit preservation of critical slow entity state machine transitions (inventory/eggs/breeding/timekeeping). Don't assume a pig/zombie or custom invader has matching safe inactive method.
- Replay/verification: NOT_RUN.

## SC-118 — 1.21.1 iron farm exclusion reload

[Issue #118](https://github.com/Wesley1808/ServerCore/issues/118): report says `activation-range` reduced iron-farm golem spawn rate on Minecraft **1.21.1**. Maintainer advises exclusion changes can require `/sc reload` then unload/reload chunks or world; reporter reports chunk reload resolved effect.
- This establishes **reported** runtime config sensitivity and the usefulness of manual exclusion/reload, not an actual 1.20.1 Forge performance regression or an upstream patch.
- Actual code-level behavior at [1.20.1 ANCHOR source](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/config/tables/ActivationRangeConfig.java): config `ENABLED=false` by default.
- Exact cause beyond reporter/config hypothesis UNKNOWN; KNEEKURA tests NOT_RUN.

Captured issues and source through GitHub read, raw immutable CAS/index IDs and precise issue-text SHA unavailable; history adapter NOT_IMPORTED.
