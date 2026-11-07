# Switches added or used by the proposals

`%APPDATA%\eden\nx2_switches.txt` overrides the file next to the exe, which overrides `BuiltinSwitches`.
Read once at start-up.

| Switch | Values | Default in the code | AkiiTW runs | Proposed for V3.5 | Proposal |
| --- | --- | --- | --- | --- | --- |
| `EDEN_NX2_TC_RT_NO_UPLOAD` | 0, 1 (render targets), 2 (+ new depth/stencil images), 3 (+ depth images with join copies) | 0 | 3 | 3 after your visual check | P01 |
| `EDEN_NX2_TC_RT_EVICT` | frames a render target may stay unused before it is dropped without download; 0 = off | 0 | 4 (2 was worse) | 4 | P01, P13 |
| `EDEN_NX2_TC_RT_REUSE` | 0, 1: reuse dropped targets' host images by shape | 0 | 1 | 1 with P01 | P12 |
| `EDEN_NX2_BANK_COMPARE` | 0, 1 | 0 | 1 | 1, or your item-13 design | P02 |
| `EDEN_NX2_PERF_ON=clean_words` | V3 option list | `clean_words` off | on | on after a Kokiri check | P03 |
| `EDEN_NX2_VERTEX_KEY_MERGE` | 0 turns off | on | on | on | P04 |
| `EDEN_NX2_PIPELINE_DIFF` | 1 | off | off | off (diagnostic) | P04 |
| `EDEN_NX2_PREFLUSH` | 1 | (removed from built-ins) | off | off | P05 |
| `EDEN_NX2_PLACEMENT` | off, gpu, split | off | split | split on multi-L3 CPUs, or your scheme | P07 |
| `EDEN_NX2_PLACEMENT_DOMAIN` / `_GPU` / `_CORES` | index / hex mask / 0 | last domain / auto / whole cores | default | — | P07 |
| `EDEN_NX2_PIPELINE_EVICT_FRAMES` | frames, 0 = never | 9000 | 0 (dist) | your RAM-based cap | P08 |
| `EDEN_NX2_PRELOAD_ALL_PIPELINES` | 1 | (V3 switch) | 1 (dist) | your call | P08 |
| `EDEN_NX2_TC_OLD_AGE` | frames, 0 = off | 1800 | 0 (dist) | your call | P08 |
| `EDEN_NX2_TC_EXPECTED_MIB` / `_CRITICAL_MIB` | MiB | budget-based | 9216 / 11264 (dist) | keep; 12288/13824 was worse on 16 GB | — |
| `EDEN_NX2_THREAD_USAGE` | 1 | off | 1 when measuring | off | P09 |
| `EDEN_NX2_GPU_PROFILE` | 1 | off | 1 when measuring | off | P09 (zones) |
| `EDEN_NX2_TC_LOG` | set | off | set when measuring | off | P09 |
| `EDEN_NX2_TEST_START` / `_SECONDS` | seconds after load | off | 150 / 120 | off | P10 |
| `EDEN_NX2_TEST_LABEL` / `_PREPARE` | text | "Tourne autour de la fontaine" / "Va au marché, devant la fontaine" | default | translate if you ship it | P10 |
| `EDEN_NX2_TEST_PURPOSE` | text (UTF-8 is fine) | empty (no line) | one sentence per run | off | P10 |

AkiiTW's `nx2_switches.txt` on 2026-11-08 (Setup A). For play:

```
EDEN_NX2_PERF_ON=clean_words
EDEN_NX2_BANK_COMPARE=1
EDEN_NX2_TC_RT_NO_UPLOAD=3
EDEN_NX2_TC_RT_EVICT=4
EDEN_NX2_TC_RT_REUSE=1
```
For a measured run, add `EDEN_NX2_THREAD_USAGE=1`, `EDEN_NX2_GPU_PROFILE=1`, `EDEN_NX2_TC_LOG=1`,
`EDEN_NX2_TEST_START=150`, `EDEN_NX2_TEST_SECONDS=120`, `EDEN_NX2_TEST_PURPOSE=<sentence>`;
plus the dist file next to the exe: `EDEN_NX2_PREFLUSH=0`, `EDEN_NX2_PLACEMENT=split`,
`EDEN_NX2_PIPELINE_EVICT_FRAMES=0`, `EDEN_NX2_TC_EXPECTED_MIB=9216`, `EDEN_NX2_TC_CRITICAL_MIB=11264`,
`EDEN_NX2_TC_OLD_AGE=0`, `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`.
