# Native declarations: bounded Java invocation and bootstrap callers

PRIMARY_STATIC_REVIEW_ONLY. Fixed JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. This follows NATIVE-DECLARATION-INVENTORY without inspecting or executing native implementation code.

The exact 955-class scan validates all 17 declared targets before searching. It records 17 direct invocation sites in 17 complete caller-method snapshots and three matching bootstrap-argument records with invokedynamic user locations. Fourteen distinct native declarations have direct invocation references; three other declarations are bootstrap arguments. Together these account for the 17 declarations in the inventory, within the scan's narrow reference categories. No dynamic JVM dispatch, reflection, arbitrary method-handle constants or external/native-to-Java callback closure is claimed.

## Connections

- Common native initialization is called by the local checked-return wrapper. Common shutdown appears as the Runnable target used to construct a shutdown-hook Thread, not a direct invocation instruction. Registration does not demonstrate hook execution.
- Native texture cleanup and GeoModel native release appear as Consumer bootstrap targets in constructors. Their Java ownership/disposal protocols remain described by NATIVE-TEXTURE-JAVA-BOUNDARY and LOCATOR-MATRIX-PREPARATION; bootstrap presence does not prove disposal timing or native memory safety.
- Client native initialization has a local wrapper; model-data receive has both an ordinary connection/buffer route and a null-buffer abort route. A call instruction is a request, not evidence that native work finished.
- Server model enqueue has two Java producer sites (whole-server and single-player selection). Server native receive has an ordinary message-handler call and a null-buffer abort request. Reload has one Java wrapper site. The export declaration has a command-helper invocation in `ooooO0oo00ooO0Ooo0oOooOo` at offset 8 with CommandSourceStack/String/String caller descriptor. The scan does not execute export, infer native format/security semantics or independently audit that command's whole permission tree.
- Rendering has one direct wrapper invocation; five audio native declarations each have a direct Java wrapper/constructor site. Their argument validation, lifetime and unresolved actual native effects remain in the existing boundary cohorts.

The caller auditor has two exact-match/count checks and eight rejecting record-corruption controls. Its complete snapshots are compared against the eight boundary cohorts by the separate fixed9 NATIVE-CALLER-CHECKPOINT; no prior fixed manifest is expanded. Bootstrap user bodies are available in those existing boundary cohorts, not duplicated as direct callers here. Independent semantic review NOT_RUN, no runtime executed and no central mapping promotion.

This closes a Java-reference inventory question only. It does not establish full deobfuscation, native function identities, correct execution, callback schedules, or completeness of all foreign-library APIs.
