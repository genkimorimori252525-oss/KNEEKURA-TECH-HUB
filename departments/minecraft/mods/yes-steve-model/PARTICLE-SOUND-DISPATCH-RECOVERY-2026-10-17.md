# Particle and sound function dispatch — 2026-10-17

## Scope and actual tool comparison

Exact JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
pinned source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
32 selected methods across nine owners cover particle/sound functions, dispatch
helpers and context sound-manager selection. Primary static review only, independent
semantic review NOT_RUN; central 669 map unchanged. No particle creation, audio
playback, game or target application was executed.

The owner's tool suggestion was used for an additional javap view of four exact
classes. A launcher was not on PATH, but the existing Java runtime includes the
jdk.jdeps module, so `java -m jdk.jdeps/com.sun.tools.javap.Main` ran successfully
without installing another JDK. Its four output hashes, matching particle
multi-catch entries, and sound configure/duplicate/schedule offsets are recorded
in JAVAP-EFFECT-COMPARISON-2026-10-17.json. Only the inspection tool ran. This is
not independent semantic review, original-source equivalence or runtime testing.

## Emission gates and raw return types

ParticleFunction requires allowEmitting and rejects fake-player animatables before
reading arguments; rejected calls return null. Sound Play/Stop/StopAll reject
allowEmitting=false with Boolean false, before their argument reads. Sound play
can configure fake-player audio as UI instead of rejecting it. Do not impose one
universal fake-player or return-value policy on both effect families.

ParticleFunction wraps ExecutionException and CommandSyntaxException from the
spawner in RuntimeException. Exact exception entries are start39/end51/handler52
for both types, independently visible in javap and the instruction parser.
Other outer evaluator handling remains a separate boundary.

## Particle parameters and coordinate meaning

Particle arguments are name; optional position xyz at 1..3; delta xyz at 4..6;
speed at 7; count at 8; lifetime at 9. Defaults are zero position/delta/speed/count
and lifetime20. Count is lower-clamped to 0 and lifetime to 1; no upper clamp is
encoded here. Blank name returns false. Declared arity is >=1, but arguments past
index9 are not read by the helper.

ParticleOptions are cached by the complete name/options string with 60-second
expire-after-access policy. Parsing uses ParticleArgument.readParticle, not a
command execution API. A cache timeout is not a guarantee of an exactly timed
removal or a bound on all memory. Actual registry/parser implementation is external.

- count==0 creates one precise-position particle. Relative position uses negative
  player BODY yaw for Player, otherwise entity yaw. Velocity is speed*delta xyz.
- count>0 creates that many randomized particles. Each offset component is a
  Gaussian*delta, and each velocity component separately Gaussian*speed. Relative
  rotation here uses entity yaw even for Player.
- abs_particle skips yaw rotation, but BOTH branches still add entity position.
  It is not a literal world-coordinate position parameter in this implementation.

Each particle creation is scheduled through Minecraft.execute and lifetime is set
only if createParticle returns nonnull. The eval helper's true result is dispatch
acceptance, not proof of visible particle count, lifetime or successful rendering.

## Sound ID, mode and argument order

Play reads ID, sound name, optional mode (default0, accepted0..7). Numeric IDs use
negated Number.intValue and reject only when the resulting int is positive;
other values use pooled-string conversion. Preserve that operation rather than
assuming all negative numeric inputs are rejected, because Java int overflow and
conversion boundaries remain relevant. ID0 is the manager's unnamed-sound path.

Mode bits: 1=force replacement, 2=global manager, 4=loop. The play callback checks
blank name and manager/entity availability before dispatch. Its configuration
callback sets loop, optionally reads volume/pitch at3/4 and clamps each to
[0.001f,1000f]; fake-player instances are marked UI. If instance creation fails,
that callback debugPrints and returns without reading volume/pitch.

SoundInstanceManager constructs the candidate, then invokes configure at offset83
BEFORE ID map put(111)/compute(156) and the later duplicate rejection. Thus volume/
pitch argument evaluation can occur even when an active same-ID non-force sound
makes the overall play return false. Do not assume all optional arguments are
skipped on that false result.

Names containing ':' use a parsed vanilla SoundEvent; other names request the
animatable's custom sound stream. Custom provider/native data production remains
unverified. A successful dispatch schedules Minecraft.execute at196, not an
acknowledgment that the audio engine played or the user heard it.

## Manager selection, replacement and stop

With global=false, MolangContext prefers AnimationContext's lazy manager, then
ControllerContext's manager when supported, then the global reference. global=true
skips those local scopes. Missing global manager can still mean no manager.

For nonzero ID, force replaces and stops an old active instance; non-force retains
an old active instance and returns false. ID0 appends an unnamed instance instead.
Stop removes/stops a nonzero ID but returns false for0 or missing ID. StopAll marks
both named and unnamed instances stopped and clears both collections; trim removes
those already stopped. These collection changes do not prove immediate audible
silence or thread-safe external-engine behavior.

## Verification and continuation

particle_sound_dispatch_ysm_265.py: --jar, --source-root, --evidence, --out;
203 integrity checks passed, 15 corrupted fixtures rejected. The javap receipt
adds three corroboration checks, not game tests. Raw disassembly stays outside Git.
Continue input-state observation and sync/defer gate/argument ordering without
sending packets, polling actual user keys or executing target effects.
