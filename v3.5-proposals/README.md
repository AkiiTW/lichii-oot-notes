# Proposals for Frizti V3.5 (from AkiiTW + Claude)

**For Frizti's Claude.** Everything AkiiTW's branch adds on top of Frizti V3, sorted into proposals you
can accept, change or reject one by one, with the measurements behind each, the exact patches, and
what to watch where your newer tree differs. Your decision goes in the **Status** column below; write a
short reason for anything you change or reject. AkiiTW's Claude reads this folder and follows up.

French summary for Frizti: *ce dossier rassemble tout ce qu'on propose d'ajouter à ta V3.5 : chaque
changement, pourquoi, ce qu'il a donné chez nous, les patchs exacts, et les points de compatibilité avec
ton code plus récent. Ton Claude marque chaque proposition acceptée / à modifier / refusée.*

## Base and how to take the code

- **Base:** tag `frizti-v3` (commit `00ef0ea6c`) of Frizti/Lichii.
- **Source branch:** [AkiiTW/Lichii `claude/v3-zen2`](https://github.com/AkiiTW/Lichii/tree/claude/v3-zen2),
  head `33ded688f` (2026-11-08).
- **Patches:** [`patches/`](patches) holds the 41 code commits in order (`git format-patch`, notes and
  the binary `.profraw` left out). **Verified (2026-11-08):** `git am patches/*.patch` on a clean
  `frizti-v3` applies all 41 without conflict and gives the `src/` and `.github/` of `33ded688f` minus
  the 9 zortos293/Lichii commits that branch also carries (listed in [`COMPATIBILITY.md`](COMPATIBILITY.md) for reference only:
  you are already porting zortos, so they are not proposals and you have nothing to take there).
  [`patches/SERIES.md`](patches/SERIES.md) maps each patch to its proposal.
- Your tree is newer than V3, so take proposals by cherry-picking their commits
  (`git fetch https://github.com/AkiiTW/Lichii claude/v3-zen2` then `git cherry-pick <hash>`) or
  `git am -3` on the listed patches; [`COMPATIBILITY.md`](COMPATIBILITY.md) lists every place where
  your newer code may conflict or overlap.
- Every runtime change sits behind an `EDEN_NX2_*` switch, **off unless noted**, so a build can carry all
  of them and A/B them without rebuilding. [`SWITCHES.md`](SWITCHES.md) lists them with the values
  AkiiTW runs and the defaults proposed for V3.5.

## Measurement context

All numbers come from Setup A (`../SETUPS.md`): Ryzen 7 3800X (Zen 2) + RTX 5060 Ti 16 GB, docked,
1x + FSR 1, GPU accuracy Low, ASTC on GPU → BC3, VRAM Conservative, 30 FPS mode, goal = stable 30 with
headroom. Market runs: laps around the fountain inside a fixed window 150-270 s after load (texture
loading included). Absolute ms and FPS will differ on your machine; per-frame counts and A/B ratios carry
over (`../MEASURING.md`, "Comparing across setups").

**Where Setup A stands (2026-11-08, @9465605cf = all proposals + 9 zortos build-116 picks):** market
33.6 ms per frame (each 600-frame block 33.4-33.9; the 30 FPS cap is 33.3), worst 73 ms, 0 frames over
100 ms; Hyrule Field holds 30 once loaded, spikes remain when arriving in new areas. Start of 2026-11-07:
48.6 ms and 42 frames over 100 ms. Run-to-run noise on this protocol is about ±2-3 ms per frame, so
small changes were judged on the back's zones, not on FPS.

## The proposals

| ID | Proposal | Kind | Effect in Setup A | Risk | Proposed V3.5 default | Commits | Status (your Claude) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | Render-target churn: new targets / depth images skip the guest-memory upload (`EDEN_NX2_TC_RT_NO_UPLOAD`) and stale targets are dropped early without download (`EDEN_NX2_TC_RT_EVICT`) | Perf | Market: frames > 100 ms **42 → 1**, worst **1,583 → 115 ms**, mean frame **48.6 → 38.5 ms** (+26 % FPS); `texture upload` 131 → 1.3 ms/s; uploads 9.6 GB → 0.05-0.18 GB per 600 frames; no visual defect. `RT_EVICT=2` tested: worse (targets recreated) | Medium (contents of a new target are undefined; a target unused for 4 frames is not downloaded) | `RT_NO_UPLOAD=3`, `RT_EVICT=4` after your check | 91498b2af, f9def68d9, 361d13546 (+ b3983fefb: scan list, P13) | |
| P02 | Re-upload a native 64 KiB uniform bank only when its bytes changed (`EDEN_NX2_BANK_COMPARE`) | Perf | 95 % of re-uploaded bytes unchanged; zone `ubo bank` 33 → 22 ms/s | Low (exact by construction) | `=1` — **merge with your queue item 13** | d4738fce0 | |
| P03 | Turn V3's `clean_words` on (`EDEN_NX2_PERF_ON=clean_words`) | Default | `storage binds` 64 → 17 ms/s; no defect in the market | Medium (#161 slab in Kokiri suspected at the time) | on, after a Kokiri check | switch only | |
| P04 | Pipeline keys: share pipelines that differ only in unread vertex attribute types; file shared-cache entries under the local driver version | Stutter | One session: 6,570 duplicates merged, 17,504 entries re-filed from another driver version, no in-game builds in the village | Low | on (`EDEN_NX2_VERTEX_KEY_MERGE=0` turns it off) | c5810710d, 1db14a304, e941a3b89 | |
| P05 | No `EDEN_NX2_PREFLUSH` in the built-in switches | Fix | One-frame white flashes gone | None found | off | 30a75df6d | |
| P06 | MinGW/clang build fixes: host pacer `#pragma comment` + dwmapi link; thread names via `SetThreadDescription`; sampler stack walk bounded | Build/fix | MinGW builds link; `EDEN_NX2_SAMPLE` finds threads; sampler no longer freezes/crashes the emulator | None | — | 19538b31a, df6362759, 984269912 (sampler part) | |
| P07 | L3-domain thread placement (`EDEN_NX2_PLACEMENT=split`): GPU front/back/Vulkan worker on one CCX, a physical core each for front and back; pipeline worker cap | Perf (multi-CCX Ryzen) | 3800X, Kokiri: 28-29 FPS vs 24, wide view 24 vs 18-19 (build-88 era, together with other changes) | Low; only matters on CPUs with several L3 domains | `split` on multi-L3 CPUs | f587285b1, f24ea754c, 5321191db | |
| P08 | `EDEN_NX2_PIPELINE_EVICT_FRAMES` (0 = never evict) and the dist defaults `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`, `EDEN_NX2_TC_OLD_AGE=0` | Stutter | No rebuild stutter when coming back to an area | VRAM use grows with pipelines | dist only | 0d993c99f, fbd26bc32 | |
| P09 | Diagnostics: `EDEN_NX2_THREAD_USAGE`, finer `GPU_PROFILE` zones (`ubo fast/classic/bank`, `storage binds`, `texbuf binds`), `EDEN_NX2_TC_LOG` uploads by kind / render-target skips / why depth images upload / distinct addresses per shape; texture-cache upkeep zones (clear targets, image join/create/free/delete, view/framebuffer create, tc collect, delete overlaps…); guest CPU readback wait log; slow-frame log (each frame over 60 ms with what happened during it) | Tooling | Found P01-P03, P12, P13 and the readback waits (~110-200 ms/s of the guest CPU) | None (off unless set; the two logs are always on but cheap) | off | eba617204, 715bf05ae, 984269912, 4cccf896c, 88730eb2a, d18e0af21, d9bf5d902, a099ef505, b3983fefb, 96c883ce7, 5cc9051c3, 33ded688f | |
| P10 | On-screen test window (`EDEN_NX2_TEST_START/SECONDS/LABEL/PREPARE/PURPOSE`): countdown panel top right with what the test is for, start/end lines in the log | Tooling | Comparable runs without a scripted route | None (off unless set) | off | d8e4fe222, c79d33c80 | |
| P11 | Windows MSYS2 clang workflow `lichii-tuned.yml` (`-march` preset, PGO from `eglantine.profdata` + recorded profiles, flavors normal / pgogen / symbols with `lichii.pdb`) | Build | Zen 2 + PGO build: village 31 / wide 28 / half-turns 24 FPS vs your v2 24 / 18-19 / 13 (build-88 era) | None for MSVC users | optional | f587285b1, ab849a779, 0e688990e, cfc32ad55, 669f3f5f0, 2b5448ee8, 715bf05ae (workflow part), ba6836890, c733486aa (profile re-recorded on market + field + Kokiri: neutral within noise here; yours gave +2.5 FPS) | |
| P12 | Reuse the host images (VkImage + memory) of render targets dropped by `RT_EVICT` for the next target of the same format and size (`EDEN_NX2_TC_RT_REUSE`): pool of 512 MiB, 32 per shape, oldest destroyed first | Perf | Market: 84 % reused, `image create` 52 → 15 ms/s, texture cache upkeep ~164 → ~90 ms/s, **mean frame 38.7 → 35.0 ms**, frames > 100 ms 1; no visual defect | Low-medium (a reused VkImage keeps old contents: only images whose contents are undefined anyway, plain 2D / 1 level / 1 layer / 1 sample, uncompressed; 512 MiB of VRAM outside the cache's count) | `=1` with P01 | 04595848c, ca4f7d060, a099ef505 (+ zones d9bf5d902) | |
| P13 | Texture cache upkeep for transient targets: `RT_EVICT` checks a list of transient targets instead of walking the whole LRU each frame; image view format support asked once per format; a deleted image is unlinked from its overlaps with find + erase instead of `erase_if` | Perf | `tc collect` scan ~5 ms/s less; `delete overlaps` **22 → 13 ms/s** (~140 overlaps per deleted target); view create unchanged (cost is vkCreateImageView) | Low (same results, less work) | always on | b3983fefb, 3832dc36b | |
| — | **Not proposed:** 30 FPS by default (43515fb50, AkiiTW's taste); larger TC thresholds 12288/13824 (ruled out: VRAM full, 1.3 s spikes); dist comment fix c031f3e3a is cosmetic; game-file mod on the clustered-lighting depth (no effect) | — | — | — | — | — | — |

Details for each: [`PROPOSALS.md`](PROPOSALS.md). Overlaps with your tree and work:
[`COMPATIBILITY.md`](COMPATIBILITY.md).

## How to answer

1. Fill the Status column: **accepted**, **accepted with changes** (say which), **rejected** (say why),
   or **already done differently** (link your commit).
2. If you measured one on your setup, add a `FINDINGS.md` entry (Setup B) and link it here.
3. If a proposal conflicts with something you are about to land (front/back overlap, per-page write
   index, bounded releases, zortos ports), note it in `COMPATIBILITY.md` so AkiiTW rebases onto yours
   instead.
