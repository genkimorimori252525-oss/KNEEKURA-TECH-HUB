# Collector callback metadata

Two exact private static members were verified in the original YSM JAR.

- `0xd35598+0x58` → `com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO.Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/ooOOOo00o0000o0oO000oooO;Ljava/lang/String;ZZ)V`; callback `0x410460`; 2,584,488 virtual instructions.
- `0xd35598+0x60` → `com/elfmcys/yesstevemodel/o0OooO00ooo0OO000O0OoOoO.Oo0Oo0o00O00Oo0OOoOOoooo([Ljava/lang/String;[Ljava/lang/String;[Ljava/lang/String;[Z)V`; callback `0x410480`; 2,370,227 virtual instructions.

The exact initializer raw-byte proof, immutable input hashes, callback/payload digests, original classfile proof, unchanged JNI ledger, and frame/register checks are retained in the accompanying JSON. These identities do not establish runtime invocation, task execution, successful asset processing or semantic aliases. No repository files or the central mapping were changed.

Suggested separate static join document: `NATIVE-COLLECTOR-PUBLICATION-JOIN-2026-10-18.md`. The static-analysis worker owns its dataflow and publication claims.
