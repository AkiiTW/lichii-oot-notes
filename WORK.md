# Who works on what

Edit this table when you start or finish something. One owner per row; others build on it.

| Problem | Owner | State (2026-11-08) | Where |
| --- | --- | --- | --- |
| Front waits for the back (MME DMA reads, ~2,000/s; fence and semaphore releases); the two GPU threads taking turns | Frizti + Claude | In progress: per-page write index, tracked inline uploads, EXP10 (−6 % front waiting), acquire learning (+12.6 %), frames-ahead 2, macro write shortcut (−6 % front work) | Frizti/Lichii |
| Guest CPU waiting on readbacks of GPU-written memory (~120-150 reads/s, 110-200 ms/s waited in Setup A's market) | Frizti + Claude | Preflush gave +3 FPS but overexposed loads / white flashes; zortos #641 has an "async reactive flush" being ported. AkiiTW's branch logs the waits every 10 s (P09) to measure the fix | Frizti/Lichii |
| Cost of each draw on the back (buffer binds, banks, storage buffers) | AkiiTW + Claude, Frizti + Claude | Proposed: `clean_words` (P03), `EDEN_NX2_BANK_COMPARE` (P02). Frizti on buffer binds since 2026-11-07 19:51: take P02/P03 from `v3.5-proposals/` rather than redo them | AkiiTW/Lichii `claude/v3-zen2`, Frizti/Lichii |
| Render-target churn and texture-cache upkeep (Ocarina moves its targets every frame) | AkiiTW + Claude | Done for now: P01 (no upload, early drop), P12 (host image pool, 84 % reuse), P13 (cheaper scan, overlap unlink). Market 48.6 → 35.0 ms/frame from these. Left: ~85 ms/s in small pieces (view create, image free, delete overlaps, create, join). Frizti's 21:45 "texture reuse" = P12 | AkiiTW/Lichii `claude/v3-zen2` |
| Spikes on arriving in a new area (Hyrule Field: 60-760 ms) | AkiiTW + Claude | Next: early test window + `Slow frame` log (P09, 33ded688f) to see what each spike is made of | AkiiTW/Lichii `claude/v3-zen2` |
| Per-bind native uniform bank check (~10 % of the back in Frizti's tree) | **to agree** | AkiiTW's P02 compares a bank's bytes before re-uploading it; Frizti's queue item 13 wants the per-bind check cheaper | — |
| PGO profile retrained on current code | Frizti + Claude | Done: +2.5 FPS (45.0 → 47.5) on his route. AkiiTW's retrain (c733486aa) was neutral within noise | Frizti/Lichii |
| Ports from zortos293/Lichii | Frizti + Claude | In progress (#351 + 3 speed parts of #641, cooperative-matrix HMMA confirmed +6.5 % warm). AkiiTW's branch carries 9 build-116 commits (`v3.5-proposals/COMPATIBILITY.md`) | Frizti/Lichii |
| Frizti V3.5 | Frizti + Claude | AkiiTW waits for it, then rebases the proposals onto it and re-measures the market | Frizti/Lichii |

## Open questions

- Is `clean_words` safe in Kokiri Forest (the wrong-geometry slab of zortos293/Lichii#161)? No defect in
  the market or in a PGO session that walked into Kokiri village, but nobody looked for the slab on purpose.
- How much of the back's saved time turns into frames once the two GPU threads overlap? (Setup A's
  market now sits at the 30 FPS cap with the back ~18 % idle.)
- Which reader is behind the guest readbacks: the auto-exposure / scene-shading analyzer, the
  z-prepass occlusion queries, or something else? A correct preflush (no stale reads) would remove most
  of the wait.
