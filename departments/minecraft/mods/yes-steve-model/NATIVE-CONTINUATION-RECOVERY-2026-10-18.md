# Third/fourth file-state return candidates and computed transfers

Status: PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. [Scalar/interval evidence](NATIVE-CONTINUATION-2026-10-18.json) and [expanded Ghidra/GNU cross-check](NATIVE-CONTINUATION-GHIDRA-CROSSCHECK-2026-10-18.json). The prior [post-return proof](NATIVE-POST-RETURN-GUARDS-RECOVERY-2026-10-17.md) remains a dependency.

## Conditional candidates

The third rewritten return has candidate load_bias + 0xf69c60. The fourth rewritten return has candidate load_bias + 0x132d8e6. These are conditional image-relative addresses, not recovered function names, Java/native bindings or runtime observations.

In addition to the preceding two words, this calculation uses file bytes 0xd2cd50 through 0xd2cd5a. Their exact 11-byte sequence is pinned in the evidence. Initializer writes to those bytes are not ruled out. Unknown data accessed elsewhere may affect faults or other state; normal completion and unmodified instructions remain explicit assumptions.

## Third key/data dependency

The fixed RCX arithmetic and partial-register operations give R10D=0xffffe200 before SHL R10W,5, whose outgoing carry is zero. The R9 rotate/word-mask/shift chain gives zero. Therefore the later RBX increment is six, identifying the third word at 0xd2cd52 after the two byte inputs at 0xd2cd50 and 0xd2cd51.

- The two byte transforms give decoded CL=0xd0 and DL=0xb0.
- The resulting carried key is 0xff30d23c.
- The third file word is 0x0ca71429. Its fixed XOR/add/byte-swap/rotate/add sequence produces delta 0x00080223.
- The preceding destination 0xee9a3d plus that signed delta gives 0xf69c60.

The byte SBB uses the carry from the intervening known RSI shift, not an older memory shift. The CL ADC uses carry cleared by rotating known-zero DX. Partial-register widths and carry producers are significant here; replacing them with a decompiler variable name is insufficient.

## Computed jumps and parity branch

At 0x130feb0, POP RDX consumes the nearest CALL return, load_bias+0xf69ca9. Adding 0x13cf73 makes JMP RDX at 0x130feb8 target load_bias+0x10a6c1c.

The later JMP R11 at 0xf08037 obtains the saved outer CALL return, load_bias+0x12db690, through a stack XCHG. The earlier unknown eight-byte store starts at a nonnegative offset relative to the old RSP; the outer return is subsequently pushed into offsets -8 through -1. The nested-call and PUSH-zero slots are distinct. The later fixed store overwrites the inner return, not the outer one. All 256 possible byte-derived earlier store offsets are checked by a byte-interval model. AND with known-zero ESI clears CF, XCHG preserves it, and ADC by -0x3dc8d1 gives load_bias+0xefedbf.

For JNP at 0xf1bbd3, CX=0xce07 is decremented, shifted right by two, and its low byte rotated right by six, producing 0x3306. XCHG transfers this into AX. BT of known-zero SI gives carry zero; ADC AX,0x3b4 gives 0x36ba. Low byte 0xba has odd parity, so the branch to 0x11009ad is taken under the fixed-path assumptions.

## Fourth word and return

After the third word update, byte 0xd2cd56 changes the carried key to 0xff38d0a7. Word 0xd2cd57 is 0xf452b8b0; the fixed transform gives delta 0x003c3c86. ADD RDI therefore produces load_bias+0x132d8e6.

SI remains zero through the final fixed prefix. The MOV at 0x11009ba writes RDI to current RSP; RET 8 at 0x11009be consumes it and advances the stack by 16 bytes. The unknown byte at 0xd2cd5b changes other state but is not used to claim a further concrete destination after this return.

## Validation and boundary

Ten scoped scalar/interval tests passed, including changed input bytes/words, bad widths, all 256 prior-write offsets, and altered/missing prefix rejection. Re-capture from the exact JAR matches. The ten new instruction prefixes were added to a separate fixed manifest, leaving the original 73-range receipt unchanged. Ghidra and GNU agree on all 83 ranges / 760 instruction occurrences in this expanded check; all seven imported file-backed segments still match.

The tools only evaluate explicit scalar expressions and byte intervals, and lift fixed instruction bytes. They do not load/execute the native target, run a CPU emulator, patch protection, or process protected model content. No whole-project CI or central mapping promotion occurred.

Next priority: initializer data-write dependencies, keeping these file-state candidates conditional. The next candidate is file-backed, but its runtime reachability and complete behavior remain unresolved.
