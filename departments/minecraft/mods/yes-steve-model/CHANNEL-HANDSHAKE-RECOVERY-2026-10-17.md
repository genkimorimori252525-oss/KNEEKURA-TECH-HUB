# Channel handshake: first registration is not version agreement or model readiness

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Sixteen declarations across ServerInfo `oO000OOo0o000oOoo0O000Oo`, ClientInfo `o0O0oo00OO00oO0O0o0o0o00` and LoginEvent `ooOOO00Oo0000oOOO0OoO0o0`. No handshake, login, network send or native routine was executed.

## Initial request and wire shape

LoginEvent's captured body requires YSM availability and a ServerPlayer, then constructs ServerInfo and calls the player-targeted send helper. The class EventBusSubscriber and method SubscribeEvent metadata are retained; successful event registration is not established by their presence.

Both packet default constructors embed protocol string2.6.0, separate from artifact release2.6.5. Their codecs write/read one UTF string. The existing NetworkHandler registration assigns ServerInfo51 to client reception and ClientInfo52 to server reception. These handler bodies rely on that declared routing rather than repeating all direction checks locally.

## First-write gate versus usable channel

The already captured NetworkHandler.setChannelVersion calls the connection attribute's compareAndSet(null,incomingString). The separate isChannelPresent predicate tests nonnull connection/channel and equality with2.6.0. First registration succeeding and the stored value agreeing with the expected version are therefore different checks. Neither packet handler adds that equality check to its first-write condition. This does not establish successful cross-version model synchronization; later Java/native/external processing remains separate.

ServerInfo handling calls setChannelVersion. Only a true result enqueues ClientModelManager.receiveServerInfo. On the ordinary tail it replies with a new ClientInfo regardless of whether that first-write gate succeeded, then marks handled. It does not wait for the enqueued task before replying. An already-set attribute can suppress the task without suppressing the reply.

The [client state dossier](CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md) already captures receiveServerInfo: local-server mode selects LOADING, otherwise IDLE, then listeners are invoked. The packet caller supplies an enqueueWork boundary absent from that helper itself. Queue submission, state label/listener notification and completed model loading are not equivalent.

## Server response ordering

ClientInfo handling obtains sender and proceeds only when nonnull and setChannelVersion returns true. Its ordinary sequence is:

1. ServerModelManager.checkCapability(player)
2. For present model-info capability: setMandatory(false), then stopAnimation(player)
3. For present owned-model capability: construct/send its set synchronization
4. For present starred-model capability: construct/send its set synchronization
5. ServerModelManager.syncModelsToPlayer(player,null)

The handler has no local enqueueWork, try/finally or rollback around this sequence. This is not proof of a specific network/server thread: effective dispatch belongs to the actual Forge channel implementation. The [server manager Java dossier](SERVER-MODEL-SYNC-JAVA-RECOVERY-2026-10-17.md) separately captures its server.execute boundary for the synchronization request. Neither set-message send proves the model stream completed.

The model-info callback's stop reaches the existing dirty-dependent extra-animation staging path. The first-write gate means an ordinary repeated ClientInfo after the attribute is set skips this whole initialization sequence and still reaches handled=true. A packet acknowledgement cannot be used as a new initialization-success receipt.

## Retry and connection scope

The earlier server tick callback sends additional ServerInfo at exact player tick counts200/600/1800 on its no-channel/non-mandatory branch. These are not a generic unbounded retry schedule or measured elapsed seconds. The [client login notice](CLIENT-SESSION-SKIN-EVENTS-RECOVERY-2026-10-17.md) has separate delayed notice logic and current-player checks.

The inspected attribute belongs to the supplied connection; these handlers contain no clear/reset operation for it. Reconnection, attribute lifetime, duplicate delivery and effective protocol compatibility remain external/runtime questions. No mismatched-version or duplicate packet was sent to test them. Central669 map and primary-review status remain unchanged.
