# Motion trace age and projectile identity display

The user requested visible age ordering for overlapping movement and distinguishable projectile trails. The change affects derived presentation only; original observations, SampledMotionTrace v1, source IDs and retained metrics stay unchanged. Display remains explicitly opt-in/default OFF.

## Age

Minecraft native overlay and the retained Decision Viewer use100 game/cursor ticks (normally5 seconds). Colors freeze with game/cursor time; wall-clock delay is not evidence age. SimLab uses its existing selected trail duration0..120 ticks, with0 still OFF; its three bands scale to that duration.

| Age at100-tick lifetime | Mob display | Opacity |
| --- | --- | --- |
| 0..33 | Blue RGB105/215/255 | Full |
| 34..66 | Yellow RGB255/211/83 | Reduced |
| 67..99 | Red RGB255/96/83 | Fades toward disappearance |
| ≥100, or a future sample | Absent | No draw |

Markers use each actual sample's tick. A segment uses its newer endpoint's tick, and both endpoints must remain visible. These are display connections between retained endpoints, not interpolated observations. Existing missing/teleport/identity gaps, finite caches, dimension/distance guards and source references remain enforced; display expiry does not delete evidence.

## Projectiles

Initial projectile colors derive deterministically from exact UUID/SimLab entity ID, producing a stable green/cyan/blue/violet hue rather than changing on redraw. Middle and old bands blend that identity color toward yellow and red, respectively. Finite colors can be close or coincide; they are not unique identifiers. Retained/SimLab views label each visible projectile's newest point with its short ID; the retained view also lists the full UUID and initial color. Projectile dash/diamond or native three-axis markers remain distinct from Mob markers.

The native related layer now also submits at most16 camera-facing ID labels, each anchored to its **last retained completed-tick position**, with a0.22-block presentation offset. It never queries a projectile's current position or falls back to an older point when the latest is future/expired/out of range/in another dimension. Names use `P <first4>..<last8>`; abbreviation collisions among retained groups use full UUIDs. Label colors/expiry share the exact UUID age style. Raw capture suppresses labels and lines through the same actual quiescence gate, before buffer submission. Submission receipts add label count/scope and original accepted-spawn/latest-point source IDs. Labels remain derived presentation, not evidence positions or unique color claims.

Related projectiles have their own trace/sample map; drawing never connects one UUID to another. The existing retained Decision Viewer was missing the related-projectile checkbox despite receiving that layer, causing a null-element exception even with default-OFF data. A real script-execution regression reproduced this and now verifies empty/default-OFF and multiple independent projectile traces.

SimLab's two canvas views now consume retained SampledMotionTrace projectile segments instead of reconstructing a trail from forward-filled `at(t)` values. AI-facing packet and static SVG contracts are unchanged. The original color-only generation displays one explicitly selected native entity. The subsequent [related-projectile slice and R33](NATIVE-RELATED-PROJECTILE-DISPLAY-2026-10-04.md) add bounded simultaneous native groups from flushed accepted-spawn/tick observations, with one limited real framebuffer and a three-group temporal companion receipt. Exact per-pixel attribution/all-view usability remain separate.

## Validation and remaining acceptance

Native label source contracts pass RED→GREEN, common-prefix and abbreviation-collision identities, source/last-point provenance,16-group bound, age/future/context/dimension/distance/finite-camera and capture suppression. Motion/Decision113 tests /0 skipped and genuine all-bridge/owner/API regression pass. The existing renderer guard test was updated to verify both lines and labels receive the same actual capture condition. Genuine mapped Forge compilation includes the font API. Native label pixel/readability/overlap acceptance is still pending at this publication; no final whole-diff review or full-goal completion is claimed.

Motion/Decision106 tests passed, including executable canvas/standalone-view tests, expiry, future points, identity colors, gaps and non-mutation. Pure native geometry passes its age/source/gap/dimension/distance/raw-capture suppression tests; the frozen previous geometry fails the new missing-age API contract. Java/JavaScript color/age outputs match across54 boundary cases. Genuine owner/Arena/camera/writer/world API regression and all bridge/Mixin compilation passed against hash-checked existing Forge dependencies; no new dependency was added.

The retained browser review derives from separately frozen r17 Arrow and r24 Zombie evidence with unchanged canonical hashes. It confirms visible colors and no browser console errors. Those images are derived Viewer rendering, not Minecraft overlay framebuffer acceptance. [R26/R28](NATIVE-PAIRED-OBSERVER-2026-10-04.md) retain six same-save/options observer comparisons and one private native Mob age-color framebuffer; R33 subsequently provides one limited related-projectile framebuffer with visible differently aged arcs. Fence/subject occlusion, temporal rather than per-pixel attribution, two GPU boundary samples and noisy process differences leave full usability/GPU/observer-effect acceptance open. Raw Cardinal capture intentionally suppresses the derived overlay through restoration/final acknowledgement.
