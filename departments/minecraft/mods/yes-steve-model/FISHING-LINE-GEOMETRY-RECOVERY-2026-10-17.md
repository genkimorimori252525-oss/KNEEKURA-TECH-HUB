# Fishing-line geometry and provider tail

PRIMARY_STATIC_REVIEW_ONLY. This extends semantic reading of the already captured fishing helper in [dispatcher evidence](DISPATCHER-RENDER-REPLACEMENT-EVIDENCE-2026-10-17.json), owner `oO0Ooooooo0O0OOOO00OoOo0`. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; pinned source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No extra captured-method count, mapping promotion, independent review, target or graphics execution. The existing dispatcher auditor verifies the four helper bodies described here; that receipt is structural integrity, not a separate numeric/visual test.

## Rod endpoint selects a camera convention, not a YSM locator

Hand direction starts+1 for main arm RIGHT, else-1. It flips when the main-hand stack cannot perform Forge FISHING_ROD_CAST; there is no separate offhand-item validation. Swing is sin(sqrt(attackAnimation)*pi). Body yaw uses ordinary lerp then radians, not the wrapped living-yaw adapter used for vehicle orientation.

First-person endpoint logic requires nonnull dispatcher options, first-person camera type and owner identity equal to the current client player. It gets near-plane point(handDirection*0.525,-0.1), scales by960/configuredFOV, rotates Y by swing*0.5 then X by-swing*0.7, and adds that vector to interpolated player coordinates. Eye height is added later to the line's vertical difference. The local body has no zero-FOV guard; valid option constraints are an external dependency, not a demonstrated division failure.

The other path uses interpolated player position with hand lateral offset handDirection*0.35 and arm distance0.8, body yaw sin/cos, eye height minus0.45, plus a later crouch adjustment-0.1875 or0. None of this endpoint calculation reads the custom model's hand locator hierarchy. Customized bone poses therefore do not automatically establish identical rod-line alignment through this helper alone.

Hook position is interpolated with y+0.25. The player-minus-hook differences are converted double→float; only then is the branch-specific eye-height/crouch offset added to y. Preserve that operation order when reproducing the local arithmetic.

## Seventeen vertices and an extrapolated terminal tangent

The render loop at518..565 includes indices0 through16. Each call uses t=i/16 and u=(i+1)/16;17 calls are made, and the final tangent sample uses u=17/16 rather than clamping to1.

For line vector(X,Y,Z), the emitted local point is:

- x=X*t
- y=Y*(t*t+t)*0.5+0.25
- z=Z*t

The normal input is the difference from that point to the same curve evaluated at u, divided by its computed length. The helper contains no zero-length guard before the three float divisions. For a zero vector the two curve points coincide, making the normalization denominator zero and the divisions0/0 under ordinary Java floating arithmetic. This is a conditional mathematical consequence, not proof that this input is reached in the game or an observed visual defect. No repair was applied.

The main curve uses pose.pose for positions and pose.normal for normalized direction, with supplied RGB and alpha1. The color helper ignores its hook argument and returns a new black three-float array. RenderType.lineStrip is requested, but this does not prove output pixels or shader behavior.

## Iris tail differs from curve vertices

After the17-point loop, the Iris-installed predicate gates one additional VertexConsumer call sequence: raw position(0,0,0), integer black/alpha255, raw zero normal, endVertex. Unlike the main curve calls, this sequence does not pass pose matrices. It is gated on installed status, not the Iris shadow-pass predicate. The intent or effect of this compatibility sentinel is not established solely by its existence.

The caller's push/pop and entity-pitch writes are covered in [dispatcher routing](DISPATCHER-RENDER-REPLACEMENT-RECOVERY-2026-10-17.md). Rendering-line failure can bypass the normal pop; provider behavior and outer exception handling remain separate. This closes the local Java formula and branch reading, without executing Minecraft, provider code or native rendering.
