# Domain Visual Atlas — Jujutsu Verse V8.1

This is the presentation counterpart to DOMAIN-CLASH-AND-CUTIN.md. The shared battle lifecycle is not repeated here; the focus is how each domain builds a distinct visual space.

## Shared stack

The simultaneous-domain cut-in is shared. The simulation and cinematic remain separate. Sealed domains use character-specific interior/surface materials plus DOMAINBLOCKBARRIER; symbolic Geo actors are spawned independently and sure-hit presentation is dispatched separately.

| Domain | Environment / surface | Symbol actor | Sure-hit / active visual | Notes |
|---|---|---|---|---|
| Unlimited Void | CUSTOM_PORTAL + barrier; live FBO-backed surface | UNLIMITEDVOIDENTITY, 10 bones / 72 cubes | UNLIMITEDVOIDPARTICLE_2/3 + STUN/Unlimited Void state | environment is compositing, not only a static texture |
| Coffin of the Iron Mountain | JOGODOMAINBLOCK + barrier | JOGODOMAINENTITY, 10 bones / 45 cubes; renderer scale ~14 | fire/Jogo hit semantics | 1s Geo expansion hold + 1s loop |
| Hanami / Shining Sea | HANAMIDOMAINBLOCK + CUSTOM_PORTAL_2 + barrier | HANAMIDOMAINTREE, 50 bones / 192 cubes | FLOWERSPARTICLE / flower hit | forest floor, portal surface and tree are separate layers |
| Self-Embodiment of Perfection | generic DOMAINBLOCKIN + barrier | SELFEMBODIMENTOFPERFECTION + _2 | CURSED_ENERGYPURPLE + idle-transfiguration hit | primary model 116 bones / 234 cubes with 3s start |
| Malevolent Shrine | open-field-style presentation; symbolic shrine separate from attack field | MALEVOLENT_SHRINE, 103 bones / 485 cubes | CLAVE_PARTICLE + repeated Dismantle actors; Fuga/fire branch can participate | 2.75s spawn + 1.5833s collapse |
| Chimera Shadow Garden | incomplete-domain path rather than ordinary sealed material mapping | CHIMERASHADOWGARDEN, 15 bones / 82 cubes, bounds 14 x 11.5 | shadow/shikigami-oriented field | explicit incomplete-domain advancement evidence; 1s spawn + 2s loop |
| Horizon of the Captivating Skandha | DOMAIN_GRASS + CUSTOM_PORTAL_3 + barrier | PALM_TREE, 10 bones / 44 cubes, large bounds | FISH_2/FISH_3 + water/fish hit | beach environment and fish swarm are independent |

## Portal / FBO surfaces

CustomPortalBlockEntityRenderer owns a window-sized TextureTarget and renders a domain scene off-screen before the portal shader samples it in screen space. CustomPortal2 has a separate render type/texture path; CustomPortal3 is a third environment variant. The result is a domain surface that can show a separately rendered scene rather than a normal animated block texture.

## Domain cut-in

DomainCutinOverlay:

- detects early-domain users within roughly 50 blocks,
- locks participants to stabilize layout,
- supports two-way diagonal and three-way panel composition,
- draws about 1,200 time-driven procedural line elements per panel,
- uses depth-buffer writes as a stencil-like panel mask,
- renders the actual LivingEntity model into GUI space.

**Boundary:** three-way cut-in support is presentation cardinality. Battle state still contains a singular Domain_battle_uuid and does not prove a centralized symmetric N-way solver.

## Destruction / exit

Domain teardown is scheduled progressively rather than erasing the full sphere in one server tick. Malevolent Shrine also owns a dedicated model collapse animation. Reusable layers should remain separate:

1. winner/loser state,
2. sure-hit shutdown,
3. environment cleanup,
4. symbolic actor exit animation,
5. player cooldown/burnout.