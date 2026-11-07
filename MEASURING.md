# How the numbers are taken

## Switches

Lichii V3-based builds read `EDEN_NX2_*` switches from `%APPDATA%\eden\nx2_switches.txt` (this one wins),
then `nx2_switches.txt` next to the exe, then built-in defaults. One `NAME=value` per line, `#` comments.
They are read when Lichii starts: restart Lichii after a change.

| Switch | What it gives |
| --- | --- |
| `EDEN_NX2_GPU_PROFILE=1` | Every 10 s, per GPU thread: ms per second in each zone, calls per second, counters (`video_core/nx2_profile.h`) |
| `EDEN_NX2_THREAD_USAGE=1` | Every 10 s: process CPU % and each named thread's CPU % (100 % = one logical CPU) — AkiiTW's branch |
| `EDEN_NX2_TEST_START=150`, `EDEN_NX2_TEST_SECONDS=120` | A test window 150-270 s after the game is loaded: an on-screen countdown (AkiiTW's branch) and the log lines `Nx2TestWindow: recording starts` / `ends` |
| `EDEN_NX2_TC_LOG=1` | Texture cache every 600 frames: images created/deleted, uploads and MiB, largest upload |
| `EDEN_NX2_PERF_ON=<names>` / `EDEN_NX2_PERF_OFF=<names>` | Turn V3 optimizations on/off (`video_core/nx2_perf.h`); `EDEN_NX2_PERF_VERIFY=1` checks them against the old way |
| `EDEN_NX2_TEST_LABEL` / `_PREPARE` / `_PURPOSE` | The panel's texts: what to do during the window, before it, and what the run measures (AkiiTW's branch) |
| `EDEN_NX2_TIMELINE=<dir>` (+ `_AT`, `_SECONDS`, `_DETAIL`) | A Chrome/Perfetto trace of every thread for a few seconds, `_AT` seconds after the first present (~120 MB for 6 s of coarse spans) |
| always on (AkiiTW's branch) | `Guest CPU reads of GPU-written memory per second: …` every 10 s (reads, ms waited, longest); `Slow frame: …` for each frame over 60 ms with what happened during it |

## The run

1. Same save, same spot. AkiiTW's runs: Castle Town market, laps around the fountain while turning the
   camera, inside the test window (so every run is at the same time after loading — the first minutes
   after a load are dominated by texture uploads).
2. One change per run. **Close Lichii completely between runs**: switches are read when Lichii starts,
   not when a game starts (a run with only the game restarted kept the old value).
   After a build that changes shader translation (e.g. cooperative-matrix HMMA), the first launch
   rebuilds shaders and stutters: measure on the second launch.
3. Compare **draws per frame** (draws/s ÷ frames/s) before FPS: it tells a game-side change from an
   emulator-side one. Compare zone times per call (ms ÷ calls) to see whether a cost moved.
4. Expect ±5 % noise between runs of the same build (camera, NPCs, loading): in Setup A the same code
   gave 35.0-38.3 ms per frame over five runs. A single run cannot resolve a gain under ~5 %; judge small
   changes on their own zones (ms/s and per-call µs), or do several launches per side as Frizti does.
5. The window starts 150 s after load, so it measures a warmed-up area. Spikes on arriving somewhere new
   happen before it; catch them with an early window (`EDEN_NX2_TEST_START=30`, route into new areas)
   and the `Slow frame` lines.

## Reading a profile line

`GPU back thread per second: | <zone> <ms> ms (<calls>/s) | … | split wait <ms>` — exclusive time per
zone; `other` is the back's time outside every zone; `split wait` is the back idle, waiting for the
front. The front's line has `split drain` (front waiting for the back) and its causes.

## Scripts

- `tools/cmp_windows.py <log> <log> …` — means of the main back zones, draws/s and frame time inside each
  log's test window (needs the `Nx2TestWindow` lines).
- `tools/profile_windows.py <log>` — one line per 10 s window: draws/s, back and front busy, drains,
  thread CPU, render passes.

## Comparing across setups

Absolute numbers (FPS, ms per second, µs per draw) follow the CPU: the back is one thread, so its speed
is single-core speed (clock, IPC, cache size, memory latency). A Zen 4 / Zen 5 or an X3D part does the
same work in far less time than a Zen 2. What carries over between machines:

- **Per-frame counts**, set by the game: draws per frame (~2,100 in the market), render passes per
  frame, MME DMA reads and fence releases per frame, banks per frame, images created per frame.
- **Shares**: each zone's share of the back's busy time, and whether the back is saturated
  (busy ≥ ~85 % with the front draining it).
- **Ratios of an A/B on the same machine**: "storage binds −73 %" transfers; "−47 ms/s" does not.

Memory-bound costs (texture uploads, bank copies, cache misses in lookups) gain more from a large L3 and
fast RAM than compute-bound ones, so shares shift a little between machines. VRAM size and the
texture-cache thresholds decide whether the cache thrashes at all. Always name the setup
(`SETUPS.md`).
