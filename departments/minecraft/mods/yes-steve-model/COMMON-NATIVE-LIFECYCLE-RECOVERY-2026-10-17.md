# Common setup and native lifetime boundary

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source-comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. CommonEvent comparison owner `OoOo0ooo0o00O0oooO0oooOo`: 8 declarations, including 2 native declarations without Code. Audit: 52 integrity checks and 9 rejecting corruption controls. No target class, native initialization, shutdown hook or game was executed.

## Java ordering

The owner has EventBusSubscriber(bus=MOD); common setup and capability registration methods have SubscribeEvent metadata. Setup checks YSM availability. The unavailable branch enqueues a task obtaining ModLoader and adding YSM's unavailable warning, discards the returned future and returns. The available branch enqueues a task and also discards the future.

That available task calls NetworkHandler initialization at offset 0, TlmCommonCompat registration at 3, then the common native-init wrapper at 6. It has no local rollback/finally or catches. Thus native initialization is not shown to precede all Java registration, and this method does not establish atomic startup. External Forge scheduling/exception handling remains untested.

The wrapper calls native `o0OOooo0o0OO00OoOOOo0o0O()Object` at offset 0, casts the result to Component, and treats null as its success path. A nonnull Component produces a RuntimeException with `YSM Initialization Failed: ` plus getString(256). A different result type would fail at the cast; actual native return invariants are unknown.

Only after the null-result branch does the wrapper construct a Thread whose bootstrap-linked Runnable is native `O00OOOooOoooOoo0o0o0oO0O()V`, then call Runtime.addShutdownHook at 48. This registers a hook; it is not a Thread.start or synchronous shutdown call. No Java once-only latch, hook removal, initialization rollback or ordering against other hooks occurs in this wrapper. Actual invocation count and native resource disposal are unresolved.

Capability registration separately rechecks availability. It registers five common data capabilities (model info, projectile info, vehicle info, owned models, starred models), then three animation capabilities only for physical Dist.CLIENT (player, projectile, vehicle). This is class registration, not per-entity attachment, provider initialization or model readiness; see PLAYER-CAPABILITY-PROVIDER-LIFETIME and ENTITY-CAPABILITY-TRANSPORT.

## Bounded native declaration inventory

NATIVE-DECLARATION-INVENTORY scans all 955 class files of the fixed JAR and finds 17 ACC_NATIVE declarations in 8 owners. Every declaration now has an exact member snapshot in one of eight pinned evidence cohorts. The inventory tool rechecks class hashes, access/signatures and evidence anchors; six opt-in tests exercise matching and rejected corruption. The separate native boundary checkpoint re-runs those cohort auditors.

This inventory is complete only for ACC_NATIVE declarations in this JAR. It does not enumerate native exports, Java callbacks, dynamic binding targets, third-party native methods, protected implementation instructions or all JNI entry points. Seventeen anchored declarations is NOT seventeen decoded native functions or full deobfuscation. The implementations remain unresolved; no native binary was executed, decrypted or patched.

Run tools/native_boundary_inventory_ysm_265.py with --jar and --out; add --check to compare the stored inventory without rewriting. These operations parse bytes only. Independent semantic review NOT_RUN, central mapping unchanged.
