# Native capture baseline rejections

R34 and R35 ran Java Minecraft 1.20.1 / Forge against frozen TECH HUB source `91e53f8e03c4e3b49acaa4e9f25de2720d0addd1`. The normal registered owner rejected both with `ARENA_BASELINE_MISMATCH`. Neither executed raw Cardinal capture, the separate derived framebuffer diagnostic, or JFR recording. No owner gate or declared baseline was replaced to make the trial pass.

The private natural-AI Skeleton had `NoGravity=true`, a connected fence perimeter and a declared three-air-block Arena. Its prelaunch `BOUNDED_BLOCKS_AND_SUBJECT_POSE` baseline SHA256 was `4e917c334c4530a8cffc34008cc3c25fa9b6d215146d0da5323156a0c21f4cea`: position `(4.5,224,8.5)`, yaw `-90`, pitch/velocity zero. The owner waits for the actual run snapshot before installation; prelaunch pose is therefore not necessarily its later pose.

R35 then used only the existing read-only L1 selection. `obs:forge-runtime:60044:39` / tick40668 observed `(4.300000011920929,224,8.300000011920929)`, yaw `-88.81342`, pitch/velocity zero. `:52` / tick40698 observed the same position and yaw `-88.78807`. These later samples establish drift relative to the declaration; they are not the exact installation fingerprint and do not isolate every field that caused rejection.

| Trial | Run | Canonical records | Canonical SHA256 |
|---|---|---:|---|
| R34 | `run-20261004000422-aec32db5b714` | 40 | `40d78cd2e73d5330ab780976c37c6bc497fe3a3cf168ee10c2c083378a4b06ea` |
| R35 | `run-20261004001832-8132d4c2d28f` | 65 | `a119a356b09f667998b1077b2e591b40ccf63d4588f811eeaccf3f69d3af32b9` |

Both retained stores finalized `EVIDENCE_COMPLETE` with clean flush ACK, dropped0, queue0 and verified launcher/runtime exit. That status describes evidence retention, **not scenario success**. Owner cleanup remained `OWNER_INSTALLATION_UNVERIFIED`, because authority was never installed. Original Tank and untouched control each match their85-file manifest; both private baseline and predecessor copies each retain85 verified files. Whole-world rollback is not claimed.

Natural-AI combined capture remains unaccepted. A subsequent fixed-owner synthetic Arrow trial can test overlay/raw separation through normal grants, but cannot establish natural AI shooting or resolve dynamic-state owner registration.
