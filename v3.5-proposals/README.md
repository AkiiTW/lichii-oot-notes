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
  head `d18e0af21` at the time of writing.
- **Patches:** [`patches/`](patches) holds the 29 code commits in order (`git format-patch`, notes and
  the binary `.profraw` left out). **Verified:** `git am patches/*.patch` on a clean `frizti-v3`
  applies all 29 without conflict and gives exactly the `src/` and `.github/` of `d18e0af21`.
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

## The proposals

| ID | Proposal | Kind | Effect in Setup A | Risk | Proposed V3.5 default | Commits | Status (your Claude) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | Render-target churn: new targets / depth images skip the guest-memory upload (`EDEN_NX2_TC_RT_NO_UPLOAD`) and stale targets are dropped early without download (`EDEN_NX2_TC_RT_EVICT`) | Perf | Market: frames > 100 ms **42 → 1**, worst **1,583 → 115 ms**, mean frame **48.6 → 38.5 ms** (+26 % FPS); `texture upload` 131 → 1.3 ms/s; uploads 9.6 GB → 0.05-0.18 GB per 600 frames; no visual defect | Medium (contents of a new target are undefined; a target unused for 4 frames is not downloaded) | `RT_NO_UPLOAD=3`, `RT_EVICT=4` after your check | 91498b2af, f9def68d9, 361d13546 | |
| P02 | Re-upload a native 64 KiB uniform bank only when its bytes changed (`EDEN_NX2_BANK_COMPARE`) | Perf | 95 % of re-uploaded bytes unchanged; zone `ubo bank` 33 → 22 ms/s | Low (exact by construction) | `=1` — **merge with your queue item 13** | d4738fce0 | |
| P03 | Turn V3's `clean_words` on (`EDEN_NX2_PERF_ON=clean_words`) | Default | `storage binds` 64 → 17 ms/s; no defect in the market | Medium (#161 slab in Kokiri suspected at the time) | on, after a Kokiri check | switch only | |
| P04 | Pipeline keys: share pipelines that differ only in unread vertex attribute types; file shared-cache entries under the local driver version | Stutter | One session: 6,570 duplicates merged, 17,504 entries re-filed from another driver version, no in-game builds in the village | Low | on (`EDEN_NX2_VERTEX_KEY_MERGE=0` turns it off) | c5810710d, 1db14a304, e941a3b89 | |
| P05 | No `EDEN_NX2_PREFLUSH` in the built-in switches | Fix | One-frame white flashes gone | None found | off | 30a75df6d | |
| P06 | MinGW/clang build fixes: host pacer `#pragma comment` + dwmapi link; thread names via `SetThreadDescription`; sampler stack walk bounded | Build/fix | MinGW builds link; `EDEN_NX2_SAMPLE` finds threads; sampler no longer freezes/crashes the emulator | None | — | 19538b31a, df6362759, 984269912 (sampler part) | |
| P07 | L3-domain thread placement (`EDEN_NX2_PLACEMENT=split`): GPU front/back/Vulkan worker on one CCX, a physical core each for front and back; pipeline worker cap | Perf (multi-CCX Ryzen) | 3800X, Kokiri: 28-29 FPS vs 24, wide view 24 vs 18-19 (build-88 era, together with other changes) | Low; only matters on CPUs with several L3 domains | `split` on multi-L3 CPUs | f587285b1, f24ea754c, 5321191db | |
| P08 | `EDEN_NX2_PIPELINE_EVICT_FRAMES` (0 = never evict) and the dist defaults `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`, `EDEN_NX2_TC_OLD_AGE=0` | Stutter | No rebuild stutter when coming back to an area | VRAM use grows with pipelines | dist only | 0d993c99f, fbd26bc32 | |
| P09 | Diagnostics: `EDEN_NX2_THREAD_USAGE`, finer `GPU_PROFILE` zones (`ubo fast/classic/bank`, `storage binds`, `texbuf binds`), `EDEN_NX2_TC_LOG` uploads by kind / render-target skips / why depth images upload / distinct addresses per shape | Tooling | Found P01-P03 | None (off unless set) | off | eba617204, 715bf05ae, 984269912, 4cccf896c, 88730eb2a, d18e0af21 | |
| P10 | On-screen test window (`EDEN_NX2_TEST_START/SECONDS/LABEL/PREPARE`): countdown panel top right, start/end lines in the log | Tooling | Comparable runs without a scripted route | None (off unless set) | off | d8e4fe222 | |
| P11 | Windows MSYS2 clang workflow `lichii-tuned.yml` (`-march` preset, PGO from `eglantine.profdata` + recorded profiles, flavors normal / pgogen / symbols with `lichii.pdb`) | Build | Zen 2 + PGO build: village 31 / wide 28 / half-turns 24 FPS vs your v2 24 / 18-19 / 13 (build-88 era) | None for MSVC users | optional | f587285b1, ab849a779, 0e688990e, cfc32ad55, 669f3f5f0, 2b5448ee8, 715bf05ae (workflow part), ba6836890 | |
| — | **Not proposed:** 30 FPS by default (43515fb50, AkiiTW's taste); larger TC thresholds 12288/13824 (ruled out: VRAM full, 1.3 s spikes); dist comment fix c031f3e3a is cosmetic | — | — | — | — | — | — |

Details for each: [`PROPOSALS.md`](PROPOSALS.md). Overlaps with your tree and work:
[`COMPATIBILITY.md`](COMPATIBILITY.md).

## How to answer

1. Fill the Status column: **accepted**, **accepted with changes** (say which), **rejected** (say why),
   or **already done differently** (link your commit).
2. If you measured one on your setup, add a `FINDINGS.md` entry (Setup B) and link it here.
3. If a proposal conflicts with something you are about to land (front/back overlap, per-page write
   index, bounded releases, zortos ports), note it in `COMPATIBILITY.md` so AkiiTW rebases onto yours
   instead.
