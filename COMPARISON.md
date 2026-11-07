# AkiiTW's work and Frizti's work, side by side

Two Claude sessions work on the same emulator, for the same game, toward different goals and on
different halves of the same bottleneck. This page says where they meet, so each side reuses the
other's results instead of redoing them. Last updated 2026-11-07 by AkiiTW's Claude; Frizti's column
comes from his status screens and should be corrected by his Claude.

| | AkiiTW (+ Claude) | Frizti (+ Claude) |
| --- | --- | --- |
| Goal | Stable 30 FPS (30 FPS mode on), maximum headroom under it | 50-60 FPS in Castle Town |
| Machine | Ryzen 7 3800X (Zen 2) + RTX 5060 Ti 16 GB — see `SETUPS.md` A | *to fill in* — `SETUPS.md` B |
| Build line | Frizti V3 + changes, branch `claude/v3-zen2` | Frizti/Lichii (newer than V3), branches incl. `port/zortos-nov7` |
| Market baseline | 27-30 FPS after 20 min of play; 21-22 FPS right after load | 33-38, then 34 FPS on his first recorded route; **44.6 FPS on a new recorded route** (15:58) — routes differ, compare within a route only |
| Next on the back |  Texture churn, then the remaining per-draw zones | Measuring how busy the back is (15:58) — AkiiTW's numbers: back 870-910 ms/s busy in the market |
| Half of the bottleneck | **The back's cost per draw** (buffer binds, banks, storage buffers, texture uploads) | **The front's waits for the back** (MME DMA reads, fence/semaphore releases) |
| Measuring | `GPU_PROFILE` zones + new sub-zones, `THREAD_USAGE`, on-screen test window, `TC_LOG` | Status loop, `bulk_ab`, frame-time histogram (1 % / 0.1 % lows), planned fixed-route steering, `replay_route.py` |

## Where the two meet

| Topic | AkiiTW found | Frizti found / plans | What to do |
| --- | --- | --- | --- |
| Front waits | Market: ~520-650 ms/s of the front waiting; 2,010 MME DMA reads/s (216 ms), 1,463 fence releases/s (288 ms); back idle ~90-130 ms/s | ~1,000 waits/s were a check giving up after 512 noted writes → per-page write index; EXP10 bounded dispatch/upload writes (−6 % front waiting); 14-18 ms fence-release drains in the worst frames | Frizti owns it. AkiiTW pulls his commits and re-measures in Setup A |
| Native 64 KiB uniform banks | ~33 ms/s of the back, ~4,000 banks/s, ~180 MB/s re-uploaded; `EDEN_NX2_BANK_COMPARE` skips unchanged banks: 95 % of the bytes were unchanged, zone 33 → 22 ms/s (kept) | Queue item 13: the per-bind bank check (memchr) costs ~10 % of the back; make it cheaper without bringing back a flicker (EXP4) | **Agree on one owner.** Both trees touch `BindHostGraphicsUniformBuffer` |
| Storage buffer binds | `clean_words` cuts them 64 → 17 ms/s, no visual defect in the market | `clean_words` is off by default in V3 (zortos293/Lichii#161 suspicion) | Frizti's Claude: check `clean_words` in Kokiri Forest on his tree |
| Texture cache churn | ~200 images created/s in the market, collector evicts ~250/s at the critical threshold, ~400 MB/s re-uploaded (100-160 ms/s of the back); larger thresholds made it worse (VRAM full) | Testing 2D blits noted by their destination (15:58) — blits create and write images too | AkiiTW owns the churn; tell each other if blits turn out to be part of it |
| PGO profile | Old profile (Ocarina village, build-88 code) | Retrain on current code with the market route + Hyrule Field | Frizti's profile can replace AkiiTW's once the trees are close |
| Repeatable runs | Fixed test window after load; human player | Fixed route steered from Link's position | AkiiTW adopts the steering when it lands |
| Ports from zortos293/Lichii | — | #465, #408, #463, #418, #411, #415, #232, #395/#337/#353, AMD #448/#437 | AkiiTW takes them through Frizti's tree |

## Frizti's status screens, as relayed by AkiiTW (newest first)

Frizti's Claude can replace this log with its own entries in `FINDINGS.md`.

| Time (2026-11-07) | Status |
| --- | --- |
| 20:03 | **Test run (build 9b8b6fdd87, route castletown_market3, fresh launches): `PERF_ON=none` 42.8 FPS (2 runs) vs `PERF_ON=clean_words` 42.4 FPS (1 run)**, launch 3 of 4 in progress. — *Consistent with Setup A: `clean_words` cut the `storage binds` zone (64 → 17 ms/s) but the mean frame did not move there either (draws/s +3 %, within noise). The zone time saved on the back only becomes frames where the back is the sole limit; with the front and back taking turns, it mostly turns into more `split wait`. Worth re-running once the overlap work is in.* |
| 19:51 | **Kept: macro write shortcut (front thread, ~6 % less work).** Now: the back thread (buffer binds). Testing: CleanWords (verify launch, then on/off). — *Same ground as AkiiTW's row in `WORK.md`: on Setup A `clean_words` is on since 15:13 (`storage binds` 64 → 17 ms/s, +3 % draws/s, no defect in the market; Kokiri not checked yet; it was also on during the PGO recording of ca4f7d0, market + field + Kokiri, no defect reported). Also see `EDEN_NX2_BANK_COMPARE` (P02) for the bank part of buffer binds.* |
| 19:11 | **Performance of the GPU front thread's own work** (not its waits). Testing 2 fixes in one session: macro writes, channel polls. — *On Setup A the front is ~95 % busy, with macro ~178 ms/s and resume pending ~188 ms/s (`FINDINGS.md`, "The back is the limit…"); the back stays the limit here, so front-only gains should show mostly once the overlap work lands.* |
| 18:20 | **Every stage (game CPU, GPU front, GPU back) is only 53-70 % busy: they wait on each other frame by frame.** Testing: frames-ahead 2 (the next frame prepared early). — *On Setup A in 30 FPS mode the back is busier (~85-91 %, the limit), so the gain should be smaller but real at the market's 21-27 FPS dips; costs one frame of input latency. AkiiTW will A/B it once published.* |
| 17:15 | Castle Town **45.5 → 51.3 FPS (+12.6 %) with "acquire learning"**: lets the 2 GPU threads overlap at the game's waits. Checking now: flicker (flash watcher) and wrong guesses. — *First result of the overlap work; AkiiTW will take it into Setup A once published.* |
| 16:42 | 45 FPS on his route (goal 60). **The big one: the 2 GPU threads take turns instead of overlapping; up to +25-28 % if they overlap.** Next: find what each of the game's ~2,300 waits/s waits for. — *Matches Setup A: the front waits 520-650 ms/s while the back idles 90-130 ms/s (`split wait`), i.e. drains serialize them; AkiiTW's estimate was up to ~+15 % on a Zen 2 where the back is busier.* |
| 15:58 | New Castle Town route recorded, **44.6 FPS baseline**. Testing: 2D blits noted by their destination (A/B, 8 rounds). Next: how busy the back GPU thread is. Saves restored after every test. — *AkiiTW's data on the back in the market: `FINDINGS.md`, entries "The back is the limit…" and "Where bind stage buffers goes".* |
| 15:18 | Work queue (LOOP_STATUS.md): EXP10 bounded dispatch/upload writes (−6 % front waiting); next semaphore/query releases, 14-18 ms fence-release drains, ~410 noted-write reads/s; fixed-route steering, `replay_route.py`, 1 % / 0.1 % lows, PGO retrain; zortos ports; item 13 = per-bind bank check ~10 % of the back. |
| 14:53 | 34 FPS. ~1,000 GPU-thread waits/s were a check giving up after 512 noted writes; testing a per-page write index + tracked inline uploads. |
| 14:49 | 33-38 FPS. Why the front waits ~2,000×/s; testing a byte-exact overlap check. |
