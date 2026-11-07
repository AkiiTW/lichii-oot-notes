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
| Market baseline | 27-30 FPS after 20 min of play; 21-22 FPS right after load | 33-38, then 34 FPS on his recorded route |
| Half of the bottleneck | **The back's cost per draw** (buffer binds, banks, storage buffers, texture uploads) | **The front's waits for the back** (MME DMA reads, fence/semaphore releases) |
| Measuring | `GPU_PROFILE` zones + new sub-zones, `THREAD_USAGE`, on-screen test window, `TC_LOG` | Status loop, `bulk_ab`, frame-time histogram (1 % / 0.1 % lows), planned fixed-route steering, `replay_route.py` |

## Where the two meet

| Topic | AkiiTW found | Frizti found / plans | What to do |
| --- | --- | --- | --- |
| Front waits | Market: ~520-650 ms/s of the front waiting; 2,010 MME DMA reads/s (216 ms), 1,463 fence releases/s (288 ms); back idle ~90-130 ms/s | ~1,000 waits/s were a check giving up after 512 noted writes → per-page write index; EXP10 bounded dispatch/upload writes (−6 % front waiting); 14-18 ms fence-release drains in the worst frames | Frizti owns it. AkiiTW pulls his commits and re-measures in Setup A |
| Native 64 KiB uniform banks | ~33 ms/s of the back, ~4,000 banks/s, ~180 MB/s re-uploaded; `EDEN_NX2_BANK_COMPARE` skips unchanged banks (A/B pending) | Queue item 13: the per-bind bank check (memchr) costs ~10 % of the back; make it cheaper without bringing back a flicker (EXP4) | **Agree on one owner.** Both trees touch `BindHostGraphicsUniformBuffer` |
| Storage buffer binds | `clean_words` cuts them 64 → 17 ms/s, no visual defect in the market | `clean_words` is off by default in V3 (zortos293/Lichii#161 suspicion) | Frizti's Claude: check `clean_words` in Kokiri Forest on his tree |
| Texture uploads after load | ~1 ms each on the back, 100-160 ms/s for minutes after loading | — | AkiiTW owns it |
| PGO profile | Old profile (Ocarina village, build-88 code) | Retrain on current code with the market route + Hyrule Field | Frizti's profile can replace AkiiTW's once the trees are close |
| Repeatable runs | Fixed test window after load; human player | Fixed route steered from Link's position | AkiiTW adopts the steering when it lands |
| Ports from zortos293/Lichii | — | #465, #408, #463, #418, #411, #415, #232, #395/#337/#353, AMD #448/#437 | AkiiTW takes them through Frizti's tree |
