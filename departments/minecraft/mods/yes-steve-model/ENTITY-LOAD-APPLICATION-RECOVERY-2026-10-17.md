# Client entity-load deferral and property application

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eleven selected complete
methods across EntityLoadEvent and DispatchServerDrivenProperty. The property
codec/other setters are not newly claimed fully analyzed by this subset. No
packet sending, game execution, successful subscription/delivery or security claim.

## Missing world and missing entity are different paths

executeOnEntity submits a Runnable through Minecraft.execute. The captured body
reads the current client level. Null level returns without invoking the consumer
or adding a recovery entry. With a level and matching entity, it calls the consumer;
with a level but missing entity, it adds a cached recovery handler. This is a
request to the client executor, not a measured scheduling/latency trace.

The recovery cache maps integer entity ID to a List of consumers. Static setup
calls expireAfterAccess(30,SECONDS), not expireAfterWrite or a guaranteed delivery
within30seconds. Cache maintenance/expiration timing depends on the external cache
implementation and accesses; no clock-based test was run. The key contains no
explicit world/dimension discriminator in this class.

Adding recovery gets/creates an ArrayList and appends. On entity-join invocation,
if YSM is available it gets that ID's list, executes consumers in list order, then
invalidates the ID. There is no per-consumer catch or finally invalidation; a
throwing consumer can skip later consumers and invalidation. Not-available returns
before that processing. Therefore exactly-once successful application is not proven
by the cache's existence. The source's client-event annotation was not exercised
in a game and cannot substitute for runtime listener verification.

## Handled flag is not an application receipt

The message handler checks the reception side for client, then delegates to
executeOnEntity using the message's entity ID and a captured callback. It sets
packetHandled=true on its ordinary tail even though entity application may be
deferred or skipped. That flag is not proof that a model/roaming value changed.

The entity callback proceeds only for a Player with the capability. Its selected
lambda handles extra-animation bit11 first (nonempty name plays; empty stops),
then roaming bit12. isFull tests bit0: full takes resetRoamingVars with the full-map
representation; incremental takes updateRemoteRoamingVars. Finally it calls the
player state tracker's server-driven-property update. Exceptions in earlier
operations can prevent later ones; there is no local rollback/finally on this
sequence. Other message bits and actual decode invariants are separate evidence.

This joins the ordinary receiver path to ROAMING-STATE-MERGE's model-hash/readiness
APIs without asserting transport reliability or server authorization. No payload
was executed or tested against any server/client.

## Checks and continuation

70 static checks pass;12 corrupt/missing-evidence controls reject full-bit,
deferral configuration, null-world/entity gates and invented handler cleanup.
Mapping669 remains unchanged; source equivalence and independent review remain
unproven. This post-checkpoint cohort is not part of the frozen17-cohort receipt.
Next inspect PlayerStateTracker's selected server-property masks and their Molang
consumers to close what those applied fields mean, rather than equating a handled
message with a completed visible animation change.
