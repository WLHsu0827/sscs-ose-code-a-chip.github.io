# Nominal published 27-device layout experiment

Author: **Wei-Lun Hsu, National Tsing Hua University**.

This is a separate, bounded layout and extraction experiment for the exact
`lvt_balanced_4b` circuit published at
`2ad1c4c2058060abdfdd42c35aa784c018f6fa67`, with `pair_skew=0`.
It is not the unqualified 35-device coarse/fine candidate and does not update
PR195 or its submission branch.

`protocol.json` freezes the source hash, all 15 ordered ports, nominal device
table, pinned tools/models, structural controls, extraction modes, common
stimulus, measurement contract, and monotone numerical acceptance criteria
before remote execution. `devices.json` is independently checked against that
immutable source, not populated from a layout extraction.

The four preflight attempts are exhausted. The final preflight passed 54/54
checks; its evidence and all earlier failures remain in `../layout_preflight`.
This new phase has a separate maximum of four scoped Linux jobs of at most
30 minutes, only on `verify/comparator-atlas-layout-nominal27` in the authorized
user fork. No layout or simulation is qualified merely by this protocol.

The initial layout is deliberately simple: mirrored PCell pairs, a central
tail device, real guard/body contacts, individual M2 pin escapes and M3 buses.
The placer transforms the exact native polygons produced by the pinned
open_pdks generators. It does not substitute drawn transistor placeholders.
The connected short-channel M1 gate landing repair is retained. Actual
geometric area and paired routing differences must be reported; neither
common-centroid matching nor foundry signoff is claimed.

The routed gate-area audit measures the connected polygon union including
the pinned technology's genuine M1 residues: `metal1`, `viali`, and `via1`.
Magic replaces overlapping M1 tiles with contact tiles; omitting `via1`
understates the physical landing. M2/M3 geometry, disconnected islands, and
bounding-box gaps do not count toward the unchanged 0.10 square-micrometre minimum.

Schematic, connectivity-only, capacitance-only and actual distributed-RC
netlists use identical external 5 fF loads and published measurements.
Actual simulator device dimensions must confirm geometry scaling exactly
once. All failures and finest-step contrary evidence remain visible. An
unambiguous RC pilot failure ends expansion with a root-cause report, not
geometry or stimulus retuning to make a result green.

## Authorized physical routing revision

Attempts 1 and 2 used identical physical polygons. Attempt 1's gate-area
reporter missed the real M1 residue of `via1`; attempt 2 passed all 14
structural checks with that reader corrected, but its code-zero TT C-only
and RC simulations failed for positive inputs. The original layout,
protocol, raw traces, and contrary outcomes remain retained. In that baseline,
qn has 1.28575 fF more listed coupling to VSS, VDD and the ideal input sources
than qp, while the device dimensions, junction geometry, body connections,
and actual simulator scaling agree.

The subsequent explicit decision authorizes only the two remaining
comparator jobs for separately frozen physical revisions, not electrical
retuning or relaxed qualification. `balanced-shielded-r1` preserves all
27 generated devices and their placements. Disjoint mirrored buses share
the same M3 height. The two output buses have equal full spans, real attached
M2 balancing stubs, and three M3 ground shields joined to VSS by two M4
spines and eight genuine `via3` contacts. These are layout polygons, not
inserted ideal capacitors. The stubs match metal extent, not series
resistance; the two output tracks and common tail escape retain explicitly
reported residual asymmetry. No post-layout trim calibration is enabled.

`analyze.py` checks full native LVS/C MOS-card equality including junction
parameters, all three exported device/port/bulk contracts, retained FLOATING
annotations, actual C matrices, and real resistor paths. Its path sums are
not parallel-network equivalent resistances. It measures saved-MAG metal
union areas with genuine contact residues and the actual GDS bounding box.
Fresh four-mode simulation reports the corresponding core-energy cost.
The original TT, pilot, 45-PVT, and monotone numerical gates remain identical;
a clear failure still ends expansion **within each frozen revision**.

## Reproduction and evidence

`run.sh` uses a fresh private work directory and reuses only the frozen preflight
toolchain builder, not the exhausted preflight test job. It runs `layout.py`
and the native parasitic analysis before fetching the three exact model flavors
with `setup_models.py`. Simulation
dependencies live in a job-private virtual environment. No system installation
is performed on the shared Windows host.

`simulate.py` preserves each native netlist, uses one `scale=1u`, and queries all
27 actual inner ngspice MOS W/L values in metres. It calls the unchanged
published measurement functions. Four-mode TT and worst-RC numerical audits
retain the finest pending evidence; any failed sweep condition also receives
the bounded refinement sequence before it can be classified. The five-condition
pilot precedes conditional expansion to 45 PVT conditions. The process records
an explicit failure rather than hiding a measurement error or running beyond
the bounded job budget.

`ci.yml` is an inert project-local template. Only its copy on the separate
experimental branch belongs under `.github/workflows`; inherited-workflow
exclusions are also limited to that branch. The job has a 30-minute ceiling,
a 24-minute execution timeout, and an always-upload artifact step.
`execution.json` and `manifest.sha256` preserve the last stage, exit status,
exact commit/run, and every emitted evidence file. Native MAG/GDS/EXT/resistance
extraction, independent references, raw logs, actual geometry audits, simulation
decks, waveforms, all measurements, and contrary refinements remain inspectable.

The offline controls run with:

```sh
python3 -m unittest discover -s layout_nominal27 -p test_nominal27.py -v
```

Those controls do not qualify the physical layout or execute Magic, Netgen,
or ngspice.
