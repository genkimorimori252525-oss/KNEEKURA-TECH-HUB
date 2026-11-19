# ImmediatelyFast — bounded draw-order repair history

Scope: 2023–2024 issues #129/#181/#287/#288 and two actual repair diffs; sources in 1.20 branch with newer 1.5.6-SNAPSHOT development. No complete upstream history, no 1.5.5 JAR release-code parity.

## IF-181 — modular glint ordering (1.20.1 Fabric reported)

[Issue #181](https://github.com/RaphiMC/ImmediatelyFast/issues/181): enchantment glint appears only on first module for Truly Modular. [Commit `3f7d86fbdafb...`](https://github.com/RaphiMC/ImmediatelyFast/commit/3f7d86fbdafb64fbb6e087e53bd3444bed4a717b), parent `6cc19fa68c9c01243108ce80922e2ba1e3d7d985`: adds `debug_only_use_last_usage_for_batch_ordering` optional option, for selected render layers re-inserts active layer into linked order on further use. Fix author message links #181. It is **off by default**, so no universal claim all batch ordering changed or every custom glint fixed in all config profiles.

## IF-287-288 — custom font render layers overlap incorrectly

[Issue #287](https://github.com/RaphiMC/ImmediatelyFast/issues/287): 2024 user reports custom UI item/container title order differs from vanilla, hiding bottom text. [Commit `f9fbf5d83d6...`](https://github.com/RaphiMC/ImmediatelyFast/commit/f9fbf5d83d6bd2bd73f403f833c419fff26a7368), parent `ba0826894014b4369953bcc48573071dc3c71a92`, adds order distinction to `BatchableBufferSource.getLayerOrder` for Minecraft text texture namespace vs custom-font layers and removes older glyph-matrix workaround. Compared actual diff. Source `1.20` head retains related rules; no KNEEKURA runtime retest.

## IF-129 — unresolved cross-mod UI overlay

[Issue #129](https://github.com/RaphiMC/ImmediatelyFast/issues/129), Minecraft 1.20.1 user reports XP bar overlay ModernUI conflict; turns off `hud_batching` as workaround. Issue OPEN, no related code diff verified; should not claim 1.5.5 fixed it.

**Lesson:** batching optimization and ordering correctness are inseparable; exact render layer order, blend/depth and draw barriers should remain stable. Separate author fix claim from runtime acceptance. CAS artifact/history import absent.
