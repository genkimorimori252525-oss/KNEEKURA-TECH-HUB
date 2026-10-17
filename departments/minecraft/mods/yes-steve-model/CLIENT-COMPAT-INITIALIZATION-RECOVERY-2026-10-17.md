# Client compatibility initialization and lazy parser join

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty declarations in ClientSetupEvent, CustomMolangParser and LazyValue, plus exact client subscriber annotations. Source/artifact global equivalence remains unestablished. No mapping promotion or target runtime.

## Verified Java order

`OOoo00oOOoooooooooOooOOo` has runtime-visible Mod.EventBusSubscriber metadata for CLIENT and MOD bus. Its FMLClientSetupEvent method has SubscribeEvent metadata. These annotations establish declared registration, not that a Forge session actually dispatched the event.

The handler returns early when YSM is unavailable. Otherwise it registers base animation state before submitting one Runnable via event.enqueueWork. The Runnable's bootstrap target is captured in evidence. Within that target, normal sequential order is:

Curios → FirstPerson → RealCamera → PlayerAnimator → BetterCombat → Iris → AR → Optifine → CosmeticArmor → ElytraSlot → TACZ → SWarfare → TLM → CarryOn → ParCool → SlashBlade → SWEM → Create → Sophisticated → SimpleHats → ImmersiveMelodies → IronsSpellBooks → SimplePlane → ImmersiveAircraft.

These are 24 adapter init calls, not 24 installed/successfully initialized mods. TLM call is offset36. Following adapter calls, optional compatibility warnings and an Epic Fight warning are checked, then the Java core-client wrapper is called at offset93. The Runnable has no finally ensuring the last call if an earlier operation throws.

The wrapper calls a public static native `()Object` declaration (access265) and casts the result to Component. Null returns normally; non-null produces RuntimeException with a bounded component string (256) in the failure message. The native declaration has no Code. Neither native initialization nor a game was executed, and its callbacks are not visible in this Java-only join.

## What this resolves, and what it does not

In this captured normal setup Runnable, optional adapter initialization precedes the final native client initialization call. This gives a concrete expected order for a native parser request made by that final initialization. It does not prove that no other earlier Java/native caller can rent a parser. Do not turn the [maid adapter's](MAID-QUERY-ADAPTER-RECOVERY-2026-10-17.md) conditional early-binding concern into a reproduced bug or an unconditional startup failure.

CustomMolangParser `O00o0ooOoo00o00o0OOOO0o0` uses a ConcurrentLinkedQueue for parser reuse. A missing pooled instance calls the factory. When shared EXTRA_BINDING is empty, the factory inserts lazy YSM, Ctrl, TLM then args bindings, catches ConcurrentException as RuntimeException, copies the map and installs a fresh per-parser fn binding. This map-empty test and sequence are not a transactional/thread-safe initialization proof; a partial failure could leave a nonempty partial map. That is a static conditional concern only. ReturnInstance resets before adding back; unsafe single-expression parsing returns the parser in finally. See the existing [parser pool dossier](PARSER-POOL-LIFETIME-RECOVERY-2026-10-17.md).

LazyValue `oO0OOOoO0oooO0OOo0ooOoOo` extends external Apache LazyInitializer; its own initialize body only invokes Supplier.get. This cohort does not implement or independently verify the external parent's caching/concurrency guarantees.

Command hints are separate: when COMMAND_HINT is empty, copy current EXTRA_BINDING, then add math and q. getAllBinding does not rent/create a parser first. If invoked before extras are populated, the resulting nonempty hints map is not refreshed by subsequent calls in this body. This affects the static completion-data path, not proof that actual parser namespace registration is missing. No command UI was exercised.

## Reuse

Preserve the availability gate, enqueue boundary, adapter-before-native order, and separate parser/hint lifetimes. The captured key/overlay handlers are supporting evidence, not a full UI review. The scoped auditor compares all selected methods/source anchors and actual class/member annotations, and rejects invented native Code. Independent semantic review remains NOT_RUN.
