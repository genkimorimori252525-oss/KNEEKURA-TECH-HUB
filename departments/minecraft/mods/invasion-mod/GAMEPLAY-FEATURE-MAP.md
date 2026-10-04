# Gameplay Feature Map — Invasion Mod

Player-facing material is used here as reconnaissance. It creates questions; source/JAR evidence decides implementation claims.

| Behavior hint | Secondary source | Track | Engineering evidence/result | State |
|---|---|---|---|---|
| Normal catalyst starts a Nexus invasion; Nexus becomes the objective | 9Minecraft historical guide | legacy 1.7.10 | \`TileEntityNexus.updateStatus -> startInvasion(1)\`; active Nexus returns -1 relative hardness; \`EntityAIAttackNexus\` damages the exact bound Nexus | EVIDENCE_BACKED |
| Strong catalyst jumps to a harder start | guide/current wiki | legacy + current | legacy \`startInvasion(10)\`; current behavior kept separate | EVIDENCE_BACKED for legacy |
| Stable catalyst creates continuing night attacks | 9Minecraft / current wiki | legacy | \`startContinuousPlay\`, next attack anchored near world time 14000 and randomized configured day interval; dynamic 240s wave generator | EVIDENCE_BACKED |
| Pig Engineer bridges gaps and builds vertical access | 9Minecraft reference / old forum | legacy | \`EntityIMPigEngy\`, \`NavigatorEngy\`, \`TerrainBuilder\`, \`AttackerAI\`, \`Scaffold\` | EVIDENCE_BACKED |
| Other invaders benefit from engineer structures | community reference | legacy | \`EntityAIWaitForEngy\`, helper support, shared physical blocks, no-Nexus-path engineer targeting | EVIDENCE_BACKED |
| Mobs attack fortifications rather than fail on walls | old forum / guide | legacy | destructible cells are legal path states; DIG/action callbacks and TerrainDigger clear collision region | EVIDENCE_BACKED |
| Attacks can arrive from a concentrated side | guide gameplay behavior | legacy | \`WaveEntry\` stores min/max angle; spawn points store angle to Nexus; sector has fallback/reselection | EVIDENCE_BACKED |
| Constructed stone becomes stronger when connected | historical guide | legacy | \`EntityIMLiving.getBlockStrength\` adds 10% per matching orthogonal neighbour | EVIDENCE_BACKED |
| Current releases add death-zone intelligence / strip mining | CurseForge 3.0.0 notes | modern distribution | treated as FRONTIER reconnaissance only; corresponding public source revision for 3.0.0 not proven | DISCOVERED_NOT_SOURCE_BOUND |

## Preserved disagreement: construction bonus

The historical guide describes stone-family strength as base 5.5 with a maximum presented as 8.25 (+50%). The pinned 1.7.10 source checks **six** orthogonal neighbours (up, down, ±X, ±Z), each adding 10%, so the implementation can calculate 5.5 × 1.6 = **8.8** when all six qualifying neighbours exist.

Engineering conclusion: the guide is useful to discover the mechanic, but the pinned source controls the implementation claim. The discrepancy is retained instead of averaging or silently selecting the guide.

Source:
https://github.com/UnstoppableN/Invasion-mod/blob/644a52ddea104c206d022bef9edc135c060cba1d/src/main/java/invmod/common/entity/EntityIMLiving.java#L1510-L1558

## Search terms produced by reconnaissance

- Nexus Catalyst / Stable Nexus Catalyst / Strong Catalyst
- Pigman Engineer, bridge, ladder, scaffold, tower
- destructed-blocks-drop / block strength
- invasion wave / continuous mode / spawn radius
- bound player / Nexus destroyed
- blocked path / no Nexus path
- death zone / strip mining (modern-only lead)
