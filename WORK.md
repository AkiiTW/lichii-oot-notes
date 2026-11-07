# Who works on what

Edit this table when you start or finish something. One owner per row; others build on it.

| Problem | Owner | State (2026-11-07) | Where |
| --- | --- | --- | --- |
| Front waits for the back (MME DMA reads, ~2,000/s; fence and semaphore releases) | Frizti + Claude | In progress: per-page write index, tracked inline uploads, bounded dispatch/upload writes (EXP10, −6 % front waiting); next: bounded semaphore/query releases, 14-18 ms fence-release drains | Frizti/Lichii |
| Cost of each draw on the back (buffer binds, banks, storage buffers) | AkiiTW + Claude | In progress: `clean_words` kept (storage binds 64 → 17 ms/s); `EDEN_NX2_BANK_COMPARE` kept (95 % of bank bytes unchanged, ubo bank 33 → 22 ms/s) | AkiiTW/Lichii `claude/v3-zen2` |
| Texture cache thrash in the market (collector evicts ~250 images/s at the 11,264 MiB critical threshold, re-uploads ~400 MB/s) | AkiiTW + Claude | Cause found: render targets recreated in reused memory and filled from guest memory (6.6 GB of depth uploads per 600 frames). `EDEN_NX2_TC_RT_NO_UPLOAD=2` kept: market mean frame 48.6 → 40.4 ms, frames >100 ms 42 → ~5. Done: `RT_EVICT=4` + `RT_NO_UPLOAD=3` (texture upload 131 → 1 ms/s, market 48.6 → 38.5 ms/frame, >100 ms frames 42 → 1). Tried and ruled out: `EDEN_NX2_TC_RT_REUSE` (pool of dropped targets' VkImages, ~35 % reused, no frame gain, +1 GiB VRAM). Texture-cache work done for now | AkiiTW/Lichii `claude/v3-zen2` |
| Per-bind native uniform bank check (~10 % of the back in Frizti's tree) | **to agree** | Both sides touch it: AkiiTW's `EDEN_NX2_BANK_COMPARE` compares a bank's bytes before re-uploading it; Frizti's queue item 13 wants the per-bind check cheaper | — |
| PGO profile retrained on current code (market + Hyrule Field) | Frizti + Claude | Planned | Frizti/Lichii |
| Repeatable test route (Link steered around the fountain, fixed camera) | Frizti + Claude | Planned | Frizti/Lichii |
| Ports from zortos293/Lichii (#465, #408, #463, #418, #411, #415, #232, #395/#337/#353, AMD #448/#437) | Frizti + Claude | In progress on `port/zortos-nov7` | Frizti/Lichii |

## Open questions

- Why does each texture upload cost ~1 ms on the back right after loading? (ASTC is decoded and BC3
  re-encoded on the GPU in these builds, so the CPU part is staging/copies or something else.)
- Is `clean_words` safe in Kokiri Forest (the wrong-geometry slab of zortos293/Lichii#161)? Market looked
  clean.
- How much of the back's saved time turns into frames once the front stops draining it so often?
