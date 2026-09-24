# Comparator Atlas - reviewer and demonstration guide

**Wei-Lun Hsu - National Tsing Hua University**

## Start with the current submission

- [View the executed primary notebook](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb)
- [Run this submission in Colab now](https://colab.research.google.com/github/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb)
- [Official submission PR](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/pull/195)
- [Public source tree](https://github.com/WLHsu0827/sscs-ose-code-a-chip.github.io/tree/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas)

The direct Colab link above points to the author's submitted branch and works
before upstream merge. The official-owner badge inside the notebook is the
canonical post-merge link; it must not be mistaken for an already merged entry.

Download the project for the offline report at `results/study/report.html`.
GitHub's normal HTML file viewer is not an interactive website preview.

## Three-minute evaluation path

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
   Original 1 ns RC is 12/20;
   the retained post-hoc 2 ns window is
   20/20.
   Both the success scope and the missed original target stay visible.

The **Waveform lab** makes the distinction concrete: eight representative
saved examples have a movable deadline, complementary output thresholds and
source run identities. A wrong-sign schematic decision, its calibrated
counterpart, and late extracted RC decisions are all visible. These examples
are not every raw trace in the atlas and add no new validation coverage.
Moving the display deadline does not rerun SPICE or reduce full-cycle energy.

## What Run all does

Default execution checks supplied source/data hashes, recomputes tables and
figures, parses actual GDS and remeasures saved transistor-level waveforms.
It needs no Magic installation and does not silently launch the full campaign.
The notebook installs its declared review dependencies when needed. If Colab
already imported a different package version, it explicitly requests one
runtime restart; the complete downloaded entry is reused on the next Run all.

`RUN_LIVE_SPICE` requests six fresh schematic simulations using an installed
ngspice and pinned public device models. `RUN_FULL_CAMPAIGN` is the much longer
schematic design/characterization flow. The exact historical physical-flow
source is separately prepared by `scripts/reproduce_layout_reference.py`.
None of these modes is silently substituted for another.

For local review from the project directory:

```text
python -m pip install -r requirements-review.txt
python -m pytest --nbmake --nbmake-timeout=600 Comparator_Atlas.ipynb
python -m nbqa flake8 --ignore=E402,E226 Comparator_Atlas.ipynb
```

Use a short checkout path on Windows. All public entry content stays below
`ISSCC27/submitted_notebooks/comparator_atlas`.

## Demo and questions

**Opening explanation:** “Comparator Atlas follows one comparator from
schematic sizing and calibration to a real extracted layout. It makes
wrong decisions, late decisions, and numerical uncertainty inspectable rather
than replacing them with one favorable nominal performance number.”

**Why is the physical workflow marked failed?** Its original 1 ns pilot
failed at slow corners. DRC, LVS and all 17 structural
checks passed; the failure is not hidden. The 2 ns table is explicitly an
additional characterization of already saved waveforms, not a new passing
qualification threshold.

**Did the layout improve?** Against the earlier legal balanced layout, matched
TT +/-3 mV mean RC delay fell from 0.84288
to 0.64511 ns and core energy from
520.84 to 425.36
fJ. This benefit belongs to the complete compact routing versus the legal
balanced layout, not to the four pad bridges alone. The repaired RC energy
still exceeds its matched 244.05 fJ
schematic value.

**Is it a novel circuit, a tapeout, or a yield result?** No. It is an
open-source, reproducible characterization and educational design flow around
established circuitry. The actual nominal GDS and extraction are included;
foundry signoff, silicon, calibrated mismatch/yield, and continuous-input
guarantees are not claimed.

**Who owns the work?** Wei-Lun Hsu, National Tsing Hua University. GitHub
Copilot assistance is disclosed in the notebook; the entrant remains
responsible for understanding and presenting the work.

## Submission state is not an award

PR #195 is the official submitted item. Maintainer review and organizer
decisions remain separate from completing this artifact. The entry-specific
Linux review and historical physical run are linked in the PR description.
Inherited repository-wide notebook-glob failures require maintainer attention;
the entry does not modify root workflows outside its allowed project folder.
