# Comparator Atlas: correct before the deadline - or NONE?

**SKY130 StrongARM comparators | sampled design decisions**

**Wei-Lun Hsu - National Tsing Hua University**

IEEE SSCS Code-a-Chip - ISSCC 2027 | Original code: MIT

[Notebook](Comparator_Atlas.ipynb) | [Quick tour](REVIEWER_GUIDE.md) | [Reproduction](REPRODUCIBILITY.md) | [Run in Colab](https://colab.research.google.com/github/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb)

Which SKY130 StrongARM comparator meets your sampled input band and deadline?
Calibration alone does not ensure a correct decision on time. Comparator Atlas lets you
compare three designs using saved schematic measurements: choose a specification, inspect
correct, wrong and unresolved outcomes, and trace failures to their exact records.
Rank mean energy only after every included point qualifies. If none does, return NONE,
not the best average.

**System at a glance.** Inputs enter at the top; the selector at the bottom returns the answer.

```text
 vinp, vinn (signed input v)      clk (10 ns)       VDD, PVT, width skew             <- inputs
        |                              |                     |
        v                              v                     v
 +----------------------------------------------------------------+
 | StrongARM core: input pair -> xp, xn -> cross-coupled latch    |<- trim current +
 +----------------------------------------------------------------+                |
        | qp, qn (outputs)                  | I(VDD)                               |
        v                                   v                                      |
 +------------------------------+   +----------------------------+    +-------------------------+
 | deadline judge at T: both    |   | core energy E = VDD x      |    | trim array: auxiliary   |
 | rails reached, sign correct? |   | charge drawn in 20-30 ns   |    | input NFETs switched    |
 +------------------------------+   +----------------------------+    | by the trim code c      |
        | correct / wrong /                 | E                       +-------------------------+
        | unresolved, decision time         |                                      ^ c
        |                                   |                                      |
        v                                   v                         +-------------------------+
 +----------------------------------------------------------------+   | calibration search:     |
 | strict selector (input band, deadline T): every included point |   | zero-input code scan +  |
 | correct, then lowest mean core energy                          |   | input bisection; leaves |
 +----------------------------------------------------------------+   | residual offset m       |
        v                                                             +-------------------------+
    selected design, or NONE                                                         <- output
```

- **StrongARM core** (Section 3): amplifies vinp − vinn onto xp/xn during evaluation, then the latch
  regenerates it into complementary rail-to-rail outputs qp/qn.
- **Trim array and calibration** (Sections 2, 3): code-switched auxiliary input devices add a current that
  cancels the core's offset; a search picks the code at the 3.5 ns deadline and leaves a residual offset m.
- **Deadline judge and energy** (Section 1): each decision is correct, wrong or unresolved at deadline T,
  with its decision time and full-cycle core energy.
- **Strict selector** (Section 4): for an input band and deadline, a design qualifies only if every included
  point is correct; the lowest mean energy among qualifiers wins, otherwise the answer is NONE.
- **Extension** (Section 9): the residual m explains every wrong decision, so later studies redesign the trim
  (unit cells, a segmented decoder) until ±1 mV qualifies.

**Why NONE at 1 mV? (Section 9, later extension.)** Later schematic studies, kept separate from the sealed record, find the cause and designs that do qualify:

- **Cause: the trim, not latch speed.** Every wrong decision lies between zero and the static post-calibration residual offset (303/303, no misses, four observed-correct false positives), and sealed predictions for six new designs matched 97.9% of 10,584 held-out decisions. The binary array's major-carry step limits first; once unit elements remove it, the trim range does (a 5-bit unit trim saturates in 11 of 49 conditions).
- **Two designs that qualify (r15b, r19).** In the finite 49-condition schematic atlas, two 6-bit unit-trim designs, each tested with sealed predictions, pass ±1 mV (98/98 decisions per deadline): `unit6_w6` (input W = 6 µm) at 1 and 2 ns with 760 fJ mean core energy, and `u6_w12_l05` (input W = 12 µm, half-length trim elements, chosen after an energy screen) at 0.75, 1 and 2 ns with 623 fJ. The shipped design needs a ≥3 mV band and averages 250 fJ there; these are different specifications, not a same-specification energy comparison. Paired mismatch Monte Carlo (40 seeds at each of two conditions; not a yield estimate) keeps the residual within 0.59 mV and 0.82 mV. Neither design has a layout of its own; an RC estimate on the archived extraction keeps ±1 mV correct at 2 ns but not at 1 ns (69/90 and 78/90 at code 0; misses are unresolved, none wrong).
- **The original selection holds (r20–r22).** The atlas width skew is not design-neutral under the PDK's width-binned models; rerun with an exact 4% current skew, the three-design selection is unchanged. At 1.95 V 125 °C the shipped trim covers 38/40 mismatch seeds; the two ~3σ seeds it misses are also missed by `lvt_base_3b`.
- **Noise (r23, r24).** With transient thermal noise (white BSIM4 noise, no flicker) the shipped design has 0.71 mV input-referred noise at TT, so its ±1 mV results are noiseless counts rather than low error rates; a 10⁻⁶ error rate needs about 4 mV at TT and 7 mV at SF 1.95 V 125 °C. A measured impulse sensitivity of the decision reproduces those noise runs realization by realization, maps the noise over 45 PVT conditions (0.35–1.21 mV) and shows that it follows the input pair's inversion level, so the input common mode is a noise knob.
- **Trim memory and range (r24c, r25).** A causal probe traces a 7.5 µV decision memory to the trim's floating nodes; one equalizing switch per bit removes it at 3% energy but does not recover the two hot-corner seeds. A fifth trim bit with the equalizer covers all 40 seeds at both hot corners at 55% more energy, with ±1 mV about unchanged (68 and 71/80), because that is limited by the ~2 mV trim step.
- **Unit-cell trim (r26b–r26d).** Building each bit from identical unit cells makes the weights binary at every corner; with the input pair widened 1.5×, ±1 mV reaches 240/240 paired decisions at SF, FF and TT for 4.8% more energy than r25. At 200 seeds over five conditions it passes ±1 mV at 1 ns for 978/1000 seeds, losing at the cold corners to the per-bit equalizer kept from r24c; a unit-cell equalizer gives 996/1000 with no unresolved decision (+7.3% energy), and a 1.75× input pair 999/1000 (+3.2%, not statistically resolved). The remaining miss follows a binary carry law, step sd = √(σ0² + (2^j − 1)σu²) with σu ≈ 0.1 mV per unit cell, which predicts that thermometer-coded MSBs would remove it.
- **Segmented trim with a real decoder (r26e, r26f).** With three thermometer MSBs (ideal decoder) the trim passes 1000/1000 at the same energy and its steps above 2 mV fall 3.3× (3.6× predicted); the steps are Gaussian with a 0.53%-per-cell carry drift. A transistor-level CMOS decoder adds no measurable energy, keeps the transfer monotonic and still passes 1000/1000 on 200 paired seeds at each of the five conditions, but clock-edge gate kickback weakens the segments 1.5–4.7%; a 4 µm MOS hold capacitor per segment gate removes it.
- **Kickback law and its fixes (r26g–r26j).** The kickback follows one capacitive-divider law over switch sizes, drivers and hold capacitors (within 8%), and a hold capacitor is about 3× more area-efficient than scaling the switch drivers. A linear series-R / shunt-C driver shows that the loss follows the dip's shape rather than the MOS device; the remaining MOS difference comes from the off gates, which a state-aware linear driver reproduces within 0.08 percentage points. A 4× decoder pull-down cuts the hot-corner loss 3–7× and the worst corner from 2.50% to 2.09%, but at equal gate area a larger nfet hold capacitor gives the lower worst corner (1.82%). In 40-seed Monte Carlo (r26j) these rankings hold in 40 of 40 seeds, every fix calibrates to ±1 mV, with no measurable energy cost; with the extracted gate-net coupling the two fixes tie (2.00% and 2.01%), and at four times that coupling the pull-down is the better fix (1.77% against 2.20%).

See Notebook Section 9 and the [research extension](REPRODUCIBILITY.md#research-extension).

## A three-minute route

1. Download [the self-contained report](results/study/report.html) and open it locally; GitHub's viewer does not run its controls. Opened as a single file, each folder link is followed by a pinned public copy. Try the three 1 ns presets below.
2. Inspect each design's qualification and exact failing keys, trim codes, latencies and CSV record locations. Only identity-matched retained traces get a waveform link; other keys show measurement records.
3. Compare wrong with unresolved: the same 20 selected +/-1 mV wrong samples remain at 2 ns. Then read the separate b1/a1 layout example and its physical-fidelity warning.

| Original sealed three-design atlas: 1 ns sampled band | Strict choice | Correct / included points | Mean core energy |
|---|---|---|---|
| >=1 mV | NONE | No candidate qualifies at all points | null, not zero |
| >=3 mV | lvt_balanced_4b | 294/294 | 249.655 fJ |
| >=30 mV | lvt_base_3b | 98/98 | 150.531 fJ |

This is a post-hoc comparison of exactly three schematic designs, local_boundary calibration, all 49 controlled-width-stress conditions and both signs at six finite sampled magnitudes through 30 mV. The six deadlines produce 36 cells: 28 NONE, 5 selected, 3 lower-energy control. Exact mean-energy ties retain every tied design; no interpolation or global optimization is implied. The original nine-candidate training choice is unchanged.

**Different input bands are different specifications.** The table is not a same-specification energy improvement.

**Energy and evidence contract.** Full-cycle 20-30 ns core energy excludes input/clock drivers and calibration/controller infrastructure. A null unresolved latency is not zero; failed designs and NONE retain null sampled limits. The report shows all keyed witnesses with their source table and record number; a retained raw wave is not promised for every measurement.

## Separate secondary demonstration: archived b1 vs a1

The adopted b1's 110 x 17.03 um all-material GDS bbox is 1873.3 um2 versus matched a1's 2074.254 um2 (-9.688013%), not die or signoff area. Historical native proofs are reused, not rerun. In the separate known-nonblind nominal code-zero 45-PVT comparison, b1 RC gives 158 correct / 0 wrong / 22 unresolved at 1 ns versus a1's 156/0/24; both C modes 170/0/10; all four 180/0/0 at 2 ns. Only SS / 1.62 V / 125 C / +/-10 mV improve; FS 1 ns failures/nulls remain. Mean b1 RC 412.879469 fJ and worst sampled 1.760276 ns are archived finite observations, not robust physical PPA. 1440 actual transients differ from 720 numerical pairs, 720 finest traces and 1440 two-deadline rows.

**Archived RC-deck outcomes; model physical fidelity not yet qualified.** No silicon, independently qualified physical PEX, yield, physical uncertainty or timing-signoff claim.

## Notebook, artifacts and execution

The [Notebook](Comparator_Atlas.ipynb) has the same integrated strict Python selection controls and saved static presets. Run all in the review environment; its bootstrap retrieves the submitted GitHub entry when needed, refuses support files from a different release than the Notebook (for example a stale `comparator-atlas-source` folder) and checks requirements-review.txt. Default execution analyzes saved data. Optional live/full modes require the explicitly documented tools and models and are false by default.

[Poster PDF](results/study/Comparator_Atlas_Poster.pdf) | [Poster preview](results/study/poster_preview.png) | [Abstract](results/study/abstract.txt) | [Methodology and dated execution scope](REPRODUCIBILITY.md).

Saved results, source links and maintainer executions are distinct forms of evidence; the dated reproduction scope states which source was actually executed.

GitHub Copilot assisted implementation, experiment automation, figures and documentation; the author is responsible for the work.


## Audit route

The integrated decision JSON is [here](results/study/decision_data.json); the unchanged [strict source](presentation/specification_map.py) and [original 36-cell summary](results/study/specification_map/summary.json) define the selection. All disqualifying records link to [original/selected measurements](results/study/verified_measurements.csv) or [lower-energy-control measurements](results/study/professional/measurements.csv). Keys include design, condition, signed input, deadline and run ID. The record number is 1-based excluding the CSV header. The stored map is now the complete three-design local_boundary grid; other calibration policies remain in the original saved tables, not synthesized as missing control measurements.
