# Rendering and effects deep dive

Jujutsu Verse's visual strength comes from multiple rendering primitives rather than one large particle system.

## A. Particles

There are 50 particle definition files.

ParticlePacketMixin targets ClientboundLevelParticlesPacket.isOverrideLimiter and forces true.

Benefit:
- forced server particles stay visible.

Risk:
- particle-heavy scenes can bypass the normal client limiter.

## B. Custom world geometry

### Black Flash

BlackFlashRenderer runs at AFTER_TRANSLUCENT_BLOCKS.

It finds BlackflashEntityEntity instances during their first ~20 ticks and procedurally builds:
- seeded jagged brush strokes
- multi-layer explosive ribbons
- red/dark width and alpha layers
- round sparks

Deterministic seeds give chaotic-looking geometry without unrelated per-frame flicker.

### BeamRenderer

BeamRenderer.BeamClientEvents maintains a trailMap keyed by entity ID.

Tracked actors include:
- PureloveentityEntity
- FireEntityEntity
- LaserEntity

Laser synchronized state includes RGBA, charge/fire, curve, lock and max length.

Client TrailData stores start/end positions, history, scale queues, color/alpha, curve/fire/charge state, fade state and random seed. The renderer builds billboard beams, history beams, caps and spikes locally.

### VFXRenderer

VFXRenderer.VFXClientEvents runs at AFTER_TRANSLUCENT_BLOCKS and stores UUID-keyed OrbData/OpenVFXData caches.

OrbData includes trail history, ray parameters, spark positions/velocities/scales and explosion state.

OpenVFXData includes fountain paths, ascending sparks, colored streak parameters, pillar parameters and fog parameters.

Drawing helpers include:
- soft glow
- volumetric beams
- colored/trail ribbons
- smooth fire streams
- pillar streams

## C. Model/render-layer augmentation

DomainAmplificationRender attaches a layer to all player skins and available LivingEntity renderers.

It is gated by DOMAIN_AMPLIFICATION and uses a full-bright glint-like path.

Observed palette:
- normal: cyan-like (0, 0.784, 1)
- cursed spirit: purple-like (0.439, 0, 0.6)

UniversalAuraMixin wraps vanilla LivingEntityRenderer.
GeckolibAuraMixin wraps GeckoLib GeoEntityRenderer.

Both use shared AuraRenderUtils/AuraRenderType, giving one aura mechanism across renderer families.

## D. Target-anchored post processing

RippleEffectManager owns a PostChain based on shaders/post/entity_ripple.json.

Dynamic uniforms:
- Time
- Intensity = 1.2
- WaveCount = 8
- WaveSpeed = 6 normally
- WaveSpeed = 20 in cancel mode
- EpiCenter

The target LivingEntity's interpolated 3D position is projected through current model-view/projection matrices into normalized screen coordinates and fed to EpiCenter.

The fragment shader:
- aspect-corrects radial distance
- adds multi-frequency sin/cos organic noise
- combines four delayed waves
- distorts UV sampling
- masks screen edges
- adds RGB deconvergence in normal mode
- disables deconvergence when WaveSpeed > 10 (cancel mode)

JujutsuNetwork defines ripple_sync_channel. RipplePacket carries entity ID + cancel boolean and can be broadcast to TRACKING_ENTITY_AND_SELF.

## E. GUI cinematic

DomainCutinOverlay provides 2/3-way simultaneous Domain presentation. It uses depth masks, procedural backgrounds and live entity models. See DOMAIN-CLASH-AND-CUTIN.md.

## F. FBO-backed domain surfaces

CustomPortalBlockEntityRenderer.DomainRenderDispatcher allocates a window-sized TextureTarget.

At AFTER_LEVEL it:
1. creates/resizes the target,
2. clears/binds it,
3. renders the domain background,
4. completes target rendering,
5. returns to the main target.

The custom portal fragment shader samples the off-screen target using gl_FragCoord divided by texture size. The surface therefore displays a live separately rendered scene rather than a static texture.

A second portal shader uses projective texture sampling.

## Extraction rule

Do not collapse these systems into one universal VFX engine. Preserve separate primitives for:
1. particles
2. procedural world geometry
3. model aura layers
4. screen-space post effects
5. GUI cinematics
6. off-screen surface compositing

Their separation is the main architectural strength.
