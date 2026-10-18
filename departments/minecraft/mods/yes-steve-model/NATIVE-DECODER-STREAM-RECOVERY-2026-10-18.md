# Decoder: derived output to buffered block-XOR stream

The 32-byte transform output becomes the next stream's working key material. Its next consumer is selected table slot +0x20, with state, source, destination and byte length arguments. The generic implementation has a provable ChaCha-family block/feed-forward/XOR structure using 30 rounds and a 64-bit block counter. These semantics are conditional on that implementation being selected; no backend execution or selection is asserted.

## Setup and owned/borrowed state

Let B be the stream object passed to 0x4dc3a0 and S=B+0x58. At 0x4dc4c4..0x4dc4d4 the 32 output bytes of table +0x28 are copied from the stack temporary into S[0..0x1f]. The surrounding initialization establishes:

| B offset | S offset | Meaning proven by writes and later reads |
|---|---|---|
| +0x58..0x77 | +0..0x1f | derived 32 bytes |
| +0x78..0x7f | +0x20 | zero-initialized 64-bit block counter |
| +0x80..0x87 | +0x28 | 8 bytes copied from K+0x30 |
| +0x88..0x8f | +0x30 | round count, 30 in the proven caller |
| +0x90..0x97 | +0x38 | pending byte count, initially zero |
| +0x98..0xd7 | +0x40 | pending 64-byte block, initially zero |
| +0xd8 | outside S | borrowed upstream stream pointer |

B+0x10 and B+0xe0 are buffer objects; their data fields are B+0x18 and B+0xe8, and their logical sizes are B+0x28 and B+0xf8. Constructor block count is shifted left six at 0x4dc3c4; the proven caller's count1 gives a 64-byte refill size. B+0x30/+0x38/+0x40 are output data/length/consumed position; +0x48 is refill size and +0x50 marks a short final refill. Data/size getter relocations are verified. Earlier cleanup ownership remains in the shared-decoder receipt; the derived bytes are copied, not a borrowed reference to the temporary.

## Refill and parser-visible bytes

0x4dd1d0 first copies already-buffered bytes to the requested span, bounded by the minimum of destination remaining bytes and buffered remaining bytes (0x4dd231..0x4dd25a). Empty output triggers buffer preparation and the stream virtual +0x18 refill call at 0x4dd300. ELF relocation 0xd1d868 resolves that call to 0x4dc550.

Refill reads upstream into B+0xe0's buffer. It repeatedly calls upstream virtual +0x10 with argument flag1, accumulates reported bytes, and checks that the reported count does not exceed remaining capacity (0x4dc5c0..0x4dc613). A pre-read upstream EOF flag at upstream+8 selects the final path. No independent zero-progress escape is visible when the upstream keeps its EOF flag clear; this is a caller/stream-contract boundary, not an executed hang claim.

On the normal full-refill path, pending input is completed to 64 bytes if necessary; full units are transformed through 0x574820 (calls at 0x4dc754 and 0x4dc783), with residual bytes retained at S+0x40 and count S+0x38. The proven 64-byte refill starts with pending zero, so the ordinary path emits one 64-byte unit. The produced count is checked against the input buffer's logical size at 0x4dc7d9; mismatch takes an exception-construction branch. The post-block hook at 0x4dc815 resolves through 0xd1d870 to the single RET at 0x2aade0 for this vtable. It does not modify the block count here.

At upstream EOF after some bytes were collected, the final path processes whole units then transforms any remaining partial bytes through selected table +0x20 (0x4dc902..0x4dc941). Unaligned output uses the pending block in place followed by a bounded copy. It advances the destination span by exactly the produced count, checks remaining accounting, then calls the fill-function pointer at 0xd2ff38 with (S,0,0x80) at 0x4dc943..0x4dc956. Its original ELF target is 0x5766d0, a byte-fill implementation. Thus this branch requests zeroing S[0..0x7f]. EOF with zero bytes collected jumps directly to return at 0x4dc68d and does not traverse that wipe; no all-path erasure guarantee is claimed.

The outer reader marks B+0x50 when a refill produces fewer bytes than its span capacity, preserves those bytes for consumption, and later sets B+8 EOF when exhausted. The non-short-read mode follows an exception branch after EOF; normal/short-read mode may return. These flags concern stream exhaustion, not validation of the decoded model. The resulting byte stream feeds the prefix/selector/parser reader already traced in the shared-decoder receipt.

## Alignment adapter and generic +0x20 interface

0x574820 forwards (S, source, destination, length) to selected table +0x20. It tests source/destination alignment modulo8. Aligned paths dispatch directly; other paths use a 1024-byte stack scratch buffer, copy in/out as necessary, and bound each chunk to min(remaining,1024). A null source is preserved on the relevant paths. This helper does not itself implement the cipher or select a particular CPU table.

Original ELF slot 0xd1ded0 (generic table +0x20) resolves to 0x575bc0. That function returns immediately on length zero; otherwise it copies the 48-byte key/counter/nonce state locally and reads round count S+0x30. Each block initializes these sixteen little-endian 32-bit words:

- 0..3: 61707865,3320646e,79622d32,6b206574
- 4..11: S[0..0x1f], the previous transform output
- 12..13: S+0x20, the low/high 32-bit halves of the block counter
- 14..15: S+0x28, copied from K+0x30

Eight quarter-round windows are recorded in evidence.json, covering the same four column and four diagonal index groups as the prior HChaCha-form proof. Operations are 32-bit modular addition, XOR, rotate-left16/12/8/7. Loop 0x575ff0..0x575ff4 subtracts two rounds per iteration. The known count30 means fifteen double rounds. Unlike the preceding HChaCha-form function, 0x575ffa..0x57607c adds every original state word back, including constants.

With nonnull source, 0x57608a..0x576117 XORs the 64-byte block output with input and writes destination. With null source it emits the serialized block directly. For a final length1..63, the function uses local 64-byte scratch and copies only requested tail bytes to the caller (0x576316..0x5763e0). Each generated block, including a partial one, increments counter low32 at 0x5762e2 and carries into high32 at 0x5762ef. Updated halves are stored back at S+0x20/+0x24 at 0x5763f0..0x5763fb. No overflow rejection is visible; no security conclusion is inferred from that scoped observation. The stream wrapper avoids consuming a partial block until terminal EOF, so ordinary chunking does not discard partial-block keystream.

The generic helper calls global fill pointer 0xd2ff38 on its local 48-byte state copy before return. This is not proof that every stack/register copy is erased. No allocation or input ownership transfer occurs in the generic block routine.

## Primitive identification and limits

The pinned [RFC 8439, sections2.1–2.4](https://www.rfc-editor.org/rfc/rfc8439.txt) supports the exact quarter-round, feed-forward and XOR comparison. Its source SHA256 remains 25bef70fbf7a07ff45c2fe4cb7c6ce954eac687413d8610603268b4e4415324c. The native candidate differs in round count and uses a 64-bit counter/64-bit tail arrangement; it is not identified as the RFC's ChaCha20 instance. The earlier pinned XChaCha draft supports the preceding subkey-construction comparison only. This receipt establishes a 30-round HChaCha-form derivation followed by a 30-round ChaCha-family stream transform in the generic candidate path. It does not establish a standardized whole-payload protocol, an authentication mechanism, actual backend selection, or equivalent semantics of untraced optimized implementations.

Reproduction verifies 11 original code ranges and eight ELF relocations and links earlier receipts/primary sources by hash. All analysis is static. No assets, target code, candidate tests, host/JVM execution or repository edits were involved. Broad exception metadata and full parser schema remain outside scope.

Evidence: [NATIVE-DECODER-STREAM-EVIDENCE-2026-10-18.json](NATIVE-DECODER-STREAM-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external.
