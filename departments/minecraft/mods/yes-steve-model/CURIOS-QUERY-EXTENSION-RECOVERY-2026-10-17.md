# Curios query extension and visible-slot selection — 2026-10-17

## Scope

Primary static review of exact JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, pinned source
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
47 methods across seven owners capture CuriosCompat/Inner, three functions,
MolangCache and Function placeholder support. Counts include support/debug/lambda
bodies, not new central mappings. Independent semantic review NOT_RUN; no Curios,
game, native implementation or live inventory executed. Central map stays 669.

## The catalog extension is conditional behavior, not missing names

The YSMBinding tail previously left outside the 171-name base catalog invokes
CuriosCompat owner `o0OOoO0oOOO00OO0ooOOoO0O`. Its init records whether
LoadingModList.getModFileById("curios") is nonnull. addMolangBinding chooses
CuriosCompatInner `O000ooOO00O0oooO0000o0o0` when installed, otherwise placeholders.
Both branches register the same four names:

- has_any_curios
- has_any_curios_with_all_tags
- has_any_curios_with_any_tag
- dump_curios

The first three absent-mod bindings use Function.PLACE_HOLDER, which returns null
without evaluating supplied expression arguments and inherits default argument-
size acceptance. The real functions have stricter arity below. The absent-mod
dump is a LivingEntity variable whose callback debugPrints a missing-mod notice
and returns null on normal completion. Query-name existence alone therefore does
not prove an installed provider or equivalent argument evaluation.

The base constructor catalog remains exactly 171 entries; these four names are a
separately resolved extension. This does not assert a complete global runtime
registry. Installation flag changes do not themselves rerun the recorded binding
registration method; initialization/rebinding order is a separate lifecycle.

## Slot and ID preparation

All three real functions validate a LivingEntity context. They read the first
argument as a string, returning null for null/empty. They pass the string to the
Curios slot handler without YSM-side lowercasing or trimming. Provider-side slot
semantics are not inferred.

HasAnyCurios accepts at least one argument. It obtains a per-thread identity item
set, clears it, then resolves every reached ID from index 1. An invalid resource
ID returns null; a syntactically accepted ID missing from the item registry is
skipped. The search predicate is `itemSet.isEmpty() || itemSet.contains(item)`.
Thus a slot-only request means any selected nonempty item; a request whose every
valid ID resolves to no registered item also reaches the same empty-set behavior.
Do not silently convert that case to always false in a reconstruction.

The all/any-tag variants require more than one argument, size a per-thread list
to args.size()-1, and fill it with tag keys in order. A reached invalid ID returns
null. Preparation happens before inventory scanning; this is not the same lazy
short-circuit sequence as the ordinary equipped-item tag queries.

## Rendered slots and cosmetic precedence

The adapter first gates on INSTALLED, obtains Curios inventory, selects the named
stacks handler and searches, otherwise false. searchCuriosHandler:

1. Reads render toggles, optional cosmetic stack handler, and normal stacks.
2. Iterates while index is below BOTH normal slot count and toggle-list size.
3. Skips a slot whose render toggle is false.
4. If a nonnull, nonempty cosmetic stack exists, test it. On a match return it;
   on a mismatch continue to the next slot, without testing that slot's raw item.
   The exact failed-cosmetic-predicate branch at offset 109 goes to increment 148.
5. Only without a nonempty cosmetic stack does it test the nonempty normal stack.
6. Return null after no match.

The result is a visible/cosmetic selection, not a query over every physically
equipped raw item. All-tags means one selected stack satisfies every tag; different
stacks do not jointly satisfy the set. Any-tags means one selected stack satisfies
at least one tag. Whole-inventory helper order follows the provider's map values;
no stable sorted result ordering is introduced by YSM.

## Cache and external boundaries

MolangCache `o00Ooo0OO000000OO00000o0` uses separate ThreadLocal containers with
initial capacity 16 for the item set and tag list. It reuses containers rather
than allocating a new set/list for every query. ThreadLocal is not a claim of
reentrant-call isolation or a lock on the external inventory. Lazy argument
expressions can invoke other functions; concurrent/reentrant behavior has not
been reproduced. Do not accept an optimistic source comment about architecture
as a thread-safety proof.

## Verification and continuation

`tools/curios_query_extension_ysm_265.py` takes --jar, --source-root, --evidence,
--out. 270 integrity checks passed; 13 mutated fixtures rejected, including the
installed/placeholder registration gate. No optional provider was installed or
probed, and no failure was patched based solely on static concerns.

Continue remaining entity/item/projectile callback bodies through the compact
query-name catalog; distinguish default-item IDs, live stack IDs, client hit
state, mixin fields and cached remote-player state.
