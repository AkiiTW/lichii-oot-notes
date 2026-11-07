# Lichii × Ocarina of Time — shared notes

Findings about running *The Legend of Zelda: Ocarina of Time* (Switch 2, `0400486024DEC000`) well on
[Lichii](https://github.com/zortos293/Lichii) and its forks, written by the people working on it and by
their Claude sessions, so nobody measures the same thing twice.

**Français :** carnet partagé des trouvailles sur les performances d'Ocarina of Time dans Lichii.
Chaque dev (et son Claude) y note ce qu'il a mesuré, ce qui marche, ce qui ne marche pas, et sur quoi il
travaille. Les Claude écrivent en anglais pour coller au code ; posez vos questions en français si vous
voulez.

| File | What it holds |
| --- | --- |
| [`CLAUDE.md`](CLAUDE.md) | How a Claude session reads and adds to these notes (read it first) |
| [`WORK.md`](WORK.md) | Who works on what right now, and the open questions |
| [`SETUPS.md`](SETUPS.md) | Each contributor's machine, emulator settings, switches and goal — numbers only compare within a setup |
| [`COMPARISON.md`](COMPARISON.md) | AkiiTW's and Frizti's work side by side: goals, baselines, where they meet |
| [`FINDINGS.md`](FINDINGS.md) | Dated findings, newest first, each with numbers, build and status |
| [`MEASURING.md`](MEASURING.md) | How the numbers are taken: switches, test window, log lines, scripts |
| [`tools/`](tools) | Small scripts that read Lichii logs |
| [`v3.5-proposals/`](v3.5-proposals) | **For Frizti:** everything AkiiTW's branch proposes for V3.5 — proposals, measurements, patches, compatibility notes, a Status column to fill |

**Where things stand (2026-11-08):** Setup A (Ryzen 7 3800X + RTX 5060 Ti, 30 FPS goal) went from
48.6 to 33.6 ms per frame in the Castle Town market (at the 30 FPS cap, 0 frames over 100 ms) with the
changes in [`v3.5-proposals/`](v3.5-proposals) and 9 zortos build-116 commits; the biggest single
causes were render targets recreated every frame (P01, P12) and the guest CPU waiting on GPU readbacks
(still open). Details: `FINDINGS.md`, newest first.

Nothing from the game itself goes here: no game files, dumps, textures or shaders. Only measurements,
conclusions and code references.

Contributors so far: AkiiTW (+ Claude, branch
[`claude/v3-zen2`](https://github.com/AkiiTW/Lichii/tree/claude/v3-zen2)), Frizti (+ Claude,
[Frizti/Lichii](https://github.com/Frizti/Lichii)).
