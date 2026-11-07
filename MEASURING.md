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

## The run

1. Same save, same spot. AkiiTW's runs: Castle Town market, laps around the fountain while turning the
   camera, inside the test window (so every run is at the same time after loading — the first minutes
   after a load are dominated by texture uploads).
2. One change per run. Restart Lichii between runs.
3. Compare **draws per frame** (draws/s ÷ frames/s) before FPS: it tells a game-side change from an
   emulator-side one. Compare zone times per call (ms ÷ calls) to see whether a cost moved.
4. Expect ±5 % noise between runs of the same build (camera, NPCs, loading). Frizti's planned
   fixed-route steering will remove most of it.

## Reading a profile line

`GPU back thread per second: | <zone> <ms> ms (<calls>/s) | … | split wait <ms>` — exclusive time per
zone; `other` is the back's time outside every zone; `split wait` is the back idle, waiting for the
front. The front's line has `split drain` (front waiting for the back) and its causes.

## Scripts

- `tools/cmp_windows.py <log> <log> …` — means of the main back zones, draws/s and frame time inside each
  log's test window (needs the `Nx2TestWindow` lines).
- `tools/profile_windows.py <log>` — one line per 10 s window: draws/s, back and front busy, drains,
  thread CPU, render passes.
