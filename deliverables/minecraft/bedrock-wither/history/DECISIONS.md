# Bedrock Wither — Decision Log

## BWR-D001 — standalone entity

Date: 2026-10-02  
Status: ACTIVE

Decision: implement `kneekura_bedrock_wither:bedrock_wither` as an independent entity rather than using Java `WitherBoss` as the behavioral superclass.

Reason: Java Wither owns private timers, attack and destruction behavior. Independence makes Bedrock parity testable and prevents accidental Java behavior inheritance.

## BWR-D002 — observable parity, not hidden-code reconstruction

Date: 2026-10-02  
Status: ACTIVE

Decision: reproduce measured player-visible/runtime behavior. Do not claim recovery of Bedrock's closed native implementation.

## BWR-D003 — research values are candidates until measured

Date: 2026-10-02  
Status: ACTIVE

Decision: exact cadence, dash and destruction constants from community-maintained sources remain `TBD_MEASURE` unless direct Bedrock observation or stronger evidence accepts them.

## BWR-D004 — product/research separation

Date: 2026-10-02  
Status: ACTIVE

Decision: product source/history lives under `deliverables/minecraft/bedrock-wither/`; research remains under `departments/minecraft/`.

Reason: long-lived AI handoffs must not confuse one active product with the purpose of KNEEKURA TECH HUB.

## BWR-D005 — prior art is technique input by default

Date: 2026-10-02  
Status: ACTIVE

Decision: BEStyleWither is studied for architecture and failure history. Its source is not copied into the product unless a later explicit license/reuse decision says otherwise.


## BWR-D006 — death visuals must preserve semantic death

Date: 2026-10-02  
Status: ACTIVE

Decision: Bedrock-style delayed death visuals/explosion may extend rendering and removal timing, but the killing hit must enter the normal semantic death lifecycle and preserve killer attribution/event compatibility.

Evidence lead: BEStyleWither Issue #4 and repair commit `3c519d708fb1856f4661a3670aad36a6be9353da`.

Acceptance consequence: later death implementation must test `isDeadOrDying`, kill credit/events, loot and advancement-compatible attribution before visual parity is accepted.
