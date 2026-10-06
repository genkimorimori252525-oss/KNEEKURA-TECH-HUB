# Technique VFX Atlas — Jujutsu Verse V8.1

Status: **STATIC EXACT-JAR ANALYSIS; runtime NOT_RUN**

This atlas is presentation-centric. It records how each named player technique is staged: motion topology, authoritative actor/hit logic, visual primitive, player/entity animation, camera/sound, and evidence confidence.

## Evidence labels

- **DIRECT** — the named UI move is connected to exact Procedure/entity/resource behavior in the V8.1 JAR.
- **DIRECT_FAMILY** — exact visual family is evidenced, but several UI variants share one actor/state machine.
- **DIRECT_SYSTEM** — the move is primarily control/state behavior rather than a standalone visual attack.
- **PARTIAL** — the UI identity is known but its complete standalone visual branch is not isolated enough to claim more than the shared family.

## Visual primitive vocabulary

- **Actor** — a persistent synchronized entity owns technique state.
- **Analytical path** — a Procedure samples mathematical positions instead of vanilla projectile physics.
- **Client reconstruction** — compact synchronized state becomes dense trails/geometry on the client.
- **PostFX** — screen-space shader chain.
- **Render-layer/Mixin** — modifies ordinary model rendering.
- **GUI cinematic** — overlay composition separate from world geometry.
- **FBO surface** — an off-screen scene is composited onto blocks.

## Yuji Itadori

| Technique | Trajectory / staging | Visual / actor layer | Animation / camera / sound | Evidence |
|---|---|---|---|---|
| Manji Kick | melee step-in | player body animation, no projectile | manji_keri 0.6667s; charge_manji; no-knockback punch | DIRECT |
| Divergent Fist | delayed hit layered on punch | CURSEDENERGYBLUE + delayed UUID/tick/hit state | divergent_fist 1.25s; Breakwallblock; wither-shoot cue | DIRECT |
| Sukuna | character/state transition | SUKUNA_EFFECT/state path | bell/character-transition cues; exact standalone VFX not isolated | PARTIAL |
| Extreme Focus | self-buff cinematic | BLACK_FLASH_RATEUP, no attack actor | extreme_focus_1 3.25s; low_sound; special-gauge gate | DIRECT |

## Nobara Kugisaki

| Technique | Trajectory / staging | Visual / actor layer | Animation / camera / sound | Evidence |
|---|---|---|---|---|
| Diffuse Throwing Nails | spread nail-throw family | nail actor path | diffuse_throwing_nails 1s; anvil/place cue | DIRECT_FAMILY |
| Hairpin | remote nail detonation | Nail_tick: CURSEDENERGYBLUE + explosion + lightning_short | finger-snap charge; heirpin tag; heirpindamage | DIRECT |
| Resonance | target-linked curse strike | dedicated ResonanceEntity Geo model + target/UUID/amount state | Tomonari-style Geo animation ~1.5s hold | DIRECT |
| Sharp Strike | close nail/hammer strike | NAILENITTYANIMATED + camera/state integration | sharp_strike 1.75s; nail_hit/source tags | DIRECT |

## Toge Inumaki

All seven commands reuse cursed_speech1 0.75s, beep audio and the target-anchored Ripple PostFX, while the gameplay payload changes.

| Technique | Payload / world response | Evidence |
|---|---|---|
| Don't Move | STUN | DIRECT |
| Blast Away | BreakblocksLevel3 + strong knockback + explosion | DIRECT |
| Explode | glass/block break + cursed-speech damage + explosion | DIRECT |
| Get Twisted | STUN + cursed-speech damage; punch4-style hit cue | DIRECT |
| Get Crushed | STUN + cursed-speech damage; punch1-style hit cue | DIRECT |
| Crumble Away | BlockDestruction + STUN + cursed-speech damage | DIRECT |
| Die | high-impact damage escalation; creeper-primed cue | DIRECT |

The ripple itself is not a particle cloud. RippleEffectManager projects the target LivingEntity from world space into normalized screen space and drives a PostChain with Intensity 1.2, WaveCount 8 and WaveSpeed 6, or 20 in cancel mode.

## Yuta Okkotsu

| Technique | Presentation family | Evidence |
|---|---|---|
| Come!! Rika!! | RIKA_ORIMOTO / RIKA_INPERFECT / RIKA_CULLING_GAME actors + WATERBLACKPARTICLE; rika_call1/2; thunder/electric | DIRECT |
| Return Rika | persistent Rika UUID/state dismissal/reposition; electric cue | DIRECT |
| Match my movements, Rika | MATCH_MY_MOVEMENTS_RIKAEFFECT + sword/player pairing; match_up_rika | DIRECT |
| Rika, let's do that | Rika shared coordination state | PARTIAL |
| Pure Love | PURELOVEENTITY + BeamRenderer/VFXRenderer client reconstruction; it_is_pure_love; sparks/lightning; block break/explosion | DIRECT |
| come, rika | RIKA_EFFECT transition | PARTIAL |
| Return Rika (alternate command) | RIKA_EFFECT transition | PARTIAL |
| Drop it!! Rika!! | Rika target/command state | PARTIAL |
| Which one do you want? | copy-selection system, not a projectile VFX | DIRECT_SYSTEM |
| Let's go Rika | PURELOVEENTITY target/teleport/camera state; lets_go_rika hold | DIRECT |

## Satoru Gojo

| Technique | Trajectory / staging | Visual implementation | Evidence |
|---|---|---|---|
| Infinity | persistent defense/interception | INFINITY effect; infinity_use 1s; motion/interaction interception instead of visible projectile | DIRECT |
| Lapse: Blue | moving vacuum field | BLUEENTITY; synchronized radius/yaw; BLUEPARTICLE_1/2/3; vacuum vectors; sphere/block operations; screen shake | DIRECT |
| Maximum Output Blue | larger/stronger Blue state | same BLUEENTITY family with Blue2/radius escalation | DIRECT_FAMILY |
| Reversal: Red | repulsive blast | REDPARTICLE_1/2; knockback; block destruction; explosion; reversal_red_1/2/3; camera/screen shake | DIRECT |
| Hollow Purple | persistent destructive field/projectile | HOLLOW_PURPLE_2/HOLLOWPURPLE + HOLLOWPURPLEPARTICLE; large entity query; purple damage; glass/block destruction | DIRECT |
| Unlimited Void | sealed domain | UNLIMITEDVOIDENTITY + CUSTOM_PORTAL/FBO surface + Unlimited Void particles; domain animation/cut-in | DIRECT |

Blue and Purple are not ordinary arrow-like projectiles. Their actors own state and area logic over time.

## Toji Fushiguro

| Technique | Presentation | Evidence |
|---|---|---|
| Thrust Attack | item animation + SlashActive + block destruction/screen shake | DIRECT_FAMILY |
| Double Attack | multi-hit item/punch/slash chain; stun/neutralization windows | DIRECT |
| Combo Attack | longer combopunch/comboslash chain with block destruction | DIRECT |

The visual vocabulary is weapon/body animation plus impact/world response rather than large particle systems.

## Jogo

| Technique | Trajectory / visual | Animation / sound | Evidence |
|---|---|---|---|
| Jump Attack | ballistic leap -> impact; SMOKEPARTICLE_3; sphere block hit | jump/land; block_break/explosion; screen shake | DIRECT |
| Eerie Flame | FIRE_ENTITY + FIREPARTICLE_1/2; block-fire destruction | jogo_technique_1; fire cues; camera | DIRECT |
| Piercing Flame | repeated FIRE_ENTITY rapid-fire shots | machinegun/machinegun_2; side_counter | DIRECT |
| Volcanic Eruption | VOLCANICROCK projectile/emitter -> FIRE_ENTITY | jogo_technique_3 | DIRECT |
| Ember Insects | EMBERINSECT target_UUID homing swarm -> explosion/fire hit | primed/explosion cues | DIRECT |
| Molten Sea | WATERENTITY reused as area-fluid carrier via Sea_Type | lava pop/ambient; screen shake | DIRECT |
| Sapphire of the Flame | large held/released FIRE_ENTITY state | jogo_technique_5 92.2917s hold -> _6 1.5s | DIRECT |
| Coffin of the Iron Mountain | JOGODOMAINBLOCK + JOGODOMAINENTITY | domain hold/transition/idle + Geo expansion/loop | DIRECT |
| Maximum: Meteor | METOR + OPEN_PARTICLE; spherical fire/block destruction; vacuum/impact | maximum_meteor1 hold -> _2 release; camera/explosion | DIRECT |
| Maximum Meteor Small | same METOR pipeline with variant scale/state | same charge/release family | DIRECT |

## Hanami

| Technique | Trajectory / visual | Evidence |
|---|---|---|
| Flower Field | FLOWERSPARTICLE area-status field; STUN/CONFUSION | DIRECT |
| Wooden Ball / Spear | WOODBALL; ParabolicMotion; attack/attack2; may spawn SEEDOFCURSE; flower_beam_particle | DIRECT |
| Roots | TREESPIKE + SMOKEPARTICLE_2; emerge/dive Geo animation | DIRECT |
| Cursed Bud | SEEDOFCURSE + SEEDOFCURSEEFFECT | DIRECT |
| Offering Flowers | SEEDOFCURSEBOUQUET with emerge/dive/idle model animation | DIRECT |
| Shining Sea domain | HANAMIDOMAINBLOCK + CUSTOM_PORTAL_2 + 50-bone/192-cube HANAMIDOMAINTREE; flower sure-hit | DIRECT |

Woodball is an especially useful reusable pattern: its parabolic gameplay motion, Geo animation, impact response and flower-beam particle are separate layers.

## Mahito

| Technique | Trajectory / visual | Evidence |
|---|---|---|
| Idle Transfiguration | contact/soul effect; IDLE_TRANSFIGURATIONEFFECT + idle_transfigurationdamage + CURSED_ENERGYPURPLE | DIRECT |
| Modified Human | TRANSFIGUREDHUMAN summoned actor + purple cursed-energy presentation | DIRECT |
| Body Repel | BODYREPELSMALL/BODYREPEL with Motion_x/y/z and impact logic | DIRECT |
| Self-Embodiment of Perfection | two symbolic domain actors; primary hand model 116 bones/234 cubes; 3s start; purple sure-hit | DIRECT |

## Kento Nanami

| Technique | Visual implementation | Evidence |
|---|---|---|
| Ratio Technique | common Attackhit1 resolver emits RATIOPARTICLE_1 and RATIOPARTICLE_2 when Ratio state qualifies; uses ratiodamage | DIRECT |
| Overtime | OVERTIME_EFFECT self-buff; overtime player animation exists; no projectile required | DIRECT |
| Collapse | STONE actor + stone_type/material block-break presentation; garagara start/idle | DIRECT |

## Ryomen Sukuna

| Technique | Trajectory / visual | Evidence |
|---|---|---|
| Dismantle | DISMANTLEENTITY_2 + analytical path sampled in 0.5-unit steps; damage and block-cut resolvers separated | DIRECT |
| Cleave | CLAVE_PARTICLE + freeze/look positioning + close slash; camera/stun/screen shake | DIRECT |
| Malevolent Shrine | MALEVOLENT_SHRINE symbolic actor + repeated Dismantle actors at varied yaw + CLAVE_PARTICLE; separate open attack field | DIRECT |
| Divine Flame — Open | OPEN_ENTITY -> OPEN_ENTITY_2 staged fire/explosion; FLAME_OAB + procedural Fuga topology | DIRECT |

FugaFlameParticleProcedure is mathematical rather than random scatter: base radii 35 and 80, 12/20 ring samples, trigonometric phase/noise and six radial branches.

## Megumi Fushiguro

Every shikigami uses WATERBLACKPARTICLE as a common shadow-summoning language, but each summoned actor owns its own AI and animation set.

| Technique | Actor / presentation | Evidence |
|---|---|---|
| Divine Dog | DIVINEDOGWHITE/BLACK; idle/sprint/attack Geo animation | DIRECT |
| Nue | NUE; flying actor | DIRECT |
| Toad | TOAD; idle/sprint/attack | DIRECT |
| The Well's Unknown Abyss | THEWELLSUNKNOWNABYSS; sprint/idle/attack/fly | DIRECT |
| Great Serpent | GREAT_SERPENT; attack/dive/dive2/leap; impact cues | DIRECT |
| Rabbit Escape | RABBIT_ESCAPE swarm/distraction; long summon hold + release | DIRECT |
| Max Elephant | MAX_ELEPHANT; locomotion/fall/landing/water animations; can spawn WATERENTITY | DIRECT |
| Chimera Shadow Garden | CHIMERASHADOWGARDEN field actor; incomplete-domain path; 15 bones/82 cubes; 1s spawn + 2s loop | DIRECT |

## Choso

| Technique | Trajectory / visual | Evidence |
|---|---|---|
| Convergence | CONVERGENCE_ENTITY persistent blood reservoir/preparation state | DIRECT |
| Piercing Blood | PIERCINGBLOODENTITY for logic + dedicated client tube renderer: 20 longitudinal segments, thickness 0.04, UUID-linked source | DIRECT |
| Slicing Exorcism | dedicated spinning SLICING_EXORCISM actor | DIRECT |
| Blood Meteorite | BLOOD_METEORITE + BloodMeteorite_power state | DIRECT |
| Flowing Red Scale | self-buff FLOWING_RED_SCALE state | DIRECT |
| Flowing Red Scale: Stack | stronger state in same presentation family | DIRECT_FAMILY |
| Sea of Blood | WATERENTITY reused via Sea_Type as area-fluid carrier | DIRECT |
| Supernova | SUPERNOVA_PARTICLE + BLOODPARTICLE; freeze/stun/block destruction/screen shake | DIRECT |

Piercing Blood demonstrates the strongest hitbox/render separation in the kit: the logical projectile moves independently while the client draws a continuous tube from source to projectile.

## Masamichi Yaga

| Technique | Presentation | Evidence |
|---|---|---|
| Discipline | jump-punch physical hit + Breakwallblock | DIRECT |
| Return to Inventory | cursed-corpse release/inventory state | PARTIAL |
| Target him! | target_UUID assignment/control | DIRECT_SYSTEM |
| Advance! My Cursed... | yaga_ult 3s command/ultimate animation | DIRECT |

## Naobito Zenin

| Technique | Presentation | Evidence |
|---|---|---|
| Barrage | rush_projection melee chain + Breakwallblock | DIRECT |
| Projection Sorcery | PROJECTION_SORCERY_ENTITY + recorded positions/projection_number + glass-break framing; 24 run_N hold-frame clips | DIRECT |
| We'll Crush You With... | PROJECTIONFLAME + teleport sync + stun + targeted punch/kick/rush chain | DIRECT |

Projection Sorcery also uses ProjectionFreezeMixin plus vanilla-render, Gecko-render and culling mixins. The technique changes rendering/time-frame rules rather than merely adding particles.

## Aoi Todo

| Technique | Presentation | Evidence |
|---|---|---|
| Boogie Woogie | instant positional swap; BOOGIE_WOOGIE + TeleportSYNC + CURSEDENERGYBLUE; clap_todo | DIRECT |
| Stone Throwing | STONE actor + CURSEDENERGYBLUE; 3s throwing animation | DIRECT |
| Are you satisfied with that? | FIRE_STONE_ENTITY + LASER finisher; beam_type; Black Flash/increased-damage states | DIRECT |

## Dagon

| Technique | Presentation | Evidence |
|---|---|---|
| Disaster Tides | WATER_BALL -> WATERENTITY; water_level/Sea_Type | DIRECT |
| Defence from Water | DEFENCEFROMWATER state, no projectile required | DIRECT |
| Death Swarm [1] | FISH_1 + FISH_3 homing actors | DIRECT |
| Death Swarm [2] | FISH_2 + FISH_3 + WATER_SPLASH_PARTICLE | DIRECT |
| Horizon of the Captivating Skandha | DOMAIN_GRASS + CUSTOM_PORTAL_3 + PALM_TREE; fish sure-hit | DIRECT |
| Death Swarm [3] | FISH_1/2/3 + water splash + screen shake/explosion | DIRECT |

## Ryu Ishigori

| Technique | Presentation | Evidence |
|---|---|---|
| Granite Blast | LASER actor; BeamRenderer reconstructs history/trail/caps/spikes from synchronized state | DIRECT |
| Granite Blast [2] | LASER with alternate beam_type/type | DIRECT |
| Have A Seat at Our Table | stronger LASER variant + screen shake/increased damage | DIRECT |

The long Granite Blast hold clips (68.0417s and 79.7917s) hand off to short release clips while LaserTick owns collision/block interaction and the client renderer owns dense beam geometry.

## Cross-technique conclusions

1. **There is no universal projectile template.** Dismantle is sampled geometry, Fuga is trigonometric topology, Piercing Blood separates projectile logic from tube rendering, Blue/Purple are persistent fields, Granite Blast is a client-reconstructed beam, and shikigami are full AI actors.
2. **Charge / hold / release is a visual grammar.** Long PlayerAnimator clips preserve a pose while short transition clips hand control to technique actors.
3. **Visual identity is shared per kit, not globally.** Megumi shares shadow particles, Choso shares blood/convergence state, Jogo shares fire semantics but changes topology, and domain users share lifecycle/cut-in while keeping unique environments.
4. **Hit logic and visible geometry are often different systems.** Piercing Blood, Black Flash, BeamRenderer and Projection Sorcery make this explicit.
5. **Cinematics observe combat state.** Domain cut-ins, camera effects, screen shake and PostFX do not own authoritative damage resolution.

## Static-analysis boundary

Runtime interpolation quality, exact frame pacing, z-fighting, client FPS cost and multiplayer latency have not yet been observed in a live client. PARTIAL rows should only be promoted after deeper bytecode tracing or runtime capture.