# Molang command producer and the separate roulette relay

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.24 declarations/five owners,148 integrity checks/11 negative controls. CommandRegistry contributes only its selected RegisterCommandsEvent body; its full declaration/annotations remain support. Other command nodes and utility feedback methods are not all semantically reviewed merely because their supporting declarations/bodies are retained.

No command, packet, expression, server or game was executed. This dossier does not establish global authorization or exploitability.

## Registration and one permission-gated producer

The selected CommandRegistry handler `OoOo0000o0o0o00o0o0Oo00o` has an actual SubscribeEvent annotation. If YSM is unavailable it calls the placeholder root registration and returns. Otherwise it registers the ordinary root, and additionally registers the client root only when the physical distribution is CLIENT.

RootCommand `OOoO0ooOOoO00oOoo0OOOoo0` adds MolangCommand's subtree under ysm. The placeholder uses a greedy argument to report the unavailable message, not the Molang execution subtree. Registration is a Java call path, not proof that a particular running server exposed it successfully.

Server-side MolangCommand `o0o000oO00o0O0OOO0O0OOoo` creates a molang node with a requires predicate calling CommandUtil.hasPermission(source,2). Its execute branch takes a players selector and greedy expression string. It reads the selected ServerPlayer collection, maps entity IDs into an array, constructs ExecuteMolang and requests NetworkHandler.broadcastToAllPlayers. It returns command success1 after that request, not after client parsing/evaluation completion. The selected targets and packet recipients are different: the packet contains target IDs but this producer uses the ALL distributor, not one send per selected player.

## Permission predicate has a local-profile alternative

CommandUtil `OOO00O0Oo00oooooo0ooo00O` first tests the supplied permission level. If that fails, its CommandSourceStack overload accepts a nonnull source entity that passes isLocalPlayer. That helper requires a nonnull entity, physical Dist.CLIENT and equality of the entity UUID to the current Minecraft user's GameProfile ID. It does not independently query a single-player/host flag or require the entity to be a Player subclass.

The Entity overload rejects null, then applies the entity's permission-level check or the same local-profile alternative. Therefore the inspected command predicate is not simply an unconditional operator-only check, nor does it grant every multiplayer participant the alternative. Preserve the exact physical-side/profile conditions instead of generalizing the source comment. This predicate belongs to this command tree; it is not inherited by every packet producer.

## Constructor inventory found another application producer

The fixed955-class [constructor inventory](EXECUTE-MOLANG-PRODUCERS-EVIDENCE-2026-10-17.json) checks that both target constructors actually exist before scanning. It finds three direct construction sites, in three methods, and zero bootstrap constructor references:
- server MolangCommand: array-ID constructor, followed by ALL broadcast
- ExecuteMolang decoder: array-ID constructor, deserialization rather than an application emitter
- SubmitRouletteConfig relay: single-ID constructor, followed by TRACKING_ENTITY broadcast

Consequently command permissions alone cannot describe every observed Java route to ExecuteMolang. This remains an exact-symbol inventory, not closure over reflection, native calls or external mods.

## SubmitRouletteConfig is a separate relay

Owner `oOooOooO0Oo0oo0o0o00O0Oo` retains a string expression and target entity ID. Its codec writes UTF then VarInt; no local semantic validation is added there. The already-captured NetworkHandler registration binds this message at17 to PLAY_TO_SERVER.

The outer handler tests server reception, enqueues work capturing the context supplier and message, then marks handled on the normal tail. The worker calls the supplier again, obtains the sender, requires nonnull/alive, and resolves the supplied target ID in the sender's level. If an entity exists, it constructs ExecuteMolang for that ID and expression and requests broadcastToVisiblePlayers centered on that entity.

This body does not invoke CommandUtil.hasPermission, compare the target to the sender or a maid-owner UUID, constrain it to player/maid before forwarding, or parse/filter the expression before the relay. The client receiver separately routes only its supported entity types and performs parsing there. These are specific boundaries to preserve and review before using such a design with untrusted inputs; no claim of a reproduced attack or of every surrounding policy is made. No malformed payload, remote probe or network test was performed.

## Implications for reuse

Treat a restricted command emitter, a client-submission relay, transport direction, channel-presence checks, target authorization, client parsing and eventual expression execution as separate stages. A guarded emitter does not automatically guard another emitter that constructs the same packet class. The [packet routing dossier](ANIMATION-PACKET-ROUTING-RECOVERY-2026-10-17.md) captures the shared receiver and transport helper; the [common maid bridge](MAID-COMMON-MODEL-COPY-RECOVERY-2026-10-17.md) captures the maid consumer.
