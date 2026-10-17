# Extra-animation keys: registration, routing and differing guards

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Nine declarations/two owners,61 integrity checks/eight negative controls. Exact annotations include these owners and the supporting ClientSetupEvent; its method bodies/source are reused from CLIENT-COMPAT-INITIALIZATION. No input injection, UI opening, packet transmission or game execution.

## Registration has an explicit caller

ExtraAnimationKey `o0o000O000oOOO0O0o0OOo0o` registers eight keys, indices0..7 inclusive, with IN_GAME/NONE/KEYSYM and unknown-key default. It registers each with the supplied event and appends it to a public static List without clearing/deduplicating. These are eight registrations per normal invocation, not evidence of an actual duplicate event run.

ClientSetupEvent's captured MOD-bus subscriber method explicitly calls this registration helper after its availability gate, alongside the ordinary roulette/lock mappings. Thus do not infer that extra keys cannot register merely from the helper class's own default-bus annotation. The default roulette key is Z; lock is Alt+L in the static key definitions, subject to external user remapping.

## Shared in-game check is stronger than player-not-null

Both handlers require availability and InputCheckUtil.isInGame. That already-captured helper rejects a nonnull overlay or screen, requires mouse grabbed and window active. keyIsMatch combines key/scancode matching with equality to the active modifier. [Movement/lock handling](CLIENT-VIEW-MOVEMENT-RECOVERY-2026-10-17.md) uses different checks and must not be conflated with these two handlers.

## Indexed shortcuts

On press, ExtraAnimationKey scans the key List in order and requires a nonnull local player with no movement input. At the first match it looks up the capability and then returns, even if capability absence or an out-of-range animation index resulted in no action. Later keys sharing the same physical binding are not tried through that invocation.

The callback obtains the model, derives the index with the current List.indexOf(key), and reads the model's ordered extra-animation keys. It locally checks size>index but adds no model-null or initialized/enabled check. The three routes are:
- exact #return: construct the stop message and call sendToServer
- #name whose suffix exists in the classify map: add root classification, construct a classified roulette screen and setScreen
- otherwise: construct SetPlayAnimation(index,emptyString) and call sendToServer

An unknown #category follows the final index-message route; it is not locally rejected as an unknown category. No remote-channel or server-switch-config test appears in this shortcut callback; any further protection belongs to NetworkHandler/server consumers. Do not infer packet delivery or server acceptance from these calls. The path does not itself locally play/stop the animation before sending, unlike movement-triggered stop. The movement lock does not remove this handler's own !isMoveKey requirement.

## Main roulette key

AnimationRouletteKey `o0OOOOOO0O0oO0o0Oo00Oooo` requires press/match and either no remote channel or CAN_SWITCH_MODEL=true. A pointed-to-maid adapter route takes precedence; otherwise a nonnull local player's capability is used. The callback requires a nonnull model with a nonempty extra-animation order map, then opens a roulette screen when current screen is null or closes one when current screen is already that type.

However the handler's earlier in-game gate rejects any existing screen. Under a stable screen state, the ordinary entry reaches the opening branch, not a general toggle-close of an already open GUI. Other screen-owned key handlers or state changes need their own evidence; a closing branch's presence alone is not proof that this handler receives and closes an open roulette screen.

## Integration consequence

Preserve the different rules for indexed shortcuts, wheel opening, movement-driven local cancellation and lock toggling. Registration counts, initialized capability state, model availability, network helper calls, classification routing and actual playback are separate observations. This completes another Java input seam without modifying upstream policy or inventing an offline/network fallback.
