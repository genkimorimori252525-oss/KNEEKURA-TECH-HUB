# Eight ordered initializer callbacks completed

DT_INIT remains complete under the declared isolated scenario. Init-array callbacks0 through7 have now returned in order, preserving callee-saved registers and the exact callback return frame. Callback8(entry0x326630) stops at lazy index122 __tls_get_addr, descriptor0xd2cf38. This is8/45 callback completion, not a percentage of the entire deobfuscation project.

## C-locale support without host locale access

A narrow synthetic GNU C-locale fixture supplies only public ctype/name fields, ASCII classification/conversion tables, C-handle lifetime, logical uselocale, and required wide-character predicates/conversions. Private __locales fields remain unknown. Its readonly storage is reserved from the top of the existing1MiB private budget, leaving normal allocation addresses unchanged. Unknown locales, descriptors and unsupported operations stop.

Contracts were checked against primary GNU libc sources: [locale layout](https://github.com/bminor/glibc/blob/glibc-2.39/locale/bits/types/__locale_t.h), [ctype bit encoding and index domain](https://github.com/bminor/glibc/blob/glibc-2.39/ctype/ctype.h), [C-locale creation](https://github.com/bminor/glibc/blob/glibc-2.39/locale/newlocale.c), [C-handle duplication](https://github.com/bminor/glibc/blob/glibc-2.39/locale/duplocale.c), [C-handle free behavior](https://github.com/bminor/glibc/blob/glibc-2.39/locale/freelocale.c), and [thread-locale selection](https://github.com/bminor/glibc/blob/glibc-2.39/locale/uselocale.c). These define the fixture's supported ABI subset, not the user's actual libc version or environment.

Bounded byte/string models cover memcpy, memcmp, strlen, strcmp and strncmp. Private and granted working-image destinations obey the same write ledger; overlap-undefined memcpy, unknown sources and readonly destinations stop. Existing memset now follows this shared destination guard. Heap aliases model malloc/free and C++ delete, with no reuse, invalid/double-free rejection, and unknownness restored for freed storage. No host libc/allocator is invoked.

## External data is not silently zero

The artifact has eight unresolved external-object slots. Treating their raw zeros as resolved pointers is unsafe in an analysis image mapped at base0: a zero pointer could incorrectly read the ELF header. Native/model reads now stop at unresolved object slots. A fresh guarded replay confirmed the first such boundary is stdout during callback0, before the previous raw-slot locale frontier. Earlier exploratory callback completions without this guard are not authoritative for external-data reasoning.

The authoritative continuation installs explicit standard-stream pointer variables, each pointing to an opaque unmapped FILE token. No FILE contents, actual stream access or output is fabricated. Their first-use bindings are recorded separately from native writes; all other unresolved objects remain guarded. The sequence driver rejects older snapshots predating this guard. These three logical loader bindings preserve guest page permissions and immutable reference bytes.

## Registration, environment and tail returns

__cxa_atexit only records bounded callback/argument/DSO tuples; it neither registers with the host nor invokes destructors. secure_getenv models only an explicitly absent GLIBCXX_TUNABLES key. A modeled import may finish a tail-called initializer only with the verified sentinel and exact post-return stack; wrong stack or unregistered return targets still stop.

The current authoritative chain begins with the fresh external-data-guarded replay, then resumes from its first stdout use with opaque stdio bindings, C-locale/memory support, environment absence and bounded malloc. Eight callbacks complete; none are skipped. The paired JSON preserves chain hashes, cumulative steps and completion events.

## Next frontier

PT_TLS has216 initialized bytes,15408 total bytes and16-byte alignment. Three symbol-zero DTPMOD64 descriptors occur at0xd2cf38,0xd2d020 and0xd2d030, with offsets0,0xf0 and0xe8. Their module IDs remain unresolved. Next add a bounded single-virtual-thread TLS template and explicit local module ID, based on the original PT_TLS metadata and TLS ABI. Do not access host TLS or silently treat module0 as valid.

163 scoped tests pass, including fixture/memory lifetime, external-data guards, readonly state/checkpoint restoration and tail-return tests. Original file/reference preserved; mutations are confined to the verified working copy/private storage. Central mapping669 unchanged; independent semantic review NOT_RUN. JNI lifecycle and native method bindings remain unresolved.
