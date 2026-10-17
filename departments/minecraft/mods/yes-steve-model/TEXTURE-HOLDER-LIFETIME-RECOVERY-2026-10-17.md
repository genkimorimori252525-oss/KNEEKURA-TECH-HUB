# Texture-holder Java readiness and delayed release

Primary static review; independent semantic review NOT_RUN. Exact artifact
SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No target execution, GPU
verification or native implementation analysis. No mapping promotion.

19 methods cover CustomTextureManager `OOOOoO0o0Oo00O0o0oOoOo00`, its holder
`$Oo0Oo0o00O00Oo0OOoOOoooo`, TextureHolder `Oo0o0oO0000oO00O00oo00OO` and
CleanerUtil `ooooo00oOO000OO0o0oOOoOO`. Four source records represent three files.
Evidence includes exact fields/access flags, methods, encoded operands, exception
handlers and bootstrap links.

## Readiness is published after two operations

Holder.id returns Optional.of(id) only when ready=true, else Optional.empty.
The ready field has access66 (private + volatile); id/delay fields are final.
doRegister first checks ready, invokes the external Minecraft texture manager's
register method at18, then registers a cleanup action at39, then setReady at43.
There is no finally/rollback in that body. This is a Java publication boundary,
not proof of completed GPU work or of all referenced PBR textures being ready.

The two-argument register overload uses a default delay200. The main overload
asserts render thread, looks up the texture object in an IdentityHashMap whose
values are weak holder references. A still-live holder is returned directly;
if immediately=true and not ready it is first registered. A new delay argument
does not replace an already-live holder's stored delay. A cleared weak reference
is removed during this lookup path.

If a pending-removal entry exists, it is removed and its resource ID is reused
with the newly requested delay. The reused-ID constructor does not set ready;
it retains Java's initial false value, so an existing ID alone does not make the
new holder immediately readable. Otherwise a new yes_steve_model:textures/counter
ID is allocated. PBR child holders are recursively registered and retained in a
list. The main holder is entered in the identity map, then either registered now
or enqueued with its texture for later processing. Pending entries hold strong
references until polled; this differs from the weak cache values.

## Cleanup registration is separate from explicit release

CleanerUtil delegates both Consumer/BiConsumer overloads to Netty ObjectCleaner
through captured Runnable lambdas. The texture-manager callback captures texture
and later places ID/delay into REMOVING_TEXTURES; its bootstrap target is retained.
Actual garbage-collection timing and ObjectCleaner implementation are not tested.

CustomTextureManager.release(texture) asserts render thread and removes only the
identity-map entry. It does not directly invoke TextureManager.release, clear
pending registration, cancel cleanup or mark a live holder not-ready in this body.
Do not confuse this Java cache operation with immediate GPU disposal.

## Tick order and soft work budget

A tick first iterates pending removals. A delay already <=0 is moved into the
removed-ID queue and erased from the removal map; otherwise the delay decreases
by one. Starting at1 therefore decrements to0 on one visit and queues on a later
visit, rather than queuing in the decrementing branch itself.

Only after this whole removal-countdown phase does StopWatch.createStarted run.
Pending registrations are polled/registered before removed IDs are released.
After each registration or release, elapsed>=20 returns from tick. Thus 20ms is
an after-operation soft budget, not a hard upper bound for the whole tick; one
slow operation can exceed it, and the earlier countdown phase is outside it.
If registration consumes the budget, removed-ID processing is deferred. The
pending queue is polled before doRegister, with no restoration handler if that
operation throws. None of these conditional limitations proves an observed leak,
starvation, failed texture or frame-time regression.

## Verification and next boundary

118 static checks pass;15 malformed-evidence controls reject changed readiness,
thread assertion, zero-delay boundary, 20ms equality and fabricated finally.
This is evidence-integrity verification, not independent semantic approval.
Whole source equivalence remains unproven and mapping669 is unchanged.

Next follow the client tick caller and renderer selection using TextureHolder.id.
Keep resource readiness, actual texture upload and visible model replacement
separate until their caller paths are grounded. No decryption/native expansion.
