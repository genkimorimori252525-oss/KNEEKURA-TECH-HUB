# WWII Air Combat Tactics — Evidence and AI Adaptation v1

Status: historical research / design evidence only (2026-10-11). This document introduces no executable AI, runtime proof, or new aircraft-performance measurements.

## 1. Scope and provenance rules

Goal: give Warfare Wings aircraft believable **mission-specific decision policies** while allowing the actual aircraft dynamics to come from the supplied artifact, the pinned Immersive Aircraft source model, and eventually same-artifact runtime telemetry.

Evidence classifications used below:

- **HISTORY_FACT**: directly supported by the named historical institution, contemporary action report, or an identifiable retrospective study. Describe the specific service, operation, year, and aircraft variant whenever known.
- **HISTORICAL_INTERPRETATION**: cautious inference from an account rather than a universal written doctrine.
- **PROJECT_FACT**: observed in this repository's extracted Warfare Wings ANCHOR; this describes project data, **not** the real aircraft.
- **DESIGN_INFERENCE**: plausible AI decision rule justified by an identified historical pattern; requires play-testing.
- **GAME_ADAPTATION**: simplified mechanical representation chosen for Minecraft gameplay; never present as a real-world performance measurement.
- **TEST_REQUIRED**: a claim about runtime behavior that needs a same-artifact Minecraft experiment before promotion.

Local grounding: [TECHNICAL-ANALYSIS](../TECHNICAL-ANALYSIS-2026-10-07.md), [AIRCRAFT-PERFORMANCE-MODEL](AIRCRAFT-PERFORMANCE-MODEL.md), [AIRCRAFT-ATLAS](reports/AIRCRAFT-ATLAS.md), and [base-aircraft-anchor-v1.json](data/base-aircraft-anchor-v1.json). The ANCHOR is SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`; the linked Immersive Aircraft source contract is `1.3.3+1.20.1`, commit `550b38d3dfdbf5cb6ec3f78468e0e60725a47605`. The source microkernel's predictions are not identical to demonstrated ANCHOR Minecraft runtime outcomes. In particular, do not quietly substitute historical horsepower, mass, real speed or turn radius for the addon's movement formula. The host controls direct yaw/pitch response with its corresponding values; its lift is predominantly velocity-vector alignment, and visual roll factor does not confer physical bank-to-turn authority.

The ANCHOR-derived roster has 24 base aircraft and 66 schemes/liveries (90 JSON aircraft entries in all): IJN `a6m,d4y,g10n1,g10n2,g4m`; IJA `ki61,ki84`; USAAF `b17,b29,p40e,p47n,p51d`; USN `f4u,f6f,sbd`; RAF `spitfire`; VVS `il2,mig3,yak3`; Luftwaffe `bf109,fw190,he111,ju87`; Regia Aeronautica `mc202`. Extracted role totals: **14 fighters, 5 bombers, 4 attackers, 1 torpedo bomber**. These are **project labels**; no `ai` JSON object is evidence of shipped active flight AI. The extracted `escort` doctrine on B-17, B-29, He 111, G10Ns and G4M is a data label; it is particularly misleading if read as a claim that the bomber itself is a fighter escort.

**Never give a whole nation a fixed personality.** Training, commander, squadron, operational year, aircraft model, fuel, altitude, damage, visibility, mission, target, escort, and tactical learning matter. The same air arm can operate different doctrines simultaneously. War-era organizational records describe patterns; individual crews could adapt or depart from them. In the simulator, select **mission + service/unit + year/phase + observed aircraft capabilities + current threat** before picking maneuvers. Use historical fact as a source of candidate decisions, not an infallible script.

## 2. Evidence-backed service and period differences

| Context | HISTORY_FACT | DESIGN_INFERENCE / GAME_ADAPTATION | Source |
|---|---|---|---|
| IJN carrier fighter operations, early Pacific War; A6M | Zero lightweight design supported strong close-in maneuvering, with tradeoffs in pilot protection and fuel-tank resistance. U.S. pilots changed their response over time to avoid long turning engagements against the Zero. | An A6M pilot defending bombers may commit to a close engagement when the target remains within its feasible turning envelope; a pilot aware of an enemy diving pass should first protect the escorted aircraft or disengage from a losing pursuit. Treat turn pursuit as conditional, never compulsory. | [H1], [H2] |
| U.S. Navy fighters versus A6M, 1942 onward | The two-aircraft defensive maneuver called the Thach Weave was developed to offset the Wildcat's disadvantages; sources document its use at Midway. U.S. pilots also emphasized altitude/speed advantage and one-pass attacks against Zeros. | A cooperative pair may exchange cover/fire tasks. Implement separation, collision, and mutual-support guards; do not impose the weave on all USAAF/USN fighters or on aircraft with no nearby wingman. | [H1], [H3] |
| USAAF P-47 (especially Southwest Pacific 348th FG), 1943 onward | P-47 pilots under Neel Kearby used high-altitude staging, diving high-speed attacks and regained altitude for another pass. P-47s also served as high-altitude escorts and low-level fighter-bombers; missions changed with the campaign. | Use a reusable dive/extend/recover/reassess engagement pattern when speed/altitude and clear escape space favor it. On armed reconnaissance or ground attack, select a separate mission policy. | [H4], [H5], [H6] |
| RAF Fighter Command, Britain 1940; Spitfire | RAF intercepts relied on the Dowding detection/control network. Initially tight formations restricted combat flexibility; operational units adapted toward looser sections. A later RAF Historical Society discussion says some units adopted four-aircraft arrangements during the battle while training units still used the older vic in early 1941. | Include ground-controlled intercept and target-priority orders; model early formation rigidity only in explicitly dated scenarios. Permit unit-specific formation transition rather than a universal 1940 finger-four rule. | [H7], [H8], [H9] |
| Luftwaffe fighter cover and Ju 87 dive attack, 1939–40 | Stukas were effective when aerial resistance was weak; fighter opposition in the Battle of Britain inflicted severe losses and led to withdrawal. Luftwaffe fighters often protected bomber raids, creating competing escort/interception tasks. | A Ju 87 mission should require approach geometry and a feasible escape; a vulnerable dive-bomber aborts when fighter protection/target window is lost. Luftwaffe fighter AI should weigh its escort obligation against pursuit. | [H10], [H8] |
| VVS battlefield support, Il-2, 1941 onward | The armored Il-2 was created for low-level ground attack and Soviet combined-arms warfare. Early single-seat aircraft were vulnerable from the rear; a second crew position with rear gun was adopted as the war progressed. | Il-2 policies should prioritize terrain, ground targets, egress and vulnerability of uncovered rear aspects, with year/variant-dependent rear protection. An attacker is not automatically slow to point its nose in the **game**; the supplied Il-2 has strong yaw/pitch values. | [H11], [H12] |
| USAAF strategic bombing, Europe, 1943–44; B-17 | Combat-box formations were designed to combine defensive fire and concentrate bombing. Limits of fighter escort range caused heavy early losses; later drop tanks and additional fighter capability improved escort coverage by early 1944. | Keep a stable bomber formation and route, track escort coverage and mutual defensive arcs, and select diversion/abort on damage or loss of the route. Do not let individual B-17s dogfight like interceptors. | [H13], [H14], [H15] |
| Naval torpedo attack, Pacific, 1942 versus 1944 | The U.S. Mark 13 torpedo's early restrictions and reliability problems exposed slow torpedo aircraft to danger; improved equipment allowed more flexible drops by 1944. Midway action reports show torpedo sections separated from much of their fighter cover; earlier plans envisioned timing dive and torpedo attacks for mutual assistance. These **U.S. weapon figures do not apply automatically to Japanese torpedoes**. | Torpedo runs must depend on selected weapon/era release-envelope data, anti-aircraft exposure and the target's predicted movement. Prefer coordinated arrival with fighter/dive units if assets exist, but retain explicit lost-contact contingencies. | [H16], [H17], [H18] |
| IJN land-based maritime attack; G4M, 1942–43 | G4Ms made low-level torpedo attacks around Guadalcanal in August 1942; contemporary U.S. Navy photographs document this. An August 1942 strike against USS Jarvis included G4M torpedo bombers and A6M fighter escorts. The G4M's long-range design carried considerable combat survivability costs. Some units made specialized night torpedo attacks in late 1943. | G4M can select maritime strike, torpedo, or other mission logic by loadout and scenario. Prioritize attack geometry and group coordination; let mission time (night/day), escort, and target air defenses adjust risk thresholds. | [H19], [H20], [H21], [H22] |

Comparison caution: **P-47N** is the supplied variant, while much of the cited history pertains to P-47s generally or an earlier operational subtype in the 348th FG. The historical maneuver logic is a candidate; any variant-specific turning performance must come from the ANCHOR and telemetry. Similarly `spitfire`, `il2`, `ju87`, `g4m` and `b17` do not alone identify the precise historical sub-variant, loadout or year.

## 3. Representative aircraft: historical claim → policy → verification

### A6M (IJN fighter)

- **HISTORY_FACT:** lightness aided maneuverability; external opponents learned to attack with altitude/speed, then leave instead of entering repeated tight turns [H1, H2]. A battle outcome also depends on training and situational advantage.
- **PROJECT_FACT:** `a6m` = fighter / IJN / `turn_fighter`; `engineSpeed=0.075`, `yawSpeed=3.8`, `pitchSpeed=3.5`, `durability=2.5` (ANCHOR data). The source microkernel reaches a 90° yaw change in 42 ticks with equal-angle speed retention 0.925567; **SOURCE_MICROKERNEL**, not ANCHOR runtime measured.
- **DESIGN_INFERENCE:** try turning pressure only if reachable intercept and remaining speed margin permit, otherwise break pursuit, retain cover or seek an advantage. Prioritize wingman protection when escorting G4M or carrier strike aircraft.
- **TEST_REQUIRED:** compare turning intercept versus disengagement against P-47N in altitude/speed-matched and mismatched setups; log time to firing solution, speed loss and damage.

### P-47N (USAAF fighter / fighter-bomber)

- **HISTORY_FACT:** high-speed diving and altitude recovery are documented for the P-47 (348th FG) [H4]; escort and low-level attack were distinct documented service missions [H5, H6].
- **PROJECT_FACT:** `p47n` = fighter / USAAF / `energy_fighter`; `engineSpeed=0.102`, `yawSpeed=2.5`, `pitchSpeed=2.4`, `durability=5.0`. Source-microkernel 90° turn 60 ticks, retention 0.964626. Historical **P-47 group tactics** are not proof of precise P-47N performance.
- **DESIGN_INFERENCE:** establish energy advantage, make a time-limited attack pass, extend, climb/reposition, and re-enter on favorable geometry. When assigned escort duty, avoid extending so far that protectee coverage fails. Fighter-bomber mission selects a separate attack planner.
- **TEST_REQUIRED:** measure target exposure, successful separation distance and sustained combat efficiency under ANCHOR physics; don't derive climb from historical turbocharger performance.

### Spitfire (RAF fighter)

- **HISTORY_FACT:** 1940 British fighter interception linked radar and ground observers to fighter-control instructions; squadron formation tactics evolved in combat [H7–H9]. RAF Museum notes the pilot's proficiency influenced Spitfire Mk I combat outcomes [H23].
- **PROJECT_FACT:** `spitfire` = fighter / RAF / `turn_fighter`; `engineSpeed=0.095`, `yawSpeed=3.6`, `pitchSpeed=3.4`.
- **DESIGN_INFERENCE:** mission planner prioritizes interception of raids, chosen bomber or fighter threats and protecting airfields, then local flight policy chooses maneuver from measured capabilities. Units/era can use close vic or looser pair/section structures.
- **TEST_REQUIRED:** evaluate intercept success versus scramble delay, estimate reliability and altitude staging; formation spacing must be collision-safe.

### Il-2 (VVS armored ground attacker)

- **HISTORY_FACT:** armored low-level ground attack as part of combined arms; early rear-sector vulnerability prompted a gunner-equipped version [H11, H12].
- **PROJECT_FACT:** `il2` = attacker / VVS / `attacker`; `engineSpeed=0.070`, `yawSpeed=4.0`, `pitchSpeed=3.5`, `durability=5.0`. High yaw authority in this MOD directly rebuts simplistic 'heavy attacker = cannot turn' coding.
- **DESIGN_INFERENCE:** acquire ground target from a safe route, make a constrained attack pass and climb/turn to egress. Escorts protect the vulnerable approach; rear-gunner capability must be queried from the instantiated aircraft/weapon rather than guessed from the name.
- **TEST_REQUIRED:** target hit rate, terrain clearance, escape probability and vulnerability changes for selected defensive weapon mounts.

### Ju 87 (Luftwaffe dive bomber)

- **HISTORY_FACT:** effective precision strike in low fighter-opposition environments; combat against defending fighters in 1940 forced withdrawal [H10].
- **PROJECT_FACT:** `ju87` = attacker / Luftwaffe / `attacker`; `engineSpeed=0.050`, `yawSpeed=1.8`, `pitchSpeed=1.8`, `durability=4.5`.
- **DESIGN_INFERENCE:** set entry bearing/height and pull-out clearance before committing. With no escort and active enemy CAP, delay or abort rather than attempt fighter-like maneuvering. Simulated anti-tank missions require the selected variant and equipped weapon.
- **TEST_REQUIRED:** safe dive entry, collision-free pull-out, bomb release constraints, and survival conditioned on escort.

### B-17 (USAAF heavy bomber)

- **HISTORY_FACT:** combat-box formation combined mutual protection and grouped bomb pattern; lack of persistent escort helped cause severe losses in 1943, and fighter range later improved [H13–H15].
- **PROJECT_FACT:** `b17` = bomber / USAAF / `escort` **(metadata label only)**; `engineSpeed=0.045`, `yawSpeed=1.2`, `pitchSpeed=1.1`, `durability=6.0`. The source-microkernel's 118-tick 90° result measures time-to-turn; high equal-angle retention alone is not fighter agility.
- **DESIGN_INFERENCE:** maintain formation spacing and steady bombing corridor, coordinate defensive mounts if present, assess damage/escort status and preserve egress corridors. Formation dispersion has a cost even if it temporarily avoids one attacker.
- **TEST_REQUIRED:** route stability, collision count, mutual defense coverage, group bomb spread and loss rates with/without escorts.

### G4M (IJN torpedo / land attack bomber)

- **HISTORY_FACT:** photographs and Navy narratives demonstrate torpedo attack and escorted operations, including low-level approaches [H19–H21]; Smithsonian documents long-range tradeoffs and susceptibility to enemy fire [H22]. Specialized night attacks appeared in some units [H21].
- **PROJECT_FACT:** `g4m` = `torpedo_bomber` / IJN / `escort` **(badly named doctrine label)**; `engineSpeed=0.065`, `yawSpeed=2.9`, `pitchSpeed=2.7`, `durability=4.0`. Its direct nose response differs drastically from the B-17; do not bind them to a single bomber maneuver template.
- **DESIGN_INFERENCE:** route to maritime target, choose viable torpedo release approach, synchronize with escort if available, drop only within actual installed weapon constraints, evade and exit. A G4M mission need not always carry a torpedo.
- **TEST_REQUIRED:** weapon loadout, release envelope, moving-ship intercept, terrain/water clearance, AA exposure and escape.

### SBD (USN dive bomber; companion to torpedo operations)

- **HISTORY_FACT:** USN Midway action reports describe separate high-altitude SBDs and low-altitude torpedo groups and the consequences of timing and escort coordination [H17, H18].
- **PROJECT_FACT:** `sbd` exists as `attacker` / USN in the ANCHOR.
- **GAME_ADAPTATION:** give dive bombers an independently timed strike window. A combined strike scenario should validate whether one group's combat attracts defensive aircraft away from another, but must not guarantee that outcome.

## 4. Controller design contract

Keep doctrine and physics separate. Recommended policy inputs:

| Input | Meaning | Evidence boundary |
|---|---|---|
| `mission.type` | combat air patrol, intercept, escort, bomber raid, close air support, dive strike, torpedo strike, armed reconnaissance | Scenario / task; never inferred solely from `faction` |
| `historical_context` | service, unit (if known), year/phase, theater, available command/control, formation training | Historical scenario hypothesis; cite when populated |
| `aircraft_state` | position, velocity, altitude, health, fuel, weapon mounts, loadout, squad members | Runtime/game state |
| `kinematic_envelope` | turn time, speed retention, climb/dive response, ground collision clearance | Source prediction until same-artifact measured |
| `threat_context` | target class/heading, fighter and AA threats, escort proximity, visibility | Sensor state and bounded belief; unknown ≠ zero |
| `mission_constraints` | route, protection radius, release limits, abort thresholds, return fuel | Configurable GAME_ADAPTATION, validated separately |

Suggested behavior hierarchy (**DESIGN_INFERENCE**):

1. **Observe and assess:** classify objectives and visible threats; attach confidence and last-known timestamps.
2. **Select duty first:** intercept, maintain protective CAP, attack a surface/ground target, stay in bomber box, or return home. Duty may override pursuit.
3. **Check feasibility:** reachable attack geometry, fuel reserve, obstacle clearance, wingman positions, weapons available, control-rate and speed envelope.
4. **Execute a bounded maneuver:** one-pass attack, turn pursuit, mutual-cover crossing, dive/run/pull-out, box station keeping, or release-and-egress.
5. **Reassess after every pass:** damaged aircraft, new fighters/AA, formation dispersion, disappearing target, or expired attack window can trigger mission abort / regroup.

Avoid hard-coded, history-looking values such as 'always turn within N meters' or 'release torpedoes at X blocks above water' without a documented source or locally measured weapon envelope. Developer-selected distances can exist as clearly labeled **GAME_ADAPTATION** parameters and must be evaluated against the real game implementation. Historical release parameters for the **U.S. Mark 13** [H16] must not be transplanted into the Japanese G4M's unknown loaded torpedo.

## 5. Concrete scenario / evaluation backlog

Each scenario records a seed, exact ANCHOR hash, model/source version, AI policy version, aircraft/weapon variant, missions, initial height/heading/speed, visibility, escort and defensive threats. Report both source-microkernel previews and same-artifact Minecraft traces with separate provenance labels; do not mark predicted results as measured.

| ID | Test scenario | Desired observed distinction and failure checks |
|---|---|---|
| T01 | A6M vs P-47N, matched energy; repeat with P-47N above/faster | Policy switches between feasible turning pressure and hit-and-run; log shot quality, damage, energy consumption and target escape. |
| T02 | Paired fighters with mutual-cover objective, wingman absent/present | Cover and cross-protection work only with actual coordination; no scripted turn into collision. |
| T03 | 1940 RAF raid interception: radar cue available/unavailable, early vs adapted formation | Intercept delay and formation change affect bomber engagement; no magical always-known target. |
| T04 | Ju87 bomb run, air cover present/absent | High threat creates re-route/abort; successful pull-out never goes through terrain or player-built structures. |
| T05 | Il-2 surface/ground strike, single-rear-sector coverage versus installed rear gun | Ground attack and rear-defensive decisions differ by equipped variant; do not fabricate an unavailable rear weapon. |
| T06 | B-17 3+ aircraft combat-box route, escort range expires mid-mission | Box stability, AAA/fighter defense and escort-loss reaction; detect dispersion, collision and unintended dogfighting. |
| T07 | G4M torpedo attack on moving ship, with/without A6M escort | Calculated run, verified weapon release envelope and realistic escape; abort if no viable solution; no guarantee of hit. |
| T08 | USN SBD + torpedo aircraft synchronized versus staggered arrivals | Compare defensive attention and strike survival in the actual AI environment; no predefined victory for either arrangement. |

Promotion gate for each tactical claim: (a) named source for historical motivation; (b) exact project data for aircraft/loadout; (c) deterministically repeated sandbox trace; (d) Minecraft 1.20.1 + Forge same-artifact comparison; (e) report both passes and failures. If weapon behavior or formation coordination does not yet exist, label its status **PROPOSED**.

## 6. Source register

Museum pages summarize technical/historical evidence; named U.S. Navy reports additionally provide firsthand operational context. A contemporary after-action report may contain incorrect or unverified combat claims (including claimed hits), and a 1990 symposium records participants' retrospective perspectives: neither should be treated as omniscient truth.

| ID | Publisher / specific item | Supported scope |
|---|---|---|
| H1 | Smithsonian National Air and Space Museum, [Mitsubishi A6M Zero Fighter](https://airandspace.si.edu/stories/editorial/mitsubishi-a6m-zero-fighter) | Zero capability and Allied response, including energy attacks; model variants and late-war changes |
| H2 | National Naval Aviation Museum / NHHC, [A6M2 Zero](https://www.history.navy.mil/content/history/museums/nnam/explore/collections/aircraft/a/a6m2-zero0.html) | 1945 comparative trials' recommendation against extended turning pursuit |
| H3 | National Naval Aviation Museum, [The Faces of Midway: Jimmy Thach](https://navalaviationmuseum.org/faces-midway/?pid=390) | Thach Weave as unit-specific defensive cooperation; Midway |
| H4 | National Museum of the USAF, [Col. Neel E. Kearby: Pacific Thunderbolt Ace](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/196209/col-neel-e-kearby-pacific-thunderbolt-ace/) | 348th FG P-47 altitude/dive/reclimb tactics in Pacific |
| H5 | National Museum of the USAF, [Republic P-47](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/858869/republic-p-47/) | Multi-role P-47 employment and variant differences |
| H6 | National Museum of the USAF, [Pillars of Tactical Airpower](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/4273897/the-pillars-of-tactical-airpower/) | Ninth Air Force tactical mission roles and ground coordination |
| H7 | RAF Museum, [How RADAR Works / Dowding System](https://www.rafmuseum.org.uk/research/online-exhibitions/history-of-the-battle-of-britain/how-radar-works.aspx) | Radar, observers and RAF fighter direction |
| H8 | RAF Museum, [The New Tactics](https://www.rafmuseum.org.uk/research/online-exhibitions/history-of-the-battle-of-britain/the-new-tactics/) | Early tight formations, operational adaptations and bomber interception |
| H9 | Royal Air Force Historical Society / RAF Museum, [The Battle Re-Thought](https://www.rafmuseum.org.uk/documents/Research/RAF-Historical-Society-Journals/Bracknell-No-1-Battle-of-Britain.pdf), pp. 68–69 | Veteran/historian debate on vic-to-four transition and uneven unit adoption |
| H10 | RAF Museum, [Junkers Ju87G-2](https://www.rafmuseum.org.uk/research/collections/junkers-ju87g-2) | Dive-bombing role and dependence on air superiority |
| H11 | Smithsonian National Air and Space Museum, [Ilyushin Il-2 Shturmovik](https://airandspace.si.edu/collection-objects/ilyushin-il-2-shturmovik/nasm_A19950142000) | VVS low-level combined-arms ground attack |
| H12 | Smithsonian National Air and Space Museum, [Stalin's Essential Aircraft](https://airandspace.si.edu/stories/editorial/stalins-ilyushin-il-2-shturmovik) | Armored structure, rear vulnerability, two-seat adaptation |
| H13 | National Museum of the USAF, [Combat Box: Bomber Formations](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/1513340/combat-box-bomber-formations/) | Bomber formation objectives and defensive fire |
| H14 | National Museum of the USAF, [AAF Fighter Escort](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/196181/aaf-fighter-escort/) | 1943 P-47 escort and limited escort range |
| H15 | National Museum of the USAF, [Fighter Escort: Little Friends](https://www.nationalmuseum.af.mil/Visit/Museum-Exhibits/Fact-Sheets/Display/Article/1519676/fighter-escort-little-friends/) | 1944 fighter escort improvements |
| H16 | U.S. Naval History and Heritage Command (NHHC), [H-008-3 Torpedo Versus Torpedo](https://www.history.navy.mil/content/history/nhhc/about-us/leadership/director/directors-corner/h-grams/h-gram-008/h-008-3.html) | Mark 13 reliability/release-era changes and coordination ideal |
| H17 | NHHC, [Commander-in-Chief Pacific Fleet Midway Action Report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-battle-of-midway/commander-in-chief-pacific-fleet.html) | Flight groups, escort/dispersal, different attack altitudes |
| H18 | NHHC, [USS Yorktown Midway Action Report](https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-battle-of-midway/uss-yorktown-action-report.html) | Torpedo approach, enemy fighter interception, divergent strike components |
| H19 | NHHC / National Archives, [80-G-17066 photo: Guadalcanal torpedo attack, August 1942](https://www.history.navy.mil/our-collections/photography/numerical-list-of-images/nara-series/80-g/80-G-10000/80-G-17066.html) | Verified low-level G4M Type 1 torpedo attack |
| H20 | NHHC, [H-093-1 USS Jarvis](https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-093/h-093-1.html) | G4M attack formation with A6M escort, Guadalcanal 1942 |
| H21 | NHHC, [H-025-1 Operation Galvanic](https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-025/h-025-1.html) | Late-1943 specialized G4M night torpedo missions and target maneuver |
| H22 | Smithsonian National Air and Space Museum, [G4M3 Betty Forward Fuselage](https://airandspace.si.edu/collection-objects/mitsubishi-g4m3-model-34-betty-forward-fuselage/nasm_A19600336000) | Range/protection tradeoffs; later variant adaptation |
| H23 | RAF Museum, [Supermarine Spitfire I](https://www.rafmuseum.org.uk/research/collections/supermarine-spitfire-i/) | Mk I interception role, tactical adaptation, pilot effects |

Future research should prefer original operational manuals and war-diary archives for **unit-specific** formations and weapons before adding finer-grained doctrines. Forum anecdotes and unspecified 'nation style' lists are not substitutes for dated evidence.
