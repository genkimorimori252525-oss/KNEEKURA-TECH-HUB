# CullLeaves — selected issue history, no verified repair chain

Track: static `multiversion` source of 2026 (top-level 4.1.2, 1.20.1 Forge source branch included). Historical issues:
- [#69](https://github.com/TeamMidnightDust/CullLeaves/issues/69) (2025-12, after requested 4.1.1): reporter noticed lower FPS with bundled SmartLeaves pack vs leaving it disabled; suspected pack changes leaf models. **No original benchmark captures or actual fix diff** reviewed. Closing Issue 2026-03 is not proof pack setting changed.
- [#53](https://github.com/TeamMidnightDust/CullLeaves/issues/53): **1.19.2 Forge**, CullLeaves 3.0.0 / Embeddium 0.3.18 jungle crash report; issue OPEN, not 4.1.1 ANCHOR.
- Code-backed lifecycle: `CullLeavesClient.ReloadListener` restores force flags and reloads resourcepack-specific culling options; `CullLeavesConfig` requests renderer update on changes. This is an *existing correctness guard*, **not confirmed repair for #69**.

History scope selected symptoms/report vs current code only, **no issue-linked before/after diff**, no verified failure reproduction, no binary verification, and no history adapter import. Reusable lesson: runtime-visible FPS comparisons must hold resource pack geometry/configuration fixed; optimizing faces may be outweighed by geometry change due packs.
