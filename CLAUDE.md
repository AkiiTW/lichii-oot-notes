# For Claude sessions working on Lichii and Ocarina of Time

You were pointed here because several people (each with their own Claude) optimize the same emulator
for the same game. This repository is how you learn what the others found and tell them what you found.

## Before you start work

1. Read [`SETUPS.md`](SETUPS.md) and [`COMPARISON.md`](COMPARISON.md): whose numbers come from which
   machine, settings and goal. Add or update your own setup before your first finding.
2. Read [`WORK.md`](WORK.md): who owns which problem right now. Do not start on a problem someone else
   owns without saying so in `WORK.md` first; build on their result instead.
3. Read [`FINDINGS.md`](FINDINGS.md) from the top until you reach entries older than your own last
   visit. Entries marked **ruled out** save you a test; entries marked **to test** are open.
4. Use [`MEASURING.md`](MEASURING.md) so your numbers compare with everyone else's.

## Adding a finding

Add an entry at the **top** of `FINDINGS.md` (newest first), in this exact shape:

```
### YYYY-MM-DD — <short title> — <status>
- **Who:** <person> (+ Claude) · **Setup:** <letter in SETUPS.md> · **Build:** <repo@commit or tag>
- **Goal / settings that matter:** <e.g. 30 FPS mode, 1x, GPU accuracy Low; anything that differs from the setup>
- **Where measured:** <spot and test window, e.g. Castle Town market, 150-270 s after load>
- **Measured:** <the numbers, with units; before → after for an A/B>
- **Conclusion:** <one or two sentences>
- **Code / switch:** <commit, file, function, EDEN_NX2_* switch>
```

Status is one of: **confirmed** (measured, reproducible), **to test** (idea or single run),
**ruled out** (measured, no gain or broke something — say what broke), **superseded** (link the newer
entry).

Rules:

- Say what was measured and what is a guess. Numbers need units and the build they came from.
- One finding per entry. Update an old entry's status in place (add a line `- **Update YYYY-MM-DD:** …`)
  instead of writing a contradicting new one.
- Never paste game files, shader dumps, textures, keys or full logs. Short log excerpts are fine.
- Keep personal data out (names of local folders, emails, hardware serials).

## How to write here

- **Collaborators** (write access): commit straight to `main` with a message like
  `findings: <title>`; keep commits to these Markdown files.
- **Everyone else:** open a pull request with the change, or an issue titled `Finding: <title>` that
  uses the entry shape above; a collaborator copies it into `FINDINGS.md`.
- When you change who works on what, edit `WORK.md` in the same commit.

## Vocabulary used in these notes

- **front / GPU thread** and **back / GPUBack:** Lichii's split GPU thread (`video_core/gpu_split.*`).
  The front parses command lists and runs macros; the back executes methods, sets state and prepares
  every draw. In Ocarina the back is the limit (~90 % busy in the market).
- **drain:** the front waiting until the back has executed everything queued (MME DMA reads, fence
  releases, semaphore acquires).
- **zones:** `EDEN_NX2_GPU_PROFILE=1` logs, every 10 s, milliseconds per second of wall time spent in
  each zone of each GPU thread (`video_core/nx2_profile.h`). Zone times are exclusive.
- **test window:** a fixed stretch after the game is loaded (`EDEN_NX2_TEST_START/SECONDS`), shown on
  screen in AkiiTW's build, so two runs compare the same phase (textures still loading or not).
