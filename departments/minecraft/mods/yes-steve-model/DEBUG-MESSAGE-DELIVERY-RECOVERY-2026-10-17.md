# Debug message delivery and client-task capture

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Five declarations of CustomDebugSource counterpart `OO00OOOOo0Ooo0oo0o0Oo0OO`, including the bootstrap-linked delivery lambda. No Minecraft task execution, chat delivery or independent review occurred.

The String overload calls String.format(message,args) first, creates a literal Component and delegates. It provides no local formatting-error catch, explicit Locale or lazy formatting gate. The Component overload checks current Minecraft.player for null, returns if absent, otherwise calls Minecraft.execute with a Runnable capturing the Component reference.

The lambda rereads Minecraft.player when it runs. It does not capture the originally checked player or session, and has no second null check. It creates a translated debug-prefix component, appends the captured message and calls sendSystemMessage on that then-current player. A session change between scheduling and execution can therefore change the receiver or invalidate the earlier null check; actual scheduling/interleaving and a runtime failure are not established. Minecraft.execute may run immediately depending on its external implementation/thread, so do not describe this as an unavoidable delayed race.

The captured Component is not defensively copied by this adapter. Debug display is not necessarily an immutable snapshot of a mutable supplied component. This adapter itself has no debug-enabled gate: callers such as MolangContext or parser/UI paths apply their own gates. The helper's existence does not mean every direct caller is gated, nor that a caller-side gate is rechecked in the Runnable.

This complements [instruction/debug expression evaluation](INSTRUCTION-DEBUG-EVALUATION-RECOVERY-2026-10-17.md): expression evaluation, formatting and client message delivery are distinct stages with different side effects and timing. Do not treat diagnostic evaluation as automatically side-effect-free or claim a chat message was displayed based solely on this Java call path.
