# Java render-cycle and state-array boundary

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, candidate
source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No JAR/game/native execution
and no native-library extraction. This closes the Java handoff, not rendering
inside the native implementation. Central mapping remains669.

21 method declarations across IGeoRenderer `oo0OOoOOOOO0Oo0O0oo0O0OO`,
NativeRenderer Java wrapper `ooOOo000OOO0ooO0oo0ooooO`, its nested legacy writer
and EModelRenderCycle `o0oO0OoOoOOOOoOOOOOOo0oo`. Four source records cover three
files. Abstract/native methods remain declarations without fabricated Code.

## Interface default render path

preRender sets current buffer source, then invokes renderEarly and renderLate.
Default renderEarly scales width,height,width only for INITIAL cycle; ordinary
renderLate and cycle setter defaults are empty. Concrete renderer overrides are
therefore relevant; interface defaults alone do not prove persistent cycle state.
The earlier GeoReplacedEntityRenderer dossier retains its field-backed setter.

Default render uses the supplied VertexConsumer when nonnull, otherwise asks the
buffer source for one. It calls animatable.countRender at17 before invoking the
Java native-wrapper method at54, then sets REPEATED at61 after normal return.
A counted render therefore means reaching that call path, not successful pixels:
wrapper/native failure can leave countRender recorded without advancing cycle.
No finally protects these three stages.

The call passes poseStack.last, the GeoModelState model, inputState and outputState
arrays, texture index, mode0, packed lighting/overlay and RGBA. The arrays come
straight from the previously inspected getters; there is no copy at this call.
This joins the bone input-buffer commit path to the Java rendering boundary.
It does not resolve the output buffer's fourth slot or native mutation semantics.

Default render-type selection prioritizes visible over glowing. Visible selects
custom translucency or cutout-no-cull; invisible+glowing selects outline; neither
returns null. This explains the main-body skip in the prior renderer dossier
without asserting what external RenderType factories actually draw.

## Wrapper-only native boundary

The wrapper calls Iris setup, computes forceLegacy as Optifine-installed OR
compatibility-config, multiplies projection by model-view into shared POST_MAT,
computes renderOnGui as inventory OR paper-doll, and forwards arguments at92.
These flags are not identical to level-exclusive/immutable predicates from the
scheduling path. Thread-safety of shared matrix access is not established here.

The callee declaration has access266: private, static, native. It has no Code
attribute. Argument descriptors and flags are known; the native body, output
writes, skeletal transforms, draw batching and actual visual result are not.
No claim in this dossier should be read as recovering those internals.

## Legacy Java writer contract

The nested Java callback iterates i<vertexCount, using float stride12 and int
stride2. Per vertex it supplies xyz at float0..2, rgba at3..6, UV at7..8, overlay
and light at int0..1, normals at float9..11 to VertexConsumer. Zero/negative count
executes no iteration on this body; positive counts have no independent array
length preflight beyond JVM array access checks. The native caller's guarantee
of valid lengths or whether this path is selected is not proven. This is a Java
callback contract, not an implementation of the hidden native producer.

## Checks and next connected work

128 fixed-artifact/source/body/declaration/bootstrap checks pass;16 negative
controls reject altered array getter/mode/buffer gates, writer index, missing
native flag and invented native instructions. Independent semantic review has
not run; whole-source equivalence remains unproven.

The main Java path is now joined at bounded seams: entity/event time → condition
and player state → point/queue evaluation → bone input buffers → renderer arrays.
This is not whole-mod completion. Next return upstream to EntityStateTracker and
Molang query inputs, keeping this native boundary explicit rather than treating
it as permission to expand into protected native/model internals.
