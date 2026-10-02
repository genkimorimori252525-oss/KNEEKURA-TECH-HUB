# Bedrock Wither Reconstruction

Deliverable ID: `minecraft/bedrock-wither`  
Lifecycle: **PROTOTYPE**  
Anchor: Minecraft Java Edition 1.20.1 / Forge / Java 17

## Purpose

Build a standalone Java Edition boss that reproduces the **observable Bedrock Edition Wither behavior** as closely as supported by evidence and bounded runtime comparison.

This directory is the product home. It is deliberately separate from the Hub's Wither research/design.

## Where to start

For another AI:

1. Read [STATUS.md](STATUS.md).
2. Read [ADOPTION.md](ADOPTION.md) before importing a researched technique.
3. Product code is under [mod/](mod/README.md).
4. Product decisions and failures are under [history/](history/README.md).
5. Small verification receipts belong under [evidence/](evidence/README.md).

Research authority:
- [Design](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/DESIGN.md)
- [Source ledger](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCES.md)
- [Acceptance](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/ACCEPTANCE.md)
- [Prior art](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/PRIOR-ART-BESTYLEWITHER.md)
- [Implementation plan](../../../docs/superpowers/plans/2026-10-02-bedrock-wither-reconstruction.md)

## Product boundary

This deliverable does **not** own:
- general Bedrock research;
- BEStyleWither analysis;
- Java/Forge technique catalogues;
- KNEEKURA Tank infrastructure;
- canonical Hub claims.

It owns:
- the KNEEKURA Bedrock Wither MOD source;
- product-specific configuration and tests;
- product decisions;
- its own build/runtime evidence;
- its own failure/repair history.
