# Inner gun-animation state and event-reset join

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Sixty-nine declarations across TacCompatInner, SWarfareCompatInner, TacEvent and CustomHumanoidEntity support, plus exact event annotations. No central promotion, independent semantic review or target/provider execution. This describes game animation selection, not projectile/weapon simulation.

## Shared animation selection contract

Both inner main-animation adapters prefer a present `tac:`+baseName clip, otherwise select baseName, retaining the caller's loop override. Their type-specific selection first asks ConditionTAC for the exact registered ID variant. Otherwise choose pistol, rpg, then rifle suffix. TACZ compares external gun type to lowercase(Locale.ENGLISH) GunTabType names; SWarfare uses item tags superbwarfare:animated/pistol and superbwarfare:animated/rpg. These are different type sources.

Their private playback helpers directly call coded-controller setAnimation and return CONTINUE. They do not use the format-aware hand helper, so do not apply its format>=19 loop-override omission here. Most fallback names are not locally checked for clip existence. The wrappers' null versus STOP precedence is in [entry adapters](GUN-ANIMATION-ADAPTERS-RECOVERY-2026-10-17.md).

## TACZ selection and reset producer

TacCompatInner `ooOoOo0o0OO0ooOO00Oo0ooO` hold/once paths require IGun and a CommonGunIndex, returning STOP when absent. Hold priority: non-swimming entity in SWIMMING pose chooses climb versus climbing using abs(event limb amount)>0.05; otherwise aiming progress>0 chooses aim; otherwise grounded sprint chooses run; otherwise hold. All use type/ID name resolution.

Once-animation reads synced shoot cooldown, takes max with client shoot cooldown when the living entity implements IClientPlayerGunOperator, then consumes the humanoid reload-request flag. If set, it first selects looping empty; flag is then cleared unconditionally on this normal path. It next selects reload if reload countdown>0; else melee if cooldown>0; else fire if shoot cooldown>0. Fire branches choose stationary crawling (abs limb amount<=0.05), then aiming>0, then holding. Selected once names request PLAY_ONCE. With no condition it returns CONTINUE, allowing an existing animation/recovery to proceed rather than forcing STOP.

TacEvent `o0O00Oo0ooOo000OoOooO0oo` has actual SubscribeEvent metadata on GunFireEvent, GunMeleeEvent and GunReloadEvent methods. Each first checks YSM availability, obtains shooter/entity, sets player capability's tacGunAnimationNeedReload=true when capability present, and calls the TLM marking adapter. TACZ init's registered event instance connects to these methods; event delivery itself is not tested. CustomHumanoidEntity stores a plain boolean request and clears it during geometry reset. Multiple event writes can coalesce into one boolean; it is not a counted shot queue or a guaranteed animation replay per event.

## SWarfare differences

SWarfareCompatInner `Ooo00oOooO0o00O0oOoOO00o` hold first checks local player's LungeMine animation path, explaining why the outer hold wrapper does not pre-require isGun. That path selects sprint, draw, attack, grounded run, then idle in order from external client fields, and uses the no-loop-override helper. Nonlocal or non-LungeMine returns null to continue normal hold eligibility; nongun then returns null.

Ordinary gun hold uses the same crawling-pose split, but aiming uses ClientEventHandler.zoomTime only for the local player (other entities get0), with threshold>0.3. Grounded sprint and hold follow. It is not the TACZ synced per-entity aim>0 contract.

Once-animation requires GunItem and local-player identity, otherwise STOP. It asks GunData.from before the local identity rejection. A non-null coded controller whose animation is finished gets indicateReload. Priority is reloading with reload.time()>40, melee client counter>5, then fire with strict0<fireRotTimer<1. Fire branch prefers stationary crawling, then zoomTime>0.3, then hold. No matching state returns CONTINUE. External timer units and mutation rules are not inferred here.

## Render support, not validated output

Captured offhand rendering uses locator matrices and 0.65 scale, with differing pistol rotations between providers. These bodies and global muzzle/shell flags are support snapshots, not a complete render correctness review or executed visual test. TACZ grenade detection is an unconditional false stub; existence of grenade-named helper animations does not prove a working grenade integration.

Preserve event flag coalescing, player-local versus synced sources, strict thresholds, adapter null/STOP distinctions and idle CONTINUE behavior. Scoped audit compares exact bytecode/source/annotations and negative mutations. It does not simulate optional mods or replay firing events, and is outside the earlier fixed nine-cohort batch.
