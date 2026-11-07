# Compatibility with Frizti's newer tree and work

The patches are against `frizti-v3` (`00ef0ea6c`). Your tree has moved on (EXP4, EXP10, per-page write
index, tracked inline uploads, port/zortos-nov7, pacer work, `9b8fef282d`, `7d5ddd36b7`,
`82a514211d`, `4f515cfc07`, `f319e1076a`…). Below, every place where a proposal and your work touch
the same code or the same problem, and what to check. Your Claude: add a line when you find another.

## Same code

| File / function | AkiiTW proposal | Your side | What to check |
| --- | --- | --- | --- |
| `buffer_cache.h` `BindHostGraphicsUniformBuffer`, the 64 KiB native bank block | P02 compare-before-upload (`bank_shadows`) | Queue item 13: per-bind bank check (`memchr`), EXP4 flicker fix | **Pick one design.** P02 assumes V3's block (`BankCheck` set + `IsRegionGpuModified` + `native_indirect_uniforms_this_frame`); if yours replaced it, port the idea (skip the upload when the bytes match the last upload) or drop P02 |
| `buffer_cache.h` `BindHostStageBuffers` | P09 wraps storage and texture buffer binds in zones | — | Trivial; keep the zones if you want the split numbers |
| `nx2_profile.h` `Zone`, `zone_names`, `Counter` | P09 appends 5 zones and 6 counters at the end | You may have added zones/counters | Append ours after yours; `zone_names` must stay the same length as `Zone::Count`; `Counter::Count <= 64` |
| `texture_cache.h` `JoinImages` (`overwritten_by_clear`), `FindRenderTargetView` | P01 adds a branch before `overwritten_by_clear()` and the `finding_render_target` flag | Your `overwritten_by_clear` skip; 2D blits noted by destination (15:58) | Keep both: P01 only applies with no join copies and not sparse. Blits create images too: check whether blit destinations should be covered (they are not by `=1`; `=2` covers depth ones) |
| `texture_cache.h` `TickFrame` (`EDEN_NX2_TC_LOG` block), `RefreshContents`, `WriteMemory`, `UnmapGPUMemory` | P09 counters and Info lines | — | Counters only; no behaviour change |
| `vk_pipeline_cache.cpp` disk loader, `CurrentGraphicsPipelineClean`, slow path, `CreateGraphicsPipeline` | P04 | `9b8fef282d` (cache fix), zortos #465 (bounded wait for unbuilt pipelines), #408 (no mid-game rebuilds) | Highest conflict risk. Re-apply P04 on top of yours by hand if needed: the essentials are `RecordAttributeMask` / `NormalizeVertexInputKey`, filing under the normalized key, and the driver-version re-filing in the loader |
| `vk_pipeline_cache.cpp` `EvictUnusedPipelines` | P08 `EDEN_NX2_PIPELINE_EVICT_FRAMES` | Queue item 6 (cap from installed RAM) | Yours supersedes; keep the switch as an override if useful |
| `common/thread.cpp` `SetCurrentThreadName` | P06 `SetThreadDescription` on `_WIN32`; P09 `Nx2ThreadUsage::OnThreadNamed` hook | `Nx2SampleProfile::OnThreadNamed` already there | Keep all hooks |
| `common/nx2_placement.*`, `cpu_manager.cpp`, `gpu_split.cpp`, Vulkan worker | P07 | Queue item 5 (Intel P-cores, one CCD on dual-CCD Ryzen), zortos #418 (GPU thread pinning), #232 (hybrid P-cores, merged) | Keep one pinning scheme. P07's value is L3-domain awareness and a full physical core each for front and back on multi-CCX parts |
| `src/yuzu/main.cpp` `BuiltinSwitches` | P05 removes `EDEN_NX2_PREFLUSH` | Your plug-and-play settings `4f515cfc07` | Make sure PREFLUSH did not come back |
| `vk_host_pacer.cpp`, `video_core/CMakeLists.txt` | P06 dwmapi | Pacer safety `82a514211d`, 30 FPS phase alignment `7d5ddd36b7` | P06 is only the link line; no conflict expected |
| `core/core.cpp`, `yuzu/main_window.*` | P10 test window | — | Independent |

## Same problem, different halves

- **Front waits vs back cost.** Your overlap work (the two GPU threads taking turns; up to +25-28 %)
  and AkiiTW's back savings (P01-P03) add up: once the front stops draining the back, every ms saved on
  the back becomes frame time. In Setup A the back is ~840-910 ms/s busy, so overlap alone is capped
  lower there (~+15 %).
- **Render target churn vs blits.** If your blit tracking shows blit destinations being recreated like
  the targets in P01, tell AkiiTW: the same "reuse a free image of the same shape" fix would cover both.
- **PGO.** Your retrained profile (market route + Hyrule Field) can replace AkiiTW's
  `pgo/ocarina-village-cd1f029.profraw` once the trees are close.

## Switch names

No collisions found with V3's switches. New names: `EDEN_NX2_TC_RT_NO_UPLOAD`, `EDEN_NX2_BANK_COMPARE`,
`EDEN_NX2_THREAD_USAGE`, `EDEN_NX2_TEST_START`, `EDEN_NX2_TEST_SECONDS`, `EDEN_NX2_TEST_LABEL`,
`EDEN_NX2_TEST_PREPARE`, `EDEN_NX2_VERTEX_KEY_MERGE`, `EDEN_NX2_PIPELINE_DIFF`,
`EDEN_NX2_PIPELINE_EVICT_FRAMES`, `EDEN_NX2_PLACEMENT*`. If one clashes with yours, rename ours.

## Platforms

Everything builds with MSVC as well as MinGW clang (the MinGW fixes are guarded). `THREAD_USAGE` and
the sampler are Windows-only and compile to nothing elsewhere. The test overlay needs Qt (the CLI build
only gets the log lines).
