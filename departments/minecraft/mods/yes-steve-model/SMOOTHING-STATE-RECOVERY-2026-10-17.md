# Stateful first/second-order smoothing — 2026-10-17

## Scope

Exact JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
pinned source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
27 methods across seven owners capture both query functions, FirstOrder,
SecondOrder, IPhysics, PhysicsManager and selected AnimatableEntity lifecycle
callers. Primary static review only; independent semantic review NOT_RUN. No
numerical/game runtime, target JVM or native implementation executed. Map 669
unchanged; counts are method snapshots, not tested animation cases.

## Keys, defaults and call-time result

Both functions require at least two arguments: pooled string key then float input.
An EMPTY key returns Integer 0 before evaluating input/parameters. First order
uses optional response at index 2, default 1. Second order uses optional frequency,
coefficient, response at indices 2/3/4, each default 1. Additional arguments are
accepted by the >=2 arity contract but not read by these bodies.

Both use the animatable's SAME PhysicsManager key space. A missing key creates
its requested concrete type and returns input immediately. An existing key merely
receives IPhysics.setArgs and returns getValue; the function does not replace it
or check whether the existing value is FirstOrder versus SecondOrder. Reusing a
key across the two names therefore reuses the originally created concrete model,
with that model's own parameter interpretation. This is not one independent
storage slot per function name.

Constructors initialize simulated output to zero, not input. Consequently the
first return of input is not evidence that the internal integrator was seeded to
input. A second query before any manager advance can return the retained zero
while replacing pending args. This is a conditional static sequence, not a
reported in-game discontinuity.

## Manager time and frame ordering

PhysicsManager.update(renderTicks) only advances if lastRenderTicks > 0 AND the
new time is strictly greater. Otherwise it seeds the marker when last <=0, or
ignores a non-increasing timestamp. It uses `(new-old)/20f`, writes the new marker
BEFORE fastForEach updates, then calls each existing model's update. A timestamp
of zero is not a positive seed, and there is no rollback handler in this body.
reset sets the marker to zero and clears every keyed model.

AnimatableEntity calls this manager inside shouldUpdate, before preAnimationSetup,
processor ticking and postAnimationSetup. It is not nested solely inside shouldTick.
Geometry reset clears the manager. Thus current query calls generally set inputs
for a future advance and read existing output; they do not integrate on demand.
The selectively copied child context can retain the parent's animatable/manager.
These source-order implications do not establish actual frame rates or timing.

## First-order arithmetic

Each update performs float arithmetic:

`y = (1 - dt/response) * y + (dt/response) * input`

There is no exponential solver, clamp on dt/response, or response>0 check here.
setArgs updates input and response and ignores its two remaining arguments.
getValue returns the stored output. Do not silently substitute a stable analytic
filter or promise finite results for arbitrary parameter values; later typed
conversions can also change what a caller observes.

## Second-order arithmetic and substeps

The constructor clamps frequency to [0,5] and coefficient to [0,1]. setArgs stores
all four raw arguments, and update applies those same clamps again. Response is
not clamped. The update computes float coefficients using the captured PI constant:

- k1 = coefficient / PI / frequency
- k2 = 1 / (2*PI*frequency) / (2*PI*frequency)
- k3 = response*coefficient / 2 / PI / frequency

It computes input derivative from the previous inputFunction and dt, then stores
current inputFunction. maxTimeStep is sqrt(4*k2+k1*k1)-k1, narrowed to float;
cycleTime is an int cast of ceil(dt/maxTimeStep); dt is divided by cycleTime.
For each positive cycle count it updates output first, then its derivative using
that updated output. Finally it stores both simulated values.

The frequency clamp includes zero, and the body adds no positive denominator
floor or independent cap on cycleTime. No universal stability/finite-result
claim or reproduced numerical failure is made. Preserve float operation order,
substep selection and update order rather than importing a textbook formula that
differs from this implementation. External Math/Mth behavior and actual input
ranges are separate from the instruction-integrity checks.

## Verification and next seam

`tools/smoothing_state_ysm_265.py` takes --jar, --source-root, --evidence, --out.
170 integrity checks passed; 12 mutated fixtures rejected, including fabricated
Code for the abstract IPhysics contract. No authored numerical stand-in was used
to claim execution of original classes.

Continue particle/sound/input/sync/defer function gates and their argument order.
Keep stateful smoothing, pure numeric queries and externally visible effects
separate; a function name alone is not an allowEmitting policy.
