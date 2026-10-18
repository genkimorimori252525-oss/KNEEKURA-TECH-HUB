# Shared decoder framing and ownership contract

## Result

`3d0b20` validates an eight-byte footer over the preceding raw bytes, builds layered borrowed/generated-word-XOR/buffered streams, consumes a short transformed prefix, and compares a decoded selector to the caller's expected selector. Only a match reaches parser virtual +0x10. Its boolean does not prove complete input consumption, model validity, authenticated origin, or later application completion.

The footer is loaded before any local null or length>=8 guard. The inspected JNI-capacity call paths do not add such a gate before the call. This is a bounded precondition gap, not a demonstrated crash, exploit or whole-program missing validation: no malformed payload or target code was executed, and earlier Java/transport invariants remain separate.

`reproduce.py` verifies immutable SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`, extracts 14 source-backed half-open windows, verifies nine ELF vtable relocations, and runs eight authored valid integer-encoding algebra checks plus pointer-offset/state-recurrence arithmetic. It does not execute original instructions, emulate a decoder or extract assets. Named windows in [evidence receipt](NATIVE-PAYLOAD-FRAMING-EVIDENCE-2026-10-18.json) are authoritative; hexadecimal exploratory excerpts may overlap or end before a function ends.

## Arguments and callers

System V register flow at entry establishes:
- RDI: raw data pointer D
- RSI: raw byte length N
- RDX: separate material pointer K
- RCX: material hash length L
- R8: parser object P
- R9D: expected selector T

Caller joins, with exact parser +0x10 ELF relocations:
- Client `39a857`: T=3, P vtable `d1be68` → `3a2770`. K/L come from task-associated object +8 virtual +0x18/+0x20.
- Client `39aca6`: T=5, P vtable `d1bfe0` → `3a2660`. K/L come from associated object +0x48 virtual +0x18/+0x20.
- Client fallback `39c64a`: T=1, P vtable `d1bfb0` → `3a51b0`; K=`d1ba88`, L=0x38. Material contents are not extracted here.
- Server `403d1f`: T=2, P vtable `d1be38` → `3a5140`; K/L come from active object +0xd8 virtual +0x18/+0x20.

Client D/N are JNI GetDirectBufferAddress/+0x730 and GetDirectBufferCapacity/+0x738 results at `39a73b`/`39a752`; server equivalents are `403c4e`/`403c61`. Saved values flow directly to these decoder calls. No Java position/limit adjustment or >=8 check is present in these bounded segments. Object/state/shutdown gates exist and must not be confused with capacity validation. Prior client/server ownership receipts are hash-pinned in evidence.json; this decoder borrows D and K while its enclosing task owns the relevant lifetime.

## Footer check before stream construction

`3d0b47` computes N−8 in a 64-bit register. `3d0b4b` loads the eight-byte word from D+N−8 directly; on this x86-64 target it is a little-endian load. `3d0b50..3d0b5d` calls `573dd0(D,N−8,0xee6fa63d570bd77b)`. Mismatch at `3d0b65` branches to false return `3d0df7` without allocating the stream state.

No N minimum, D null, or pointer-wrap validation precedes that load in this function. Integer arithmetic fixtures document the offsets/wrap only; they do not dereference or execute short inputs. The later `3d0b6b..3d0b6f` conditional move normally changes stream length to N−8, but leaves original N when N−8 equals all ones (N=7 modulo 2^64). This unusual special case occurs after the unsafe-to-assume footer/hash precondition and must not be interpreted as a short-input guard.

The hash is over raw bytes before any stream transformation. Its footer seed is embedded in code and independent of K; this integrity comparison alone does not establish keyed authentication. No cryptographic authentication or confidentiality property is inferred.

## Hash helper: operations, no guessed algorithm name

`573dd0..574278` is a self-contained 64-bit length-dispatched mixing function. It branches for length <=32, <=16, <8, <4, <=64 and larger blocks. Operations include little-endian word loads, end-relative loads, rotates, byte swaps, multiply/add/XOR and shift-XOR by 47. Constants include `0xaf29ce778879d9c7`, `0x91af10802cab25a5`, `0xe4986a230e5aaa17` and multiplier `0xde0f6ee09bdbab91`.

All length paths converge on the seeded finish at `5741ef`: add `0x50d6318877862639` to the prior mixed accumulator, combine with the third argument using XOR/multiplication, and perform repeated 47-bit shift-XOR/multiply steps (`5741ef..57421b`). For larger paths the third argument is saved/restored before this finish. Zero-length handling is internal to the helper, not protection against a caller's wrapped N−8.

No exact primary-source algorithm match is established, and no standard hash or encryption name is assigned. Similar-looking structure alone would be insufficient to identify an exact standard implementation or output equivalence. No original payloads or extracted assets were hashed for behavioral tests.

## Stream setup and data transitions

1. Borrowed raw span: stack+0x50 has vtable `d1d7f8`, flag +8=0, D at +0x10, effective length at +0x18 and position +0x20=0 (`3d0b73..3d0b95`). Vtable read slot resolves to `4dc180`, which delegates to `4dc270`. For a valid span, that helper computes remaining length, selects min(request,remaining), copies and advances position; with a strict request exceeding remaining it takes an exception path rather than the copy path. This later bound check does not protect the earlier footer load.

2. Generated-word XOR state: allocate 0x9e0 at `3d0bad`; state+0 points to the borrowed stream. Its seed at +8 is `573dd0(K,L,0xd017cbba7b5d3581)` (`3d0bcd`). The loop `3d0bf0..3d0c3b` initializes 312 64-bit words with recurrence, modulo 2^64,
   x[0]=seed; x[i]=0x5851f42d4c957f2d*(x[i−1] XOR (x[i−1]>>62))+i, i=1..311.
   State+0x9c8 receives 312; +0x9d0/+0x9d8 are cleared. The authored fixture checks only this algebra, not the complete generator.

3. XOR stream: stack+0x30 uses vtable `d1d940`, read slot `4dd600`. It forwards reads into the underlying borrowed span, updates destination progress, then calls `4df880` in-place on the bytes actually read. `4df880` XORs full eight-byte words with values produced by `43bfe0`; partial words retain byte state at generator-relative +0x9c8/+0x9d0. The generator body is outside this slice. This is an operation-level XOR description, not a security claim or named cipher assignment.

4. Buffered transform: `3d0c75` calls `4dc3a0(out, XOR-stream, K, K+0x20, 1, 0x1e)`. The constructor allocates two 64-byte buffer capacities (1<<6), stores the upstream pointer, and initializes a transform through `[d2ff30]+0x28` at `4dc4c1`, passing K, K+0x20, an output state record and 0x1e. It also reads a word at K+0x30 (`4dc4e1`). Thus L is not a proven comprehensive bound on all subsequent material accesses; runtime dynamic material size invariants are outside this slice. The runtime-selected dispatch identity and its exact transformation remain unresolved.

The final stream vtable is `d1d850`; read slot +0x10 resolves to `4dd1d0`, refill +0x18 to `4dc550`. Reads copy buffered output while advancing positions; refills call upstream and transform machinery. Concrete buffers and cursor checks are visible, but this is not a proof of every transitive stream-bound invariant.

## Transformed prefix and selector

`3d0c7a..3d0caa` requests exactly two transformed bytes with strict flag 0. The little-endian uint16 is masked to 0x7f (`3d0cad..3d0cb5`); if nonzero, that count of transformed bytes is read/discarded into global scratch `d2f9b0` at `3d0ce7`. Hence the consumed prefix is 2+(first16&127) bytes; the upper nine bits are ignored at this point. The global scratch's concurrency discipline is not evaluated here.

A parser-facing reader with vtable `d1d408`, flag +8=1, field +0xc=32, upstream +0x10 and counter +0x18=0 is then built. `4c39e0` reads a 32-bit integer using one-byte strict reads, seven low bits per group at shifts 0,7,14,21,28. Each read increments its counter. The first four bytes continue when their high bit is set. The fifth is shifted into a 32-bit register without an explicit low-nibble range check; high continuation at byte five takes an exception-construction branch. No shortest-encoding/canonicality check is visible. This is a bounded integer-reader contract, not a complete wire-format schema.

`3d0d24` compares decoded integer to T. On mismatch it skips P entirely. On match `3d0d3b` invokes `P->vtable[+0x10](P, reader)`; that parser's return value is not used. On the normal cleanup path, the function returns the saved equality boolean. There is no subsequent check that raw/transformed input was exhausted, that no trailing material remained, or that downstream application completed.

## Cleanup and limits

After selector/parser handling the function frees two owned transform buffers and the 0x9e0 generated-word state. D and K are not freed in this boundary. Visible exception landing paths destroy stream-owned allocations and join a false return, but complete exception matching requires LSDA analysis and is not claimed. Parser side effects are not rolled back by any visible transaction mechanism in this wrapper.

The receipt distinguishes footer equality, selector equality, parser invocation, ownership cleanup and later model application. No successful runtime decode, malformed-input behavior, authenticated sender, complete parser schema, dynamic transform identity or exploitability is established.

## Follow-up dispatch and return-contract boundary

The [initial dispatch continuation](NATIVE-DECODER-DISPATCH-RECOVERY-2026-10-18.md) resolves the preserved pointer to a lazy trampoline, not yet the actual transformation body. Wrapper failure/success statements do not establish a callee ABI return type: no status register is tested after the parser call, but a void parser may signal failure only through exceptions. Whole-input exhaustion may also be enforced inside unexpanded callees; this wrapper alone does not establish it.
