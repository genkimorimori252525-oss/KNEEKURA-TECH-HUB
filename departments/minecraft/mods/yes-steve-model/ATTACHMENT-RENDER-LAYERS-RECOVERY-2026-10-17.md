# Concrete item, head, elytra, shoulder and backpack layers

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty-two declarations across five layers plus backpack's anonymous empty model. No mapping promotion, independent semantic review, target/GPU rendering or external provider execution. Parent renderer eligibility is separate from the local layer gates described here.

## Hand items and extra locators

CustomPlayerItemInHandLayer `o000Oo0OO0O00Oo0OOoOoooO` requires loaded GeoModelState and at least one nonempty raw main/offhand item. Its local routing associates mainhand with right-hand locator/THIRD_PERSON_RIGHT_HAND and offhand with left-hand locator/THIRD_PERSON_LEFT_HAND; it does not query the entity's dominant arm in this method.

Mainhand requires a nonempty right-hand hierarchy. SlashBlade uses its special renderer; other items use ordinary arm rendering between TACZ flash/shell-open and stop calls. When renderLayersFirst, nonempty item and IExtendedBufferSource all hold, endBatchFixedRenderType is called. Offhand requires a nonempty left hierarchy; SlashBlade is special, SWarfare guns skip ordinary offhand rendering, other items use ordinary rendering. After the outer pose pop, TACZ and SWarfare offhand adapters are called separately. Thus special offhand adapters are not simply the same path as ordinary left-hand drawing.

Ordinary arm rendering rejects empty item, pushes pose, gets the [locator preparation flag](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md), and only renders when that flag is false. It translates(0,-0.0625,-0.1), rotates X by-90degrees, then for SWarfare guns adds x=0.1 translation and1.25 scale before ItemInHandRenderer.renderItem. Extra hierarchies repeat the same item with their own pose pushes and flag checks; their SWarfare adjustment scales1.25 but omits the base-hand x=0.1 offset. Base hierarchy gate at the outer call means extra ordinary items are not reached solely because an extra hierarchy exists.

The helper's flag only reports an all-zero ancestor scale, not all invisibility or the leaf scale. The layer does not add an independent hidden-bone check. push/pop, flash/shell restoration and flush calls appear on normal paths without a local finally covering all exceptions. That is an ordering/cleanup boundary, not an observed leak or render failure.

## Head item layer

`oOoOoooOoOo0oOO0Oo0o0O0o` requires loaded model and nonempty head locator. It reads raw HEAD equipment, renders nonempty items except ArmorItem whose declared equipment slot is HEAD, then independently tries a nonempty SimpleHats Curios head item. The second item does not replace the first by this local code; both can render if both qualify. Each uses locator prep (return ignored), scale0.625, translate y0.25 and ItemDisplayContext.HEAD. This is not an ordinary armor-mesh renderer or proof of cosmetic head-slot replacement.

## Elytra layer

`oOooOo000o0oo0o0OO00oO00` obtains equipment through the dedicated elytra helper and requires nonempty item, loaded model, nonempty elytra locator and AbstractClientPlayer. Texture precedence is loaded/non-null elytra skin → loaded/non-null cape with CAPE model part enabled → textures/entity/elytra.png.

After locator prep (return ignored): translate y1.5, rotate Z180degrees, scale2, run ElytraModel.setupAnim, obtain armorCutoutNoCull foil buffer using stack foil state, render with no overlay and RGBA1, then pop. This names the Java render API/pass request, not a GPU or visible-texture result.

## Shoulder parrots

`oO0OO0000o0oOo00oOo00000` processes each nonempty shoulder hierarchy independently. It reads the corresponding shoulder tag and requires EntityType.byString(id) to resolve exactly PARROT before drawing. Merely nonempty NBT does not suffice, unlike the broad has-shoulder query. It applies locator prep (return ignored), y1.5/Z180, resolves variant through Parrot.Variant.byId, chooses variant texture and passes player.tickCount to renderOnShoulder. External variant fallback and actual parrot mesh output are not executed here.

## Sophisticated backpack layer

`O0OooOOOOO00OooOoo0Oo0o0` requires loaded model and nonempty backpack hierarchy, then a non-null selected backpack from the [adapter](BACKPACK-SPELL-BLADE-INPUTS-RECOVERY-2026-10-17.md). It applies locator prep (return ignored), X180 then Y180, translates y-0.1 and invokes provider renderBackpack with false final boolean. The anonymous EntityModel has empty setupAnim/renderToBuffer bodies and is a placeholder; this does not prove the external provider's output or internal model requirements.

## Reuse and limits

Keep ordinary versus provider-special item paths, raw versus provider-selected equipment, side conventions, per-layer transform order, repeated extra attachments and buffer/cleanup scope distinct. The caller inventory's15 discarded scale flags does not mean those transforms are skipped; matrix mutation still occurs. No vanilla renderer, provider or native draw was invoked. The scoped auditor checks exact evidence/source and negative mutations only; later than the fixed14 checkpoint.
