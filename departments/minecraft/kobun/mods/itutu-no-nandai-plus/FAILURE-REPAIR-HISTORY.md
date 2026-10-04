# Failure / repair lessons

Status: **bounded historical review / runtime NOT_RUN**

This is not an exhaustive issue tracker reconstruction.

## F1 — packaging metadata can lie

**Observed:** bundled `mcmod.info` in the X1 core is an Example Mod placeholder, while the actual `@Mod` annotation declares `THKaguyaMod`, "Itutu no Nandai MOD+" and version 2.90-1.7.10.

**Lesson:** historical MOD identity must be triangulated from executable metadata, archive contents and distribution context. One metadata file is not automatically authoritative.

## F2 — hidden optional dependency became a hard JVM linkage failure

**Binary:** TOHOU MAIDs directly references `illusion_Laser.Item_LaserCore` but declares only THKaguyaMod + lmmx.

**ERA-CONTEXT:** a 2020 crash reports `NoClassDefFoundError: illusion_Laser/Item_LaserCore` in `New_EntityMode_Toho.onUpdate`.

**Lesson:** optional integrations must be separated behind presence checks/adapters before class linkage. A class reference inside normal method bytecode can turn an apparently optional addon into a runtime hard dependency.

## F3 — list size is not an ID allocator

**Binary:** automatic maid mode ID uses `maidEntityModeList.size()+1`.

**ERA-CONTEXT:** a user reports that `-1` automatic allocation still conflicts with/replaces Fencer.

**Lesson:** numeric extension registries require explicit free-ID checking and ownership. Modern systems should use namespaced IDs.

## F4 — SRG/runtime symbol mismatch on dedicated server

**Binary:** `ItemSakuyaWatch` invokes `EntityPlayer.func_71052_bv()I`.

**ERA-CONTEXT:** a dedicated-server crash reports `NoSuchMethodError` for that exact symbol.

**Lesson:** mappings and transformed runtime symbols are part of artifact compatibility. Client success or a nominal Minecraft version does not prove dedicated-server symbol compatibility.

## F5 — source loss converted maintenance into archaeology

**ERA-CONTEXT:** Illusion Laser's author later reports the source code was lost and decompilation was the remaining maintenance path.

**Lesson:** preserve distribution hashes, class inventory, protocol formats and behavior maps even when source is currently available. Historical source lineage can disappear.

## F6 — names are discovery hints, not behavioral proof

**Observed:** `THKaguyaTimeStopEventHandler` exists and is registered, but its supplied `CanUpdate` handler is effectively no-op. Actual time stop is performed elsewhere by state rollback.

**Lesson:** do not infer mechanics from class names/registration. Verify bytecode/call flow.

## Positive pattern P1 — collision-aware spell extension

Add_Last Judgment scans spell IDs from 60 upward until a free registry slot is found before registering.

That is a historically sensible mitigation for a shared numeric registry, even though a modern namespaced registry is safer.

## Positive pattern P2 — addons reuse the core instead of forking it

Sakuya, Last Judgment and Illusion Laser all reuse core entities/registries/geometry rather than duplicating the entire danmaku subsystem.

This is a strong ecosystem design lesson worth retaining.
