# JNI export file backing and first branch only

PRIMARY_STATIC_REVIEW_ONLY. Exact image hashes are inherited from NATIVE-IMAGE-METADATA; JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. This extends static metadata with virtual-address-to-file mapping and one recognized direct branch at each file-backed JNI export. It does not load a library, execute, unpack protected payloads or decode subsequent function bodies.

## Linux and Android

ELF PT_LOAD entries, rather than missing/unreliable section names, locate export bytes. Both JNI exports in each ELF image are file-backed. The first x86-64 instruction is JMP rel32; the first A64 instruction is B immediate. Each target maps into a file-backed executable PT_LOAD range. Thus the tiny exported symbol sizes are entry branches, not evidence that the initialization/unload implementation is only four/five bytes.

| Image | Entry | Export address | First branch target | Target file offset |
|---|---|---:|---:|---:|
| Linux x86-64 | JNI_OnLoad | 0x418760 | 0x121fe24 | 0x1088e24 |
| Linux x86-64 | JNI_OnUnload | 0x418770 | 0x10e09d2 | 0xf499d2 |
| Android AArch64 | JNI_OnLoad | 0x20abe4 | 0x78d3c0 | 0x71d3c0 |
| Android AArch64 | JNI_OnUnload | 0x20abe8 | 0x7b4ec8 | 0x744ec8 |

These are fixed-image virtual addresses, not ASLR-resolved process addresses. Target mapping is not function identification or proof of meaningful decoded code at that address. The four-byte production marker is file-backed in the ELF images; its raw bytes are recorded without interpreting it as a semantic or compatibility guarantee.

Instruction arithmetic is supported by the [Intel instruction-set manual](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf) for signed relative JMP and LLVM 19.1.7's primary [AArch64 encoding definitions](https://github.com/llvm/llvm-project/blob/llvmorg-19.1.7/llvm/lib/Target/AArch64/AArch64InstrFormats.td) and [unconditional-branch decoder](https://github.com/llvm/llvm-project/blob/llvmorg-19.1.7/llvm/lib/Target/AArch64/Disassembler/AArch64Disassembler.cpp). The A64 decoder sign-extends the 26-bit immediate and scales it by four; the x86 displacement is relative to the next instruction. These references describe encoding only, not YSM semantics. The Arm documentation page could not be fetched, so it was not treated as verified evidence.

## Windows: export RVA is not readable file code

The PE export table itself is file-backed and parsable, but its JNI_OnLoad RVA0x203f40 and JNI_OnUnload RVA0x203f50 lie in .text, whose virtual size is nonzero and SizeOfRawData is zero. The production-marker RVA0xd1df0c similarly lies in a virtual-only .data section. There is no corresponding static file byte range for these export entries under the section mapping. The scanner records file_backed=false and does not read bytes from offset0 or pretend RVAs are file offsets.

The image has several virtual-only original sections and data-bearing YSMS1/YSMS2 sections. That is a file-layout observation, not attribution of a packer, an unpacking recipe, or proof of runtime reconstructed contents. Actual loader effects and native implementation remain unknown. This explains why reading the Windows export table is insufficient to read its exported bodies from the file.

## Verification and next boundary

The inventory is recomputed from exact image bytes and compared with the stored result. Twelve synthetic tests cover signed branches, rejection of BL/unknown instructions, mapping offsets, virtual tails, overlapping ranges and truncation. GNU objdump separately agrees with both x86-64 five-byte branch targets. The A64 calculation is checked against the primary LLVM format/decoder and synthetic cases; no installed AArch64 disassembler or independent semantic reviewer was used.

The evidence contains no decoded subsequent control flow, JNI registration table or Java-method/native-address bindings. It must not promote the 17 Java native declarations to resolved implementations. Useful next analysis can start from the file-backed ELF targets while keeping Windows virtual-only exports explicitly unresolved; no protected payload was unpacked or modified here.
