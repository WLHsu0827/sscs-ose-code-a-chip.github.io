# Layout and extracted-circuit results

The selected 27-transistor comparator is implemented with nominally matched
devices and code zero. The physical experiment uses five PVT conditions,
four signed inputs (-10, -3, +3, +10 mV), 5 fF output loads and a 10 ns clock
with 50 ps edges.

![Repaired comparator layout](../results/presentation/actual_layout.png)

The layout passes the specified `sky130A drc(full)` deck and independent
LVS checks. Negative controls reject incorrect connections, bulk ties,
widths and SVT/LVT substitutions. The distributed-RC export has 675
resistors and 319 listed capacitors; counts and sums are not effective
network impedances.

## Timing

| Reporting window | Schematic | Connectivity only | C-only | RC |
| --- | ---: | ---: | ---: | ---: |
| Original 1 ns pilot | 20/20 | 20/20 | 16/20 | 12/20 |
| Retained 2 ns window, post-hoc | 20/20 | 20/20 | 20/20 | 20/20 |

The eight late RC points occur at the two SS conditions. Each mode has
20 sampled points; the table does not represent 80 independent RC tests.
The original 1 ns pilot is not fully qualified. The 2 ns result describes
the same retained waveforms, not a revised original target.
The 45-condition extracted sweep has not been performed.

## Layout comparison

At matched TT +/-3 mV points, compact routing improves mean RC delay from
0.84288 to 0.64511 ns and core energy from 520.84 to 425.36 fJ, relative to
the prior legal balanced layout. Bounding-box area changes from 3297.024
to 2207.088 um2. The matched schematic consumes 244.05 fJ.

Four M2 bridges repair pad-notch spacing in the compact geometry. Because
the preceding illegal compact layout was not simulated, these measurements
compare the complete repaired layout against the earlier legal layout;
they do not isolate the bridges' contribution.

## Files and reproduction

- [GDS](../layout_compact_repair/evidence/attempt1/atlas.gds)
- [Connectivity-only netlist](../layout_compact_repair/evidence/attempt1/atlas.lvs.spice)
- [C-only netlist](../layout_compact_repair/evidence/attempt1/atlas.c.spice)
- [Distributed-RC netlist](../layout_compact_repair/evidence/attempt1/atlas.rc.spice)
- [Measurements](../layout_compact_repair/evidence/attempt1/matched-metrics.csv)
- [Reproduction instructions and tool versions](../REPRODUCIBILITY.md)

These are nominal-geometry simulations, separate from the schematic
width-stress study. Core energy excludes external drivers and calibration
infrastructure. DRC/LVS do not establish silicon performance, statistical
yield or full foundry signoff.
