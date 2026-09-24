# Separate compact-layout repair

Author: **Wei-Lun Hsu, National Tsing Hua University**.

This is a new, explicitly bounded engineering-qualification phase for the
Code-a-Chip entry, not a new circuit, routing algorithm, publication claim,
or retroactive change to an earlier result. The completed four-job preflight
and four-job nominal27 ledgers remain frozen at local commit
`2268e09bccc023177ac488a785244bc19c540c10`.

The target is the actual `compact-shielded-r2` geometry from nominal27 job 4,
experimental commit `561477fe230dff5642fa9c292051c98e04c57856` and
[run 35829241108](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/actions/runs/35829241108).
That layout passed full device/port/LVS and passive-connectivity checks but
failed DRC with 48 `met2.2` regions, so its simulation was **not run**.
The best prior legal layout remains balanced-r1: TT code-zero C/RC decisions
pass, but 14/80 five-condition pilot rows miss the fixed 1 ns requirement.

## Exact repair, not a waiver

The four PFET VDD body transitions `Xrxp.B`, `Xrxn.B`, `Xrqp.B`, and `Xrqn.B`
have 0.26/0.28 um native M2 via pads joined by 0.20 um necks. Their side
notches have a 0.075 um facing-edge gap, below the 0.14 um spacing rule.
The repair paints four continuous **0.36 um-wide M2 rectangles**, each
covering y = -1.800 through -0.955 um at x = -21.2, 21.2, -26, and 26 um.
They fully cover both pads, with at least 0.04 um lateral overhang beyond
the widest pad and 0.01 um vertical coverage beyond the native pad extent.

`protocol.json` fixes the four rectangles on the native 0.005 um grid before
execution. Their exact predicted net material addition is **0.3568 um2**
total; M2 union area becomes 80.3847 um2 and the bounding-box area remains
2207.088 um2. These are geometric calculations, **not assumed parasitic,
speed or energy gains**.

`repair.py` composes the frozen nominal27 PCell, routing, Magic, Netgen and
extraction helpers without editing them or changing their globals. It
regenerates the same real PCells and compact routing, verifies their
placement/pins, and appends only the four M2 paint operations. After actual
Magic execution it checks that saved M2 material equals the old material
union plus exactly those rectangles. All other native layer unions,
contacts, labels and the GDS bounding box must remain unchanged.
The failed MAG also contains 16 `error_p` DRC-feedback rectangles. Their
before/after counts are reported separately from physical mask material;
no erase command removes them, and only full actual DRC may establish that
the violations cleared.
Full named-style DRC, the deliberate spacing negative, independent-reference
LVS and wrong-net/bulk/width/SVT-for-LVT negatives still run.
All 27 devices, full model flavors, W/L/m, body ties and 15 ordered ports
must match. No error polygon, device, body tie, resistor or capacitor is
deleted; no ideal balancing component is inserted.

## Frozen measurements and separate budget

The original non-layout fingerprint remains
`386bc16f5c55c467d0c7d72ec93d553907f8a2f290aa054b2cd50e0cfcf05454`.
Its historical four-job budget is preserved as data, **not reused as new
authorization**. This repair has at most **two new jobs of 30 minutes**,
only on `verify/comparator-atlas-layout-repair-compact` in the authorized
fork. Failed jobs and reruns count. A second job is allowed only for a
concrete integrity/DRC/execution defect, not arbitrary performance retuning.
PR195, both main branches and both older experimental branches are untouched.

The fresh schematic/LVS/C/RC comparison uses the exact published 27-device
`lvt_balanced_4b`, `pair_skew=0`, code zero, 5 fF external loads, 10 ns clock,
50 ps edges, 0.5 VDD common mode, 80%/20% rails and 1 ns primary deadline.
`compare.py` reuses the original simulator, point/deck generators, published
measurements and monotone pending-trace numerical contract. Every scored
condition is audited from 10 to 5 ps, with the same sensitive finer halvings,
1% energy tolerance, 20 ps latency tolerance and identical decisions.
Added numerical coverage does not alter stimuli or acceptance thresholds.
No prior finer contrary evidence can be replaced by a coarse restart.

All 17 structural checks must pass before models or simulation run.
TT +/-3 and +/-10 mV precedes the unchanged five-condition pilot. Only an
all-mode/all-point numerical and functional pilot pass allows the original
45-PVT product within the same job budget. Failures and unfinished stages
are recorded explicitly, not converted to pass or zero-valued metrics.
The native parasitic analysis retains FLOATING annotations, actual R/C
attachment, ground/dynamic pair couplings, true metal areas and path sums;
path sums are not equivalent parallel-network resistances.

## Reproduction and evidence

On the authorized disposable Linux runner, the inert `ci.yml` template is
copied only to the new experimental branch's root workflow directory.
It uses public shallow sparse checkout, exact tool/model pins, the lean
preflight builder and a private simulation virtual environment. There is no
shared-Windows system installation or large PDK image.
Run `bash layout_compact_repair/run.sh` from the entry directory in that
environment; fresh output/work directories are required.

Offline controls:

```sh
python3 -m unittest discover -s layout_nominal27 -p test_nominal27.py -v
python3 -m unittest discover -s layout_compact_repair -p test_repair.py -v
```

These checks do not claim actual DRC or circuit performance.
`inherited-sha256.json` pins every reused module and relevant native source.
Linux requires exact committed LF bytes. The seven preserved pre-existing
Windows CRLF preflight copies have separately recorded exact hashes for
offline checks only; no old file is rewritten or silently normalized.
The immutable published source remains byte-exact, including CRLF.

Each run retains its separate repair protocol and original baseline protocol,
source/hash audit, exact request/delta, native MAG/GDS/LVS/C/RC/EXT/resistance
files, complete structural controls, actual ngspice geometry tables, raw
waveforms/decks/logs, all matched measurements and numerical histories.
`execution.json` records the new phase and exact commit/run URL, while
`manifest.sha256` covers the full payload even on failure.
There is no density/antenna, foundry/silicon, mismatch-stress, or novelty
qualification implied by this repair.
