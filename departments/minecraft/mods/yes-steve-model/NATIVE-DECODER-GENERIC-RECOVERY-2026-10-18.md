# Generic +0x28 candidate: parameterized HChaCha-form transform

Original function [0x576430,0x5766ca) matches the HChaCha state arrangement, ChaCha quarter-round schedule, and HChaCha output selection. Its round count is a parameter. The previously proven caller supplies 0x1e: this candidate would perform **30 rounds**, not the 20 rounds specified for HChaCha20. This conclusion describes the candidate's code; neither actual backend selection nor successful candidate tests are established.

## Interface and memory bounds

- RDI: eight 32-bit little-endian loads, offsets 0..0x1c, at 0x576442..0x57645c. Required readable span: 32 bytes. These become state words 4..11.
- RSI: four 32-bit little-endian loads, offsets 0..0xc, at 0x57645f..0x576467. Required readable span: 16 bytes. These become words 12..15.
- RDX: saved at 0x57643d; restored at 0x576602. Output is exactly 32 bytes, written individually at offsets 0..0x1f through 0x5766bc.
- RCX: copied to R8 at 0x57643a. Each complete double round subtracts 2 at 0x5765f8 and loops while nonzero at 0x5765fc. There is no entry zero/odd/range check.

All input loads precede all output stores; there are no calls, allocations, frees, input modifications or loader/CPU queries in this function. Pointer validity and output capacity are caller preconditions. The earlier dispatch supplies K, K+0x20, a 32-byte stack output temporary, and 30; thus this candidate consumes K[0..0x2f]. The surrounding setup separately reads K+0x30, already recorded in the shared-decoder receipt.

For ordinary positive even RCX, iterations equal RCX/2. Pure modular arithmetic also shows an initial zero requires 2^63 iterations to return to zero; odd values cannot reach zero by subtracting two modulo 2^64. These are mathematical consequences of the visible loop, not executed tests or evidence that the fixed-30 caller violates its precondition.

## Instruction-level primitive correspondence

Words 0..3 are initialized at 0x57646e..0x576486 with 0x61707865, 0x3320646e, 0x79622d32, 0x6b206574. Each quarter round uses 32-bit wrapping addition, XOR, and rotate-left counts 16,12,8,7, in that order. Eight instruction windows map to state indices:

| Range, end exclusive | Indices |
|---|---|
| 0x576495..0x5764bf | 0,4,8,12 |
| 0x5764bf..0x5764ea | 1,5,9,13 |
| 0x5764ea..0x576512 | 2,6,10,14 |
| 0x576512..0x576543 | 3,7,11,15 |
| 0x576543..0x576574 | 0,5,10,15 |
| 0x576574..0x5765a2 | 1,6,11,12 |
| 0x5765a2..0x5765d0 | 2,7,8,13 |
| 0x5765d0..0x5765f8 | 3,4,9,14 |

The stores serialize final words 0..3 followed by 12..15 in little-endian order. They do not add the original state back. There is no payload XOR, authentication-tag generation/verification or message-length processing in this function.

## Pinned primary-source comparison

[RFC 8439, sections 2.1 and 2.3](https://www.rfc-editor.org/rfc/rfc8439.txt) specifies the quarter-round operations, rotations, constants and column/diagonal index schedule used for comparison. Local source SHA256: 25bef70fbf7a07ff45c2fe4cb7c6ce954eac687413d8610603268b4e4415324c.

[Version 03 of the XChaCha Internet-Draft, section 2.2](https://www.ietf.org/archive/id/draft-irtf-cfrg-xchacha-03.txt) specifies HChaCha20's 32-byte key, 16-byte nonce state and output selection of the first and last four words after 20 rounds. Local source SHA256: fa796b50265eeee383d40e82fed880267c7835e1b3d64c50c4f06162adaa1cfd. This is an expired Internet-Draft, used as an exact versioned algorithm-description source, not a claim of current protocol standardization.

The structural match is therefore stronger than constant resemblance, but the proven 30-round invocation differs from HChaCha20. No claim is made that the whole payload implements standardized XChaCha20, Poly1305, AEAD or any confidentiality/authentication guarantee. No claim of source-code provenance or particular library is made.

## Reproduction and limits

reproduce.py verifies the original SO hash, extracts the exact function and objdump listing, verifies both downloaded primary-source hashes, and records manual instruction/state correspondence. It does not execute the function, any candidate tests or algebra fixtures. Prior resolver/shared-decoder receipts remain unchanged. No original assets, target execution, JVM execution or repository edits were involved.

Evidence: [NATIVE-DECODER-GENERIC-EVIDENCE-2026-10-18.json](NATIVE-DECODER-GENERIC-EVIDENCE-2026-10-18.json). Reproduction scripts and raw binary ranges remain external.
