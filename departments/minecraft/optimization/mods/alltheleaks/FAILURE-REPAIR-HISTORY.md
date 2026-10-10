# AllTheLeaks 1.20.1 — scoped cross-project failure/repair and contrary outcomes

Period: 2025–2026 EventBus listener bug + AllTheLeaks Issues #70/#79/#99. **PARTIAL and source-selected**, not full issue archive or full 356 classes. Release binary and runtime NOT_RUN.

## ATL-EVENTBUS65 — actual Forge EventBus upstream repair, guarded by AllTheLeaks

[Forge EventBus PR #65](https://github.com/MinecraftForge/EventBus/pull/65) (merged **2025-01-22**), addresses EventBus #39: old `ListenerListInst#getListeners` retained built arrays after deregistration until a later call. PR replaces stale `shouldRebuild()` path with `null` marker invalidating cached listener array eagerly; also reduces lookup indirection and possible memory retention.

AllTheLeaks `Issue39` workaround for older Forge EventBus rebuilds all listeners during `ServerStoppedEvent` to flush old cached arrays; but such forced rebuild can create **never-used** listener arrays on newly fixed EventBus. On pinned [Issue39.java](https://github.com/pietro-lopes/AllTheLeaks/blob/5f4157f5362ea6471601114f8695ae44b0a3e28e/src/main/java/dev/uncandango/alltheleaks/leaks/common/mods/forge/Issue39.java), code checks detected EventBus version; for >=6.2.26 it **skips** installing repair.

[ATL Issue #79](https://github.com/pietro-lopes/AllTheLeaks/issues/79) (2026-01-20) warns Forge 47.4.16 and newer ship EventBus 6.2.33; reporter then adds [comment acknowledging existing skip](https://github.com/pietro-lopes/AllTheLeaks/issues/79#issuecomment-3775193796). **Important historical chronology**: selected ATL revision is from **2025-11**, already includes guard. #79 was a useful report of edge case / counterevidence, NOT proof a Jan2026 fix was committed. Runtime correct threshold must be validated with loaded eventbus JAR hash/version.

Causal lessons: a repair of an old framework bug can become a regression after upstream resolves bug; detect dependency version before installing hook, and stop work around when no longer needed. Unlike speculative mods, this chain has actual upstream PR patch + selected ATL guard source. No game replay.

## ATL-70 — retention with chunk pregeneration, attribution unresolved

[Issue #70](https://github.com/pietro-lopes/AllTheLeaks/issues/70) (2025-12-28): reporter's 1.20.1 Forge pack including AllTheLeaks 1.1.1 displayed growing memory while Chunky pregeneration. Author requested `spark heapsummary`, comments noted ~80k resident chunks. User later suspected Fast Async World Save or Smooth Chunk Save stopped saving/flush; problem improved removing those mods, not directly blamed on ATL by evidence. That attribution remains **USER_INFERENCE**, not source-proven root cause. Investigate saved chunks vs retained heap path independently.

## ATL-99 — unresolved sustained heap across pregen

[Issue #99](https://github.com/pietro-lopes/AllTheLeaks/issues/99) (2026-06) reported Forge 1.20.1 memory high after chunk pregeneration/loading despite `/atl force_refresh`. Does not prove ATL-induced leak or success of forced GC; retain logs/heap before causal conclusion.

**No performance/GameTest/correctness reconstruction on user's JAR**, history adapter raw CAS IDs unavailable, so this is a scoped research-draft.
