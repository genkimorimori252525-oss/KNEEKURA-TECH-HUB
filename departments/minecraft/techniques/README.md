# Minecraft Reusable Technique Notes

This directory stores **cross-target engineering techniques** recovered from MOD/source/runtime analysis.

It is not:
- a copy of upstream source;
- a product source directory;
- a replacement for Source → Evidence → Claim governance;
- proof that a technique is safe on every version/loader.

A technique note should state:
- originating target/revision/evidence;
- invariant engineering idea;
- implementation-specific details that must not be generalized;
- ANCHOR adaptation notes;
- known failures/counterexamples;
- products currently evaluating/adopting it.

Product code remains under `deliverables/`. A product may link a technique in its `ADOPTION.md`.

## Current notes

- [Boss combat state machines and lifecycle boundaries](boss-combat-state-machines.md)
