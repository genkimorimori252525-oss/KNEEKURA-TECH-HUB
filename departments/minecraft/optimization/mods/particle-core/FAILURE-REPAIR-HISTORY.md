# Particle Core — issue-led bounded investigation

Track: selected Forge 1.20.1 branch and **comparative** Fabric 1.21.11 issues. The selected source fixes/general safeguards are observed, but not linked to exact issue repair in an immutable commit diff.

## PC-39 — Forge 1.20.1 visual corruption report

[Issue #39](https://github.com/fzzyhmstrs/pc/issues/39) (2026-01-21) describes altered particle size / visual artifacts after upgrading to Particle Core 0.3.0, on Forge Minecraft 1.20.1. Issue closed, **no source diff trace or KNEEKURA reproduction** established. Avoid inferring closed == fixed or 0.3.3 free of it.

## PC-47 — Fabric newer random-source safety

[Issue #47](https://github.com/fzzyhmstrs/pc/issues/47) (2026-01-30) contains a **Fabric 1.21.11** stack indicating asynchronous particle update collided with non-thread-safe `LegacyRandomSource`. The selected 1.20.1 source's `ParticleManagerAsyncMixin` recognizes exception patterns, marks classes unsafe and retries those on calling thread — mechanism static-confirmed, but **timeline/patch linked to #47 not audited**. Track must remain COMPARATIVE.

## PC-65 — palette read races

[Issue #65](https://github.com/fzzyhmstrs/pc/issues/65) (2026-09-16, open) asserts unsafe off-thread palette access may cause `MissingPaletteEntryException`. Exact mod version/environment and crash root not fully audited. Cannot generalize to this user's binary.

Performance/reproduction/fix evidence NOT_RUN. No fabricated repair claim, no history adapter import without raw captured bytes/index IDs.
