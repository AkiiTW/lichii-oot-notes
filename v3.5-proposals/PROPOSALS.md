# Proposals in detail

Each section: the problem as measured, the change (files, functions, exact conditions), the switch,
the measurement, the risk and how to check it, and how it meets your work. Numbers are Setup A
(Ryzen 7 3800X + RTX 5060 Ti 16 GB) unless stated.

---

## P01 — New render targets and depth images skip the guest-memory upload

**Problem.** In the Castle Town market the texture cache creates ~7,000-8,500 images per 600 frames.
`EDEN_NX2_TC_LOG` shapes show they are render targets: `R16G16B16A16_FLOAT` 1280×720 ×882,
`D32_FLOAT` 384×384 ×734 (shadow depths), `A8B8G8R8_UNORM` 1280×720 ×591, `D32_FLOAT` 2560×1440 ×301,
`B10G11R11_FLOAT` 2560×1440 ×301, `D32_FLOAT` 1280×720 ×301, 640×360 targets ×~300, all around
`0x81xxxxxxxx`. The collector deletes about as many (aggressive mode at the critical threshold,
`ticks_to_destroy = 10`). Each new one went through `RefreshContents` and uploaded guest memory:
4,561 uploads = **9.6 GB per 600 frames, 6.6 GB of it into D32 depth buffers** the GPU overwrites
anyway. Your `overwritten_by_clear` skip in `JoinImages` does not catch them (no full clear at
creation). This was the 100-160 ms/s of `texture upload` on the back and most of the >100 ms frames.

**Change** (`src/video_core/texture_cache/texture_cache.h`, `texture_cache_base.h`):
- New member `finding_render_target`, set to `true` around the `FindOrInsertImage` loop in
  `FindRenderTargetView` and back to `false` after it.
- In `JoinImages`, before the `overwritten_by_clear()` branch:
  ```
  static const int rt_no_upload = EDEN_NX2_TC_RT_NO_UPLOAD ('1' or '2', else 0), logged once
  depth_format = GetFormatType(new_info.format) != SurfaceType::ColorTexture
  if (rt_no_upload != 0 && (finding_render_target || (rt_no_upload >= 2 && depth_format)) &&
      join_copies_to_do.empty() && !(new_image.flags & Sparse)) {
      new_image.flags &= ~CpuModified;
      if (!(new_image.flags & Tracked)) TrackImage(new_image, new_image_id);
      runtime.TransitionImageLayout(new_image);
      ++render_target_uploads_skipped;
  } else if (overwritten_by_clear()) { ... unchanged ... } else { RefreshContents(...) }
  ```
- `=1`: images created while looking up a render target (`FindColorBuffer` / `FindDepthBuffer`).
  `=2`: also any new depth/stencil-format image (e.g. a shadow map first created by a texture lookup).
- Never applied when an older overlapping image has to be copied in (`join_copies_to_do` not empty)
  or to sparse images. The image is tracked, so a later CPU write to its memory still marks it
  `CpuModified` and uploads it.

**Measured** (market, 150-270 s window): before (@d4738fce0) / `=1` (@91498b2af) / `=2` (@f9def68d9):
mean frame 48.6 / 44.0 / 40.4 ms; frames > 100 ms 42 / 6 / 5; worst 1,583 / 147 / 140 ms;
`texture upload` 131 / 72 / 66 ms/s; uploads skipped 4,500-6,700 per 600 frames. No visual defect seen
(shadows, reflections, screen) in the market.

**Risk / check.** A game that renders on top of memory the CPU filled *without* a CPU write after the
image exists (e.g. CPU-written texture later used as a render target in the same memory before the cache
saw it), or that reinterprets a deleted GPU-written image's downloaded contents, would see undefined
contents. Check: Kokiri Forest, Hyrule Field at dusk/night, the castle interior, menus and the map
screen, the pause-menu background blur, cutscenes. `EDEN_NX2_TC_RT_NO_UPLOAD=0` restores the old path.

**Still open.** Depth uploads remain at 350-990 per 600 frames (1.4-5 GB) with `=2`, from a later path;
patch 28 (@88730eb2a) counts why (guest write by size / whole image, unmap, created with copies,
sparse). The deeper fix is to stop the churn: patch 29 (@d18e0af21) counts distinct addresses per shape
to see whether the game moves its targets every frame (then: reuse a free image of the same shape) or
the collector drops them at the same address.

**Update (17:00).** The distinct-address count answers it: Ocarina moves its targets to a new address
almost every frame (e.g. 974 created at 873 addresses per 600 frames), and every remaining depth upload is
a new depth image with older images copied in. Under test (@361d13546): `EDEN_NX2_TC_RT_NO_UPLOAD=3`
(skip those too; the copies still run) and `EDEN_NX2_TC_RT_EVICT=<frames>` (drop render targets unused
for that many frames first, without the download that waits on `runtime.Finish()`).

**Result (17:18, @361d13546, `RT_NO_UPLOAD=3`, `RT_EVICT=4`):** `texture upload` 66 → 1.3 ms/s, uploads
9.6 GB → 53-176 MB per 600 frames (0 depth), collector 13-304 deletes with 0 costly and 0-2 downloads,
device memory 7.5-9.1 GB (under expected), mean frame 38.5 ms, frames > 100 ms: 1. `RT_EVICT` code: at the
start of `RunGarbageCollector`, up to 64 images with `transient_target` (set in `JoinImages` from
`finding_render_target`) below `frame_tick - N` in the LRU are untracked, unregistered and deleted with no
download. `=3`: the skip also applies to depth images with join copies (the copies still run after it).

**Later (2026-11-07 evening).** `RT_EVICT` no longer walks the LRU (P13, @b3983fefb); `RT_EVICT=2`
was tested and is worse (image creations 396 → 672/s: some targets are reused after 2-3 idle frames), so
4 stays. P12 builds on `RT_EVICT`.

**Meets your work.** Fewer image creations also means fewer framebuffer rebuilds and fewer deferred
clears on the back; it does not touch the split or the front's waits.

---

## P02 — Re-upload a native 64 KiB uniform bank only when its bytes changed

**Problem.** `BindHostGraphicsUniformBuffer` re-uploads each 64 KiB bank of native programs once per
frame (the path guarded by `uniform_buffer_sizes == 0x10000`, `UsesNativeTiling()`, `BankCheck`,
`!IsRegionGpuModified`, `native_indirect_uniforms_this_frame.insert(...).second`). Market: ~4,000
banks/s, ~180 MB/s, zone `ubo bank` ~33 ms/s.

**Change** (`buffer_cache.h`, `buffer_cache_base.h`, `nx2_profile.h`):
- `std::unordered_map<DAddr, BankShadow> bank_shadows` with `BankShadow { BufferId buffer_id;
  std::vector<u8> bytes; }`.
- With `EDEN_NX2_BANK_COMPARE=1`, inside that path, before `UploadMemory`: `GetSpan(device_addr,
  upload_size)`; if contiguous, same `buffer_id` and same bytes as the shadow → skip the upload and
  count `UboBankSkipped`; else store the bytes and upload as before. Non-contiguous → erase the entry,
  upload.
- `DeleteBuffer` erases the shadows of that buffer id (slot ids are reused).
- Exact by construction: the host copy changes only by uploads of guest bytes or by GPU writes, and a
  GPU-written bank never reaches this path.

**Measured:** 95 % of the bytes unchanged (~6-9 MiB/s uploaded vs 120-185 MiB/s found unchanged);
`ubo bank` 32.6 → 21.9 ms/s; no visual defect.

**Overlap with your queue item 13** (per-bind bank check with `memchr`, ~10 % of the back, a flicker
fixed by EXP4). Both touch the same block. What is left of `ubo bank` with P02 is the `memcmp` of
~180 MB/s; a write-tracking signal (pages of the bank written since the last upload) would remove it.
Please decide which version lands and tell AkiiTW; his Claude will rebase onto yours.

---

## P03 — `clean_words` on by default

**Problem.** `storage binds` (now its own zone) cost ~64 ms/s in the market: ~34,000 binds/s, ~2 µs
each, mostly `SynchronizeBuffer` walking clean tracker words over whole storage buffers.

**Change.** None in code: `EDEN_NX2_PERF_ON=clean_words` (your `Nx2Perf::Opt::CleanWords`). Proposal:
take it out of `default_off` for V3.5 once checked.

**Measured:** `storage binds` 64.4 → 17.1 ms/s; draws/s +3 % (scene noise around it). No defect in the
market. Not yet checked in Kokiri Forest against the zortos293/Lichii#161 slab; `EDEN_NX2_PERF_VERIFY=1`
logs any wrong clean word (`Nx2Perf draw-binds: clean tracker words wrong near ...`).

**Update 2026-11-07 evening.** On for every Setup A run since; the PGO recording session (market,
Hyrule Field, then on foot into Kokiri village, ~3.5 min each) showed no defect, but nobody looked for
the #161 slab on purpose. Your 20:03 A/B (42.8 vs 42.4 FPS) matches Setup A: the zone saving does not
show as FPS while the two GPU threads take turns.

---

## P04 — Pipeline keys: unread vertex attribute types, driver version

**Problem.** Shared pipeline caches (and the game itself) produce keys that differ only in
`attribute_types` of vertex attributes the shaders never read, and caches made on another driver
version are not reused. Result: in-game pipeline builds in places the cache covered.

**Change** (`vk_pipeline_cache.cpp/.h`, `vk_graphics_pipeline.h`):
- `RecordAttributeMask(key, program_mask)` keeps, per pair of vertex/fragment shader hashes
  (`unique_hashes[0..1]`), the union of attribute loads of the vertex program; `NormalizeVertexInputKey`
  clears the types of attributes outside that mask (only when `dynamic_vertex_input`). Lookups go
  through the normalized key; `CreateGraphicsPipeline` files the pipeline under it
  (`stored_key.state.attribute_types &= RecordAttributeMask(...)`), and pipelines remember their disk
  key (`SourceHash`) for the used list.
- V3's clean path (`CurrentGraphicsPipelineClean`) refreshes with the raw types, then normalizes:
  `graphics_key.state.attribute_types = raw_attribute_types; Refresh(...); raw_attribute_types =
  ...; NormalizeVertexInputKey(graphics_key);`. The slow path tries the normalized key, then the raw one
  (`TakeBackgroundPipeline`).
- Disk loader: entries with the same `driver_id` but another `driver_version` are re-filed under the
  local version (logged: "N cached graphics pipelines came from another driver version"); duplicates
  after normalization are merged ("N ... differed only in unread attributes ... dropped").
- `EDEN_NX2_VERTEX_KEY_MERGE=0` turns the merge off; `EDEN_NX2_PIPELINE_DIFF=1` logs what a new
  pipeline differs in from a cached one with the same shaders (diagnostic, patch 11).

**Measured:** one session: 6,570 duplicates merged, 17,504 entries re-filed, 20,184 loaded; no in-game
builds in the village afterwards (build-88 era, with a shared NVIDIA cache).

**Meets your work.** Your fix `9b8fef282d` (pipeline cache) and zortos #465 / #408 touch the same file;
compare before merging.

---

## P05 — No `EDEN_NX2_PREFLUSH` in the built-in switches

`{"EDEN_NX2_PREFLUSH","1"}` in `BuiltinSwitches` (`src/yuzu/main.cpp`) caused one-frame white flashes
(video sent by AkiiTW at the time); removing it fixed them with no measurable loss. Patch 15 also
carries one workflow line.

---

## P06 — MinGW / clang build fixes

- `vk_host_pacer.cpp`: `#pragma comment(lib, "dwmapi.lib")` only under `_MSC_VER`;
  `video_core/CMakeLists.txt` links `dwmapi` on `WIN32` (MinGW has `-Werror` on unknown pragmas).
- `common/thread.cpp` `SetCurrentThreadName`: call `SetThreadDescription` (looked up in KernelBase) on
  all `_WIN32` builds, not only `_MSC_VER`. Without it, `EDEN_NX2_SAMPLE` matched no thread in MinGW
  builds.
- `common/nx2_sampler.cpp` `Walk`: reads only between the paused RSP and the thread's stack base (from
  the TEB via `NtQueryInformationThread`, `THREAD_QUERY_INFORMATION` added to `OpenThread`) and stops
  at a frame whose RSP does not move up. Without it the sampler froze then crashed a MinGW build at
  start (likely a wrong unwind through code without unwind data). Not re-tested since; GPU_PROFILE
  zones were enough.

---

## P07 — L3-domain thread placement (multi-CCX / multi-CCD Ryzen)

`common/nx2_placement.{h,cpp}`, applied from `thread_worker.h`, `cpu_manager.cpp`, `gpu_split.cpp` and
the Vulkan worker. `EDEN_NX2_PLACEMENT=gpu` keeps GPU front, back and VulkanWorker on one L3 domain;
`split` also keeps guest cores, pipeline builders and texture workers off it;
`EDEN_NX2_PLACEMENT_DOMAIN`, `EDEN_NX2_PLACEMENT_GPU=<mask>`, `EDEN_NX2_PLACEMENT_CORES=0` (by default
front and back each get a whole physical core). Log: `Nx2Placement: mode=split gpu=0xff00 rest=0xff
front=0x300 back=0xc00 worker=0xf000` on a 3800X. Measured in the build-88 era (Kokiri): 28-29 FPS vs
24, wide view 24 vs 18-19 — together with other changes of that build. Your queue item 5 (P-cores on
Intel hybrid, one L3/CCD on dual-CCD Ryzen) and zortos #418 (GPU thread pinning) overlap: keep one.

---

## P08 — Pipeline eviction switch and dist defaults

`EDEN_NX2_PIPELINE_EVICT_FRAMES=<frames>` (0 = never) in `EvictUnusedPipelines`; your
`EDEN_NX2_PIPELINE_EVICT_ABOVE` stays. AkiiTW's dist file also sets `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`
and `EDEN_NX2_TC_OLD_AGE=0`. Your queue item 6 (eviction cap from installed RAM) supersedes the fixed
numbers.

---

## P09 — Diagnostics

- `EDEN_NX2_THREAD_USAGE=1` (`common/nx2_thread_usage.{h,cpp}`, hooked in `SetCurrentThreadName`):
  every 10 s, process CPU % and each named thread's CPU % (pools summed by name), Windows only; exited
  threads counted once then dropped.
- `GPU_PROFILE` zones appended to `Nx2Profile::Zone` (after `ListGpuWait`): `ubo fast`, `ubo classic`,
  `ubo bank`, `storage binds`, `texbuf binds`, and counters `UboFastBytes`, `UboClassicBytes`,
  `UboClassicSynced`, `UboBankBytes`, `UboBankSkipped` (the back line gains "uniform buffer sizes: …").
  Appended at the end so your zone indices do not move.
- `EDEN_NX2_TC_LOG`: uploads by kind (ASTC / BCn / depth / colour) and into GPU-written images; created
  shapes at Info with distinct addresses per shape; render targets not uploaded (P01); why depth images
  are marked CPU-modified; host images reused / made new / pooled (P12); images deleted and overlaps
  unlinked (P13).
- More `GPU_PROFILE` zones, appended after the ones above: `clear targets` (a clear finding its render
  targets and framebuffer — the old `clear` time was nearly all this and what it nests), `image join`,
  `image create` (VkImage + memory), `view create`, `framebuffer create`, `tc tick`, `image free`,
  `tc collect`, `image delete`, `framebuffer remove`, `delete views`, `delete overlaps`,
  `delete sentence`. They showed texture-cache upkeep at ~170 ms/s of the back in the market (→ P12, P13).
- Guest CPU readback wait log (`GPU::OnCPURead`, always on, every 10 s): reads/s, ms waited, longest wait,
  KiB. Market: ~120-150 reads/s, 110-200 ms/s waited (~1.2 ms each) — the guest CPU stops that long while
  the GPU threads catch up; the game's auto-exposure / scene-shading analyzer and occlusion queries are
  the likely readers. Your preflush / async reactive flush work is the fix; this line measures it.
- Slow-frame log (`HostPacer::LogSlowFrame`, always on): each frame shown more than 60 ms after the one
  before is logged with the guest readbacks and their wait, textures uploaded, images made, pipelines
  built and collector deletes since the previous frame (`Nx2Perf::g_hitch` counters). Meant for the
  spikes on arriving in a new area, which the fixed test window (150 s after load) never sees.

---

## P10 — On-screen test window

`common/nx2_test_window.{h,cpp}` (started in `core.cpp` right after `Nx2Sampler::StartFromEnvironment`,
stopped in `ShutdownMainProcess`) and `yuzu/render/test_overlay.{h,cpp}` (created in
`MainWindow::OnLoadComplete`, deleted with the performance overlay). Switches:
`EDEN_NX2_TEST_START`, `EDEN_NX2_TEST_SECONDS`, `EDEN_NX2_TEST_LABEL`, `EDEN_NX2_TEST_PREPARE`,
`EDEN_NX2_TEST_PURPOSE` (what the test measures, wrapped under the title for the whole test, the panel
grows to fit; also logged — asked for by the player so he knows what each run is for); follows
`EDEN_NX2_SAMPLE_START/SECONDS` when the sampler is on. Log lines `Nx2TestWindow: recording starts` /
`ends` let scripts cut a log to the window (`../tools/cmp_windows.py`). Your fixed-route steering is the
better tool for A/B; this one is for runs played by hand.

---

## P11 — Windows MSYS2 clang workflow

`.github/workflows/lichii-tuned.yml`: MSYS2 UCRT clang 23, `-march` preset (zen2 for AkiiTW), PGO merged
from `eglantine.profdata` and the profiles in `pgo/` (weight 4), flavors `normal`, `pgogen` (only GPU
emulation and the shader recompiler instrumented) and `symbols` (`-gline-tables-only -gcodeview`,
`lichii.pdb`). Packages DLLs by walking `objdump -p` imports. Note: MSYS2's zlib 1.4 now ships
`libz-1.dll`; copy the whole artifact, not only the exe. Optional for an MSVC release.

---

## P12 — Reuse the host images of dropped render targets (`EDEN_NX2_TC_RT_REUSE`)

**Problem.** With P01 the market still makes ~400 new render-target images a second (Ocarina moves its
targets to a new address almost every frame). The zones of @d9bf5d902 put a price on it: **image create
52 ms/s (136 µs each: VkImage + VMA memory)** and `tc tick` 80 ms/s (freeing them) on the back.

**Change** (`renderer_vulkan/vk_texture_cache.{h,cpp}`, `texture_cache/texture_cache.h`):
- `TextureCacheRuntime` keeps a pool of `vk::Image` keyed by shape: `ImagePoolKey` = (format + 1) << 48 |
  width << 24 | height, only for plain 2D, 1 level, 1 layer, 1 sample, depth 1, no ASTC/BCn/huge ASTC/
  opaque BC1, not sparse or unwritten sparse (contents of such a target are undefined anyway).
- `Image`'s constructor takes `original_image` from `AcquireOriginalImage`: a pooled image of that key
  when `EDEN_NX2_TC_RT_REUSE=1`, else `MakeImage` as before. `TransitionImageLayout` already starts a new
  `Image` object from `UNDEFINED` (`ExchangeInitialization`), so a reused VkImage is valid.
- The `RT_EVICT` drop loop calls `image.MarkPoolable()` (public: the texture cache tests for it with a
  `requires` expression, which silently skips a private member — the first build did nothing for that
  reason). `~Image()` gives a poolable, unscaled `original_image` to `PoolImage` when the sentenced image
  is finally destroyed (GPU done with it).
- Bounds: 32 per shape, 512 MiB in all; when over budget the **oldest pooled images are destroyed
  first** (`image_pool_order`). The first version refused new images once full and stayed stuck on
  shapes no longer asked for (~35 % reuse, no gain).
- Not for MSAA (per-VkImage resolve shadows).

**Measured** (market, @a099ef505 vs @d9bf5d902): 84 % of host images reused (5,000-8,000 per 600 frames,
700-1,650 made new, pool 380-510 MiB); `image create` 52 → 15 ms/s; `tc tick` 80 → ~45 ms/s; texture-cache
upkeep ~164 → ~90 ms/s; **mean frame 38.7 → 35.0 ms**, every block 34.3-35.7 ms; frames > 100 ms 1.
Player: "best performance so far". No visual defect.

**Risk / check.** A reused VkImage keeps the old target's pixels until written; only images whose
contents are undefined anyway are pooled (P01's targets). 512 MiB of VRAM sits outside the cache's
count (the cache still reads the real device usage). Off: `EDEN_NX2_TC_RT_REUSE=0`.

**Meets your work.** Your 20:11 status found the same churn (~9 % of your back creating/freeing
textures) and tried a larger cache cap; here the cap was not the cause (new address every frame), and a
larger cap on a 16 GB card was worse (VRAM full, spikes). Take P01 + P12 + P13 together.

---

## P13 — Cheaper upkeep of transient render targets

Three small changes found with the P09 zones, same results with less work:
- **`RT_EVICT` scan** (@b3983fefb): the drop loop walked the LRU from its oldest end every frame,
  through thousands of textures older than a few frames, to find ~15 stale targets. A
  `transient_targets` list (filled in `JoinImages`, swap-removed in `DeleteImage`) is checked instead,
  with `LeastRecentlyUsedCache::GetTick` (new) for the last use. ~5 ms/s less.
- **View format support** (@b3983fefb): `ImageView`'s constructor asked the driver for depth-comparison
  and min/max filter support of the view format on every view (~600/s); `TextureCacheRuntime::
  view_format_support` keeps the answer per `VkFormat`. No measurable change (the two
  `vkCreateImageView` calls are the cost); kept as harmless.
- **Overlap unlink** (@3832dc36b): `DeleteImage` removed the image from each alias's and overlap's list
  with `erase_if` over the whole list. A transient target has ~140 overlaps whose lists are about as
  long. `std::ranges::find` + `erase` (order kept, an image is in such a list once): `delete overlaps`
  **22 → 13 ms/s**.

Left after P12 + P13 (market, ms/s on the back): view create ~17, image free ~17, delete overlaps ~13,
image create ~15, image join ~12, clear targets ~10.
