# Five client registration wrappers: static forwarding and registry contract

## Result

The five separately decoded registrations target existing LWJGL OpenGL 3.3.1 public static native declarations. One wrapper forwards deletion first and then removes keys from a native integer set. Four wrappers test their first Java integer argument against that set: a match returns without calling the saved LWJGL export; a miss tail-forwards the original argument sequence. The inspected code establishes no protective or malicious intent and no successful runtime installation or GL behavior.

`reproduce.py` freshly verifies the original SO, separately supplied metadata receipt, exact official dependency JAR/class/native declarations, original GL11C constant values, seven extracted code ranges and six saved-export identities. It does not execute native code, Java, an emulator, or a GPU. [evidence receipt](NATIVE-LWJGL-WRAPPERS-EVIDENCE-2026-10-18.json) pins the original metadata receipt SHA256 `19237b6d0385d888a9cdcc4735b31ceab7cb1dc6de3f39c1bafe53ed55a57811`; that receipt and the prior 17-binding receipt are unchanged. The dependency is an official Minecraft 1.20.1 declared artifact, not evidence of the user's installed runtime.

## Exact registration and forwarding targets

The earlier client-startup receipt establishes that these five records are passed to registration helper327000 at3bd5d8, after the following export slots have been populated. Listing a conditional registration attempt does not assert an effective override.

|Native entry|Exact Java method|Saved export slot|Export symbol|
|---|---|---|---|
|3c2320|org/lwjgl/opengl/GL11C.nglDeleteTextures(IJ)V|d35a68|Java_org_lwjgl_opengl_GL11C_nglDeleteTextures__IJ|
|3c2560|org/lwjgl/opengl/GL11C.nglGetTexImage(IIIIJ)V|d35998|Java_org_lwjgl_opengl_GL11C_nglGetTexImage__IIIIJ|
|3c2650|org/lwjgl/opengl/GL45C.nglGetTextureSubImage(IIIIIIIIIIIJ)V|d359a0|Java_org_lwjgl_opengl_GL45C_nglGetTextureSubImage__IIIIIIIIIIIJ|
|3c2740|org/lwjgl/opengl/GL43C.glCopyImageSubData(IIIIIIIIIIIIIII)V|d35990|Java_org_lwjgl_opengl_GL43C_glCopyImageSubData|
|3c2830|org/lwjgl/opengl/GL43C.glTextureView(IIIIIIII)V|d359b8|Java_org_lwjgl_opengl_GL43C_glTextureView|

Each saved slot is the result of dlsym against the opened LWJGL module in startup. None of these five wrappers performs its own null-pointer guard on the saved forwarding slot. Startup checks are a prerequisite, not proof of present runtime validity.

## Shared native registry

The inspected code operates on a chained/bucketed integer set with bucket pointer d348e8, bucket count d348f0, before-first node d348f8, element count d34900. Nodes have a next pointer at+0 and a 32-bit key at+8. Match tests compare the full 32-bit key; hashing uses the sign-extended integer and an unsigned remainder with a 32-bit fast path when both operands fit. This structural description does not assume a source-level C++ container name.

All four checking wrappers read the same set. They follow bucket chains when count is nonzero, or the linked-list path when count is zero. They do not modify its keys/count, acquire a lock, perform JNI calls, or write the caller's pixel buffer in the wrapper body. Absence of a lock here is not a whole-program race finding; calling-thread ownership remains unproved.

One concrete producer is function3a52c0, additionally traced from original bytes:

1. `3a52d7..3a52e3` calls saved export d35ad8, exact `Java_org_lwjgl_opengl_GL11C_nglGetIntegerv__IJ`, with query0x8069 and a stack pointer. Original official GL11C ConstantValue confirms0x8069 is GL_TEXTURE_BINDING_2D.
2. The queried 32-bit value is loaded at3a52e9. Zero returns at3a52f1→3a5815, without insertion.
3. The nonzero path sets texture parameters and performs saved TexImage2D/TexSubImage2D calls using target0xde1, format0x1908 and type0x1401. Exact original constants establish GL_TEXTURE_2D, GL_RGBA and GL_UNSIGNED_BYTE. TexImage2D at3a5390 passes a null pixel pointer; later TexSubImage2D at3a547a passes the caller-supplied pixel pointer. Width/height are preserved from incoming EDX/ECX. This is an allocation/upload request path, not observed GPU success.
4. After those calls return,3a5480 onward searches for the queried texture-binding key. Existing membership returns without duplicate insertion. Missing membership allocates a16-byte node at3a5584, writes the key at3a5593, optionally grows/rehashes buckets, links the node and increments d34900 at3a580e. No GL-error query appears between those upload calls and insertion; insertion alone does not prove upload success.

This establishes that at least one producer inserts nonzero bound-2D texture names. It is not an exhaustive inventory of every producer or lifetime path.

## Deletion wrapper3c2320

At entry, RCX (the second Java argument, a native address) is saved in RBX and EDX (count) in EBP. `3c2330` sets ESI=0, replacing the JNI jclass argument, and `3c2332` calls saved original export d35a68. JNIEnv RDI, count EDX and address RCX remain the original arguments at the call. No deletion IDs are filtered and count is not rewritten before forwarding.

Only after that call returns does `3c2338..3c233a` test count. Count<=0 returns without traversing the array. Count>0 iterates exactly count 32-bit integers from the originally supplied pointer (`3c238f`), looks each up in the set, unlinks a matching node, frees16 bytes at3c236d, and decrements element count at3c2379..3c237c. Absent keys are skipped. Repeated IDs therefore only remove a present node once. There is no pointer-range validation or GL-success test in this wrapper.

Order matters: the forwarded LWJGL call precedes every registry erasure. This does not prove GL deletion succeeded; if the call returns with a GL error or a pending Java exception, the native body contains no corresponding check before erasing. If control does not return normally, this demonstrated erasure sequence is not established.

## Four membership-check wrappers

All four preserve their first Java integer argument from EDX into R10D, use it as the lookup key, and then choose:

|Entry|Match return|Miss load/jump|Semantic argument caution|
|---|---|---|---|
|3c2560|3c2631..3c2636|d35998 at3c2637; jump3c2646|nglGetTexImage's first argument is the target enum, not a queried bound texture name|
|3c2650|3c2721..3c2726|d359a0 at3c2727; jump3c2736|First argument is the texture argument|
|3c2740|3c2811..3c2816|d35990 at3c2817; jump3c2826|Only the first/source-name argument is tested here; no destination-name test|
|3c2830|3c2901..3c2906|d359b8 at3c2907; jump3c2916|First argument is the new/destination texture argument; no original-texture argument test|

On match, the function simply restores saved registers and returns void: there is no replacement pixel fill, Java exception creation, or alternate GL call in that path. On miss, EDX is restored from R10D; saved RBX/R14/R15 and stack pointer are restored; JNIEnv, jclass, RCX/R8/R9 and stack-passed Java arguments have not been modified. A tail jump forwards all original Java argument values. Unlike deletion, these four do not zero the JNI class argument.

Do not collapse this into 'all protected textures cannot be read/copied'. The exact predicate is membership of the first integer's numeric value; the API parameter meaning differs. In particular the GetTexImage predicate compares a target enum numerically against this set and does not query GL_TEXTURE_BINDING_2D. These observations are bounded semantics, not an asserted bug, security boundary, or author intent.

## Limits

No actual RegisterNatives replacement, module/driver compatibility, GL context, rendering, pixels, deletion outcome, exception state, or concurrent use was observed. No whole-program interception/registry coverage or all texture lifetimes is claimed. Fresh dependency declaration checks establish signatures, not installed-version identity. This static follow-up closes the five callback identities and their direct wrapper behavior while leaving manager d355e8/+60's Java identity and earlier opaque startup guards separate.

### Primary parameter-role sources

The separate analysis independently checked the exact-version generated sources [GL11C.java](https://raw.githubusercontent.com/LWJGL/lwjgl3/3.3.1/modules/lwjgl/opengl/src/generated/java/org/lwjgl/opengl/GL11C.java) and [GL43C.java](https://raw.githubusercontent.com/LWJGL/lwjgl3/3.3.1/modules/lwjgl/opengl/src/generated/java/org/lwjgl/opengl/GL43C.java). GL11C names the first nglGetTexImage integer `tex`; its wrapper annotates it GLenum and accepts texture-target constants, so the report's 'target' wording describes its API role rather than claiming the Java parameter is literally named target. GL43C.glTextureView names the first GLuint `texture`, with source `origtexture` third. These parameter roles supplement exact original dependency classfile descriptors; neither source nor classfile establishes runtime override installation.
