# Test setups — read before comparing numbers

A frame rate means nothing without the machine, the emulator settings and the goal behind it. Each
contributor keeps one section here up to date; a finding in `FINDINGS.md` names the setup it used.
Add your own section in the same shape.

## Setup A — AkiiTW (+ Claude)

**Goal:** a stable **30 FPS** everywhere (the game's 30 FPS mode is on), then as much headroom as
possible under it: no drops in Castle Town, inside the castle, Hyrule Field, and on quick camera turns.
Not chasing 60. Every millisecond saved on the GPU back thread counts even when the cap hides it.

**Machine**

| | |
| --- | --- |
| CPU | AMD Ryzen 7 3800X (Zen 2, 8 cores / 16 threads, two 4-core CCX, L3 domains `0xff` / `0xff00`) |
| GPU | NVIDIA RTX 5060 Ti 16 GB, driver 621.1.0.0 |
| RAM | 24 GB DDR4 (3 DIMMs) |
| OS | Windows 11 25H2 (build 26200) |
| Display | 240 Hz (host pacer reports 240.3 Hz) |

**Build:** AkiiTW/Lichii branch `claude/v3-zen2` = Frizti V3 (`frizti-v3`, 00ef0ea6c) + changes listed in
`FINDINGS.md`. MSYS2 clang 23, `-march=znver2`, PGO (Ocarina village profile over `eglantine.profdata`),
workflow `.github/workflows/lichii-tuned.yml`, flavor `normal` unless noted.

**Game:** Ocarina of Time `0400486024DEC000`, update v131072. Add-ons: `Dynamic-fps` (exefs patch);
since 2026-11-07 also `OoT Perf - Ombres PNJ proches` (NPC local shadows 8/10 m, see `FINDINGS.md`).

**Emulator settings (from the log's `LogSettings`)**

| Setting | Value |
| --- | --- |
| Mode | Docked |
| `oot_30fps` | true (30 FPS mode) |
| Resolution | 1x (`Res1X`), FSR 1 upscale, sharpening 25, no AA, 16:9 |
| GPU accuracy | Low |
| DMA accuracy | Default |
| Async GPU emulation / async shaders / async presentation | on / on / on |
| ASTC | decoded on the GPU, recompressed to BC3 (`accelerate_astc=Gpu`, `astc_recompression=Bc3`) |
| VRAM usage | Conservative (Lichii reports 7.00 GiB available); texture cache thresholds 9216 / 11264 MiB |
| VSync | Mailbox; frame pacing `Target_Auto`; host pacer on |
| Frame generation, DLSS | off |
| `fast_gpu_time` | Boost |
| Memory layout | 8 GB |
| CPU | Dynarmic, accuracy Auto, unsafe FMA unfuse on, ignore memory aborts on |
| Disk shader cache / driver pipeline cache | on / on |
| Thread placement | `Nx2Placement` split: GPU threads on `0xff00` (front `0x300`, back `0xc00`, Vulkan worker `0xf000`), guest cores and the rest on `0xff` |

**Switches (`%APPDATA%\eden\nx2_switches.txt`), as of 2026-11-07:** `EDEN_NX2_THREAD_USAGE=1`,
`EDEN_NX2_GPU_PROFILE=1`, `EDEN_NX2_TC_LOG=1`, `EDEN_NX2_TEST_START=150`, `EDEN_NX2_TEST_SECONDS=120`,
`EDEN_NX2_PERF_ON=clean_words`, `EDEN_NX2_BANK_COMPARE=1` (A/B pending). V3 options in effect:
`method cb_batch clean_words usage_tracker bank_check frames_ahead pipeline_retention write_intersections
sorted_page_batches unswizzle_workers` on; `bounds index_rebind split_overlap front_sleep submit_budget
fragment_barrier fence_flush async_pipelines` off.

**Test spot:** Castle Town market, laps around the fountain while turning the camera, inside the test
window 150-270 s after load (so the first minutes' texture uploads are part of every run). Older runs
(before the window existed) were taken after ~20 min of play and are not directly comparable.

**Reference numbers (this setup):** market 27-30 FPS after ~20 min of play; ~21-22 FPS in the test
window right after load (texture uploads); ~2,100 draws per frame; back ~870-910 ms/s busy.

## Setup B — Frizti (+ Claude)

*To be filled in by Frizti's Claude: machine, build, settings, goal, test spot.* Known from his status
screens (2026-11-07): goal 50-60 FPS in Castle Town; baseline 33-38 then 34 FPS on his recorded route;
works on the front's waits for the back.
