# Net connectivity review — v0.3.1

## Decision under review

`design/PCB_CAD_ASSUMPTIONS.md` item 4 documents that DRIVE+/SENSE+ share
one KiCad net (`DRIVE_SENSE_PLUS`) and DRIVE-/SENSE- share another
(`DRIVE_SENSE_MINUS`), instead of 4 distinct nets tied together with
KiCad's "net tie" footprint feature. That decision was made before KiCad
was available in this environment, as a syntax-risk-averse choice.

**This review's job**: now that real KiCad is available, confirm whether
that representation is electrically valid, and per the task brief, *keep
it if so* rather than introducing a net-tie "merely for conceptual
elegance."

## What real KiCad DRC found

Running the merged-net representation through actual `kicad-cli pcb drc`
surfaced a real bug unrelated to the net-merging choice itself: the
original routing code used the wrong rotation-sign convention for 90-degree
footprints, so the `+`/`-` labeled traces landed on the wrong physical
pads. This produced genuine `shorting_items` and `unconnected_items`
errors. That bug has been fixed (see `pcb/generate_pcb.py`,
`mlcc_pad_positions()`, and `design/PCB_CAD_ASSUMPTIONS.md` item on
rotation) and is a separate, now-resolved issue from the net-model question
below.

With that routing bug fixed, DRC on all 5 boards, `--severity-all`:

| variant | errors | warnings | unconnected | shorting_items |
|---|---|---|---|---|
| S90-0402 | 0 | 5 (lib_footprint_mismatch) | 0 | 0 |
| S90-0603 | 0 | 5 (lib_footprint_mismatch) | 0 | 0 |
| S90-0805 | 0 | 5 (lib_footprint_mismatch) | 0 | 0 |
| W90-0603 | 0 | 5 (lib_footprint_mismatch) | 0 | 0 |
| S0-0603  | 0 | 5 (lib_footprint_mismatch) | 0 | 0 |

**Zero `shorting_items` violations on any board.** This is the direct test
of whether the merged-net representation is electrically sound in KiCad's
own model: if DRIVE+ and SENSE+ being the same net were somehow still
producing an unwanted connection to something else, or if the DRIVE+/
DRIVE- (opposite terminal) nets were touching anywhere they shouldn't,
DRC's shorting-item and clearance checks would have caught it — the same
class of check that caught the real routing bug above. It didn't, on any
of the 5 boards, across both routing geometries in this design (the direct
3-segment route used for `+`-group traces, the overshoot detour used for
`-`-group traces on 90-degree boards, and the pad-1-bypass detour used on
the 0-degree board).

## Conclusion

**Keep the existing representation.** DRIVE+/SENSE+ sharing
`DRIVE_SENSE_PLUS`, and DRIVE-/SENSE- sharing `DRIVE_SENSE_MINUS`, is
electrically valid in KiCad — confirmed by DRC, not merely asserted by
the earlier written rationale. No net-tie footprint was introduced.

## Final net structure

| KiCad net | member pads | physical meaning |
|---|---|---|
| `DRIVE_SENSE_PLUS` (net 1) | edge pad `DRIVE+`, edge pad `SENSE+`, MLCC pad "1" (+ terminal) | the MLCC's + terminal and both of its external takeoff points (current-carrying drive path and low-current sense path) |
| `DRIVE_SENSE_MINUS` (net 2) | edge pad `DRIVE-`, edge pad `SENSE-`, MLCC pad "2" (- terminal) | the MLCC's - terminal and both of its external takeoff points |

This is a 2-net board. The 4-wire/Kelvin *function* (drive current and
sense current using physically separate copper paths, so DRIVE's trace
resistance doesn't corrupt what SENSE reads) is implemented at the
**routing level** — 4 physically distinct, non-touching traces, each
individually reaching the MLCC pad — not at the netlist level. The netlist
correctly reflects that DRIVE+ and SENSE+ are the same electrical node.

## What would change if a human later wants true 4-net modeling

Nothing about the copper geometry would need to change — only the net
declarations and a `net_tie_pad_groups` attribute on the MLCC footprint
would need to be added, splitting `DRIVE_SENSE_PLUS` into `DRIVE+` and
`SENSE+` (and similarly for the minus side) while marking them as an
intentionally-tied group at the MLCC pad. This is recorded as a possible
future refinement, not a defect in the current design.
