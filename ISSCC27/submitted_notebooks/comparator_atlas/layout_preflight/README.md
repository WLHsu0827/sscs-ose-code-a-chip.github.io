# Experimental SKY130 layout toolchain preflight

**Wei-Lun Hsu - National Tsing Hua University**

This is a bounded toolchain experiment, not the submitted Comparator Atlas
result and not a layout of the proposed 35-device comparator. The published
entry and its source commit `2ad1c4c2058060abdfdd42c35aa784c018f6fa67` are unchanged.
No comparator DRC/LVS/PEX, foundry signoff, silicon result, density coverage, or
antenna coverage is claimed.

## Reproduce on a disposable Linux host

Ubuntu 24.04, Python 3 standard library, and the packages in `apt-packages.txt`
are the declared environment. Install those packages using the host's package
manager only when authorized. Then, from this directory:

```sh
python3 -m unittest discover -s . -p test_preflight.py -v
timeout --signal=TERM --kill-after=30s 24m bash run.sh
```

All compiled tools and sources stay under `.work`; evidence stays under `out`.
Existing paths are rejected rather than overwriting evidence. Set `LAYOUT_WORK`
and `LAYOUT_OUT` to fresh absolute paths for another run. The scripts do not use
sudo, install system-wide tools, install WSL, use Docker, or fetch a full PDK.

`pins.json` fixes Magic, Tim Edwards' **circuit Netgen** (not the unrelated mesh
generator), and open_pdks to full source commit hashes. The build uses shallow
filtered Git fetches and a sparse open_pdks checkout. It invokes the genuine
`configure` and `make -C sky130 magic-A netgen-A` preprocessing targets, including
their required `custom/scripts` helpers. It never runs vendor/prerequisite or
full-PDK installation targets and never substitutes a fabricated extraction
deck. Generated technology files, hashes, executable/source versions, dependency
versions, build logs, and installed sizes are preserved.

## What is exercised

The accepted four-terminal primitive alternative is used instead of an inverter.
Each of the ten independent cells contains one transistor, actual PCell-generated
contacts and a contacted guard/body ring, with explicit `D G S B` port order.
All have `nf=1`, `m=1`; requested dimensions may not be silently clamped.
The gate metal1 landing is extended north on the same connected polygon. Its
actual M1/contact union area must be at least 0.10 um2, independently measured
from the saved geometry and Magic's grid scale, in addition to passing DRC.

| Primitive | W (um) | L (um) |
|---|---:|---:|
| Ordinary SVT NFET input | 3 | 0.15 |
| Ordinary SVT NFET switches | 1, 2 | 0.15 |
| Ordinary SVT PFET | 3 | 0.15 |
| LVT NFET fine-device matrix | 0.42, 0.84 | 2, 4, 6 |

The harness checks nonempty `.mag` rectangles and GDS layer geometry, extracted
transistor count/model/W/L/m/bulk, and Magic **sky130A `drc(full)`**, with Euclidean
distance enabled. A separate 0.07 um metal1 spacing violation must produce DRC
errors. These are local open-source deck checks, not complete tapeout checks.
The selected style is read with `drc list style` and corroborated by captured
raw Magic output.

The independent schematic reference is constructed from `devices.json`, never
copied from the extracted netlist. Netgen explicitly recognizes the four-terminal
primitive classes as `nmos`/`pmos` while retaining distinct SKY130 model names and
the unmodified generated SKY130 setup's W/L and bulk comparisons. No device is
replaced by an empty black box. Four reference mutations must fail: gate/source
short, incorrect bulk, doubled width, and SVT substituted for LVT. A tool exit
code alone is not counted as an LVS match.
Magic itself emits the named top with `ext2spice subcircuit top on`. Both its
SPICE wrapper and the actual `.ext` port order are checked before Netgen starts;
the harness does not manufacture a wrapper around an invalid extraction.

Two PCell-based branched drain probes have 0.36 um metal2 width and 20/400 um
spans from the drain to the external port. A trunk reaches a fork halfway along
the span; upper/lower arms connect through two genuine PDK-generated via1
contacts, 2 um apart on the existing 3 um drain. This is a physical multi-contact
network, not a hand-split resistance model. The external drain port is at the
far end, without a zero-ohm alias. The larger span makes the geometry dependence
clear against fixed contact/diffusion resistance; numerical criteria are not
reduced. Separate files contain:

- `*.lvs.spice`: connectivity only; no parasitic R or C.
- `*.c.spice`: layout-derived capacitance without distributed resistance.
- `*.rc.spice`: actual `extract do resistance` / `.res.ext` output incorporated
  with `ext2spice extresist on`, zero capacitance threshold, and finite resistance
  threshold, explicitly set after the LVS preset.

The pinned modern Magic interface uses `threshold`/`minresist` in milliohms and
`mindelay` in picoseconds, not deprecated `tolerance`. The harness requires
positive R/C values, multiple connected resistors between the external drain and
a transistor terminal, an extracted branch junction, internal nodes, and
increasing extracted drain RC for the longer route. Every MOS terminal and
parasitic node must be DC-connected to the correct external port without shorts.
`FLOATING`-annotated capacitances are retained and checked, not deleted.
It records every resistor/capacitor value, the drain component's element names,
terminal memberships, branch nodes, and actual route coordinates in
`capabilities.json`.
Resistance sums describe the extracted component, not an AC impedance or a
general effective resistance measurement.

The explicit `ngspice()` extraction style emits device geometry in **micrometres**; the
unscaled W/L values are checked directly and extra scale directives are rejected.
No SPICE smoke simulation is included. The earlier schematic-model source is
`google/skywater-pdk-libs-sky130_fd_pr` at
`f62031a1be9aefe902d6d54cddd6f59b57627436`; it is recorded but not downloaded.
The open_pdks layout technology has separate provenance. Model equivalence
between these revisions and a foundry-qualified RC corner is not established.

## Restricted CI and evidence

`ci.yml` is an inert project-scoped workflow template. Its only authorized root
installation is `.github/workflows/comparator-atlas-layout-preflight.yml` on
the author's fork branch `verify/comparator-atlas-layout-preflight`. It triggers
only that branch, only for this experiment, and only in the author's fork.
Never place the root workflow on the submitted branch or upstream; do not open
a formal PR for this preflight. The job is limited to 30 minutes, with a 24-minute
toolchain timeout and an always-run artifact upload.

On that verification branch only, exclude the same branch from the inherited
`lint.yaml` and `run.yaml` push triggers so they do not start an unrelated
historical-notebook checkout. The scoped workflow uses an unauthenticated,
shallow, sparse fetch of this public fork at `GITHUB_SHA`, never recursive
submodule operations. This avoids the historical dangling submodule entry that
caused the first attempt's checkout-action credential cleanup to fail.

At most two initial remote runs are authorized. CI artifacts contain the actual
GDS, Magic layouts, connectivity/C/RC netlists, `.ext`/`.res.ext`, independent
references, DRC/LVS reports, and source/deck/binary/artifact hashes. Successful
installation alone is not a passed layout. Execution receipts and the actual
capability outcome are reported separately after inspecting downloaded evidence.

A subsequent bounded decision authorized up to two more runs (attempts 3/4,
each at most 30 minutes) to repair concrete implementation defects. The initial
`verification_receipt.json`, both original runs, and the following historical
failure analysis remain unchanged. Further runs do not retrospectively turn the
initial 12 PASS / 42 FAIL result green.

Original harness code is MIT licensed under the parent project's license.
Fetched third-party sources retain their own licenses. Magic, open_pdks and
circuit Netgen are credited to their upstream projects and contributors.

## Initial verification provenance

Attempt 1: [run 35808864758](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/actions/runs/35808864758),
commit `9b194bb4fc4d6328b2546f983a71b550df084257`, failed in checkout before
dependencies or tools ran. The checkout action's auth cleanup reported
`No url found for submodule path ... sky130-opamp in .gitmodules`.
This is an infrastructure failure, **not** a DRC, LVS, or PEX result.
Attempt 2: [run 35809175154](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/actions/runs/35809175154),
commit `0cd79b96016b4ebc39af26d7c1542bb667c8dce6`, completed in 48 seconds with
**failure**. Both authorized attempts are now consumed. No third run was started,
no controls were relaxed, and no comparator layout was attempted.

Unlike attempt 1, attempt 2 actually built and executed Magic **8.3.684** and
circuit Netgen **1.5.323**, generated the open_pdks **1.0.608** tools-only deck,
and wrote real layouts, extracted devices, DRC results and RC networks.
The recorded source/build/install directories totaled 91,812 KiB (about 89.7 MiB).

| Capability | Actual evidence from attempt 2 | Outcome |
|---|---|---|
| Pinned tools / genuine PDK staging | Built tools, executed version/commit, generated deck and source hashes retained | Passed |
| Ten four-terminal primitives | Nonempty MAG/GDS; one correct model/W/L transistor per cell; D/G/S/B labels and `.ext` ports present | Observed |
| Six LVT dimension combinations | `drc(full)` logs and zero raw DRC errors for all six | Observed local DRC pass |
| SVT NFET, PFET and two routed probes | Three error rectangles each for gate-contact metal1 minimum area, `met1.6` | Failed |
| Deliberate spacing error | Two `met1.2` errors for a 0.07 um gap below the 0.14 um rule | Detected |
| Positive LVS and four LVS mutations | Missing top-level `.subckt` wrapper; Netgen cannot find the named circuit | Blocked, not comparisons |
| Separate C and RC extraction | Each C-only file: 6 C / 0 R; each RC file: 21 R / 11 C plus `.res.ext` | Partial, not accepted PEX |

**First substantive blocker:** the short-channel primitives' isolated gate metal1
landing is approximately 0.29 by 0.23 um (0.0667 um2), below `met1.6`'s
0.083 um2 minimum. The PCell device dimensions themselves are extracted correctly;
this is missing legal landing/routing area in the preflight structure. The
three rectangles are regions for one rule, not three independent rule types.

There are additional harness/integration blockers, all preserved in the failed
evidence rather than relabeled as passes:

- `[drc style]` prints the style but returns an empty Tcl value, so the report's
  style field is blank. The captured Magic log explicitly names `drc(full)`.
  The automated geometry/DRC assertions therefore failed even for the six
  raw-zero-error LVT cells and the correctly detected spacing control.
- `.mag` and `.ext` contain numbered ports, but the selected flat SPICE output
  has no `.subckt` wrapper. Netgen launches and reads the files, then reports
  `Cannot find cell n_input3`; the setup/classification and real comparisons
  are not reached. Wrong-connection/bulk/width/flavor controls are **unproven**.
- `extract style ngspice` is ambiguous at this version; the actual `.ext` style
  is `ngspice()`. The obsolete `-y` accuracy option also produces a warning.
- Both RC files contain real positive extracted elements, but the long drain
  path is represented by only one resistor, not the multiple drain-path
  segments required by the acceptance check. Some internal capacitances carry
  Magic's `; **FLOATING` comment, which the strict parser also needs to handle
  without discarding connectivity checks. No simulation or PEX signoff occurred.

The short/long drain resistors are **51.6048 / 175.749 ohm**. Across each whole
RC netlist, resistor values span 5.8005 to 3285.26 ohm; the latter values include
body-network resistance, not just the deliberately routed metal. Total extracted
RC capacitance is **5.95932 / 35.43025 fF**, with individual capacitors ranging
from 0.03067 fF to 4.64862 / 34.05628 fF. These measurements establish that the
outputs are not the parasitic-free LVS files, but do not satisfy the complete
DRC/LVS/distributed-route acceptance.

The automated receipt remains **12 PASS / 42 FAIL**, not a green preflight.
Post-run read-only inspection verified all **141** recorded artifact hashes and
the device/layer facts above without modifying the downloaded outputs.
`verification_receipt.json` records the exact run, commit, artifact, deck hash,
capability limitations and measured values. The downloaded evidence is also
retained in the session artifact directory. Further execution requires a new
decision; the experimental branch remains at the attempt-2 commit.
