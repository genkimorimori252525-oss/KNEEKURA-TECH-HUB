# Client model containers: shared data and eager factory assembly

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.42 complete declarations/five owners,237 integrity checks/ten negative controls. These owners previously appeared only in broad role catalogs; those names did not establish complete method semantics. Central669 mappings unchanged; independent semantic review NOT_RUN. No model, native decoder, texture, controller factory or authorization routine was executed.

## ClientModel is a reference container

ClientModel `oOo0oO0OOo0ooOoo0oOo0oOo` directly retains PlayerModel, projectile/vehicle maps, CommonAsset, ModelInfo, ClientModelInfo and the registered-texture list. Getters return those same objects. The constructor performs no defensive collection copy, null validation, registration or resource cleanup. This class declares no close method or AutoCloseable contract. The registeredTextureIds name does not itself prove the listed textures are registered, loaded or uploaded.

getDisplayName calls info().metadata(). If metadata is nonnull it asks LanguageManager for `metadata.name` using metadata.name as fallback. The caller-provided defaultName is used only when metadata is null; it is not an additional blank/null/failed-translation fallback on the metadata branch. There is no separate null check on info itself. The existing [language dossier](MODEL-LANGUAGE-FALLBACK-RECOVERY-2026-10-17.md) establishes locale-map selection, not guaranteed translation availability.

## PlayerModel assembles three factories during construction

PlayerModel `Oo0o0o0o0OOo0000ooo00o00` first assigns geometry, main/arm animation maps, main/arm condition managers, controller map, texture map and default texture name/object. It then calls PlayerControllerCollection.build at65, FPArmControllerCollection.build at75 and TlmClientCompat.buildControllerFactory at85, assigning each returned object in that order.

Those build calls receive this and the supplied CommonAsset during construction. The factories are assembled eagerly here; their later Consumer.accept applications are separate operations. There is no local try/finally rollback if a later builder throws. This does not demonstrate unsafe publication, a partially usable escaped object or a real exception. The nullable/optional maid factory remains an Object-typed field whose presence depends on the compatibility helper; no successful optional-mod initialization follows from the field alone.

The default texture name and default texture object are separate retained arguments. This constructor does not recompute one from the other or verify map membership. The actual [client-model builder](CLIENT-MODEL-COMPOSITION-RECOVERY-2026-10-17.md) chooses those inputs; callers reusing this constructor must preserve that contract themselves. Getter access does not rebuild a factory after an externally mutable map changes.

## Projectile and vehicle factories follow the same boundary, not identical behavior

ProjectileModel `OoOoOOoO0oO0o00Oo00o0Oo0` and VehicleModel `ooO0Oooo00ooo0oo00OOoooO` retain their geometry, animation/controller maps and texture, then call their respective controller collection build(this,assets) at29. Their getters return retained references/factory. The wrapper shape is similar, but their [controller collections](VEHICLE-PROJECTILE-CONTROLLERS-RECOVERY-2026-10-17.md) have distinct behavior; a shared container pattern does not make the animation logic interchangeable.

The containers do not add player-default animation fallback. That decision belongs to the previously reviewed builder, which fills missing player main/arm animations but does not apply the same fallback to projectile/vehicle maps. Keep container ownership, builder fallback and factory application separate.

## ClientModelInfo is not a lifecycle receipt

ClientModelInfo `OO0oO0000O0O00o0O0oo0O0O` retains its name and both supplied texture maps, and a mutable boolean metadata flag. Its getters/setter are direct field operations. No policy or verification semantics are inferred from the flag name here, and no flag was changed.

The author-avatar getter exposes the original map. guiForeground and guiBackground each perform a direct lookup of `gui_foreground` or `gui_background` in the retained GUI image map and return the result. Missing keys can yield null; there is no fallback image, map copy, readiness wait or load operation inside those getters. A final map reference does not freeze map contents.

## Reuse and verification

The fixed seven-cohort checkpoint joins these containers to the existing builder, player/arm/vehicle-projectile/maid factory and language dossiers. It checks evidence integrity and repeated snapshots, not live factory success or GPU output. For reuse, define which layer owns mutable assets, when factories are assembled/applied and which manager disposes textures. Do not infer deep immutability, registration completion or lifecycle ownership solely from these holder types.
