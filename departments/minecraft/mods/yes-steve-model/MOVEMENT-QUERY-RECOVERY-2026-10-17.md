# Movement query provenance and unit boundaries

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` and source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eleven selected complete
methods, not every method in QueryBinding/YSMBinding: constructors, speed/time
helpers and MoveInputVariable. Full owner declarations/bootstrap records plus a
fixed exact selected-method key set prevent silent omission. No mapping promotion.

## Similar names use different data

QueryBinding constructor wires delta_time, ground_speed and vertical_speed through
bootstrap10,16,18. YSMBinding constructor wires time_delta, ground_speed2,
input_vertical and input_horizontal through bootstrap8..11. The implementation
handles and registration calls are retained, so these correspondences are not
inferred solely from similarly named source methods.

- query.ground_speed reads Entity.getDeltaMovement, computes horizontal magnitude
  (double squares/sum narrowed to float before Mth.sqrt), then multiplies by20.
- query.vertical_speed reads tracker displacement.y, narrows to float, multiplies
  by20 and divides by tracker renderTickDelta.
- ysm.ground_speed2 reads tracker horizontal displacement magnitude, narrows the
  squared sum to float before sqrt, multiplies by20 and divides by renderTickDelta.
- query.delta_time and ysm.time_delta divide tracker renderTickDelta by float20
  and box the float result. These are not independently read wall-clock durations.

The first speed is based on the entity velocity field, while the latter two use
accepted interpolated tracker samples. They must not be substituted as identical
measurements. Tick-to-second scaling is explicit arithmetic, not measured speed
or frame-rate calibration.

The displacement-based speed helper bodies have no zero-denominator branch.
At that helper boundary zero/zero can produce NaN and nonzero/zero infinity under
Java float arithmetic. This does NOT establish the final value visible to every
Molang caller: variable wrappers and evaluator conversion/error handling must be
followed separately. Do not diagnose a runtime bug from the division alone.

## input_vertical/input_horizontal are displacement-derived directions

Both methods read tracker delta.x/z and the animation event's actual partial tick.
If sqrt(x*x+z*z)<double0.0001, they return double0. Equality continues; NaN does
not take that early-return comparison. No normalization by renderTickDelta occurs.

They compute movement angle from atan2(z,x), narrow to float and convert to
degrees; derive entity angle as90-wrapDegrees(-viewYaw(partialTick)); wrap their
difference; convert to radians. Vertical returns float cosine widened to double,
horizontal float sine widened to double. These indicate facing-relative direction,
not a keyboard/analog input read and not speed magnitude. World-axis meanings or
signs should be derived from the explicit formula rather than assumed from names.

The magnitude threshold depends on displacement between accepted samples, so it
is not a speed threshold independent of sampling interval. External Minecraft
trigonometric/wrapping helpers remain dependencies; no numerical game trace ran.

## Verification and continuation

74 fixed-artifact/source/declaration/selected-body checks pass;11 negative controls
reject changed threshold/equality, division, units, registration label and lambda
target. Constructors are captured for binding evidence, not full semantic review
of every query they register. Whole source equivalence remains unproven; map669.

Next inspect ContextBinding→LambdaVariable/EntityVariable and runtime conversion
to determine how null/NaN/exceptional results propagate at the user-visible Molang
boundary. Keep helper arithmetic distinct from end-to-end evaluation outcomes.
