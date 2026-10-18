# Isolated loader and platform scenarios

This checkpoint adds optional counterfactual inputs, not recovered host loader metadata. Original-image permissions, unknown-byte guards and transactional instruction behavior remain unchanged. Neither target imports nor host OS APIs are called.

## Loader contract

The verified dladdr JMP thunk is at 0x13d8466, GOT 0x184d820, ELF GLOB_DAT symbol 276. --virtual-loader image-only supplies a read-only synthetic name /virtual/libysm-core.so, image base zero, and no matching symbol. Its 32-byte Dl_info layout contains four 64-bit pointers. It validates the query belongs to a modeled image region, the output is private memory, the import slot/code match and the caller return address is valid before writing. The name is not executable or guest-writable. Success returns 1.

--virtual-loader unavailable returns 0 and does not initialize the output buffer. Default disabled retains the prior unresolved-import stop. These scenarios do not claim to reproduce the actual process loader. API layout and success/failure meaning follow the [Linux man-pages dladdr documentation](https://www.man7.org/linux/man-pages/man3/dladdr.3.html).

The first synthetic successful lookup leads to open('/virtual/libysm-core.so', O_RDONLY), JMP thunk 0x13d84a7, GOT 0x184d870, symbol 286. The unavailable lookup reaches sysconf(30), pushed-slot RET thunk 0x13d84cf, GOT 0x184d898, symbol 291. The number 30 is the Linux/glibc SC_PAGESIZE ABI selector; it is not a real page-size observation.

## Optional bounded platform input

--virtual-platform explicitly models only the exact virtual module path with read-only flags returning open failure (32-bit -1), and sysconf(SC_PAGESIZE) returning a declared 4096-byte page size. Other paths, flags and sysconf selectors stop. The fixture supplies no errno/TLS state. No actual file is opened, no host page-size query is used, and the original file remains unmodified. These failure inputs explore a conditional path, not success of opening/mapping the module.

12 loader tests and 5 platform tests cover layouts, return-frame variants, disabled modes, invalid slots/thunks, unknown/invalid caller returns, query bounds, private-write bounds and rejected requests. Existing 24 guard tests and 8 CRC test methods are also required. No target executes on the host.

Use the pinned original ELF and external Unicorn venv with the CRC command from the preceding checkpoint, adding --virtual-loader image-only (or unavailable), optionally --virtual-platform. Keep binaries and full traces outside Git. Original-image writes and unmodeled calls, including memory-protection changes, still stop. No mapping or runtime binding promotions; independent semantic review NOT_RUN.

## Retained target outcomes

The image-only loader plus open-failure/page4096 scenario completes 1,460,181 instruction/model steps. The unavailable-loader plus page4096 scenario completes 1,370,841. Both retain nine CRC summaries and all 12 static oracle checks, then stop at the same mprotect import: pushed-slot RET 0x13d84d6, GOT 0x184d8a0, GLOB_DAT symbol292. Both request address0xec5000, length0x510e52, protection7 (read/write/execute). No permission change is applied. This agreement is limited to these two synthetic scenarios.

The requested interval ends at0x13d5e52 and concerns original-image memory. The next task is to inspect its caller and intended write behavior without granting host permissions or applying original-image writes. The paired JSON records exact trace/source hashes and states. Initialization remains unfinished.
