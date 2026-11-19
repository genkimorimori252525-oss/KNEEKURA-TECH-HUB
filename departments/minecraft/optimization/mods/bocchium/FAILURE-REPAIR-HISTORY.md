# Bocchium — bounded no-supported-case history

Scope: `MCTeamPotato/Bocchium` branch `1201` pinned `57a2e920273422253dde64f2c3d907bca8679afe`; reviewed all 3 Java source bodies, Mixin registration, config and build dependencies. Queried public GitHub Issues for `cull`: **no relevant returned issues**. No proven bug/fix pair in this exact limited scope. This is a scoped negative outcome **not** evidence that Bocchium has no bugs.

Source facts that merit future correctness verification rather than being registered as historical failures:
- `shouldCull(Direction,int)` checks face direction and world Y boundary but no BlockState type.
- `BlockOcclusionCacheMixin` is the **only registered client Mixin**, even though source has `SodiumGameOptionPagesMixin`.
- Build depends on Embeddium 1.20.1 but `mods.toml` lacks a dedicated loader dependency on it.

No dated issue/fix commit established. Full Git commit history not reviewed. Exact release binary not obtained, runtime/benchmarks NOT_RUN, no formal history-adapter import.
