## Actual layout and parasitic evidence

The physical addendum continues the same competition question: does the
comparator still make a correct decision after real layout parasitics?
It is not a new circuit topology or a replacement for the original
schematic selection record.

`layout_compact_repair/evidence/attempt1/atlas.gds` is the repaired layout.
Native MAG, connectivity-only LVS, C-only and distributed RC netlists,
DRC/LVS logs, negative controls, and measured waveforms are alongside it.
All 17 structural checks passed: named-style DRC reports zero errors and
independent LVS accepts the actual layout while rejecting deliberately
wrong connections, bulk ties, widths and SVT/LVT substitutions.
There are 27 transistor instances, 15 ordered ports, 675 extracted
resistors and 319 listed capacitors in the RC network.
This is not density/antenna or foundry signoff.

![Actual repaired GDS geometry](results/presentation/actual_layout.png)

The physical comparison uses nominally matched devices, **code zero**,
common mode 0.5 VDD, 5 fF output loads, 50 ps edges and a 10 ns clock.
It is separate from the 49-condition schematic width-stress study.

| Reporting window | Schematic | Connectivity only | C-only | RC |
| --- | ---: | ---: | ---: | ---: |
| Original 1 ns pilot | 20/20 | 20/20 | 16/20 | 12/20 |
| Retained 2 ns window, post-hoc | 20/20 | 20/20 | 20/20 | 20/20 |

Each mode has five conditions times four signed inputs
(-10, -3, +3, +10 mV): **20 points per mode**, not 80 independent RC tests.
The original 1 ns pilot remains not fully qualified; its nominal
45-condition expansion was not run. All retained 10-to-5 ps comparisons
at 2 ns pass the unchanged 1% energy, 20 ps latency and equal-decision
limits. The largest measured 5 ps RC decision time in this sample is
1.58124 ns. A 3.5 ns layout window was not evaluated. No continuous
input-range guarantee, noise probability or manufacturing yield follows.

Against the prior **legal balanced layout**, matched TT +/-3 mV mean RC
delay improves from 0.84288 to 0.64511 ns and core energy from 520.84 to
425.36 fJ. The repaired layout occupies 2207.088 um2 instead of
3297.024 um2. It still uses substantially more core energy than the
matched 244.05 fJ schematic.

The compact predecessor failed M2 pad-notch spacing and was never
simulated. Four actual M2 bridges, totaling 0.3568 um2 of additional
metal, repair those notches without changing other mask geometry.
There is no bridge-only speed claim: the comparison includes the whole
compact routing versus the prior legal balanced layout.

### What is preserved

- `layout_compact_repair/verification-receipt.json`: exact source/tool/model
  identities, physical checks, original failed 1 ns gate, comparisons,
  sampling limits and separate repair-run ledger.
- `layout_compact_repair/evidence/attempt1/snapshot.sha256`: all 108 files
  in the representative local snapshot. It is **not** presented as the
  complete 1,235-file CI payload.
- `matched-metrics.csv` and `retained-window-characterization.json`:
  all 80 four-mode observations and the separately labeled 2 ns checks.
- `trace-examples`: six original RC waveforms at TT, cold SS and hot SS,
  both signs, with netlists, simulator logs and geometry audits.
- `layout_nominal27` and `layout_preflight`: exact preceding source and
  historical artifacts, including the illegal unsimulated predecessor.

Native annotations and parasitics are retained. Sums of listed R/C elements
are not effective network impedances. Historical receipts describe the
state when sealed; current publication status is recorded separately.

Actual verification:
[compact-repair run 35945064081](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/actions/runs/35945064081).
Its workflow conclusion is failure because the **original 1 ns performance
gate** is enforced. That does not erase the passed DRC/LVS checks, the
measured improvement, or the explicit retained-window characterization.

### Reproduce the exact physical experiment

The historical physical runner binds the original experimental source,
including its original entry checksum file. An updated reviewer notebook
is not a substitute for that frozen context.

From the current entry directory:

```text
python scripts/reproduce_layout_reference.py --prepare-only
```

This creates a project-local sparse source checkout at exact public
experimental commit `68832ec0ae7c526afcb4cded405a0bfd753a65c3` and verifies
the original entry checksum map. It installs no system package and runs
no layout or SPICE process. It prints the prepared entry path.

For a full replay, use that prepared source in a **disposable Ubuntu
24.04** environment. The pinned package list and command sequence are in
its `layout_compact_repair/ci.yml`; the original runtime uses Python 3.12,
Magic 8.3.684, circuit Netgen 1.5.323, open_pdks 1.0.608, ngspice
`42+ds-3build1` and NumPy 2.2.6.
After installing the declared disposable-runner packages, execute
`bash layout_compact_repair/run.sh` from the prepared entry directory.
This deliberately returns a nonzero result when the original 1 ns pilot
fails, while retaining all structural and simulation evidence.
Do not suppress that exit or call the original pilot fully passed.

The default competition notebook instead reviews the saved, hash-checked
evidence and recomputes example measurements. It needs neither Magic nor
an automatic system-package installation.
