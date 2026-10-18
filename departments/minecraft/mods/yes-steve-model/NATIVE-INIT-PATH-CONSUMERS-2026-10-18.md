# Native path consumers: bounded static review

Only original-byte reading/disassembly and immutable checkpoint reads were performed. No target/native/JVM execution, checkpoint resume, host filesystem scenario success, asset decoding, or repository edit.

## Result

The first useful contract after temporary-directory selection is a distinct native owned path graph, followed immediately by an independent child-directory status/creation boundary. It is not a generic permission to make OS calls succeed.

## Retained configuration paths

After CONFIGDIR string extraction and join with yes_steve_model at 3d58a5, the native path is moved into global object d35348 (pointer write 3d58e6, length/capacity 3d58ed..fa, component representation transfer to d35368 at 3d595a..6f). Stack sources are zeroed and destroyed. Thus global lifetime must not alias a released JNI UTF borrow or stack path storage.

The same copy-left/append-right helper 35caa0 builds further owned paths; its body copies string storage and component representation then calls 31cc30. Child globals include custom=d352d0 (join3d5a93), auth=d35320 (join3d5c3b), builtin=d352f8 (join3d5de9), export=d35230 (join3d5f6e). Literal cache is joined at3d60f5, then server_index at3d6181 and stored at d35148. These are intended path values, not observed filesystem contents. General append edge cases remain unaudited.

## Temporary path and immediate next filesystem boundary

3d661b calls311760 with destination stack+60. If directory validation returns normally,3d6620 loads literal43437="ysm" and3d662f constructs its path object via3db8d0. Join3d6646 builds <selected-temp>/ysm into stack+08. Original temp-root and suffix temporaries are destroyed before3d66d0 calls313c20 on that child.

313c20 initializes an error_code, calls312a00 at313c43, and throws if its error code is nonzero. 312a00 first checks empty path, then calls311210 at312a4b. Therefore even explicit success for stat(selected-temp) cannot imply success for stat(selected-temp/ysm). Existing-directory status tag2 returns without creation. Non-directory/error branches are separate contracts. The larger routine walks parent paths and calls311350 at312e6a/312eca;311350 invokes mkdir(path,0777) at311364 through d14ab0. Two-stage ELF import resolution identifies mkdir; see NATIVE-INIT-PATH-LITERALS-2026-10-18.json. On EEXIST it rechecks directory status at3113ba. No mkdir outcome, umask, permissions or path-state transition is inferred.

After this operation returns, native code constructs 17-byte remote_model_info at3d66f3..670f, joins it to stack+08 at3d6742, and moves the resulting owned path into global d34fb0 (pointer3d677e, length/capacity3d6785..92, component field d34fd0 at3d680d). This is <selected-temp>/ysm/remote_model_info, not a claim that it has been opened or written.

Later config-related operations include311020(builtin) at3d68c7, whose deeper operation is not resolved here, and313c20 on custom/auth/builtin/export and other globals at3d68d3..6918. 3d6946 passes a builtin-relative path, a 100-byte warning message about clearing the directory each game start, and length100 to4dfb30. That helper initializes stream-like state and may create the parent path, but its complete open/write protocol and the global child filename d34f88 remain missing identities. The message itself does not establish actual deletion.

## Next JNI identity boundary

After cleanup,3d6b59 is JNI+488 GetStaticObjectField using manager d35588+48. Immutable earlier checkpoint metadata resolves this to net/minecraftforge/fml/ModList.INSTANCE:Lnet/minecraftforge/fml/ModList;. 3d6bdb is JNI+2f8 GetObjectField using d35588+50, resolved to ModList.fileById:Ljava/util/Map;. See NATIVE-INIT-MODLIST-FIELDS-2026-10-18.json. This is a new typed ModList singleton and Map content/lifecycle contract; FMLPaths or FMLEnvironment state alone does not supply it. No map membership, mod-file objects, initialized ModList state, or JNI_OnLoad completion is established.

## Recommended scope and stop

For research/model planning, retain explicit owned config/temp path identities, bounded append semantics, immutable scenario provenance, and move/destruction lifetime. The later explicit absent-environment cohort has now reached the unchanged stat(selected-temp) guard on `/tmp`. Any later separately reviewed directory-status fixture must stop again at unresolved stat(<temp>/ysm), mkdir, directory traversal/removal, stream opening/writing, or ModList object/map identities. Do not collapse these into a blanket filesystem-success fixture or per-PC success stubs.

Evidence windows and hashes are in NATIVE-INIT-PATH-CONSUMERS-EVIDENCE-2026-10-18.json; import/literal provenance in NATIVE-INIT-PATH-LITERALS-2026-10-18.json; checkpoint-derived field metadata in NATIVE-INIT-MODLIST-FIELDS-2026-10-18.json. Some broad windows end mid-instruction; claims use complete instructions strictly before those endpoints. The 3d61ff window starts at the prefix of the instruction truncated in the previous window. Original image SHA256 is pinned by extract.py. Runtime import binding remains unverified.

## Subsequent closure

The [cleanup and notice-output continuation](NATIVE-BUILTIN-CLEANUP-NOTICE-2026-10-18.md) resolves the earlier missing filename and distinguishes recursive-removal intent from directory status checks. Its later exact findings supersede the missing-identity statements above; no filesystem behavior was executed.
