# Findings (newest first)

Shape and statuses: see [`CLAUDE.md`](CLAUDE.md). **Every entry by AkiiTW below uses Setup A**
([`SETUPS.md`](SETUPS.md)): Ryzen 7 3800X + RTX 5060 Ti, docked, 1x + FSR 1, GPU accuracy Low, ASTC on
GPU → BC3, 30 FPS mode, goal = stable 30 FPS with headroom. Builds from
[AkiiTW/Lichii `claude/v3-zen2`](https://github.com/AkiiTW/Lichii/tree/claude/v3-zen2) (Frizti V3 +
changes). Runs dated 2026-11-07 after 14:55 use the 150-270 s test window right after load; earlier ones
were taken after ~20 min of play — compare like with like.

---

### 2026-11-07 — RT_EVICT scan on a transient list; view format support cached: small — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@b3983fefb (+ zones image delete, framebuffer remove)
- **Where measured:** market, fountain laps in the 150-270 s window, switches as in the RT_REUSE entry
- **Measured:** `tc collect` 26.3 → 3.4 ms/s, but 17.4 ms/s of it is now shown as `image delete` (407/s, **43 µs each**, framebuffer remove only 0.8 ms/s): the LRU walk itself was ~5 ms/s. `view create` unchanged (17.4 ms/s, ~27 µs each): the format query was not its cost (two vkCreateImageView per view). Texture cache upkeep ~90 ms/s as before. Mean frame 38.3 ms (35.0 in the run before) with ~4 % more draws per frame and 5 ms/s of texture uploads (1 before): scene variation, not the change (it only removes work).
- **Conclusion:** kept (cheaper, no risk). Still unexplained: 43 µs per `DeleteImage` outside its nested zones. Left: image free 19, view create 17, image delete 17, image create 17, join 14, clear targets 10 ms/s.
- **Code / switch:** `TextureCache::RunGarbageCollector` (transient_targets), `ImageView::ImageView` (view_format_support)

### 2026-11-07 — `EDEN_NX2_TC_RT_REUSE` with oldest-first eviction: market 38.7 → 35.0 ms per frame — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@a099ef505
- **Where measured:** market, fountain laps in the 150-270 s window, camera moved everywhere; switches as in the RT_EVICT entry plus `EDEN_NX2_TC_RT_REUSE=1`. Compared with the run just before on d9bf5d902 (same zones, no reuse).
- **Measured:** host images reused **~84 %** (5,000-8,000 per 600 frames vs 700-1,650 made new; pool 380-510 of 512 MiB, 400-1,060 old ones destroyed to stay in budget). Back thread per second: **image create 52 → 15 ms**, tc tick 80 → 45 ms (image free 18 + tc collect 26 + rest 0.5), view create 19 → 17, image join 13 → 13; texture cache upkeep **~164 → ~90 ms/s**. **Mean frame 38.7 → 35.0 ms (−10 %, ~28.6 FPS on average)**, every 600-frame block 34.3-35.7 ms; draws/s 53.9 k → 58.7 k; frames > 100 ms 1 (worst 101 ms). The back's `split wait` rose 109 → 138 ms/s: the front is closer to being the limit now. Player: "best performance I've had, even moving the camera everywhere; held 30 nearly all the time"; small drops only when water splashes on Link in the fountain (seen before this build too). No visual defect.
- **Conclusion:** kept. From the start of the day (@d4738fce0): 48.6 → 35.0 ms per frame (**+39 % FPS**), frames > 100 ms 42 → 1. Left in texture cache upkeep: tc collect 26, image free 18, view create 17, image join 13, clear targets 10 ms/s.
- **Code / switch:** `EDEN_NX2_TC_RT_REUSE=1` (with `RT_EVICT=4`, `RT_NO_UPLOAD=3`)

### 2026-11-07 — The back's "clear" time is the texture cache making render targets: ~170 ms/s of upkeep — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@d9bf5d902 (new `GPU_PROFILE` zones: clear targets, image join, image create, view create, framebuffer create, tc tick)
- **Where measured:** market, fountain laps in the 150-270 s window; switches as in the RT_EVICT entry (no RT_REUSE)
- **Measured (per second, back thread):** `clear` itself 3.1 ms (1,650/s, 1.9 µs each) — the rest of the old ~70 ms was nested work: **image create 52 ms (385/s, 136 µs each: VkImage + memory)**, image join 13 ms (34 µs each), **view create 19 ms (591/s, 32 µs each)**, framebuffer create 0.4 ms (283/s, cheap), clear targets 10 ms; **tc tick 80 ms (3.1 ms per frame: collector, early drops, freeing sentenced images)**; `other` fell from ~155 to 78 ms (tc tick used to land there). Mean frame 38.7 ms, 53.9 k draws/s (a good run).
- **Conclusion:** texture cache upkeep is ~165-170 ms/s, ~20 % of the back, nearly all from Ocarina's transient render targets (new address each frame). Image creation is not cheap after all (136 µs each), so the earlier `RT_REUSE` result was hidden in the run-to-run noise. Next (a099ef505): pool keeps the most recently freed images (512 MiB, 32 per shape, oldest destroyed first) and tc tick split into image free / tc collect.
- **Code / switch:** `nx2_profile.h` zones; `TextureCache::JoinImages`, `FindOrEmplaceImageView`, `GetFramebufferId`, `TickFrame`

### 2026-11-07 — PGO profile re-recorded on current code (market + field + Kokiri): no measurable gain — confirmed neutral
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@c733486aa (profile `pgo/ocarina-market-field-kokiri-ca4f7d0.profraw`, weighted 4 over `eglantine.profdata`; replaces the Kokiri-only profile of cd1f029)
- **Where measured:** market, fountain laps in the 150-270 s window; switches as in the RT_EVICT entry
- **Measured:** first 600-frame block of the window had 29 frames > 100 ms (worst 839 ms; arrival/loading overlap), the rest 7 over 100 ms in 4 blocks, like the two runs of the same code with the old profile (10 each). Mean frame over the last four blocks 40.9 ms vs 41.9 and 40.4 ms (old profile, same code). Back work per draw 13.8 µs vs 14.1 / 14.3 µs; zone `other` 145 vs 156-162 ms/s, the rest within noise.
- **Conclusion:** neutral within this protocol's noise (±2-3 ms per frame; at most ~3 % less back work per draw). Kept, since it matches the current code. A single-run A/B cannot resolve gains under ~5 %; use several runs per side (as Frizti does) for small changes.
- **Code / switch:** `pgo/`, `.github/workflows/lichii-tuned.yml`

### 2026-11-07 — Navi hovering over NPCs and animals does not drop the frame rate — ruled out
- **Who:** AkiiTW · **Setup:** A · **Build:** AkiiTW/Lichii@ca4f7d060
- **Where measured:** next to an NPC/animal, fixed camera, Navi alternately on the NPC and back with Link, every 30 s
- **Measured:** by eye on Lichii's frame-time graph: no change between the two states.
- **Conclusion:** ruled out (suspected by players; not worth a log analysis).

### 2026-11-07 — `EDEN_NX2_TC_RT_REUSE`: reusing dropped render targets' host images gains nothing — ruled out
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@ca4f7d060 (04595848c had the switch silently doing nothing: `MarkPoolable` was private, so the `requires` test skipped it)
- **Where measured:** market, fountain laps in the 150-270 s window; same switches as the RT_EVICT entry below plus `EDEN_NX2_TC_RT_REUSE=1`
- **Measured:** 2,750-3,700 host images reused per 600 frames out of ~8,000 new targets (~35 %); the pool sat full at its 1 GiB cap (8 per shape), so most shapes missed. Back zones unchanged within noise (`other` 159 → 156, `clear` 72 → 63, `update buffers` 60 → 64 ms/s). Mean frame 42.5 ms vs 38.5 (test 9) and **40.8 ms in a rerun of test 9's code** (the build where the pool did nothing) → **run-to-run noise here is ~±2-3 ms per frame**; frames > 100 ms 10 in both of the two later runs. Device memory median 9.1 → 10.2 GB (the pool's 1 GiB is outside the cache's count, closer to its 11,264 MiB critical threshold).
- **Conclusion:** ruled out at the time — **revisited:** the clear breakdown above shows each image creation costs ~136 µs, so the gain was likely lost in the noise; the pool is being retried with oldest-first eviction.
- **Code / switch:** `EDEN_NX2_TC_RT_REUSE=1` (off)

### 2026-11-07 — `EDEN_NX2_TC_RT_EVICT=4` + `RT_NO_UPLOAD=3`: texture uploads gone from the back — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@361d13546
- **Where measured:** market, fountain laps from the start of the 150-270 s window
- **Measured:** `texture upload` **66 → 1.3 ms/s** (131 before the texture work); uploads from guest memory 9.6 GB → **53-176 MB per 600 frames**, depth uploads 0; 6,700-7,600 stale render targets dropped early per 600 frames; collector 13-304 deletes, **0 costly, 0-2 downloads**; device memory 7.5-9.1 GB, under the expected threshold (was pinned at critical). Mean frame **40.4 → 38.5 ms**, draws/s 49.4 k → 54.0 k, frames > 100 ms **1** (worst 115 ms). From the start of the day (@d4738fce0): 48.6 → 38.5 ms (+26 % FPS), > 100 ms frames 42 → 1. Player: "much better, 21 FPS minimum, very few drops". No visual defect seen.
- **Conclusion:** kept. The cache now holds real textures; the remaining texture-cache cost is creating ~8,000 images per 600 frames (host image reuse was tried next: no gain, see above).
- **Code / switch:** `EDEN_NX2_TC_RT_EVICT=4`, `EDEN_NX2_TC_RT_NO_UPLOAD=3`

### 2026-11-07 — Ocarina moves its render targets to a new address almost every frame — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@d18e0af21 (`EDEN_NX2_TC_LOG=1`, `RT_NO_UPLOAD=2`)
- **Where measured:** market, 150-270 s after load
- **Measured (per 600 frames):** `R16G16B16A16_FLOAT` 1280×720 created 974-1,152× at 873-1,076 distinct addresses; `D32_FLOAT` 384×384 774-920× at 680-804; `A8B8G8R8_UNORM` 1280×720 652-765× at 591-715; the 2560×1440, 1280×720 and 640×360 targets ~300-390× at ~280-370 addresses. Collector deletes 7,000-7,650 (400-500 costly, 50-59 downloaded — each download waits for the GPU with `runtime.Finish()`). Device memory stays at the critical threshold. Every remaining depth upload (735-797, ~3.8 GB) is "made with an older image to copy from"; none come from guest writes or unmaps.
- **Conclusion:** the targets come from a transient allocator, so the cache can never reuse them by address; stale ones fill it and push the collector into aggressive mode against real textures. Next build (AkiiTW/Lichii@361d13546): `EDEN_NX2_TC_RT_EVICT=<frames>` drops render targets unused for that many frames first, without download; `EDEN_NX2_TC_RT_NO_UPLOAD=3` skips the upload of depth images with join copies too. A further step: reuse a free host image of the same shape instead of creating one (~250 creations/s).
- **Code / switch:** `TextureCache::RunGarbageCollector`, `JoinImages`

### 2026-11-07 — `EDEN_NX2_TC_RT_NO_UPLOAD=2` (new depth images made for sampling too) — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@f9def68d9
- **Where measured:** market, fountain laps from the start of the 150-270 s window
- **Measured:** mean frame 44.0 (`=1`) → **40.4 ms** (`=2`); before any of the texture work (@d4738fce0) it was 48.6 ms. Frames over 100 ms stay low (5 over 7 windows), worst 140 ms. `texture upload` 72 → 66 ms/s. Depth uploads still 350-990 per 600 frames (1.4-5 GB): they now come from a later path, not from image creation. No visual defect seen (shadows checked).
- **Conclusion:** kept. Next: find where the remaining depth uploads come from (CPU-modified marks after a download of an aliased image?), and why the targets are recreated at all (keeping aliased targets alive would also remove most of the ~70 ms/s of clears).
- **Code / switch:** `EDEN_NX2_TC_RT_NO_UPLOAD=2`

### 2026-11-07 — `EDEN_NX2_TC_RT_NO_UPLOAD=1`: far fewer spikes in the market — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@91498b2af
- **Where measured:** market, fountain laps from the start of the 150-270 s window; compared with the same window before the switch (@d4738fce0)
- **Measured:** frames over 100 ms (per ~5 windows of 600 presents) **42 → 6**, worst frame **1,583 → 147 ms**, mean frame 48.6 → 44.0 ms, draws/s 45.0 k → 49.3 k (+9.5 %), `texture upload` 131 → 72 ms/s. 4,500-6,600 new render targets per 600 frames skipped their upload. No visual defect seen (shadows, reflections, screen).
- **Conclusion:** kept. Depth images created by a texture lookup (not as a render target) still upload 3.4-5.4 GB per 600 frames; `EDEN_NX2_TC_RT_NO_UPLOAD=2` (AkiiTW/Lichii@f9def68d9) also skips new depth/stencil images made for sampling — to test.
- **Code / switch:** `TextureCache::JoinImages`

### 2026-11-07 — The churn is render targets recreated every frame or two, each filled from guest memory — confirmed (fix to test)
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@4cccf896c (`EDEN_NX2_TC_LOG=1`)
- **Where measured:** market, 150-270 s after load
- **Measured (per 600 frames):** created 7,934 images, collector deleted 4,997. Most created shapes are render targets: `R16G16B16A16_FLOAT` 1280×720 ×882, `D32_FLOAT` 384×384 ×734 (shadow depths), `A8B8G8R8_UNORM` 1280×720 ×591, `D32_FLOAT` 2560×1440 ×301, `B10G11R11_FLOAT` 2560×1440 ×301, `D32_FLOAT` 1280×720 ×301, 640×360 targets ×~300, all at 0x81xxxxxxxx. Uploads from guest memory: 4,561 = 9.6 GB, of which **depth 1,521 uploads = 6.6 GB**, other colour 589 = 2.3 GB, ASTC 1,215 = 345 MB, BCn 1,236 = 315 MB.
- **Conclusion:** the targets live in memory the game reuses for differently shaped targets (transient heap / aliasing), so the cache drops and rebuilds them, and each rebuild uploads guest memory the GPU overwrites anyway. The existing skip (`overwritten_by_clear`) does not catch them. `EDEN_NX2_TC_RT_NO_UPLOAD=1` (AkiiTW/Lichii@91498b2af): a render target made from scratch (no older image to copy from) starts undefined and is tracked, so CPU writes still upload. The real fix — keeping aliased targets alive — is larger.
- **Code / switch:** `TextureCache::JoinImages`, `FindRenderTargetView`

### 2026-11-07 — Larger texture cache thresholds (12288/13824 MiB) on a 16 GB card: worse — ruled out
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@d4738fce0
- **Where measured:** market, 150-270 s after load, `EDEN_NX2_TC_LOG=1`
- **Measured:** device memory pinned at the new critical (~13,850 MiB), ~4,400 images / ~11 GB, the collector still evicts ~5,000 images per 600 frames (6-9 GB re-uploaded); 14.2 GB VRAM in use on the card, frame spikes up to 1.3 s, ~29-32 frames over 100 ms per 600, mean frame 48.6 → 51.5 ms, draws/s 45 k → 39 k.
- **Conclusion:** the working set does not fit at any threshold this card allows: something creates and drops images continuously (~200 created per second). Back to 9216/11264. Next: `EDEN_NX2_TC_LOG` now logs uploads by kind (ASTC / BCn / depth / colour, into GPU-written images) and the shapes of created images (AkiiTW/Lichii@4cccf896c).
- **Code / switch:** `EDEN_NX2_TC_EXPECTED_MIB`, `EDEN_NX2_TC_CRITICAL_MIB`

### 2026-11-07 — The texture cache thrashes at its critical threshold in the market — confirmed (fix to test)
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@d4738fce0
- **Goal / settings that matter:** `EDEN_NX2_TC_EXPECTED_MIB=9216`, `EDEN_NX2_TC_CRITICAL_MIB=11264` (from the dist `nx2_switches.txt`), VRAM mode Conservative, 16 GB card
- **Where measured:** market, fountain laps, 150-270 s after load, `EDEN_NX2_TC_LOG=1`
- **Measured:** device memory pinned at ~11,250-11,350 MiB (critical 11,264), ~3,800 images / ~8.6 GB. Per 600 frames (~27 s): the collector deletes 6,200-10,200 images and 2,800-5,900 are uploaded again from guest memory, **8.9-17 GB uploaded** (~400 MB/s). This is the 100-160 ms/s of `texture upload` on the back (~1 ms each) and the slower clears.
- **Conclusion:** the "texture uploads after load" entry below is mostly cache thrash, not first-time loading. Raising the thresholds did not help (entry above): the churn is in what gets created, not in the cap.
- **Code / switch:** `TextureCache::TickFrame` collector, `ApplyThresholdOverrides`

### 2026-11-07 — `EDEN_NX2_BANK_COMPARE`: 95 % of re-uploaded bank bytes were unchanged — confirmed
- **Who:** AkiiTW (+ Claude) · **Setup:** A · **Build:** AkiiTW/Lichii@d4738fce0
- **Where measured:** market, 150-270 s after load
- **Measured:** banks ~6-9 MiB/s uploaded vs ~120-185 MiB/s found unchanged; zone `ubo bank` 32.6 → 21.9 ms/s. Frame time not comparable between the runs (texture cache thrash, entry above). No visual defect seen.
- **Conclusion:** kept on. What remains of the zone is the compare itself (memcmp of ~180 MB/s) and its bookkeeping; a cheaper change detector (e.g. tracking writes to those pages) would remove most of it.
- **Code / switch:** `EDEN_NX2_BANK_COMPARE=1`

### 2026-11-07 — Native 64 KiB uniform banks re-uploaded every frame: ~180 MB/s — superseded (see BANK_COMPARE above)
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@984269912 · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market, fountain laps, 150-270 s after load
- **Measured:** zone `ubo bank` ~33 ms/s of the back, ~4,000 banks/s, ~180 MB/s uploaded (~45 KiB each).
- **Conclusion:** the once-per-frame re-upload in `BindHostGraphicsUniformBuffer` (the path for
  `uniform_buffer_sizes == 0x10000` with native tiling) copies the same bytes most frames.
  `EDEN_NX2_BANK_COMPARE=1` (AkiiTW/Lichii@d4738fce0) keeps each bank's last uploaded bytes and skips the
  upload when they still match (exact: the host copy only changes by uploads of guest bytes or GPU writes,
  and GPU-written banks never reach that path). A/B pending. Related: Frizti's queue item 13.
- **Code / switch:** `buffer_cache.h` BindHostGraphicsUniformBuffer, `bank_shadows`; `EDEN_NX2_BANK_COMPARE=1`

### 2026-11-07 — `clean_words` cuts storage buffer binds 64 → 17 ms/s — confirmed (market)
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@984269912 · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market, fountain laps, 150-270 s after load; one run each
- **Measured:** `storage binds` 64.4 → 17.1 ms/s; draws/s 46,400 → 47,800 (+3 %); mean frame 44.7 → 45.1 ms
  (scene noise from texture loading; see the texture entry). No visual defect seen in the market.
- **Conclusion:** `SynchronizeBuffer` walking clean tracker words dominates storage buffer binds
  (~34,000 a second, ~2 µs each). Kept on (`EDEN_NX2_PERF_ON=clean_words`). Not yet checked in Kokiri Forest
  (zortos293/Lichii#161).
- **Code / switch:** `Nx2Perf::Opt::CleanWords`, `BufferCache::SynchronizeBuffer`

### 2026-11-07 — Where "bind stage buffers" goes — confirmed
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@984269912 (new zones) · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market, fountain laps, 150-270 s after load
- **Measured (ms per second of the back):** storage binds ~66 (~34 k/s) · ubo bank ~33 (~4 k/s) ·
  ubo fast ~21 (~240 k/s, ~500 B each, 0.09 µs) · ubo classic ~13 (~46 k/s, ~28 KB each, ~900/s with
  CPU-written data) · rest of the zone ~13. Uniform buffers compared in place: ~150 k unchanged / ~85 k
  changed per second.
- **Conclusion:** the small-uniform fast path is already cheap. The first guess (big banks taking the
  slow path) was wrong. Storage buffers and bank re-uploads are the targets.
- **Code / switch:** zones `ubo fast`, `ubo classic`, `ubo bank`, `storage binds`, `texbuf binds` in
  `nx2_profile.h`

### 2026-11-07 — Texture uploads cost the back ~1 ms each for minutes after loading — superseded (cache thrash, above)
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@d8e4fe222 · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market, 150-270 s after load, vs. the same spot after 20 min of play
- **Measured:** `texture upload` 100-160 ms/s (~90-180 uploads/s) after load vs. ~8 ms/s later; `clear`
  ~40 µs each vs. ~13 µs. Same per-call cost for every other zone. Market ~21-22 FPS in that window vs.
  28-30 later.
- **Conclusion:** right after loading, texture uploads are the biggest single cost on the back. Settings:
  `accelerate_astc=Gpu`, `astc_recompression=Bc3` (transcoded on the GPU), so the CPU part is something
  else (staging, copies). `EDEN_NX2_TC_LOG=1` run pending. Idea: do uploads off the back thread.
- **Code / switch:** `TextureCache::RefreshContents` (zone `texture upload`)

### 2026-11-07 — The back is the limit in the market: ~2,100 draws per frame at ~15 µs — confirmed
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@eba617204 · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market, fountain laps, after ~20 min of play
- **Measured:** back ~870-880 ms/s busy, ~60,000 draws/s, ~2,100 draws/frame, 27-30 FPS. Front 95 % busy
  of which ~520 ms/s waiting for the back (fence release 288 ms at 1,463/s, macro DMA read 216 ms at
  2,010/s). Guest cores 40-60 % each, VulkanWorker ~20 %, presents never wait on the host GPU fence.
  Back zones (ms/s): bind stage buffers 184, method 163, other 109, update buffers 62, draw 52,
  flush work 48, compute 46, pipeline lookup 35, fill image views 30, read handles 26, clear 25.
- **Conclusion:** per-draw cost on the back and the front↔back waits set the frame rate; the host GPU
  does not. The console does ~126,000 draws/s (1080p60).
- **Code / switch:** `EDEN_NX2_GPU_PROFILE=1`, `EDEN_NX2_THREAD_USAGE=1`

### 2026-11-07 — Game-file mods: only NPC shadow distance helps — confirmed / ruled out
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@eba617204 · **Hardware:** 3800X / 5060 Ti
- **Where measured:** market then Hyrule Field, same route each run
- **Measured:** `System/GameGraphics/LocalDepthShadowParam` `NPCFadeStart/End` 25/30 → 8/10 m:
  ~2,270 → ~2,100 draws/frame in the market (−6 %), 26-27 → 27-29 FPS (**confirmed**).
  `gsys/ModelSceneConfigParam/Main` `DepthShadowCascadeNum0` 3 → 2: same draws, rainbow/blown-out lighting
  in Hyrule Field (**ruled out**: shaders expect 3 cascades). Handheld mode (`_hh` LOD settings): ~0
  (**ruled out**).
- **Conclusion:** draws come from the scene itself; game files will not move the frame rate much more.
  Patch values in place (same file size, no RESTBL change).
- **Code / switch:** LayeredFS mods in `load/0400486024DEC000/<mod>/romfs/`

### 2026-11-07 — MinGW builds: threads had no OS names; the sampler crashed — confirmed, fixed
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@df6362759, @984269912 · **Hardware:** 3800X / 5060 Ti
- **Measured:** `SetThreadDescription` was only called in MSVC builds, so `EDEN_NX2_SAMPLE` matched no
  thread in clang/MinGW builds. Once names were set, the sampler froze then crashed the emulator when it
  started.
- **Conclusion:** names fixed for `_WIN32`; the sampler's stack walk now reads only between the paused
  RSP and the thread's stack base and stops at a frame that does not move up. Not retested yet; zone
  profiling (`GPU_PROFILE`) was enough so far.
- **Code / switch:** `common/thread.cpp` SetCurrentThreadName, `common/nx2_sampler.cpp` Walk

### 2026-11-07 — "HostTiming" threads at ~98 % CPU are a wait, not work — confirmed
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@eba617204
- **Conclusion:** `Common::Event::WaitFor` uses MONITORX/MWAITX on Ryzen: the OS counts the thread busy
  while the core sleeps in C1. Low priority; could matter only if it shares a core with a GPU thread.

### 2026-11-06 — Pipeline cache: merge keys that differ only in unread vertex attribute types — confirmed
- **Who:** AkiiTW (+ Claude) · **Build:** AkiiTW/Lichii@1db14a304, @e941a3b89 · **Hardware:** 3800X / 5060 Ti
- **Measured:** one session: 6,570 duplicate cached pipelines merged, 17,504 rewritten from another driver
  version, 20,184 loaded; no in-game pipeline builds in the village afterwards.
- **Conclusion:** keys carry vertex attribute types the shader never reads; clearing them (per vertex
  shader pair) and filing shared caches under the local `driver_version` when `driver_id` matches removes
  most mid-game builds when using a shared cache. `EDEN_NX2_VERTEX_KEY_MERGE=0` turns the merge off.
- **Code / switch:** `vk_pipeline_cache.cpp` NormalizeVertexInputKey, disk loader

### 2026-11-06 — `EDEN_NX2_PREFLUSH=1` causes one-frame white flashes — ruled out
- **Who:** AkiiTW (+ Claude) · **Build:** Frizti V3
- **Conclusion:** removed from the built-in switches in AkiiTW's branch (@30a75df6d); flashes gone.

### 2026-11-05 — Earlier tries without gain — ruled out
- `TC_NO_CAP` (texture cache following the whole VRAM budget): worse half-turns (13 FPS, white flash);
  fixed thresholds 9216/11264 MiB were better.
- `DMA_READ_WAIT=track`: 98 % of reads still waited, slightly slower.
