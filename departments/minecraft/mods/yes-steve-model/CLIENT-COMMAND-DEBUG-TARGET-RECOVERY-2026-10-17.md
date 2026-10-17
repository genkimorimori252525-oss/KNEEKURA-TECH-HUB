# Client Molang commands, watch expressions and debug target ownership

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Five owners,66 declarations including support lambdas/constructors. No commands/expressions/game were executed. These are comparison roles, not proven original names or new central mappings.

| Comparison role | Exact owner suffix |
|---|---|
| ClientRootCommand | oooOO0O000o0OOoO0O00oOOo |
| client MolangCommand | ooOo0Ooo0ooo0O0o0o0ooOO0 |
| SimpleWatchCommand | oooO0O0ooOOOooo00o00OO00 |
| DebugCommand | oooo000OoOOoOooOoo000ooO |
| DebugAnimationScreen | O0oo0oOOo0000OOOoOooO000 |

## Entry and success have different meanings

The root literal is ysmclient. Its registration adds molang, watch and debug subtrees and a predicate that calls CommandUtil.isLocalPlayer on the command source entity. The existing [command producer dossier](MOLANG-COMMAND-PRODUCER-RECOVERY-2026-10-17.md) captures that physical-client/UUID predicate; it is not the server molang command's permission-level alternative. Root registration remains subject to the already captured YSM availability and physical-side registration path.

Molang execute and watch edits first require Minecraft and its current player to be nonnull. They return integer1 even when that readiness check fails. ParseException is caught only around parseSingleExpressionUnsafe, reported through the command source, and also returns1. An absent target/capability can likewise end with1. That command return therefore cannot be reused as an expression-success receipt. Other exceptions and later callback failures are not covered by those parse catches.

Execute parses first, obtains DebugAnimationScreen.getTarget, and falls back to the local player's animatable capability only when the debug target is null. It then calls executeMolangExp(value,true,false,resultConsumer): emission allowed, post-task queue flag, not immediate evaluation. Unlike the separate server command/roulette producer paths, this body does not construct a network packet. The result callback reads Minecraft's current local player when invoked and sends the translated result message directly; it does not capture the earlier player, check it again or explicitly reschedule through Minecraft.execute. Actual callback thread/lifetime safety remains unproven, not a reproduced defect.

## Watch registration is global debug-state editing

The explicit molang watch add pre/post forms parse before submitting a Runnable to Minecraft.execute. At runnable execution they obtain the current local player's capability. The resulting lambda does not use that capability as the observed target: it edits the static DebugAnimationScreen DEBUG_INFO. Remove and clear follow the same presence-gated static-object route. They do not automatically enable a target.

Simple watch var adds the expression with POST_ANIMATION and uses the expression text as its name. It then enables the local player only if the debug screen currently has no active target. An already active nonlocal target is retained. Thus "local capability required to edit" does not mean "always observes local player".

Simple watch state inserts a controller name and optionally enables the local player directly in its command body. Simple watch clear submits the expression clear to Minecraft.execute but calls clearDebugController on the ordinary command path before returning. These are two mutation paths, not one atomic clear transaction. No thread or scheduling behavior of the external executor is assumed.

The earlier [debug evaluation dossier](INSTRUCTION-DEBUG-EVALUATION-RECOVERY-2026-10-17.md) establishes that DebugInfo appends without name uniqueness, remove deletes matching names, and phase evaluation invokes evalUnsafe with possible side effects. Command watch syntax is not a read-only guarantee; a displayed result comes from prior evaluation, not necessarily the display frame.

## Target attachment and lazy capability interaction

DebugAnimationScreen holds one static DebugInfo, one static controller-name list and a weak target reference. enable(CustomEntity) calls disable, installs a new weak reference and gives the SAME DebugInfo to the new target. Disable detaches the previous target's debugInfo and clears the weak reference, but does not clear watch expressions or the controller-name list. Switching target therefore retains that shared watch configuration; it does not create per-entity debug state.

getTarget returns the weak referent only when nonnull and active; otherwise it calls disable. isEnabled calls getTarget. These lookup methods can therefore detach state and request a local status message; they are not purely passive field reads.

enableForLocalPlayer returns true whenever a local player exists, even if its capability Optional was empty and enable was never called. Only the missing-player branch disables and returns false. Conversely enable(Entity) maps a present capability to true and disables/returns false when absent.

The Entity overload chooses player, maid, projectile, otherwise vehicle capability in that order. It queries their exposed rendering capabilities directly; it does NOT traverse ClientLazyCapability or call initialize. The new [projectile](PROJECTILE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md)/[vehicle](VEHICLE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) provider dossiers establish that these rendering capability queries are empty before initialization. Consequently selecting an entity for debugging is not itself a lazy-renderer activation path. Do not infer successful debug attachment from entity existence alone.

DebugCommand resolves the command-selected entity's numeric ID against the current client level and passes that result to enable(Entity). Its local body has no level-null or lookup-null check. Normal command context may supply the prerequisites; no invalid command or payload was executed to claim a runtime failure.

## Suggestions and displayed results

Both suggestion providers require a SharedSuggestionProvider source and physical CLIENT, then choose the debug target or local fallback. Variable suggestions combine scoped v names, names from a LocalRoamingStruct only when getProperty is nonnull, ContextBinding names, and fn names from the current model container's user-function keys. They do not prove those functions will parse/evaluate successfully, and this body does not establish the native producer of user-function definitions. The model-container dereference has no separate readiness guard here.

Controller suggestions collect current controller names into a Set. Debug controller selection itself prepends names without a local existence/uniqueness test; display resolves each name against the current target, emitting "(N/A)" for missing controllers. Display enumerates retained DebugInfo results rather than reevaluating expressions. Font/layout calls are captured for integrity but are not a visual-output acceptance test.

The existing [client initialization snapshot](CLIENT-COMPAT-INITIALIZATION-EVIDENCE-2026-10-17.json) also contains the RegisterGuiOverlaysEvent body: after the availability guard, it gets VanillaGuiOverlay.DEBUG_TEXT.id, the literal ysm_debug_info and this overlay factory, then calls registerAbove at19. This grounds the declared registration connection without claiming a live event subscription or visible frame.

## Reuse boundary

Separate command integer returns, parse acceptance, queue submission, observation target, result formatting, callback delivery and visible overlay. Preserve shared watch configuration across target changes if matching this behavior. No independent semantic review, whole-source equivalence or target runtime is claimed;669 central entries remain byte-identical.

- [Debug target lifecycle and diagnostic scope](DEBUG-TARGET-LIFECYCLE-RECOVERY-2026-10-17.md): exact target-field/caller inventory, non-initializing key toggle, shared watches versus globally enabled diagnostic output, and bounded logout cleanup evidence. The separate fixed6 [checkpoint](DEBUG-TARGET-LIFECYCLE-CHECKPOINT-2026-10-17.json) compares20 repeated snapshots without conflict.

- [Player capability provider lifetime](PLAYER-CAPABILITY-PROVIDER-LIFETIME-RECOVERY-2026-10-17.md): player query suppliers can construct backing state, while projectile/vehicle providers are empty until explicit initialization. Attachment branches, NBT factories and clone transfer are distinct lifecycle steps. The fixed6 [checkpoint](PLAYER-PROVIDER-CHECKPOINT-2026-10-17.json) checks the connected scopes without claiming Forge/runtime lifecycle verification.
