# Resource arguments and equipment adapters — 2026-10-17

## Scope

Primary static review; fixed JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Pinned source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
31 selected methods across six owners support argument getters, literal caching,
string conversion and two optional-mod adapters. Supporting declarations are not
new central mappings; the map remains 669. Independent semantic review NOT_RUN.
No target JVM, optional mod, registry, native implementation or game executed.

## Lazy arguments and literal identity

ArgumentCollection retains its supplied List; each typed/value getter first gets
the expression at the requested index and evaluates it. getExpression returns
the raw expression. The getters do not add an index-range check or exception
handler, and list.get occurs before the expression-evaluation call. The exact
visitString method returns the StringExpression object itself, so literal object
identity survives evaluation instead of always being reduced to Java String.

asString recognizes StringExpression and String, returning null for other types;
it is not a general toString conversion. asPooledString uses the literal's pooled
ID or interns a Java String, otherwise returning StringPool.EMPTY. Existing
numeric/boolean conversion semantics remain in VARIABLE-CONVERSION evidence.

## ResourceLocation path

ArgumentCollection owner:
`O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo`.
Its resource getter first evaluates getValue at offset 3, even on a later cache
hit. For StringExpression it reads cachedValue at 22; if nonnull (branch 25),
returns it at 33. Otherwise it calls ResourceLocation.tryParse at 39, stores only
a successful parse at 53 and returns it. A Java String takes a separate parse
call at 84 without storing a literal cache. Other types go to the invalid path.

Failed parsing is not negatively cached by these bodies. The invalid path calls
context.debugPrint at 127 and returns null on ordinary completion. It does not
add a catch around debugPrint, nor accept arbitrary objects through toString.
The actual ResourceLocation parsing grammar belongs to Minecraft; its runtime
implementation was not re-executed here.

StringExpression's text and pooled ID are final fields; its ResourceLocation
cache is a mutable field with getter/setter. This caches a parsed identifier,
not the current registry's Item/Effect/Enchantment object. The queries still
perform their registry lookups. Do not infer cross-thread synchronization,
registry-object lifetime or immutable cache contents from the final text field.

## Cosmetic armor has a meaningful present-empty result

CosmeticArmorCompat owner `oO0OoOOO0o000o0Oo000000O` caches ModList.isLoaded for
`cosmeticarmorreworked` during init. isInstalled reads that stored boolean; it is
not a fresh discovery call. getSkinArmorItem itself checks armor slot, not the
installed flag; the general EquipmentUtil caller supplies the installation gate.

For armor it obtains the client cosmetic inventory by the player's UUID. If
isSkinArmor(slot index) is true, it returns Optional.of(ItemStack.EMPTY), not
Optional.empty. Otherwise a nonempty cosmetic slot yields a present stack and an
empty cosmetic slot yields Optional.empty. Joined to EquipmentUtil, this explains
why a present empty cosmetic stack can suppress the raw armor selection, whereas
an absent Optional falls back. No additional meaning of the external mod's API
or actual loaded version is asserted.

## Elytra adapter boundary

ElytraSlotCompat owner `OOo0OO0o00o00O0OOO0o00OO` similarly caches the `elytraslot`
installation result. Its getEquippedElytraItem directly delegates to
Services.ELYTRA.getEquipped(entity), with no own installation guard or handler.
EquipmentUtil conditionally calls it and checks for the vanilla ELYTRA item.
The external provider's implementation and missing-mod linkage behavior are
outside the evidence. Merely recording a guard does not prove successful runtime
class loading or compatibility with arbitrary versions.

## Verification and continuation

`tools/resource_argument_adapter_ysm_265.py` takes --jar, --source-root,
--evidence, --out. 186 checks passed; 12 mutated evidence fixtures were rejected,
including reversal of the literal-cache-hit branch. These are artifact/source
integrity checks, not behavioral game tests or independent semantic review.

Continue world-relative position/block/tag and biome query paths. Preserve
expression evaluation order, range checks, integer rounding and short-circuit
results, rather than assuming the query names imply Bedrock-exact behavior.
