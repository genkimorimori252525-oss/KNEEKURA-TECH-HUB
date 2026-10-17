# Opaque model data: Java transport and last-connection lifetime

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No packets, native protocol, connection or target class executed. This documents Java byte transport, not model-format decoding or protection bypass.

## Selected evidence

SyncDataToClient (`O0oo00oo00OoOooO000oO00O`), SyncDataToServer (`oo00oOo0OOO0OoOOo0O0oO0O`) each contribute four methods; ClientModelManager (`o0OooO00ooo0OO000O0OoOoO`) contributes only its Java ByteBuffer sender and connection/buffer receiver. Ten selected methods, three complete declaration/bootstrap records, 69 artifact checks and 11 rejecting corruption controls. Whole owner declarations are support, not whole-class semantic review.

Both message constructors retain the supplied ByteBuffer reference without copying/null/directness validation. Encoding calls FriendlyByteBuf.writeBytes on that reference, with no local duplicate, rewind, flip or snapshot. Decoding allocates a direct buffer sized to readableBytes(), invokes readBytes(buffer), then wraps that buffer. There is no explicit flip/rewind, additional length field, local payload-size ceiling or local finally/release. This does NOT establish a framing bug, empty payload, unbounded network acceptance or native ownership leak: external codec limits/position effects and native interpretation are outside these Java bodies.

Client handling requires client reception side, then forwards Context.getNetworkManager and the buffer directly. Server handling requires server reception side and nonnull sender, derives UUID from that sender, then calls native receive. There is no enqueueWork in either handler. Ordinary tails mark handled=true even when a side/sender guard skips forwarding; an exception before the tail can prevent that mark. Handled status is not protocol acceptance or model readiness. Existing channel initialization/registration remains separate.

## Client reply lifetime

The Java receiver writes LAST_CONNECTION before invoking native receive. The captured declaration flags are private static volatile (74). Its two selected Java methods do not validate directness or clone data. The source comment requesting a direct buffer is not an executable check.

The Java sender checks Minecraft.player. If present, it constructs SyncDataToServer and uses CHANNEL.sendToServer inside an Exception catch. Otherwise it copies LAST_CONNECTION to a local, calls isConnected with no null guard, returns if disconnected, or converts a PLAY_TO_SERVER packet and sends on that connection. Only conversion/send are inside the second Exception catch; the null dereference/connectivity check is outside. No local wait, delivery acknowledgment, retry or channel-version guard is present in this method. Native callback thread comments are not proof of actual scheduling.

CLIENT-SYNC-CONNECTION-CALLERS scans all 955 classes after verifying the field declaration: exactly one GETSTATIC at sender offset34 and one PUTSTATIC at receiver offset1; no matching bootstrap arguments. No explicit Java logout/abort reset of this field appears in that bounded direct-reference scan. Existing syncAbort calls native receive with null and updates state; it does not imply LAST_CONNECTION was cleared. Initial null, retained previous connection, native/reflection writes and actual callback ordering remain distinct possibilities, not a reproduced failure. Volatile publication is not by itself a session-generation or ordering protocol.

## Reuse implications

Separate raw byte forwarding from Java model-selection packets, expression packets and loaded-model publication. Preserve the sender UUID provenance and opposite-side guards. Do not treat an asynchronously retained mutable buffer as a demonstrated immutable snapshot, nor infer native pointer/capacity semantics. Use the connected OPAQUE-TRANSPORT checkpoint; all native implementations and runtime behavior remain unresolved.
