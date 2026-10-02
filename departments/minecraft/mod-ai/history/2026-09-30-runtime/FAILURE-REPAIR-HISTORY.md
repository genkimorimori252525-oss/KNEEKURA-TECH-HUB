# Bounded runtime failure and repair history

The 2026-09-30 batch did not establish the planned staff or Hydra runtime acceptance. These are two additional cases, separate from the preserved M2 history. Minecraft 1.20.1, Forge 47.4.6, Java 17, Gradle 8.8 and ForgeGradle 6.0.54 were used.

## Empty optional generated resource root

Receiving-client and control-client preflights were each rejected twice. Neither client JVM launched. After the server Gradle run, a formerly absent optional generated-resource directory existed but contained no files. Revalidation selected an empty inventory that was absent from the original captured closure and rejected it.

The repair treats only a proven directly empty real optional resource directory as the existing absence representation. It preserves rejection for nonempty or hidden content, symlinks, unreadable directories and missing mandatory outputs. The focused regression was RED with 1 failure and 7 passes; the repaired related suite recorded 66 passes and 16 deselections. The second live preflight used already-imported old controller code. No repaired fresh-process live result is claimed.

Repair SHA-256: 55489a97311ce5f310365efa48e53dbf17de8d7f8a2f41dacbcff567800d7582
Regression SHA-256: a270e1de1567564c058cfa3d71bacf4df3e2ad0fed7feb5328165866bd372039

## Late Forge gameDir append

Both Hydra JVM startups completed with exit code 1 before a window or world. The duplicate gameDir failure recurred after an intermediate ordinary-provider patch recorded 34 passing offline tests.

Actual ForgeGradle inspection found empty ordinary task arguments and providers, with the default gameDir in RunConfig. MinecraftRunTask.exec appends token-expanded RunConfig arguments after doFirst, and also sets workingDirectory and additional client arguments. The provider-only patch therefore guarded the wrong execution layer. Its passing tests are retained alongside the contrary actual startup result.

A subsequent pre-expansion patch passed 23 actual-task and 103 adjacent tests, but four new controls exposed duplicate lazy-token evaluation and premature provider timing. Those contrary results and intermediate bytes are preserved. The corrected final-provider boundary leaves stock Forge expansion intact and validates after inherited setup. Its actual inherited Forge task and JavaExec.copyTo fixture recorded 35 passes. A separate adjacent run had 70 passes and 10 fixture compilation failures caused by variable shadowing; the fixture-only rename then passed all 10 affected cases with the production repair unchanged. The fixture captures the final process specification instead of starting Minecraft. Hydra rendering, selected entity observation and screenshot acceptance remain NOT_RUN.

Corrected guard SHA-256: 5b2b4f5244678280bc28246897e49c1ec5967dcc5be7050bd97b351ba04e5193
Regression SHA-256: c2f79119ffcc163a724b54d8c447cbd1c3919df8dc5ebe35a650a8073fefb9da

Insufficient intermediate patch SHA-256: b7d96af5a00302c3b30c3d2dd2c948643f114b3cfe027825673d253b08523550
Hydra attempt 1 receipt: 89837352c404431cd8acb191e4dadb21d53dc7f542e3d0e5fb62e56a691d7c3a
Hydra attempt 2 receipt: dc5683b97ae6e7fc17dc8876d00248217f6a94bba21a95a98aae5902943b4a20
ForgeGradle JAR SHA-256: 1d54a97a225ed5180300e8070a1c818597d98ec45a11fedecb425254b7982da2

## Evidence and limits

History hash: 9ff2128604f3e552dd9f8fb99b3f43f70bbd02c4c49906b9b93ff8b76ba29147
Previous immutable draft history: 00f7d2b31b4e2eb2fdb7511cdf803bee92ef2e3548f449b124ec3dc235c668cc
Original evidence index: 2667cbde973a137c07fd77eafa078783de4ce6c3c01c5c1820e8fd3e4abd9228
Preserved earlier history: 4abaa63aa724be619293fbcfd8143f0676c4fa5f01d03a2cfcc4093fb2074971

The structured record uses the existing failure-history adapter and exact captured document membership. Both cases query successfully; missing evidence lists are empty. Coverage stays PARTIAL because live acceptance remains unresolved. The existing history adapter also passed all 16 tests; a changed-filter cursor was rejected during record verification. Import writes zero canonical records and provides no runtime attestation. Original receipts and logs remain retained outside the shareable files; this document contains derived results and immutable identities only. No further launch, publication or Core promotion is authorized by this record.

Additional repair evidence index: 451ed4c98cd61fd33e0cf7613055a72c637b5399282ad8018404e7abce75887a
