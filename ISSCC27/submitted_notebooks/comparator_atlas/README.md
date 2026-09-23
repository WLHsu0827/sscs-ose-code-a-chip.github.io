# Comparator Atlas: When Calibration Is Not Enough

**Wei-Lun Hsu - National Tsing Hua University**

IEEE SSCS Code-a-Chip, ISSCC 2027. Open-source circuit characterization and
educational workflow. Original project license: MIT.

## Review the entry

Open **Comparator_Atlas.ipynb** and run all cells with Python 3.10 or newer.
The default mode verifies the supplied source/protocol/result hashes,
recomputes corrected comparisons, and extracts measurements from six actual
SPICE waveforms. It does not silently perform a multi-hour simulation campaign.

Install the review environment from this project directory:

```text
python -m pip install -r requirements-review.txt
python -m pytest --nbmake Comparator_Atlas.ipynb
python -m nbqa flake8 --ignore=E402,E226 Comparator_Atlas.ipynb
```

The notebook includes the official-owner Colab badge. When opened without its
supporting files, it fetches only this project directory from the author's
public submission branch using a sparse Git checkout. The official main-branch
badge becomes available after upstream merge; before then use the same notebook
on the author's fork. Neither route downloads the historical notebook corpus.

**Offline interactive report:** download and open `results/study/report.html`.
It embeds all figures, data and scripts; no server, CDN or tracking is required.
Change the circuit, deadline and scoring band, then select a cell to inspect
its real recorded measurement. The post-selection lower-energy control is
reported separately rather than being presented as a newly blinded test.

## Research question and fair comparison

An accurate long-deadline switching boundary does not guarantee a correct,
rail-valid decision under a short deadline. We distinguish wrong, unresolved,
and uncalibratable results while holding supply, common mode, load, clock and
measurement thresholds equal across circuits.

The original campaign freezes a nine-circuit selection before comparing the
original and selected circuits at 49 conditions each: a 45-condition PVT grid
at controlled width skew, plus four extra nominal controls. A subsequent audit
adds a lower-energy existing candidate across the same conditions. It is
explicitly post-selection and does not alter the earlier selection record.

At 1 ns and sampled absolute inputs of at least 1 mV, under the same local
calibration policy, the current checked results are:

                 correct  points  grid_coverage  fully_passing_conditions  conditions  worst_condition_coverage  mean_core_energy_fj  simulated_points  gate_area_proxy_um2
design                                                                                                                                                                     
baseline             310     392       0.790816                        16          49                     0.000           143.013776               392                10.83
lvt_balanced_4b      372     392       0.948980                        29          49                     0.875           251.525212               392                20.55
lvt_base_3b          351     392       0.895408                        18          49                     0.250           156.646856               392                10.83

These fractions are deterministic test-grid coverage, not silicon yield.
The complete sampled envelope is recorded in the notebook. A 1 ns decision
deadline is not a demonstrated 1 GHz clock: all runs use a 10 ns period.
More energy, more gate geometry, and unfavorable input-interface behavior
are disclosed; no circuit is claimed best for every specification.

## Evidence and numerical corrections

All results are schematic-level SKY130 BSIM simulations. The initial 10-to-5 ps
check found numerical sensitivity, including cases that had looked correct at
coarse resolution. Explicit finer-step corrections replace every matching
policy/deadline row, including unfavorable corrections. Original data and the
refinement history remain available. The lower-energy control receives a
separately recorded all-nonzero-input numerical check.

The 80% / 20% complementary-rail decision contract, signed full-cycle core-rail
energy integral, waveform sampling, measured boundary intervals, and the
calibration workload are defined in the notebook. Calibration is host-driven:
reference generation, drivers, storage and an on-chip controller are not part
of the claimed core energy.

`evidence_traces` contains a small genuine waveform set with hashes and point
parameters. No absolute local model path or private cache is published.
The complete campaign can be regenerated from the source.

## Fresh transistor-level simulation

On Linux/Colab, install Git and ngspice using the host's normal package manager,
then install `requirements-review.txt`. The notebook's `RUN_LIVE_SPICE` switch
downloads the unmodified pinned SKY130 primitive models and runs the six
documented waveform points. It prints the actual simulator version and metrics.
Different simulator versions are not assumed to match the reference results.

On Windows, the optional `node scripts/setup.mjs` bootstrap provisions
project-local CPython 3.12.10, ngspice 47 and the recorded Windows environment
without changing PowerShell execution policy. The saved reference campaign
uses ngspice 47. Its binary/model hashes remain in the manifests.

For the full campaign after toolchain setup:

```text
python -m comparator_atlas optimize
python -m comparator_atlas study
python -m comparator_atlas stress
python -m comparator_atlas.professional_audit
```

The notebook's `RUN_FULL_CAMPAIGN` switch calls those stages. Full runs may
take hours. Per-condition checkpoints preserve progress. Source integrity is
verified; a stale or incomplete receipt is not relabeled as success.

## Limitations and attribution

No silicon measurement, tapeout, layout/PEX, DRC/LVS, foundry statistical yield,
random-noise error probability, global optimum or new comparator topology is
claimed. Gate area is the sum of transistor W*L, not a physical layout area.
The comparison baseline is our first prototype, not the best published design.
The finite input/PVT grid is not proof of a continuous operating guarantee.
The lower-energy control has not inherited the other circuits' interface
stress results.

Established StrongARM and auxiliary-pair calibration research, existing
SKY130 optimization examples, and the unmodified model/tool sources are
credited in the notebook and THIRD_PARTY_NOTICES.txt. Original code and prose
are MIT licensed; third-party materials retain their respective licenses.

**AI assistance:** GitHub Copilot assisted code, experiment automation and documentation. The entrant is responsible for reviewing, explaining and defending the work.

No IEEE endorsement, certification or award is implied by this entry.
