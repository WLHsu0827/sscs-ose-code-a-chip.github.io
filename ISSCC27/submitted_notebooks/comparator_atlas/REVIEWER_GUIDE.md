# Comparator Atlas - quick tour

**Wei-Lun Hsu - National Tsing Hua University**

[Notebook](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb) |
[Run in Colab](https://colab.research.google.com/github/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb) |
[Setup and data](REPRODUCIBILITY.md)

## Suggested reading order

1. **Question and circuit.** Read the abstract and 27-transistor circuit guide.
   The work asks when a calibrated regenerative comparator reaches a correct
   decision before a finite deadline, and what physical costs are involved.
2. **Compare the complete schematic grid.** At 1 ns and sampled absolute
   input at least 1 mV, the original and selected designs have
   310/392 and
   372/392 correct
   points with the same local policy. Compare the lower-energy control too;
   no design is declared best for every specification.
3. **Inspect actual layout evidence.** View the hash-checked GDS, DRC/LVS
   negative controls and matched schematic/connectivity/C/RC results.
   The full 45-condition nominal RC study gives
   156/180 correct at 1 ns and
   180/180 at its declared 2 ns
   deadline. Its worst sample is 1.835 ns at
   FS / 1.62 V / -40 C / -3 mV. The earlier five-condition pilot is retained
   separately and is not retrospectively relabeled.

The **Waveform lab** makes the distinction concrete: eight representative
saved examples have a movable deadline, complementary output thresholds and
source run identities. A wrong-sign schematic decision, its calibrated
counterpart, and late extracted RC decisions are all visible. These examples
are not every raw trace in the atlas and add no new validation coverage.
Moving the display deadline does not rerun SPICE or reduce full-cycle energy.

Download `results/study/report.html` for offline interaction. Run all notebook
cells to regenerate the analysis from the included data; full simulations
are separate optional modes. Detailed commands, versions and limitations are
collected in [Reproducibility](REPRODUCIBILITY.md).
