# Reproducing Comparator Atlas

## Run the notebook

Open `Comparator_Atlas.ipynb` and run all cells. The default mode uses the
provided data, verifies experiment records, redraws the figures and remeasures
saved waveforms. Use the fork Colab link in the README before upstream merge.

For local execution from the project directory:

```text
python -m pip install -r requirements-review.txt
python -m pytest --nbmake --nbmake-timeout=600 Comparator_Atlas.ipynb
```

The reviewer environment supports Python 3.10 with NumPy 2.2.6, pandas 2.2.3,
Matplotlib 3.10.3 and ipywidgets 8.1.7. Use a short checkout path on Windows.
If Colab has already imported another package version, restart the runtime
as prompted; the complete downloaded source is reused.

The execution tools and PDK are available free of charge; no paid API key or
commercial EDA license is required. Colab is optional and its free resources
are limited, so long experiments may instead use a local CPU. The project
does not require Colab Pro, a GPU, a paid cloud runner or a Copilot account
to reproduce its results. Keep applicable third-party license notices.

## Execution modes

| Mode | What runs |
| --- | --- |
| Default | Analyze the provided schematic and layout data; no simulator installation is required. |
| `RUN_LIVE_SPICE = True` | Run six fresh schematic examples using an installed ngspice and the pinned public models. |
| `RUN_FULL_CAMPAIGN = True` | Re-run schematic selection, PVT characterization, numerical checks and the lower-energy control. This can take hours. |

For the full schematic campaign, the corresponding CLI stages are:

```text
python -m comparator_atlas optimize
python -m comparator_atlas study
python -m comparator_atlas stress
python -m comparator_atlas.professional_audit
python -m presentation.waveform_lab
```

Windows users may use `node scripts/setup.mjs` to install project-local
Python 3.12.10 and ngspice 47. The recorded reference schematic campaign uses
ngspice 47; a different simulator version is not assumed numerically identical.

## Experiment scopes

| Experiment | Conditions and controls | Reporting |
| --- | --- | --- |
| Schematic design comparison | 45 PVT combinations at controlled main-pair width stress, plus four nominal controls; 49 conditions per design | Same calibration policy, input band and deadline for circuit comparisons |
| Lower-energy control | Existing `lvt_base_3b` candidate, characterized after the original selection | Identified separately from selection data |
| Extracted layout | Five conditions, nominal matched geometry, code zero, four inputs `-10, -3, +3, +10 mV`, four netlist modes | Original 1 ns pilot and separately labeled retained 2 ns observations |
| Waveform lab | Eight representative saved schematic/RC traces | Illustrates the measurement rules; not additional validation coverage |

The layout RC result is 12/20 correct at the original 1 ns deadline and
20/20 at the retained 2 ns window. The latter is post-hoc characterization;
the original pilot remains not fully qualified. The 45-condition extracted
sweep and a 3.5 ns layout characterization have not been performed.

## Numerical measurements

A decision requires complementary 80%/20% output rails and the correct input
polarity. Zero differential input is unscored. Core energy is integrated over
the complete 20–30 ns cycle; external drivers and calibration infrastructure
are excluded.

Timestep comparisons use identical decision/outcome labels, at most 1% energy
difference and at most 20 ps resolved-latency difference. Sensitive schematic
points receive further timestep halving, with unfavorable corrections retained.
The layout's stored 10/5 ps comparisons are provided for its sampled conditions.
These are numerical consistency checks, not a noise or yield model.

## Data and physical source

| Location | Contents |
| --- | --- |
| `results/study/selection.json` | Declared candidate-selection result |
| `results/study/verified_measurements.csv` | Reported schematic observations after explicit numerical corrections |
| `results/study/measurement_refinements.csv` | Original-to-refined observation replacements |
| `results/study/professional/` | Lower-energy control and its numerical checks |
| `evidence_traces/` | Schematic teaching waveforms and source identities |
| `layout_compact_repair/evidence/attempt1/` | Actual GDS/MAG, LVS/C/RC netlists, checks, measured tables and six RC trace examples |
| `layout_compact_repair/verification-receipt.json` | Physical experiment provenance and measured comparison |
| `layout_nominal27/`, `layout_preflight/` | Physical generation/verification support and preceding references |

The physical snapshot contains 108 selected files and review tables; it is
not the entire CI payload. Per-file hashes bind the included data to the
recorded experiment. The default notebook checks the data it displays.

### Re-run the physical flow

The physical reference uses unmodified SKY130 primitive revision
`f62031a1be9aefe902d6d54cddd6f59b57627436`, Magic 8.3.684, Netgen 1.5.323,
open_pdks/sky130A 1.0.608, ngspice `42+ds-3build1` and NumPy 2.2.6.

Prepare the exact historical source without installing tools or running SPICE:

```text
python scripts/reproduce_layout_reference.py --prepare-only
```

The helper verifies source commit `68832ec0ae7c526afcb4cded405a0bfd753a65c3`
and its checksum context. In a disposable Ubuntu 24.04 environment, install
the packages specified by that source's `layout_compact_repair/ci.yml`, then
run `bash layout_compact_repair/run.sh` from the prepared project directory.
The flow preserves structural and simulation evidence and returns a failure
status when its original 1 ns performance gate is not met.

## Checks

```text
python -m pytest -q tests presentation
python -m nbqa flake8 --ignore=E402,E226 Comparator_Atlas.ipynb
node --test tests/test_explorer.mjs tests/test_waveform_lab.mjs
```

The entry-specific Linux workflow also executes the notebook from a
notebook-only public download and again after a fresh kernel restart.
This checks the source bootstrap; it is not a Google-account runtime test.
The current run is linked in the submission PR.

Original code is MIT licensed. Model/tool licenses and references are listed
in `THIRD_PARTY_NOTICES.txt` and the notebook. Verbatim upstream tool notices
are in `third_party_licenses/`; tool binaries are obtained separately.
