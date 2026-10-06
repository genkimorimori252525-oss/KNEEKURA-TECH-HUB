# Player Animation Atlas — Jujutsu Verse V8.1

The exact JAR contains **121 GeckoLib animation JSONs** plus a large PlayerAnimator technique resource. The most important presentation pattern is **hold -> release -> idle**. Long animation lengths are frequently holdable pose/state tracks rather than literal one-shot cinematics.

## High-value PlayerAnimator sequences

| Family | Charge / hold | Release / transition | Idle / follow-up | Engineering note |
|---|---:|---:|---:|---|
| Unlimited Void | unlimited_void1 — 88.0833s | unlimited_void2 — 0.125s | unlimited_void3 — 3s | player pose remains separate from authoritative domain state |
| Jogo Domain | jogo_domain_expansion — 88s | jogo_domain_expansion2 — 0.1667s | jogo_domain_expansion3 — 3s | same grammar with a different environment actor |
| Mahito Domain | mahito_domain_expansion — 88s | mahito_domain_expansion2 — 0.25s | mahito_domain_expansion3 — 3s | hand-domain actor is independent |
| Malevolent Shrine | malevolent_shrine1 — 88.0833s | malevolent_shrine2 — 0.1875s | malevolent_shrine3 — 3s | shrine Geo actor also owns spawn/collapse animation |
| Megumi Domain | megumi_domain_expansion — 80.2917s | megumi_domain_expansion2 — 0.25s | megumi_domain_expansion3 — 3s | field actor has separate spawn/idle |
| Dagon Domain | dagon_domain_expansion — 80.2917s | dagon_domain_expansion2 — 0.25s | dagon_domain_expansion3 — 3s | environment and fish sure-hit are separate |
| Divine Flame | open_animation_1 — 95.9167s | open_animation_2 — 0.25s | OPEN_ENTITY runtime | staged actor owns post-release visuals |
| Jogo Sapphire | jogo_technique_5 — 92.2917s | jogo_technique_6 — 1.5s | FIRE_ENTITY runtime | long charged-fire pose |
| Maximum Meteor | maximum_meteor1 — 80.0833s | maximum_meteor2 — 1.5s | METOR runtime | projectile owns motion/impact after release |
| Granite Blast | granite_blast_1 — 68.0417s | granite_blast_2 — 1.5s | LASER runtime | beam geometry is client-reconstructed |
| Granite finisher | granite_blast_3 — 79.7917s | granite_blast_4 — 2s | LASER runtime | stronger beam variant |
| Piercing Blood | piercing_blood_3 — 88.5s | piercing_blood_end — 0.25s | tube renderer follows projectile | long aiming/hold phase |
| Rabbit Escape | rabbit_escape_1 — 52.0833s | rabbit_escape_2 — 1s | rabbits continue as actors | summon pose is independent of AI |

## Short technique clips

Examples include Manji Kick 0.6667s, Divergent Fist 1.25s, Cursed Speech 0.75s, Rika calls 1.5s, Reversal Red 1.25–1.5s, Hollow Purple 5s, Flower attacks about 0.64–4.49s, Body Repel 1s, Dismantle 0.5833s, Cleave 1.75s, Convergence 1.75s, Slicing Exorcism 1.3333s, Supernova 2.5s, Hairpin 2s, Projection punches/kicks 0.5–0.75s and Boogie Woogie 0.5s.

## Geo-actor animation examples

- Malevolent Shrine: 103-bone / 485-cube model; 2.75s spawn animates 54 bones; 1.5833s collapse animates 66.
- Self-Embodiment of Perfection: 116-bone / 234-cube primary model; 3s start + 0.25s loop.
- Hanami domain tree: 50 bones / 192 cubes.
- Chimera Shadow Garden: 15 bones / 82 cubes; 1s spawn + 2s loop.
- Projection Sorcery frame actor: run_1 through run_24 hold-frame animations.
- Divine Dog, Nue, Toad, Great Serpent and Max Elephant each have distinct locomotion/attack animation sets.

## Engineering extraction

Keep **player pose state**, **technique actor state** and **world VFX state** separate. A held player animation should not be the authoritative clock for projectile/field physics.