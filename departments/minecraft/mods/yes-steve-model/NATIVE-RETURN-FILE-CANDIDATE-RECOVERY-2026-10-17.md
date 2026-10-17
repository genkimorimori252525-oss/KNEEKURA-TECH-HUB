# One computed return destination under an unchanged-file-data assumption

PRIMARY_STATIC_REVIEW_ONLY. Fixed Linux image SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. This extends NATIVE-RETURN-SLICE's symbolic expression to a FILE-STATE CANDIDATE, not an observed runtime target. Extra assumption: the addressed data word still contains its fixed file bytes when read. Native initializers/runtime writes have not been ruled out.

## Stack/data provenance

Let Q be RSP at the captured load-entry target. The first callee stores a sign-extended constant whose low 32 bits are 0x8f9ba402 at Q−8. Explicit PUSH/POP/CALL/LEA accounting reaches RSP=Q−136 at the later EBX load. Earlier partial-register shifts make RSI zero; the subsequent word exchange obtains 0xc000 from the known pushed RDI low word. Thus the EBX operand `[rsp+rsi*2−0x17f80]` addresses Q−8, recovering the saved constant. Intervening captured writes do not overlap that slot. The JSON retains the stack-delta events; this is static accounting, not an executed target stack.

ROR/NEG/BSWAP/NEG on that constant yield 0xd2cd48. The following ADC adds the symbolic image load bias; its carry is zero from the preceding known SHR. A later base subtraction leaves R8D=0xd2cd48 as the word-transform key. The source read therefore addresses image-relative 0xd2cd48. These results are derived from fixed prefix bytes and documented operand widths, not source-level guessed native function names.

## File-state word and candidate

The ELF mapping gives file bytes 52 ec 51 dc at that word address, i.e. 0xdc51ec52. The captured arithmetic applies XOR with 0xd2cd48, subtraction, a 3-bit rotate, further XORs, a byte swap and the final LEA adjustment. The small rotate/LEA constants are justified by preceding register operations; the intervening OR forces the SETGE result used here to 1. The resulting ESI is0x002040f8. Substitution into the existing return expression yields candidate image-relative 0x12c3a51.

That candidate is file-backed in an executable PT_LOAD region. This structural consistency is useful evidence for the next static inspection, but it does not prove the native loader reaches it with those exact data bytes or establish its function meaning. The input word is in a writable segment, so file provenance must not be confused with immutable runtime state.

## Relocation check is deliberately narrower than runtime verification

`readelf -rDW` reports 9,114 dynamic relocation rows of five observed types. An eight-byte interval check around each listed relocation start finds no overlap with the four-byte word at 0xd2cd48. Nearby listed relocations occur before it. This checks the listed RELA/JMPREL metadata only; it does not exclude initialization routines, custom fixups, runtime stores or external interference. No loader or native initializer was run.

## What this does and does not resolve

- Resolved conditionally: saved constant provenance, addressed file word, arithmetic offset and one file-state return candidate.
- Still unresolved: actual runtime word/destination, subsequent native semantics, Java-native registration, model formats and whole deobfuscation.
- No target execution, native machine emulation, code unpacking, patching or protected-model decoding occurred.

Ten synthetic tests and exact artifact recomputation verify the helper's arithmetic/accounting. The helper is narrowly pinned; it is not a general native-state simulator. Independent semantic review NOT_RUN and central mappings unchanged. Use the candidate only with its explicit additional data-state assumption.
