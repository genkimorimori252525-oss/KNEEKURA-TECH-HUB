# Selector3 parser to receive builder: bounded schema and ownership

## Proven root contract

Original ELF slot0xd1be78 selects parser0x3a2770. Let R denote its output object, and V its reader argument. The caller initializes the root vtable and its two inline blob wrappers before passing R to the shared decoder. Reader V is the previously proven 0xd1d408 implementation, with read-mode byte V+8=1 and format/version field V+0xc=32.

In order, parser0x3a2770 reads:

| Destination | Operation | Native evidence |
|---|---|---|
| R+8 | base128 unsigned64-bit scalar | reader+0x18 at0x3a2788→0x4c3bd0 |
| R+0x18..0x4f | exactly56 raw bytes | wrapper R+0x10 getters at0x3a2796/0x3a27a3; read+0x60 at0x3a27b2 |
| R+0x58..0x8f | exactly56 raw bytes | wrapper R+0x50 getters at0x3a27c0/0x3a27cd; read+0x60 at0x3a27dc |
| object referenced by R+0x90 | nested package parser | virtual+0x10 at0x3a28b2→0x3a2b80 for newly allocated object |
| R+0xa0 | base128 unsigned32-bit scalar | tail dispatch reader+0x10 at0x3a28d4→0x4c39e0 |

Both blob wrappers use vtable0xd1caa8. Its +0x10 getter0x3608d0 returns this+8 and +0x20 getter0x3608e0 returns0x38. The raw read helper0x4c43b0 requests exactly that span with short-read flag0. No separate per-blob wire length is read in this root parser. Names such as model version, key, identity or permissions are not assigned to these fields merely from width or position.

The unsigned64 reader consumes up to ten7-bit groups. Its tenth shift is63 and it rejects a continuation bit after the tenth byte; this scope does not establish canonical shortest encoding or a high-payload-bit range check. The unsigned32 reader contract is preserved in shared-decoder-contract. Neither reader is treated as a signed ZigZag decoder.

## Root ownership and builder argument correspondence

When R+0x90 is null and reader mode equals1, 0x3a27fa allocates a0x30 package object Q, and0x3a2826 allocates a0x18 reference-count control C. Q receives vtable0xd1bed0 and initially zero fields. C receives vtable0xd1be98, counts0x100000001 at+8, and Q at+0x10. The pair is stored in R+0x90/+0x98. Replaced control state is decremented/disposed on the shown branches. Control dispose0x3a29b0 invokes Q's virtual+8 deletion path. Existing nonnull Q is reused and parsed in place. The null-object path with mode !=1 constructs an exception.

The caller's R is stack+0x90. At0x39a867..0x39a8a5, builder0x3577c0 receives:

- RDI: separate builder-result destination
- RSI: retained client state+0xf8 value
- RDX: scalar R+8
- RCX: second blob wrapper R+0x50
- R8: first blob wrapper R+0x10
- R9: Q, loaded from R+0x90
- seventh stack argument: uint32 R+0xa0

The root control pointer R+0x98 is not passed as that seventh argument. The builder borrows Q at entry; this callsite alone does not show retaining Q for deferred work.

At0x357b23 the builder allocates a0xd0 object H. 0x357b3e..0x357b5d copies all56 bytes of the second blob into H+8..0x3f. 0x357b6a..0x357b88 copies all56 bytes of the first blob into H+0x48..0x7f. New blob vtables occupy H+0 and H+0x40. The trailing uint32 is copied to H+0x80 at0x357b8c. Thus these fields have explicit copied storage beyond the parser's stack object. Their semantics and H's entire transitive lifetime are not inferred here.

## Bounded nested package contract

Q+8/+0x10/+0x18 is a vector begin/end/capacity triple. In read mode,0x3a2b80 destroys previous elements via virtual slot0, resetting end to begin, then reads a uint32 count. The subtraction/borrow loop processes exactly that count, including zero as an empty vector. No small domain-specific maximum count is proven in this prefix.

Each vector element E has stride0x48 and vtable0xd1be10. Direct helper0x35ea70 reads, in order:

1. Pair of uint64 base128 values at E+0x10 and E+0x18, through embedded object E+8 and helper0x360740.
2. Length-prefixed byte-string storage at E+0x20 via reader+0x48→0x4c40d0.
3. Boolean bytes E+0x40 and E+0x41 via reader+0x40→0x4c3ff0.
4. Uint32 base128 value E+0x44 via reader+0x10.

String reader reads a uint32 length, rejects values >=0x1000001 (so maximum accepted length0x1000000), resizes string-like storage, then reads that many bytes. No text encoding validation is visible in this helper. Boolean reader accepts only raw bytes0 or1; values>=2 take an exception path. These are reusable structural contracts, not guessed field labels.

The vector insertion shown0x3a2cc7..0x3a2d0a copies the pair and scalar fields, transfers a non-inline string pointer or copies inline string bytes including terminator, and advances end by0x48. Growth branches are preserved only as boundaries; no complete allocation-failure guarantee is asserted.

After the vector, Q+0x20/+0x28 holds a separately reference-counted map object/control. If absent, allocation0x3a3203 creates0x48 control-plus-payload storage and stores payload atQ+0x20 and control atQ+0x28. The reader clears prior map entries and reads another uint32 count. Each entry starts with a length-prefixed name-like byte string at0x3a32f4, then two nested value helpers0x3a4be0 and0x3a4d20 at0x3a32ff/0x3a330f. Lookup/insertion helper0x3a3ae0 follows. Full value schema, duplicate-key policy and semantic names remain outside this cohort.

## Geometry connection and remaining boundary

Builder0x357c2e..0x357c84 reads Q's vector begin/end, advances elements by0x48, and uses E+0x10/+0x18 as a two-word lookup key. This directly joins the newly proven pair field to builder behavior without assigning UUID or hash semantics.

The established geometry-build receipt proves callable installation0x359fdc..0x35a0fb, then the conditional route0x35d250→0x36d8c0→0x36a6e0→0x375e30. This remains a deferred edge, not a synchronous call from the root parser.

A tighter source boundary is now recorded inside that callable:0x35d32e indexes a separate0x38-stride collection;0x35d337/0x35d33c load its +0x18/+0x20 pair;0x35d344 calls0x35c9c0,0x35d357 calls0x35caa0, and0x35d3a5 calls0x4e0060. A subsequently selected native pointer at stack+0xa0 becomes the RDX model argument of0x36d8c0 at0x35d54b. Immediately beforehand0x35d500..0x35d511 copies matched E+0x41 into that native model's+0x5c9. This proves a parsed boolean reaches the downstream native model; its meaning is not assigned.

The0x38-stride collection must not be conflated with Q's0x48-stride vector. Exact assembly from Q's map/value entries through resource selection/0x35caa0 into the native model is the remaining bridge. The next useful narrow scope is those source acquisition helpers and their object outputs, rather than expanding transport transformations or decoding an original asset.

## Evidence and limits

reproduce.py verifies18 original-byte windows and11 ELF relocations and links the earlier receive/shared-decoder/geometry receipts by hash. Some exploratory windows include neighboring or unreviewed code; only the stated offsets and branches support this contract. No original data was read from assets, and no parser, JVM, target function or deferred callback was executed. No repository files changed. Parsing normal return is not assigned a Boolean success contract. No complete model/bone wire schema or complete exception/lifetime proof is claimed.

Evidence: [NATIVE-SELECTOR3-SCHEMA-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR3-SCHEMA-EVIDENCE-2026-10-18.json). Related [geometry construction](NATIVE-GEOMETRY-BUILD-RECOVERY-2026-10-18.md) and [material provenance](NATIVE-DECODER-MATERIAL-RECOVERY-2026-10-18.md). Raw excerpts and reproduction scripts remain external.
