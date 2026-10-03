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
- Native Mixin dispatch, actual group membership, clean stop and original-save preservation for this new callback are pending a fresh frozen-source private trial. Broader coordination/battle and observer-effect acceptance remain open.
