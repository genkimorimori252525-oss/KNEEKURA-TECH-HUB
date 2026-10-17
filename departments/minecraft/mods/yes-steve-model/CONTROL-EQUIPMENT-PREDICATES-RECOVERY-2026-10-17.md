# Control equipment and riding predicates

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. This cohort captures 21 method declarations in five owners; one abstract Condition declaration has no Code. No mapping promotion, independent semantic review, target execution or runtime compatibility claim.

## Entry points and evaluation order

The [CtrlBinding constructor](CONTROL-PRIORITY-ACTIONS-RECOVERY-2026-10-17.md) registers hold/swing/use from three factories on `O0O0ooOOooOOO00OO0OOOooO`, armor from `o0oOOoO0oooo0O0OoOoOoOo0`, and ride from `O000000ooOoOOo000ooO000o`. All extend LivingEntityFunction. All accept two OR three arguments, but these bodies only read indices 0 and 1: third argument is not evaluated here.

- hold/swing/use: parse slot first. Invalid or armor slot returns boxed Integer 0 before reading the match string. Blank match string returns 0. Resolve raw `LivingEntity.getItemBySlot` (offset78), not EquipmentUtil cosmetic precedence. Build InteractionHand from offhand versus mainhand and pass it to Condition.test (109), but all three captured factory predicates ignore that hand argument. Hold always permits; swing requires entity swinging and not sleeping; use requires entity using an item and not sleeping. They do not independently verify that the requested hand is the currently swinging/using hand. Condition rejection precedes even the special empty-item match.
- armor: invalid or non-armor slot returns null, unlike hand checks' Integer 0. Blank match string returns 0. Raw getItemBySlot call75, likewise no cosmetic helper. Return values below are boxed 0/1.
- ride: evaluates both strings before checking match-string blankness or selector validity. Exact selector `vehicle` chooses immediate vehicle, `passenger` chooses first passenger only, otherwise 0. Missing or non-alive selected entity returns 0. Neither searches all passengers nor recursively climbs a riding tree.

## Match language, not arbitrary resource arguments

Hand/armor allow exact `empty` when the selected ItemStack is empty. Other branches strip the first character after the blank guard, then inspect prefix:

- `$`: compare remaining text exactly with the registry key's toString. No ResourceLocation parsing, case normalization or trimming of the supplied match text here. Missing key returns 0. For ride this is entity TYPE key, not a unique entity ID.
- `#`: obtain registry tag manager; missing manager returns 0. Construct `new ResourceLocation(subInput)`, create tag key and test membership. This is a constructor call (hand250/armor208/ride217), not tryParse/getAsResourceLocation. These bodies have no local catch; invalid syntax is not locally converted into a benign false. Outer evaluator exception behavior is a separate boundary.
- `:`: hand checks only. Try InnerClassify exact nonblank category, then item's UseAnim name lowercased with Locale.ENGLISH. A classification mismatch still permits the UseAnim fallback. Supplied suffix itself is not lowercased. Armor/ride do not have this branch.
- Anything else returns 0. Matching `empty` does not bypass hold/swing/use condition gates.

## Classifier precedence

`OoOo0oO0O0OO00O00OOoOo0o` selects the first match:

slashblade → sword → gohei → axe → pickaxe → shovel → hoe → shield → crossbow → bow → fishing_rod → spear → throwable_potion → empty string.

Slashblade and gohei use optional-mod adapters; remaining categories use corresponding vanilla item subclasses OR YSM item tags. The literal `spear` is used for TridentItem/tag, not `trident`. Category precedence matters for overlapping tags. Optional provider internals, active datapack tag contents and actual loaded items are outside this cohort. The companion doClassifyTest reads the requested hand and concatenates a supplied prefix only when classification is nonempty.

## Reuse limits

Do not interchange these ctrl predicates with YSM equipment queries: raw/cosmetic item provenance, prefix parsing, invalid-slot returns and invalid-resource handling differ. Do not infer active-hand precision merely from the Condition signature. Preserve typed guards and lazy argument order. The scoped auditor verifies exact bytes/declarations/operands/bootstrap/source anchors, not game behavior; see [equipment query recovery](EQUIPMENT-EFFECT-QUERY-RECOVERY-2026-10-17.md) and [function evaluation](FUNCTION-LOOP-ORDER-RECOVERY-2026-10-17.md).
