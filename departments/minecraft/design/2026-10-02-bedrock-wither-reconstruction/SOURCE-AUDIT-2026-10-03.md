# Referenced-source audit and software completion boundary

Audited: 2026-10-03. This pass reads the linked material itself, rather than treating the previous handoff's UNKNOWN labels as proof that sources have no answer.

## Corrected conclusion

The earlier conclusion that all remaining work required measurement was too broad. Several documented behaviors were absent from the ordinary production path: phase-1 repositioning, phase-2 firing/alternating charge, and the second official armor layer. Public projectile defaults and historical native arithmetic also contained information the handoff had not resolved correctly.

The user chose to finish source-backed code without empirical Bedrock measurements. The retained source set therefore defines executable, explicitly labelled reconstruction policies. Full current-version empirical identity is not claimed. The code-completion plan and acceptance document govern that endpoint.

## Evidence classes

1. **Official exposed contract:** pinned Mojang definitions or public component semantics. Exact exposed values can be used without measuring them again. Engine-specific interpretation still needs an explicit adapter.
2. **Documented/historically corroborated behavior:** retained technical reports and historical native bodies can define labelled reconstruction behavior. They are not current BDS function-body proof.
3. **Unresolved current native detail:** the retained source does not establish the current value/equation, or source versions disagree. Use a bounded, named source-derived/adaptation policy for software completion and state its consequence.

## Item-by-item findings

### Movement

The [dedicated official goal](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_wither_random_attack_pos_goal?view=minecraft-bedrock-stable) exposes priority and control flags, not a radius or timer. Current generated goal headers provide inheritance and fields, not initializers.

[Historical movement body](https://github.com/PeratX/source/blob/ea30a251dd8fd16a7bd2e568209797a9c7be970f/Minecraft/Goal/WitherRandomAttackPosGoal.c) is more informative than the previous summary: choose a random horizontal direction, normalize, offset around the target by inherited XZ distance, preserve the boss's Y; start multiplies flight speed by 15 and stop sets shot delay 20. Its constructor receives the radius rather than defining it. Ordinary random-stroll XZ=10 is a source-labelled fallback, not proof of the dedicated goal's initialized value. Its interval=120 means a random attempt probability, not a guaranteed fixed 120-tick period.

The source is sufficient to implement an ordinary bounded reposition path. It is not sufficient to claim the exact current destination distribution or flight trajectory.

### Firing

[BedrockWiki revision 692](https://bedrockwiki.com/books/mobs/page/wither-boss/revisions/692/changes) describes 3 normal + 1 dangerous shots, an approximately seven-second cycle gap and approximately fifteen-second passive dangerous fire. It does not define a precise modern accelerated-rate table or passive-head attribution.

[Entity-format revision 2689647](https://minecraft.wiki/w/Bedrock_Edition_level_format/Entity_format?oldid=2689647#Wither) distinguishes within-volley `firerate` from the gap between volleys. The old Java code added `fireRate` after its 140-tick gap, coupling the two. That is a source-backed software issue without needing a new Bedrock observation.

Historical interval arithmetic was wrongly recorded as maxHP/3. [Actual native instructions](https://github.com/PeratX/source/blob/ea30a251dd8fd16a7bd2e568209797a9c7be970f/Minecraft/Entity/WitherBoss.c#L1773-L1778) use signed multiply-high by 715827883, giving maxHP/6: Easy 50, Normal 75, Hard 100. The damage block skips Easy, crosses a strict threshold, halves once per damage event and advances its cursor once. Later odd-value rounding remains a Java adaptation. The first 20→10→5 sequence is unambiguous. Keep the documented 75-HP NBT bucket separate; its possibly Normal-only provenance is not established.

### Blue-skull reflection and travel

[Pinned dangerous-skull JSON](https://github.com/Mojang/bedrock-samples/blob/46ba6ea985fb5a92d79a9419198f10dda14c199d/behavior_pack/entities/wither_skull_dangerous.json) explicitly enables reflection, launch power 0.6, gravity 0 and both inertias 1.0. The normal skull uses power 1.2 and omits reflection.

[Official projectile semantics](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitycomponents/minecraftcomponent_projectile?view=minecraft-bedrock-stable) give a zero-second default reflection immunity and five-tick owner launch immunity. From 1.26.0 other projectiles can reflect a reflectable projectile on hit, independently of damage. The pinned entity format 1.26.50 is compatible with that documented floor. These configured defaults were not wholly unknown.

[Historical reflection body](https://github.com/PeratX/source/blob/ea30a251dd8fd16a7bd2e568209797a9c7be970f/unmapped/ProjectileComponent.c#L1734) obtains and normalizes the hitter's view vector, applies unit motion and transfers ownership. Current headers expose a separate reflection helper and last-reflector state. Exact current vector/repeated-reflector semantics remain unproved; a retained Java vector policy must be named as such.

Actual Forge 1.20.1 bytecode inspection additionally found adaptation defects: the custom `onHit` override skipped direct entity dispatch, and inherited water travel multiplied velocity by 0.8. Real-tick collision/liquid tests, rather than direct protected-method calls, expose these paths.

### Dash and half-health transition

The [retained 2025-11 MinecraftWiki snapshot](https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/Wither#Bedrock_Edition) describes continued phase-2 firing, charging after alternate bursts, and ground descent before the half-health explosion. The old implementation disabled phase-2 volley processing and had no ordinary caller of the dash entry point.

Revision 692 independently supports half-health shield/summoning, approximately 20 active charge ticks, 6×8×6 destruction each active tick and phase-2 projectile immunity. It does not give the alternating-burst rule or exact ground-impact ordering.

The [historical charge body](https://github.com/PeratX/source/blob/ea30a251dd8fd16a7bd2e568209797a9c7be970f/Minecraft/Entity/WitherBoss.c#L3086-L3158) supplies preparation 20, damage 15 and active counter 10. The latter disagrees with the accepted technical report's approximately 20, so keep the reported 20 policy and retain the discrepancy. The motion fragment doubles stored X/Z direction components; its damaged branch formatting does not prove a full modern 3-D velocity or collision-stop equation.

The snapshot distinguishes obsidian-resistant charge from dangerous-skull destruction. A shared unconditional eligibility rule omitted that documented attack-specific exception.

### Shield and death

[Pinned official armor controllers](https://github.com/Mojang/bedrock-samples/blob/46ba6ea985fb5a92d79a9419198f10dda14c199d/resource_pack/render_controllers/wither_boss_armor.render_controllers.json) explicitly specify white and blue layers, UV functions, partial-tick input and unlit rendering. The blue layer can be implemented from that source. Texture-byte parity remains outside the Java substitute asset policy.

The entity-format reference states native Phase=0 during death and distinguishes that diagnostic field from AirAttack-driven visibility. It still lists ShieldHealth as unknown. The old controller preserved native Phase=1 when killed in the first phase.

Historical Wither code contains a 200-tick death countdown, final power-7 explosion, swell +1, overlay +0.005 and a 15-based decreasing shield-flicker divisor. These can serve as explicitly historical execution policies. The exact modern total duration, internal ShieldHealth meaning and XP timing are not established by current headers. Preserve Forge semantic-death/event/reward compatibility; do not delay or duplicate ordinary rewards to imitate an old body.

## Actual read coverage and access limits

Read directly in this audit:
- Microsoft Wither JSON, unique behaviors, dedicated movement goal and projectile component documentation
- Pinned Mojang Wither and both skull JSON files; client entity, body animation and both render-controller files
- Current pinned LeviLamina Wither/goal/projectile definitions and server/client death-system headers
- Full historical WitherBoss body with relevant constructor, reload, damage, phase, volley and death sections; historical movement and reflection bodies
- BedrockWiki revision 692 `/changes`; MinecraftWiki entity-format Wither section; retained ronlab entity-format and Wither snapshot; `mcbe-leveldb@1.21.0` descriptions
- Reddit `1ruly4a` reflection discussion and `1w2ijls` downward-burrowing discussion as discovery evidence only

The direct entity-format response identifies oldid2689647 (2024-09-17 edit). Ronlab explicitly identifies its 2025-11 snapshot. Neither is current 1.26.51 native-body evidence. Repeated descriptions in `mcbe-leveldb` are not independent measurements.

The live MinecraftWiki Wither page, some BedrockWiki non-`/changes` routes and Reddit `1wsezmj`, `1skc28g`, `1wqum13` could not be fetched in this pass. Reddit video frames were not inspected and no timers or trajectories were derived from them. No direct Bedrock, live client or Tank measurements were performed.


## Final official-persistence checklist

The pinned entity definition contains `minecraft:persistent: {}`. The independent Java Monster inherited distance/idle-random despawning until the completion checklist exposed the missing species-level override. Forge's actual `Mob.checkDespawn` checks custom persistence after its Peaceful branch; `Mob.readAdditionalSaveData` overwrites the ordinary persistence flag from NBT. Therefore the adopted adapter is species-level custom persistence, including older saves with `PersistenceRequired=false`, while preserving ordinary Peaceful removal. The regression uses an actual registered distant player and the real despawn check on new and NBT-restored bosses.
