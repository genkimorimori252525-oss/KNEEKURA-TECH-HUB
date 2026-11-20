"""Convert X1 THKaguyaRecipe.java (GameRegistry.addRecipe / addShapelessRecipe) into 1.20.1 recipe JSON.
1.7.10 semantics: a Block argument matches any metadata (32767), an Item argument metadata 0, an ItemStack its
metadata; outputs keep the ItemStack count. setRecipelessItemsRecipe recipes get the config condition.

usage: python convert-x1-recipes.py <X1 thKaguyaMod/init/THKaguyaRecipe.java> <port-1.20.1 directory>"""
import json
import re
import shutil
import sys
from pathlib import Path

x1 = Path(sys.argv[1])
port = Path(sys.argv[2])
cards_src = (port / "src/main/java/dev/kneekura/fivedifficulties/forge/spellcard/X1SpellCards.java").read_text(encoding="utf-8")
CARD_KEY = {int(m.group(2)): m.group(1).lower().replace("'", "").replace("-", "_")
            for m in re.finditer(r'r\([^,]+,\s*"([^"]+)",\s*(\d+)\)', cards_src)}
M = "five_difficulties_port:"
PEARLS = ["red", "blue", "green", "yellow", "purple", "aqua", "orange", "white"]
# X1 static stacks: name -> (port id, count)
X1 = {f"{c}_pearl": (M + f"hourai_pearl_{c}", 1) for c in PEARLS}
X1.update({
    "homing_amulet": (M + "homing_amulet", 16), "diffusion_amulet": (M + "diffusion_amulet", 16),
    "silver_knife_blue": (M + "silver_knife_blue", 4), "silver_knife_red": (M + "silver_knife_red", 2),
    "silver_knife_green": (M + "silver_knife_green", 2), "silver_knife_white": (M + "silver_knife_white", 1),
    "small_shot": (M + "small_shot", 1), "tiny_shot": (M + "tiny_shot", 1), "medium_shot": (M + "medium_shot", 2),
    "big_shot": (M + "big_shot", 3), "star_shot": (M + "star_shot", 1), "small_star_shot": (M + "small_star_shot", 5),
    "circle_shot": (M + "circle_shot", 3), "scale_shot": (M + "scale_shot", 4), "butterfly_shot": (M + "butterfly_shot", 2),
    "light_shot": (M + "light_shot", 1), "knife_shot": (M + "knife_shot", 2), "heart_shot": (M + "heart_shot", 2),
    "kunai_shot": (M + "kunai_shot", 3), "talisman_shot": (M + "talisman_shot", 2), "bigLight_shot": (M + "big_light_shot", 1),
    "rice_shot": (M + "rice_shot", 2), "oval_shot": (M + "oval_shot", 2), "crystal_shot": (M + "crystal_shot", 2),
    "arrow_shot": (M + "arrow_shot", 1),
    "middle_laser": (M + "laser", 1), "short_laser": (M + "short_laser", 1), "long_laser": (M + "long_laser", 1),
    "power_up_item_small": (M + "power_item_small", 1), "power_up_item_big": (M + "power_item_big", 1),
    "power_item": (M + "power_item_small", 1),
})
RENAME = {"soulTorch": "soul_torch", "kinkakuji": "kinkakuzi", "magic_bloom": "magic_broom", "gungnir": "spear_the_gungnir",
          "hisou_sword": "scarlet_perception_sword", "ship_ghost_dipper_fill": "ship_ghost_dipper",
          "hourai_Jeweled_branch": "hourai_jeweled_branch", "illness_recovery_charm": "byoukiheiyu_mamori"}
DYE = ["ink_sac", "red_dye", "green_dye", "cocoa_beans", "lapis_lazuli", "purple_dye", "cyan_dye", "light_gray_dye",
       "gray_dye", "pink_dye", "lime_dye", "yellow_dye", "light_blue_dye", "magenta_dye", "orange_dye", "bone_meal"]
WOOL = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan", "purple",
        "blue", "brown", "green", "red", "black"]
WOOD4 = ["oak", "spruce", "birch", "jungle"]
# 1.7.10 Block (any metadata) -> 1.20 ingredient
BLOCK_ANY = {
    "planks": {"tag": "minecraft:planks"},
    "wool": {"tag": "minecraft:wool"},
    "log": [{"item": f"minecraft:{w}_log"} for w in WOOD4],
    "leaves": [{"item": f"minecraft:{w}_leaves"} for w in WOOD4],
    "red_flower": [{"item": "minecraft:" + f} for f in ["poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip",
                                                         "orange_tulip", "white_tulip", "pink_tulip", "oxeye_daisy"]],
    "yellow_flower": {"item": "minecraft:dandelion"},
    "waterlily": {"item": "minecraft:lily_pad"},
}
VANILLA_ITEM = {"clock": "clock"}
unknown = []


def split_top(s):
    out, depth, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
            cur += ch
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def resolve(expr):
    """-> (ingredient json, result id, count)"""
    expr = expr.strip()
    m = re.fullmatch(r"THKaguyaItems\.getSpellCardForId\((\d+)\)", expr)
    if m:
        iid = M + "spell_card_" + CARD_KEY[int(m.group(1))]
        return {"item": iid}, iid, 1
    m = re.fullmatch(r"new ItemStack\((.+)\)", expr, re.S)
    if m:
        args = split_top(m.group(1))
        base = args[0]
        count = int(args[1]) if len(args) > 1 else 1
        meta = int(args[2]) if len(args) > 2 else 0
        if base == "Items.dye":
            iid = "minecraft:" + DYE[meta]
        elif base == "Blocks.wool":
            iid = f"minecraft:{WOOL[meta]}_wool"
        elif base == "THKaguyaBlocks.danmaku_crafting_table":
            iid = M + ("laser_crafting_table" if meta == 1 else "danmaku_crafting_table")
        else:
            ing, iid, _ = resolve(base)
            if meta != 0 and not base.startswith("THKaguyaItems."):
                unknown.append(f"meta {meta} on {base}")
        return {"item": iid}, iid, count
    m = re.fullmatch(r"THKaguyaItems\.(\w+)", expr)
    if m:
        n = m.group(1)
        if n in X1:
            iid, c = X1[n]
            return {"item": iid}, iid, c
        iid = M + RENAME.get(n, n)
        return {"item": iid}, iid, 1
    m = re.fullmatch(r"THKaguyaBlocks\.(\w+)", expr)
    if m:
        n = m.group(1)
        if n == "danmaku_crafting_table":
            return [{"item": M + "danmaku_crafting_table"}, {"item": M + "laser_crafting_table"}], M + "danmaku_crafting_table", 1
        if n == "danmaku_crafting_table_shot":
            return {"item": M + "danmaku_crafting_table"}, M + "danmaku_crafting_table", 1
        if n == "danmaku_crafting_table_laser":
            return {"item": M + "laser_crafting_table"}, M + "laser_crafting_table", 1
        unknown.append(expr)
        return {"item": M + n}, M + n, 1
    m = re.fullmatch(r"Items\.(\w+)", expr)
    if m:
        n = m.group(1)
        if n == "dye":
            return {"item": "minecraft:ink_sac"}, "minecraft:ink_sac", 1
        iid = "minecraft:" + VANILLA_ITEM.get(n, n)
        return {"item": iid}, iid, 1
    m = re.fullmatch(r"Blocks\.(\w+)", expr)
    if m:
        n = m.group(1)
        if n in BLOCK_ANY:
            return BLOCK_ANY[n], None, 1
        return {"item": "minecraft:" + n}, "minecraft:" + n, 1
    unknown.append(expr)
    return {"item": "?" + expr}, "?" + expr, 1


src = x1.read_text(encoding="utf-8", errors="replace")
src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
src = re.sub(r"//[^\n]*", "", src)
split_at = src.index("public static void setRecipelessItemsRecipe")
recipes, seen = [], set()
for m in re.finditer(r"GameRegistry\.(addRecipe|addShapelessRecipe)\(", src):
    i, depth = m.end(), 1
    while depth:
        depth += {"(": 1, ")": -1}.get(src[i], 0)
        i += 1
    args = split_top(src[m.end():i - 1])
    out_expr, body = args[0], args[1]
    inner = re.fullmatch(r"new Object\[\]\s*\{(.*)\}", body.strip(), re.S).group(1)
    toks = split_top(inner)
    _, rid, count = resolve(out_expr)
    result = {"item": rid} | ({"count": count} if count != 1 else {})
    conditional = m.start() > split_at
    if m.group(1) == "addRecipe":
        pattern, key, k = [], {}, 0
        while k < len(toks) and toks[k].startswith('"'):
            pattern.append(toks[k].strip('"'))
            k += 1
        while k < len(toks):
            ch = re.fullmatch(r"Character\.valueOf\('(.)'\)", toks[k]).group(1)
            key[ch] = resolve(toks[k + 1])[0]
            k += 2
        r = {"type": "minecraft:crafting_shaped", "pattern": pattern, "key": key, "result": result}
    else:
        r = {"type": "minecraft:crafting_shapeless", "ingredients": [resolve(t)[0] for t in toks], "result": result}
    sig = json.dumps(r, sort_keys=True)
    if sig in seen:
        continue
    seen.add(sig)
    if conditional:
        r = {"conditions": [{"type": M + "recipeless_items_recipe"}]} | r
    recipes.append((rid.split(":")[1], r))

out = port / "src/main/resources/data/five_difficulties_port/recipes"
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
used = {}
for name, r in recipes:
    used[name] = used.get(name, 0) + 1
    fn = name if used[name] == 1 else f"{name}_{used[name]}"
    (out / f"{fn}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("RECIPES", len(recipes), "conditional", sum(1 for _, r in recipes if "conditions" in r))
print("UNKNOWN", sorted(set(unknown)))
ids = sorted({v["item"] for _, r in recipes for v in ([r["result"]] + [x for x in (r.get("key", {}).values())
                                                                                    if isinstance(x, dict) and "item" in x]
                                                       + [x for x in r.get("ingredients", []) if isinstance(x, dict) and "item" in x])})
print("IDS", " ".join(i.split(":")[1] if i.startswith(M) else i for i in ids))
