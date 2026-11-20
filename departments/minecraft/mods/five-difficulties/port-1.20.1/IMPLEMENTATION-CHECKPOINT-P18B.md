# Implementation checkpoint — P18b recipes, yin-yang orb

Date: 2026-11-20
Oracle: X1 `THKaguyaRecipe` (`setAllRecipes`, `setRecipelessItemsRecipe`), `THKaguyaItems` / `THKaguyaBlocks`
static stacks, `THKaguyaConfig.recipelessItemsRecipe`, `ItemOnmyoudama`.

## What was done

- `tools/convert-x1-recipes.py` reads X1's `THKaguyaRecipe.java` and writes
  `data/five_difficulties_port/recipes/*.json` (109 recipes; one exact duplicate — the aqua pearl, listed in both
  methods — dropped). It reads the private X1 source, so it is run locally; only its JSON output is committed.
- The seven `setRecipelessItemsRecipe` recipes (magic broom, icicle sword, Miracle Mallet, cards 9 / 19 / 28,
  white pearl) carry the `five_difficulties_port:recipeless_items_recipe` condition
  (`RecipelessItemsCondition`, X1 config "Add Recipeless Items Recipe", default off).
- `yin_yang_orb` (X1 `ItemOnmyoudama`, a stack-of-1 material: its `onArmorTick` never runs because it is not
  armour) was missing and is added; it is a recipe ingredient.

## 1.7.10 semantics kept

- A Block argument matches any metadata (e.g. any planks / wool, the four 1.7.10 logs and leaves, every
  `red_flower` flower); an Item argument matches metadata 0 (`Items.dye` alone = ink sac); an ItemStack
  matches its metadata (dye colours, wool colours, shot / laser / pearl subtypes).
- Results keep the X1 stack counts (medium shot 2, big shot 3, small star 5, scale 4, kunai 3, amulets 16,
  silver knives 4 / 2 / 2 / 1, …).

## Deviation

- 1.20 always trims empty rows / columns of a shaped pattern, so X1 patterns padded with blanks (e.g. a
  1-wide card in a 3×3 frame) can be crafted in any position and, when they fit, in the 2×2 grid.

## Receipts

- Server: `FIVE_DIFFICULTIES_P18B_RECIPES_PASS recipes=102 medium=2 medium_shot` (102 = 109 − 7 conditional;
  8 redstone + ender pearl → red Hourai pearl; no Miracle Mallet recipe with the switch off), plus every earlier
  check, P6/P8–P17 `RUNTIME_SCENARIO_PASS` (1 local run). No recipe parse errors in the server log.
