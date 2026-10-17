# Paper-doll editing: draft values, rendering and config writes

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Nineteen declarations across ExtraPlayerConfigScreen comparison owner `oO0o0o0OOOo0OoOOo0OoO0o0`, its $1 checkbox class, and AndroidCompat `OOooOo000o0OoooOOO0OoO0o`. AndroidCompat's additional pause-menu builders are supporting captured bodies, not a claim of complete semantic review. No screen/input/config write or target class was executed.

## Constructor values versus current editing state

The constructor reads persisted-config accessors into local posX/posY ints and scale/yawOffset floats. It starts both drag flags false, controlSize5 and yaw-change button1. A true AndroidCompat predicate changes controlSize to16 and yaw button0. The exact predicate delegates to YesSteveModel.isMobilePlatform; the platform result/native-library detection is not inferred from the user's device or tested here.

Initialization adds a mobile reset button when that predicate is true and creates a checkbox from the current disable config value. The checkbox's onPress first calls its superclass, then immediately calls the disable BooleanValue setter with the selected value. Thus disabling is not deferred until closing like the four numeric draft fields.

## Drag behavior does not enforce declared config ranges locally

Mouse-click hit tests use strict inequalities around the position and scale handles. Their two left-button branches independently set the position/scale flags; they are not an exclusive else-if. The method returns its superclass mouseClicked result even after setting a flag. Mouse release clears both flags before delegating, without a local button-specific condition.

Dragging prioritizes the scale flag, then position flag, then the configured yaw button:

- Scale becomes float(min(mouseX-posX,(mouseY-posY)/2)). No local clamp to the declared8..360 config range occurs in this body.
- Position becomes int(mouseX), int(mouseY), with Java narrowing and no local nonnegative clamp.
- Yaw adds float(deltaX*2), with no angle wrapping or local bound check.

Unmatched dragging returns false. These are exact calculations and priorities, not proof that every coordinate/flag combination is reachable through a live GUI. They distinguish transient preview values from Forge's separate configuration validation contract.

Alt plus a case-insensitive 'r' invokes reset, then the character method still returns its superclass result. The mobile button invokes the same reset. Reset changes only X10,Y10,scale40,yaw5; it does not clear the two drag flags or change the disable config. No cancel/revert transaction is implied by this reset method.

## Rendering uses drafts before numeric config writes

The screen draws its controls and, when a local player exists and disable=false, calls the existing RenderUtil paper-doll helper with its current draft fields, z=-500 and Minecraft.getFrameTime. It does not wait for onClose, reread numeric config on each frame, or use the callback's supplied frameDeltaTime for that helper. The superclass screen render remains afterward on the ordinary path.

The [ordinary overlay entry](RENDER-BRIDGE-PAPERDOLL-ENTRY-RECOVERY-2026-10-17.md) skips drawing while this config-screen class is current. This explains the two entry paths: normal overlay reads config; editing screen renders drafts. Both hand the real local player to the paper-doll helper. Neither is the separate FakePlayer equipment-suppression overload discussed in the earlier preview dossier.

Consequently the declared config range alone does not bound the floats this screen passes to rendering during editing. This is a Java data-flow statement, not a measured inverted/oversized model or a claim about setter rejection. No invalid input was generated.

## Close ordering and persistence limit

onClose calls the X, Y, scale and yaw config setters in that order, widening the last two floats back to double. Only afterward does it invoke the superclass onClose. It has no local validation, rollback, catch or finally. A hypothetical setter failure could skip later writes and the superclass call; actual Forge setter behavior and a user-visible failure were not tested.

There is no explicit file-save call in this body. Calling setters does not independently establish durable disk persistence or its timing. The disable checkbox's earlier write and numeric close-time writes are separate operations, not an all-or-nothing save.

## Reuse

Keep draft storage, live preview, checkbox mutation, reset scope, close-time writes and external validation/persistence separate. The positive Double.MIN_VALUE yaw lower argument and float conversions remain as recorded in the entry dossier; no configuration or source bug was patched. Central669 map remains unchanged and independent semantic review is NOT_RUN.
