# FastSuite — bounded history and conflicting reports

Scope: 2025 `#44` / commit `49971164e235bfc819a4cca896baa95575df9cf2` on **newer 1.21+ API**, plus 2025 `#47` report. Not exhaustive, and not direct ANCHOR 1.20.1 behavior evidence.

## FS-44 — shared `StackedContents` in parallel recipe matching

- [Commit 49971164e235](https://github.com/Shadows-of-Fire/FastSuite/commit/49971164e235bfc819a4cca896baa95575df9cf2) dated 2025-04-22 says “Fix leaking StackedContents across threads” and adds `CraftingInputMixin.stackedContents()` that **returns a new StackedContents each call**. Parent `ef4d391c7a3a163571ca36364e1007bd1a020d4a`.
- The patch itself explains cached `StackedContents` in `CraftingInput` is not thread-safe, leading to rare matching failures and downstream behavior. This establishes the **author's diagnosis and concrete repair**, not recreated runtime fix evidence.
- **Version:** newer RecipeInput API, not the selected ANCHOR-adjacent `1.20` source. Backport requires checking actual 1.20.1 `CraftingContainer` and `StackedContents` lifecycle.
- Lesson: a "thread-safe" Recipe class isn't enough when the **input container's lazy cache** is shared across worker threads.

## FS-47 — disproved/at least contested attribution

- [Issue #47](https://github.com/Shadows-of-Fire/FastSuite/issues/47) reports occasional freeze in ATM10. Maintainer responds no FastSuite-related errors appear, suspects MiniHUD. Reporter then describes a MiniHUD/JEI/EMI change which changed result.
- This is **CONTRARY_EVIDENCE** to “FastSuite caused the freeze”. No root cause established and **no linked FastSuite repair diff**; do not import as known FastSuite failure. Separate recent 1.21.x modpack from user 1.20.1.
- Benchmark and post-fix game tests NOT_RUN, GitHub author history only.
