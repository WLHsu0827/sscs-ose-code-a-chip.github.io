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

The independent schematic reference is constructed from `devices.json`, never
copied from the extracted netlist. Netgen explicitly recognizes the four-terminal
primitive classes as `nmos`/`pmos` while retaining distinct SKY130 model names and
the unmodified generated SKY130 setup's W/L and bulk comparisons. No device is
replaced by an empty black box. Four reference mutations must fail: gate/source
short, incorrect bulk, doubled width, and SVT substituted for LVT. A tool exit
code alone is not counted as an LVS match.

Two PCell-based drain routes have 0.36 um metal2 width, 20/200 um horizontal
legs, and a 10 um connecting leg. The genuine PDK via1 generator connects to the
drain. The external drain port is at the far end, without a zero-ohm alias.
Separate files contain:

- `*.lvs.spice`: connectivity only; no parasitic R or C.
- `*.c.spice`: layout-derived capacitance without distributed resistance.
- `*.rc.spice`: actual `extract do resistance` / `.res.ext` output incorporated
  with `ext2spice extresist on`, zero capacitance threshold, and finite resistance
  threshold, explicitly set after the LVS preset.

The pinned modern Magic interface uses `threshold`/`minresist` in milliohms and
`mindelay` in picoseconds, not deprecated `tolerance`. The harness requires
positive R/C values, multiple connected resistors between the external drain and
a transistor terminal, internal nodes, and increasing extracted drain RC for
the longer route. It records every resistor/capacitor value in `capabilities.json`.
Resistance sums describe the extracted component, not an AC impedance or a
general effective resistance measurement.

The `ngspice` extraction style emits device geometry in **micrometres**; the
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

Original harness code is MIT licensed under the parent project's license.
Fetched third-party sources retain their own licenses. Magic, open_pdks and
circuit Netgen are credited to their upstream projects and contributors.

## Initial verification provenance

Attempt 1: [run 35808864758](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/actions/runs/35808864758),
commit `9b194bb4fc4d6328b2546f983a71b550df084257`, failed in checkout before
dependencies or tools ran. The checkout action's auth cleanup reported
`No url found for submodule path ... sky130-opamp in .gitmodules`.
This is an infrastructure failure, **not** a DRC, LVS, or PEX result.
Only one further initial verification run is authorized.
