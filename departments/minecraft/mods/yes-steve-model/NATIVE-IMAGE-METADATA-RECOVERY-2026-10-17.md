# Native image metadata: cross-platform static starting points

PRIMARY_STATIC_REVIEW_ONLY. This is a new file-format-level inspection of the three native members in the exact YSM JAR, not native execution or implementation decoding. JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. Image hashes and reproducible tool output fields are in NATIVE-IMAGE-METADATA-2026-10-17.json. Extracted images and raw binutils output remain outside Git.

## Exact members

| JAR member under META-INF/native | Bytes | Format / machine | Header observation |
|---|---:|---|---|
| libysm-core.so | 24,602,080 | ELF64 little-endian / x86-64 (62) | 12 program headers, no section-header table |
| libysm-core-android.so | 16,593,440 | ELF64 little-endian / AArch64 (183) | 11 program headers, four section headers |
| ysm-core.dll | 17,400,648 | PE32+ / AMD64 (0x8664) | Native DLL headers, not a Java class file |

The filenames are member labels; no claim is made that a particular user's machine loaded them. ELF OS/ABI reports System V for both ELF images and is not itself proof of supported distribution or Android runtime version.

## Dynamic metadata works where section-based listing did not

The initial readelf --dyn-syms listing did not expose symbols for these unusual section layouts. `readelf -DsW` reads dynamic symbol metadata instead and produces 298 symbol rows for the x86-64 image and 223 for AArch64. Each has three named defined dynamic symbols: JNI_OnLoad, JNI_OnUnload and YSM_FORGE_1200_PRODUCTION. Windows objdump -p likewise exposes those three named exports. This avoids incorrectly treating an empty section-based listing as absence of JNI entry points.

The Linux JNI symbol entries report sizes of five bytes and Android four bytes. These are symbol metadata values, not recovered function-body lengths or proof that full initialization fits in those sizes. Android's reported BAD section indices reflect indices beyond its small section-header table; this observation does not prove the image cannot load because runtime loading and native code were not tested.

ELF dynamic metadata lists libjvm along with platform libraries; Windows's interpreted import table lists jvm.dll, KERNEL32.dll, SHELL32.dll and bcrypt.dll. These are static declared imports only, not a full dynamically resolved dependency graph. The DLL's stored timestamp, section names and marker export are recorded as metadata, not authenticated build history or attribution to a protection product. Binutils emits an ignored IMAGE_SCN_MEM_NOT_PAGED flag warning for YSMS2; the diagnostic is retained, not silently discarded.

## Relationship to Java's 17 native declarations

The three exported names are not one-to-one implementations of the 17 ACC_NATIVE Java declarations. No native address-to-Java-method binding has been recovered by this inspection. Absence of individual Java_* names in these defined/named export lists does not identify the binding mechanism, JNI_OnLoad body, protection layer, callbacks or native behavior. No RegisterNatives call has been established here.

Vineflower/javap remain useful for the Java side; ELF/PE image metadata requires a different parser. Existing installed GNU binutils 2.44 was used only to read files. No new tool installation, loading with System.load/ctypes, native payload unpacking, emulation, decryption or bypass was performed.

## Reproduction and limitations

Run tools/native_image_metadata_ysm_265.py with --jar and --out, then --check. It checks exact JAR/image hashes, extracts to a temporary directory, reads bounded headers and invokes readelf/objdump as parsers; it never executes an extracted image. Six synthetic header tests cover ELF architecture/sectionless headers, PE32+ and rejection cases. Recomputed evidence matched exactly with the installed tool versions; a different binutils version can require review rather than silent acceptance.

Next native work must preserve image hashes/architecture, resolve actual binding/control flow with evidence and distinguish file-layout facts from runtime behavior. This record makes no claim of native semantic completion. Independent semantic review NOT_RUN; central mapping unchanged.
