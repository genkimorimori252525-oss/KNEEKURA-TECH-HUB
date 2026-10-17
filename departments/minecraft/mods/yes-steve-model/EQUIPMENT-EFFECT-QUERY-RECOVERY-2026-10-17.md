# Equipment and effect query inputs — 2026-10-17

## Evidence scope

Primary static review of official 2.6.5 Forge 1.20.1, artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Pinned comparison source: YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
34 selected declarations across 13 owners include binding constructors and
supporting abstract methods; they are not 34 new semantic mappings. Abstract
methods retain no Code. Independent semantic review NOT_RUN; no target/runtime,
registry fixtures, optional mods or network traffic executed. Central map 669
unchanged; whole-source equivalence NOT_ESTABLISHED.

## Function identities from registrations

QueryBinding constructor allocates these classes immediately after each name:

| Query | Owner suffix | Required argument count |
|---|---|---|
| is_item_name_any | oO0ooOo0O0OOooooooO0o0oO | >=2 |
| equipped_item_all_tags | Ooo0O0o0OO0oo0OOOOooo0OO | >=2 |
| equipped_item_any_tag | oOo0o00oooOoo0o0O0o000O0 | >=2 |
| max_durability | o0Oo0OO0Oo0oo0O0OO0OOOOo | ==1 |
| remaining_durability | Oo0ooO0oooooO00oO0o00oOO | ==1 |

YSMBinding constructor registers equipped_enchantment_level to
`OOoOo0oOOOo0O0000o0OOoOO` (>=2) and effect_level to
`oo00O0OOO0Oo0oO0oO0Oo0o0` (>=1). Arity validation is a declared function contract;
the parser/caller is responsible for invoking it, not every direct eval call.

## Shared context and slot handling

ContextFunction evaluate requires an IContext and validateContext success,
otherwise returns null. It does not add an exception handler around eval.
LivingEntityFunction additionally requires a LivingEntity. EffectLevel uses the
broader ContextFunction guard and handles player/living/arrow types internally.

MolangUtils slot parsing lowercases using Locale.ENGLISH, then looks up exactly
chest, feet, head, legs, mainhand or offhand. No trimming or alternate slot aliases
are introduced by the captured parser. Null input returns null; unknown strings
call debugPrint then return null on normal completion.

EquipmentUtil first consults CosmeticArmorCompat only for armor slots on a
Player when compatibility is installed. A present Optional stack wins, including
a present empty stack; this path does not itself reject empty cosmetic stacks.
Otherwise it uses the raw item-by-slot result. Actual optional-mod behavior is
outside this cohort. Its separate elytra helper tries a cosmetic chest elytra,
then an installed elytra-slot provider's elytra, then the vanilla chest elytra,
and returns ItemStack.EMPTY otherwise. This is not identical to general slot
selection and must not be collapsed into one unconditional provider.

## Names, tags and durability

ItemNameAny and both tag functions return null for an invalid slot, false for an
empty selected stack, and inspect later arguments lazily in order. A resource-ID
conversion returning null terminates with null if reached. ItemNameAny returns
true at the first matching registry ID; AnyTags at the first matching tag;
AllTags returns false at the first nonmatching tag. Later arguments can therefore
remain unevaluated, including later invalid inputs. AllTags only returns true
after all reached candidates match; the normal parser contract excludes a lone
slot argument.

Max/remaining durability each read only argument 0 as the slot. Unlike the name
and tag functions, their raw eval bodies have no null-slot check before calling
EquipmentUtil. A null slot reaches its slot.isArmor call. An outer evaluator may
catch an exception, but these bodies alone do not guarantee a null/zero result.
Remaining durability is maxDamage - damageValue with no local nonnegative clamp.

## Enchantment argument index: preserve actual code

The exact enchantment loop increments its loop counter from 1, but loads constant
ICONST_1 at offset 78 immediately before getAsResourceLocation at 79 on EVERY
iteration. Both fixed source and artifact use argument index 1 rather than the
loop variable. It skips null/unregistered IDs and sums getEnchantmentLevel.

For a stable normal argument list and pure constant inputs, n arguments cause
n-1 evaluations of the first enchantment argument; later enchantment arguments
are not selected by this loop. Do not generalize this into a multiplication law
when argument evaluation has side effects: the getter is lazy and reevaluated.
No corrective patch is part of this analysis, and no in-game symptom is claimed.

## Effect routing and summation

EffectLevel iterates every argument from index 0. Null/unknown effect IDs are
skipped. Valid effects choose these sources in order:

1. Remote PlayerAnimatableCapability: cached PlayerStateTracker effect level.
2. Other LivingEntity: current MobEffectInstance amplifier + 1 when present.
3. Arrow: injected accessor effect collection, first identity-matching effect,
   amplifier + 1; the inner loop then stops for that argument.
4. Other entity: returns null when a valid effect reaches this branch.

Duplicate effect arguments can contribute repeatedly; this is a sum rather than
a max or unique-effect count. An unsupported entity with only invalid/unknown
IDs can finish with integer zero without reaching the null branch. No final
clamp is present. The remote cache representation and reset lifetime remain
separate from direct live-entity effects.

## Verification and next seam

`tools/equipment_effect_query_ysm_265.py` accepts --jar, --source-root, --evidence
and --out. Receipt: 229 integrity checks, 19 intentionally altered fixtures
rejected, including the constant enchantment index. These tests validate exact
snapshots and corruption detection, not independent interpretation or execution.

Next: typed argument conversion, ResourceLocation parsing and optional equipment
adapter boundaries, then world-relative/tag queries. Keep lazy argument order,
invalid input behavior and live versus cached provenance distinct.
