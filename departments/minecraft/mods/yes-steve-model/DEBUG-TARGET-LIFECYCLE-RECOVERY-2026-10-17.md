# Debug target lifecycle, input toggle and diagnostic scope

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. This joins existing exact bodies using a new seven-target declaration-validated scan of955 classes. The inventory contains28 direct field/method sites across21 caller methods and one matching bootstrap record. It is not whole-program dispatch, reflection/native closure or runtime verification.

## Target field writes and observed cleanup

The exact weak-target field has three PUTSTATIC sites, all inside the debug-screen owner: class initialization writes null, enable(CustomEntity) stores the new WeakReference, and disable writes null. No additional direct writer to that exact field was found in the fixed artifact. Foreign code, transformers or reflective writes remain outside this scan.

The direct disable callers are the screen's own missing-player path, target switch, invalid/collected target lookup and empty-capability fallback, plus the keyboard-toggle body. The matching bootstrap reference to enable is the local-player capability consumer; one bootstrap record is not a count of runtime activations.

The previously captured ClientLoggedEvent logout body resets its logged-in flag and requests ClientModelManager.syncAbort under its own availability gate. It contains no debug-target detach or watch clear. The exact disable caller inventory also has no logout listener. This is bounded evidence about those Java routes, not a guarantee of cross-session object survival or absence of every indirect/external cleanup.

## Keyboard toggle does not force initialization

The newly located caller owner `o0000oo0oOoOo000oOooO0Oo` matches the DebugAnimationKey comparison role through its exact InputEvent.Key body and calls. It requires YSM availability, InputCheckUtil's in-game predicate, action1 and key match. It then checks isEnabled: false calls the screen's hit-target-or-local enable helper and discards the boolean; true calls disable. This is a captured method body, not proof of successful event registration or actual key delivery.

The screen's enable helper uses an entity hit when present and returns that attempt's result; it does not fall back to the local player after an entity-hit capability lookup failed. Only the no-entity-hit branch calls enableForLocalPlayer. Together with the [client command/provider dossier](CLIENT-COMMAND-DEBUG-TARGET-RECOVERY-2026-10-17.md), debugging a not-yet-initialized projectile/vehicle may take the empty-capability path; this toggle does not initialize it itself. No game input was generated.

## Diagnostic enablement is broader than the selected target

The exact isEnabled callers include the MolangParser safe parse-error handler and CustomEntity.getDebugSource, in addition to UI/command callers. CustomEntity.getDebugSource tests the global debug-screen state and returns CustomDebugSource when enabled; it does not compare this entity with the selected debug target. The parser's error handler likewise tests that global state to choose error-level reporting plus debug output versus debug-level logging. It does not establish that the failing expression belongs to the selected target.

This is different from attaching the shared DebugInfo to one target for pre/post watch evaluation. Selected-target observations and globally enabled diagnostic messages are separate scopes. The [debug message adapter](DEBUG-MESSAGE-DELIVERY-RECOVERY-2026-10-17.md) has its own current-player checks/capture timing; a caller's enabled test is not repeated there as a target identity filter.

isEnabled calls getTarget, which may disable an inactive/collected target. Therefore the diagnostic gate itself can follow the detach/status-message path. This is a conditional call-chain fact, not proof of a race or recursive failure. Parser catch boundaries, logger failure handling and asynchronous execution retain the limitations in the existing parser and frame dossiers.

## Reuse consequence

Do not equate disabling an overlay with clearing watches, choosing one watch target with filtering every diagnostic, a queried capability with forced initialization, or a logging-out flag with a completed debug teardown. The [client command dossier](CLIENT-COMMAND-DEBUG-TARGET-RECOVERY-2026-10-17.md) describes shared expressions and controller-name retention. No behavior was patched; central map669 and all historical review labels remain unchanged.
