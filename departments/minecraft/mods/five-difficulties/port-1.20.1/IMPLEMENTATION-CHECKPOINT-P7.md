# Implementation checkpoint — P7 client visual evidence

Date: 2026-11-19
Environment: local Windows 11 workstation, real GPU client, JDK 17.0.12,
Forge 1.20.1-47.4.6 MDK (SHA-1 `1a1c045f235262ff617e285ea2156571ea93bfbe`),
private X1 overlay imported from the canonical outer bundle
(`9d8ea665…a98`) into the build copy only.

## Review of the inherited P7 commit (`a73a71d`)

The P7 commits on `…-port-p7-2026-10-07` were never built by CI: the workflow only
triggers on the `-p6-` branch. Local review found:

| Check | Result |
|---|---|
| Pure-core regressions (8 suites) | PASS |
| Compile + package against Forge 47.4.6 | PASS |
| `FIVE_DIFFICULTIES_P7_CLIENT_SMOKE` marker | PASS printed |
| What the screenshot actually showed | **Homing two-pass primitive and dark field were blank** |

The inherited smoke was a false pass: it only checked that a PNG was written.

Causes (confirmed by looking at the frame and the original X1 renderers):

1. X1 `RenderHomingAmulet` draws the amulet in the XZ plane. The GUI screen
   looked at it edge-on. The renderer itself is correct.
2. The X1 dark field is `GL_ONE_MINUS_DST_COLOR, GL_ZERO` (colour inversion).
   In the GUI screen context it draws nothing at all; in-world it works (below).

Also fixed: the port `.gitignore` had literal `\n` in one line, so five of the seven
private X1 PNG paths were **not** ignored in this public repository. It now ignores
`textures/**/*.png`, and the asset importer is pointed at the build copy.

## Changes

- `P7VisualSmokeScreen`: tip the Homing primitive toward the GUI camera; remove the
  dark-field panel from the GUI smoke (no false claim there).
- `ClientRuntimeSmoke`: `FIVE_DIFFICULTIES_KEEP_SCREENSHOT=1` keeps the PNG for local
  private review (CI never sets it; the PNG contains private X1 art).
- New `ClientWorldVisualSmoke` (P7b, `FIVE_DIFFICULTIES_P7_WORLD_SMOKE=1`): creates a
  throwaway flat singleplayer world, fixes the camera, fires five live red Homing
  Amulets, then starts a live `FULL_STOP` Watch controller from an armor stand in front
  of the camera. Each frame has a pixel assertion.

## Receipts (local run 2026-11-19 13:52)

```
P7b frame p7b_baseline.png warmFraction=0.00128 skyBlueMinusRed=90.8
P7b frame p7b_homing.png   warmFraction=0.00364 skyBlueMinusRed=92.1
P7b frame p7b_timestop.png warmFraction=0.00237 skyBlueMinusRed=-94.7
FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_PASS homingWarmDelta=0.00236 skyBlueMinusRed baseline=90.8 stop=-94.7
FIVE_DIFFICULTIES_P7_CLIENT_RESOURCES_PASS canonicalTextures=7 watchLayer=ok itemModels=3
```

What the frames show (reviewed by eye, PNGs kept local only):

- live amulets render as flat X1 sprites in the real level renderer;
- the Watch field colour-inverts everything inside it (blue sky → brown, grass →
  lavender, frozen amulets → blue), which is the X1 look;
- amulets stay in place inside the stopped field.

## Not proven yet

- exact colour parity of the red second pass against a running X1 1.7.10 client
  (no X1 runtime oracle frame exists);
- player right-click/charge interaction and Watch consume/return through a real player;
- two-player behaviour.

Client smokes need the private overlay, so they stay local; CI remains server-side.
