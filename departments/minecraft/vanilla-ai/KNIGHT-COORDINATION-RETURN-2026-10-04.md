# Knight original broadcast observation

This bounded addition records `PhantomUpdateFormationAndMoveGoal.broadcastMyFormation(Ljava/util/List;)V` at its original RETURN, on the selected Knight's server-thread `mod` burst. It copies the originally passed list in original order, without calling `getNearbyKnights`, formation setters, eligibility, RNG, getters or AI again.

Source: `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625`, `src/main/java/twilightforest/entity/ai/goal/PhantomUpdateFormationAndMoveGoal.java`, blob `e61134e4ae17ee1b308a1b62e214baf14f121d06`, source SHA256 `5027f7c9ff8aae270f1962a9ba9a8db1b3e62ff062b12491cfa04421aa880aeb`. The matching development mapped TF artifact SHA256 is `7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a`; the Goal class SHA256 is `bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1`, Knight class SHA256 `5be6108fbd0606e7c03060fbe843afe8a8b2b1c57247f71f146ad307b695292f`.

The source queries nearby alive Knights once before its branch. Its leader branch picks a formation, broadcasts it, and may subsequently select a charging Knight. Broadcast skips charging members. Therefore the retained list identifies original broadcast inputs; post-state does **not** identify which members were changed, why a leader was selected, a persistent group ID or the later charge outcome. These remain `NOT_EXPOSED`. Member formation, number and progress are labeled cached fields at RETURN. The observer does not sort the list or infer membership from matching formation values.

Only the exact Goal/selected Knight cached-owner relation is eligible. The original `ArrayList` is accepted by exact class, with `min(16, maxNodes)` copied entries; custom List implementations are suppressed before `size`/`get`. Unknown member classes retain an index/class and `NOT_EXPOSED`, without invoking custom methods. No mutable list/member references are retained in the evidence. Existing session/run/process/Arena/UUID/revision, 200-tick, 256-event and byte limits remain enforced; the `mod` channel stays excluded from default bursts.

The existing TF snapshot/formation-return descriptor is unchanged so previous retained observations remain compatible. The broadcast adds a separately cached Goal artifact/resource check after the existing TF proof. Initial proof performs source IO and is included in the recorded observer-cost scope; cached resource correspondence is **not** transformed resident-byte attestation.

The additive `MOD_COORDINATION_RETURN` uses the existing original-event envelope and an EXECUTION fact/capability `mod_coordination`. The consumer validates exact source hashes, owner UUID, formation vocabulary, ordered indices, list bounds and explicit unknown statuses. It rejects unsupported added causal fields.

## Verification checkpoint

- Consumer tests: meaningful pre-implementation rejection (2 failing cases), then 3 passing cases covering original order/post-state, forged source/context/bounds/reason, and partial custom members.
- Genuine Java API/Mixin compilation and actual pinned TF classes: pre-implementation missing producer API, then cached producer/owner/thread/channel/event/member-budget tests passed. Constructor-free test objects are unit fixtures, not gameplay acceptance. Genuine mapped artifact and Goal/Knight resource hashes were verified before warming the test compatibility cache. Java output passed the JavaScript consumer.
- Motion/Decision suite: 109 passed, 0 skipped. Existing genuine Forge owner/Arena/camera/writer/world API regression passed.
- Frozen source `d5479b6ce9dffb6b6259599d26c8a4ff24e54dad` established the following private native trial. Broader coordination/battle and observer-effect acceptance remain open.

## Native-r29

The labeled prelaunch fixture restores an exact copy of the original85 files, then sets up a lit room, a controlled survival player and six actual-AI, damageable Knights numbered0–5 with a shared home. The previous R28 private world was preserved with all85 hashes. This is controlled setup, not a resize or modification of the original water tank, a full original-scene acceptance or a seeded broadcast result.

Four finite `mod`-only selections of UUID `55555555-6666-7777-8888-000000000001` produced three direct broadcast RETURNs and six separate individual formation RETURNs:

| Source observation | World tick | Retained original list | Post-state |
|---|---:|---|---|
| `obs:forge-runtime:13508:45` | 40487 | 6 exact fixture UUIDs, numbers0–5 in that original order | all six `CHARGE_MINUSZ` |
| `obs:forge-runtime:13508:436` | 40847 | 6 exact fixture UUIDs, numbers0–5 in that original order | all six `SMALL_CLOCKWISE` |
| `obs:forge-runtime:13508:636` | 41027 | original number order3,0,1,2,4,5 | number3 `ATTACK_PLAYER_ATTACK`; others `CHARGE_PLUSX` |

No member was dropped/truncated in these three records. The third list demonstrates why sorting, inferring its first member is the leader, or treating matching formation as the definition of membership would alter the evidence. The record labels all member values as post-state; it does not independently observe the per-member eligibility branch or establish that a particular member was changed/skipped. Selection4 captured no broadcast callback; no absence reason is inferred. Each observed window ended at `SELECTION_CHANGED`.

The JavaScript validator accepted all three genuine records and the retained overview included `mod_coordination_return`. All22 historical R21 formation-return records still pass the unchanged SDK descriptor. Native canonical904 unique observations finalized as `EVIDENCE_COMPLETE`, SHA256 `9fdaf56d7441bd80092628793607b5c95dfc141d312abb4c24511b4d93c32b2d`. Clean ACK, drop0/queue0, `VERIFIED_EXIT` and absence of the owned native PID13508 were verified. Original/control85 SHA hashes remain unchanged.

Actual JFR start/stop textual receipts and a3,626,713-byte JFR were retained. This is descriptive, not a matched overhead comparison. Recorded callback build/first-byte-check costs were75,227,000ns for the first additional source proof and41,500ns/37,900ns for later callbacks. The measured scope excludes final encoding/writer and GPU work; initial source IO is visibly material and no negligible-observer-effect claim is made. No new pixels or raw Cardinal requests were taken in this trial.
