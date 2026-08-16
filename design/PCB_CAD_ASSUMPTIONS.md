# PCB CAD assumptions — v0.3.1

This lists every fabrication parameter that v0.3.0 (`design/PCB_FABRICATION_SPEC.md`,
`design/pcb_variants.csv`, `design/pcb_coordinates.csv`) left unspecified,
and the assumption `pcb/generate_pcb.py` used to fill it in, per the task
instruction: *"do not silently treat a new assumption as an existing v0.3.0
decision."* Each item below is tagged **[v0.3.0, existing]** if it was
already fixed by earlier design docs, or **[v0.3.1, new assumption]** if
this stage introduced it.

No inconsistency was found between the task brief's stated common
specification / MLCC placement table and `pcb_variants.csv` /
`pcb_coordinates.csv` — they match exactly, so nothing was silently
changed.

## Environment constraint (read first)

**KiCad is not installed in this environment** (checked: no `kicad-cli` on
PATH, no `pcbnew` Python module, no `/Applications/KiCad*`, not found via
`brew`). This affects every assumption below: none of these `.kicad_pcb`
files have been opened, parsed, or DRC'd by real KiCad. See
`pcb/FABRICATION_REVIEW.md` for exactly what was and wasn't possible to
verify as a result.

## 1. Edge interface pad **center coordinates** — existing, reused

**[v0.3.0, existing]**. `PCB_FABRICATION_SPEC.md` section 5 already gives a
"suggested reference pad row" at x=5mm, y = 12.5 / 17.5 / 22.5 / 27.5 mm for
DRIVE+ / SENSE+ / SENSE- / DRIVE- respectively (marked "to be confirmed in
EDA, not final" — but it is a value, not a gap). This implementation treats
those coordinates as the thing to implement, per the task's own instruction
that its preferred default applies only *"if no value is already
specified."* The generator's `EDGE_PAD_X` / `EDGE_PADS` constants match this
table exactly.

## 2. Edge interface pad **shape and diameter** — new assumption

**[v0.3.1, new assumption]**. v0.3.0-C fixed the pad *centers* but never a
shape or size. This was genuinely open, so the task's stated preferred
default was used: **round, 2.5 mm diameter**, exposed copper (ENIG) with no
solder-mask covering, no paste layer (hand-soldered wire lead, not a
reflow part). Implemented as `EdgeContact_2.5mm_Round` in
`pcb/SC4.pretty/`.

## 3. Exact trace routing geometry — new assumption

**[v0.3.1, new assumption]**. v0.3.0-C fixed trace *widths* (0.5 mm drive,
0.2 mm sense) and the *topological* rule (SENSE traces must originate
directly at the MLCC pad copper, not tap the DRIVE trace) but never a
routed path. This implementation uses the simplest routing that satisfies
that rule without producing an unintended short:

- Each of the 4 nets gets its own dedicated staging x-lane (`mlcc_x - 8`
  through `mlcc_x - 5`, one per net) so no two different-net segments ever
  run parallel/collinear.
- For 90 deg boards (S90-*, W90-0603), each trace is a simple 3-segment
  L-route: edge pad -> its staging lane -> the target MLCC pad's row ->
  straight into the pad. No detour is needed because the two MLCC pads
  differ only in y, and each net's staging lane already sits at a distinct
  y before converging.
- For the 0 deg board (S0-0603), the two MLCC pads differ only in x, so a
  trace headed for the farther pad would otherwise have to cross straight
  through the nearer pad's copper. Only for this case, the SENSE-/DRIVE-
  pair detours above the nearer pad (`mlcc_y + pad_height/2 + 0.3 mm`
  clearance) before dropping onto the far pad. This is the "extra
  complexity only where necessary" the task asked for — the 90 deg boards
  do not need it.
- `pcb/validate_pcb.py` checks geometrically that no two different-net
  F.Cu segments touch or cross anywhere except at their one legitimate
  shared point (the MLCC pad itself).

## 4. DRIVE+/SENSE+ and DRIVE-/SENSE- net topology — new assumption, explicit trade-off

**[v0.3.1, new assumption]**. This is the most consequential CAD decision
in this package, so it's called out on its own.

A 4-wire/Kelvin connection means DRIVE+ and SENSE+ are, by design,
electrically the *same node* — they are both wired straight to the MLCC's
+ terminal with nothing in between; that's what makes it "4-wire" (the
DRIVE path carries current, the SENSE path carries ~none, so IR drop in the
DRIVE trace doesn't corrupt what SENSE reads). A PCB tool's "net" is
defined as a connectivity group, so representing DRIVE+ and SENSE+ as two
different net objects that are also physically joined at the MLCC pad is,
strictly, the same thing electrically — the question is only how to encode
it in KiCad's file format.

KiCad has a purpose-built feature for exactly this ("net ties": a
footprint attribute, `net_tie_pad_groups`, that lets two named nets touch
at one defined point without DRC treating it as a short elsewhere). That
would let this design keep 4 distinctly-named nets. **It was not used
here**, because its exact file-format syntax could not be verified without
a working KiCad installation, and getting it wrong risks producing a file
that fails to parse in KiCad at all — a worse outcome than a
syntactically-safe simplification.

Instead: **DRIVE+ and SENSE+ share one KiCad net (`DRIVE_SENSE_PLUS`), and
DRIVE- and SENSE- share one KiCad net (`DRIVE_SENSE_MINUS`)**. This is
electrically identical to the intended Kelvin topology. The 4 external
pads remain individually and correctly labeled (`DRIVE+`, `SENSE+`,
`SENSE-`, `DRIVE-` as each edge-contact footprint's reference designator)
and are routed as 4 physically separate, non-touching copper traces (see
item 3) — only the *net name* is merged, not the copper layout.

**Consequence for the validation requirement** "all four interface nets
reach the intended MLCC terminal": this is verified as *connectivity*
(each of the 4 labeled pads reaches the correct terminal's copper), not as
4 distinct KiCad net objects — there are 2. If true 4-distinct-net
modeling via KiCad net ties is wanted, that is a follow-up task for someone
with a working KiCad installation to implement and verify; it would not
change any board geometry, only the netlist representation.

## 5. Which MLCC pad is the "+" terminal — new assumption

**[v0.3.1, new assumption]**. The MLCC is a non-polarized ceramic capacitor
— "+"/"-" is a labeling convention for this design, not a real polarity.
Convention used: for 90 deg boards, the pad at the *smaller* y (closer to
the DRIVE+/SENSE+ side of the edge row) is "+"; for the 0 deg board, the
pad at the *smaller* x (nearer the edge, i.e. pad1 in `pcb_coordinates.csv`)
is "+". This keeps routing short and simple; it has no effect on the
experiment (the model treats the MLCC as an unpolarized source).

## 6. MLCC footprint pad size / pitch — existing, reused

**[v0.3.0, existing]**. Taken directly from `PCB_FABRICATION_SPEC.md`
section 4's nominal IPC-7351 table (0402: 0.6x0.6mm pads / 1.0mm pitch;
0603: 0.9x1.0mm / 1.6mm; 0805: 1.2x1.45mm / 1.9mm) and
`pcb_coordinates.csv`'s computed pad centers. Not re-derived here.

## 7. Silkscreen content and placement — new assumption, deliberately conservative

**[v0.3.1, new assumption]**. `PCB_FABRICATION_SPEC.md` section 7 permits
*only* "board/variant identification silkscreen (e.g. 'S90-0603', a rev
letter)" in the edge strip, and forbids non-essential silkscreen in the
active region entirely. This implementation:

- Prints only the variant name (e.g. `S90-0603`) as silkscreen text, at a
  single position (x=5, y=31mm) chosen to clear both the edge-pad column
  (which ends at y=27.5+1.25=28.75mm) and the top mounting hole's keepout
  (which starts at y=35-1.6=33.4mm) — this position is identical across
  all 5 variants since the edge row geometry doesn't vary by variant.
- Does **not** silkscreen individual pad-function labels (DRIVE+, SENSE+,
  etc.) next to each pad, even though there was room — the spec only
  explicitly allows variant/rev identification, and adding more was judged
  to be overstepping v0.3.0-C rather than implementing it.
- Hides the reference/value silkscreen KiCad normally auto-generates for
  every footprint (MLCC and all 4 mounting holes), since two of the four
  mounting holes (at x=95mm) and the MLCC itself sit in the active region
  (x>15mm) where that silkscreen would be disallowed.

## 8. Board stackup / manufacturing defaults not otherwise specified

**[v0.3.1, new assumption]**, using generic, non-consequential defaults
since v0.3.0 explicitly left these to "manufacturer default" /
open-at-order-time (`jlcpcb_order_settings.csv`):

- Solder-mask-to-copper clearance: 0.05 mm (generic default).
- 2-layer stackup with F.Cu/B.Cu both defined (required by the file
  format) but zero copper features ever placed on B.Cu.

## 9. Coordinate system note (not an assumption about the design, a KiCad-mechanics note)

The design docs use origin = bottom-left, x/y both increasing "up/right".
KiCad's own on-screen Y axis increases downward by default. This
implementation stores every coordinate's numeric value exactly as given in
`pcb_coordinates.csv` / the task brief as KiCad's literal (x, y) — it does
not attempt to flip anything to "look" correct on screen. This has no
effect on manufactured geometry (hole spacing, MLCC-to-hole relationships,
and silkscreen orientation are all self-consistent within the file), but
means a human opening these files in KiCad should confirm orientation by
reading the printed variant-ID silkscreen text and cross-checking numeric
coordinates (KiCad's Properties panel), not by assuming screen "up" means
larger y.

## Summary table

| item | status |
|---|---|
| Board outline, thickness, layer count, copper weight, finish | v0.3.0, existing |
| Mounting hole coordinates and diameter | v0.3.0, existing |
| MLCC center coordinates and orientation, per variant | v0.3.0, existing |
| MLCC footprint pad size/pitch, per package | v0.3.0, existing |
| Edge interface pad center coordinates | v0.3.0, existing |
| Drive/sense trace widths | v0.3.0, existing |
| Edge interface pad shape/diameter | v0.3.1, new (task default: round 2.5mm) |
| Exact trace routing path | v0.3.1, new |
| DRIVE+/SENSE+ and DRIVE-/SENSE- net topology (merged vs. net-tie) | v0.3.1, new, explicit trade-off |
| "+"/"-" terminal labeling convention | v0.3.1, new (arbitrary, no experimental effect) |
| Silkscreen content/placement | v0.3.1, new, deliberately minimal |
| Solder mask clearance and other fab-default values | v0.3.1, new, non-consequential |
