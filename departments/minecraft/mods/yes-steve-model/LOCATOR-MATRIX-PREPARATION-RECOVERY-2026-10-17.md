# Locator hierarchy and Java matrix preparation

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Forty-six declarations across RenderUtils, GeoModelState and GeoModel. Separate fixed955-class caller inventory records18 direct locator calls in11 methods and zero direct/bootstrap calls to the inverse-matrix helper. No global/native/reflection closure, target runtime, central promotion or independent semantic review.

## Hierarchy input and list ownership

GeoModel `OOoOoooOOooO0o0000o0O0o0` receives sorted bones, locator string arrays, feature flags, properties, translucency flags and native ID. It does not discover hierarchy by traversing parent pointers in this Java constructor. Locator slots are:

- 0/1 left/right hand;2 elytra;3/4 pistol/rifle;5/6 waist;7/8 shoulder;9 blade;10 sheath;11 head;12 backpack.
- 13..19 extra left-hand lists,20..26 extra right-hand lists,27..34 passenger lists. Empty extra/passenger arrays are skipped, compacting these outer lists; they do not preserve empty slot placeholders.

Each supplied hierarchy string is pooled in order into an unmodifiable IntList, without checking it resolves to a bone. Constructor accesses the documented indices directly, relying on ordinary JVM array bounds rather than validating shape. Feature flags0..2 are copied to booleans; translucency array is retained. Sorted bone array is wrapped and exposed through an unmodifiable list view, not defensively cloned. Native ID is registered with a cleanup callback to a native free declaration with no Code; no native allocation/free was invoked or inferred as valid by this analysis.

GeoModelState `OOOO0O0O000O000000oOOO0o` maps each pooled name to a mutable bone-state instance, with the already documented input stride12/output stride4 arrays. findBones maps each supplied pooled name through boneMap and wraps the resulting list unmodifiable. Missing name can yield a null element; no local filtering occurs. Named hierarchy lists are views over mutable IBone objects, not immutable pose snapshots. Extra outer list getters return their retained lists. Constructor and getter snapshots do not prove native hierarchy input is valid or concurrent access safe.

## Matrix operations and units

RenderUtils `o000OO00oooOo00000ooo0Oo` performs these Java calls:

- Position translation: (-positionX/16, positionY/16, positionZ/16).
- Pivot translation: (+pivotX/16,+pivotY/16,+pivotZ/16); reverse pivot negates all three.
- Rotation: if any Z/X/Y component is nonzero, new Quaternionf.rotateZYX(rotationZ,rotationY,rotationX), then PoseStack.mulPose. There is no degree conversion in this helper.
- Scale: always PoseStack.scale(x,y,z), then return x==0 AND y==0 AND z==0. One zero axis is not enough to return true.
- Ordinary bone prep: position → pivot → rotation → scale → reverse pivot. Its boolean is that all-zero-scale test, not a general visibility/hidden/finite-matrix check.
- translateAndRotateMatrixForBone only does pivot then rotation; it is not equivalent to full bone preparation.

These use local IBone getters; they do not read native absolute-pivot output or imply world-space coordinates. Compare [bone query units](BONE-PARAMETER-QUERY-RECOVERY-2026-10-17.md) before substituting query vectors for rendered transforms.

## Locator leaf differs from ancestors

prepMatrixForLocator applies full ordinary prep to indices0..size-2 and ORs their all-zero-scale results. The final bone gets position → pivot → rotation → scale, but no reverse-pivot translation. Its scale method's boolean result is discarded. Consequently the returned flag describes all-zero scaling on ancestors only; a one-bone locator always returns false if operations finish, even when its final scale is all zero. This does not prove visible geometry survives the zero transform.

No empty-list guard is present; the final get(size-1) relies on a nonempty caller list. No null-bone guard or hidden-flag check is added here. Preserve the leaf pivot convention instead of treating every hierarchy entry identically.

## Caller evidence and inverse helper

[LOCATOR-MATRIX-CALLERS-EVIDENCE-2026-10-17.json](LOCATOR-MATRIX-CALLERS-EVIDENCE-2026-10-17.json) captures direct caller bodies and immediate result use. Of18 calls,15 immediately POP the flag; two immediately IRETURN it; one stores it for later control. These are static instruction facts, not proof of all callers' visual behavior. The hand-layer owner `o000Oo0OO0O00Oo0OOoOoooO` accounts for the return/store sites; its higher renderArmWithItem consumer uses the returned flag. Other attachments/providers may intentionally ignore it.

The inverse helper clones inputMatrix, calls invert on the clone, then mul(baseMatrix), returning the clone. It does not invert the base or mutate inputMatrix directly in its own body, and does not guard singular input. No direct/bootstrap Java caller was found within the fixed955 classes; native or reflective use remains possible. External matrix implementation and actual numerical/render results were not executed.

## Reuse and next seam

Unmodifiable containers do not freeze bone values/backing arrays. Keep caller list validity, ancestor versus leaf transform, sign/unit conversion and scale-flag consumption separate. Next follow concrete attachment layers and render pass cleanup/hand-selection behavior. The scoped snapshot auditor and caller inventory reject evidence mutations; neither is a game/native rendering test. Added after the fixed14 optional-integration checkpoint.
