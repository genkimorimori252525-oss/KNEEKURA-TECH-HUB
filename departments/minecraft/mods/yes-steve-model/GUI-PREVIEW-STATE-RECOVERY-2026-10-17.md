# GUI preview state mutation and restoration scope

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.41 captured declarations across RenderUtil comparison owner, preview cache and GUI animatable;224 checks/8 negative controls. Reused GUI/frame/flag bodies are not newly promoted mappings. Separate955-class caller scan finds2 direct calls,0 bootstrap handles (2 checks/6 negative controls). No target/GPU/provider execution or independent semantic review.

## Temporary global flags are not stacked state

RenderUtil comparison owner `OoO00Oo00Ooo0OoOoo00o000` uses inventory/paperdoll booleans with direct setters. Texture-screen preview and model-thumbnail preview set inventory true then false on their normal tails; paperdoll similarly sets its own flag true then false. They do not save an enclosing flag value or use a nesting counter. They push/pop model-view and pose stacks on normal paths, set dispatcher shadow false then true, and switch inventory/3D lighting. These operations do not establish restoration to arbitrary caller state: true/false and lighting presets are explicit assignments, and prior dispatcher camera orientation is not saved/restored locally.

No finally spans all preview body operations. A rendering/cache failure can bypass parts of the normal cleanup. This is a static ownership limitation, not an observed crash or leaked graphics state. The inherited renderer's own event/pose scope remains separate.

## Equipment capture occurs after clearing

In the GUI-model overload `(FFFF,CustomHumanoidEntity,GeoReplacedEntityRenderer,boolean,boolean)V`, equipment suppression acts only when the final boolean is true and the entity is Player. Each eligible slot is first set to ItemStack.EMPTY through its inventory list; the returned previous item from set is discarded. Only afterward, at358, getItemBySlot is stored in the temporary array. The tail writes those captured references back. It is not a save-original-then-clear algorithm.

A second reading with pinned Vineflower1.11.1 agrees with javap on this order; [tool receipt](GUI-PREVIEW-VINEFLOWER-2026-10-17.json) records one original class, one output Java file and exit0. Full decompiled source/logs remain outside Git. This is a second tool view, not independent semantic approval or game execution.

Crucially, the exact [caller scan](GUI-PREVIEW-CALLERS-EVIDENCE-2026-10-17.json) finds two direct callers using fields typed CustomGuiPlayerEntity, both passing true for equipment suppression. That final GUI class constructs a new FakePlayer in its constructor. These observed paths are preview actors, so this finding is NOT evidence that the real player's inventory is erased. External/reflective/native callers and arbitrary reuse are not closed. Reusing this helper for live entities would require an explicit save-before-mutate contract rather than assuming one from its name.

## Rotation restoration is not identical across preview modes

The GUI-model body saves current X rotation in local17 and old X rotation in local18. Its tail restores current pitch from17 and also writes old pitch from17, leaving saved18 unused in that restoration. The texture-screen preview counterpart restores old pitch from its separately saved old-pitch local. Vineflower and bytecode agree on the distinction. This can collapse an old/current interpolation difference for a supplied actor; reachability/visual consequences are not a runtime finding.

GUI-model orientation uses yaw180 when preview rotation disabled, else200, pitch0, and a special living-vehicle yaw adjustment. Texture-screen preview separately saves/restores pose and supports sleep/swim/sneak and riding offsets. Multiple pose-condition checks are independent, so later satisfied conditions may overwrite earlier pose assignment. These should not be replaced by an assumed exclusive enum without evidence.

## Preview vehicles and cache ownership

Extra vehicle selection checks ride→ride_pig→boat and returns after the first matching branch. It fetches horse/pig/boat by entity-type ResourceLocation from a static Guava cache; creation uses the current preview actor's level only on a cache miss. The cache is built with expireAfterAccess5minutes, no level/dimension in the key and no explicit cleanup method in its owner. Actual cache expiration timing and cross-world use remain external/runtime questions.

The extra entity is drawn via dispatcher at a vertical offset based on vehicle/passenger riding offsets, with local yaw rotation and fullbright light. This helper does not establish an actual riding relationship. GUI ground/bed drawing, entity drawing, flushes and normal cleanup are Java calls, not a visible-image receipt.

## Reuse boundary

Treat previews as scoped mutations with explicit ownership of actor, equipment, previous/current rotations, pose, camera, lighting, flags and buffers. Do not infer transactional restoration or live-player safety. The central map remains669; whole-source equivalence and native output remain unproven. This cohort is later than the attachment-render checkpoint. Continue exact preview/cache callers only where needed, avoiding duplicate frame/controller analysis.
