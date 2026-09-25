"""One checked set of contest facts for the README, poster and reviewer guide."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import entry_tools as entry
import layout_evidence as physical

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ISSCC27/submitted_notebooks/comparator_atlas"
BRANCH = "wlhsu0827-comparator-atlas-isscc27"
FORK = "WLHsu0827/sscs-ose-code-a-chip.github.io"
NOTEBOOK = "Comparator_Atlas.ipynb"
PR_URL = "https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/pull/195"
NOTEBOOK_URL = f"https://github.com/{FORK}/blob/{BRANCH}/{PREFIX}/{NOTEBOOK}"
COLAB_URL = f"https://colab.research.google.com/github/{FORK}/blob/{BRANCH}/{PREFIX}/{NOTEBOOK}"
TREE_URL = f"https://github.com/{FORK}/tree/{BRANCH}/{PREFIX}"


def load_facts() -> dict:
    schematic = entry.load_evidence()
    layout = physical.load_layout()
    metadata = schematic["metadata"]
    narrow = entry.summary(schematic, minimum_mv=1.0)
    wide = entry.summary(schematic, minimum_mv=3.0)
    rc_summary = physical.deadline_summary(layout).set_index(["mode", "deadline_ns"])
    costs = physical.matched_tt_comparison(layout).set_index("implementation")
    selected = schematic["selection"]["selected_design"]
    old = costs.loc["Previous balanced RC"]
    repaired = costs.loc["Repaired Distributed RC"]
    ideal = costs.loc["Schematic"]
    return {
        "authors": metadata["authors"],
        "title": metadata["title"],
        "notebook": NOTEBOOK,
        "notebook_url": NOTEBOOK_URL,
        "colab_url": COLAB_URL,
        "source_tree_url": TREE_URL,
        "pull_request_url": PR_URL,
        "schematic": {
            "condition_count": 49,
            "primary_deadline_ns": 1.0,
            "policy": "local_boundary",
            "selected": selected,
            "baseline_correct_at_1mv": int(narrow.loc["baseline", "correct"]),
            "selected_correct_at_1mv": int(narrow.loc[selected, "correct"]),
            "points_at_1mv": int(narrow.loc[selected, "points"]),
            "selected_correct_at_3mv": int(wide.loc[selected, "correct"]),
            "points_at_3mv": int(wide.loc[selected, "points"]),
            "original_mean_core_energy_fj": float(narrow.loc["baseline", "mean_core_energy_fj"]),
            "selected_mean_core_energy_fj": float(narrow.loc[selected, "mean_core_energy_fj"]),
            "efficient_control_correct_at_1mv": int(narrow.loc["lvt_base_3b", "correct"]),
            "efficient_control_energy_fj": float(narrow.loc["lvt_base_3b", "mean_core_energy_fj"]),
        },
        "layout": {
            "nominal_geometry": True,
            "trim_code": 0,
            "condition_count": len(layout["receipt"]["protocol"]["sampled_conditions"]),
            "rc_sampled_points": int(rc_summary.loc[("Distributed RC", 1), "sampled_points"]),
            "rc_correct_1ns": int(rc_summary.loc[("Distributed RC", 1), "correct"]),
            "rc_unresolved_1ns": int(rc_summary.loc[("Distributed RC", 1), "unresolved"]),
            "rc_correct_posthoc_2ns": int(rc_summary.loc[("Distributed RC", 2), "correct"]),
            "structural_checks": layout["receipt"]["physical"]["pass"],
            "drc_errors": layout["receipt"]["physical"]["full_named_drc_errors"],
            "bbox_um2": layout["receipt"]["geometry"]["bbox"]["bbox_area_um2"],
            "previous_legal_rc_delay_ns": float(old.mean_delay_ns),
            "repaired_rc_delay_ns": float(repaired.mean_delay_ns),
            "previous_legal_rc_energy_fj": float(old.mean_core_energy_fj),
            "repaired_rc_energy_fj": float(repaired.mean_core_energy_fj),
            "matched_schematic_energy_fj": float(ideal.mean_core_energy_fj),
            "delay_reduction_percent": float(100 * (1 - repaired.mean_delay_ns / old.mean_delay_ns)),
            "energy_reduction_percent": float(100 * (1 - repaired.mean_core_energy_fj / old.mean_core_energy_fj)),
            "original_1ns_pilot_qualified": False,
            "full_45_condition_pex_performed": False,
            "posthoc_2ns_is_new_qualification": False,
            "physical_run_url": layout["receipt"]["run"]["run_url"],
            "physical_run_conclusion": "failure_at_original_1ns_performance_gate",
        },
        "limits": [
            "Schematic 49-condition results and nominal-layout five-condition results are separate experiments.",
            "Twenty RC points are not eighty independent RC tests or full 45-condition extracted coverage.",
            "The 2 ns statement is post-hoc characterization; the original 1 ns pilot remains failed.",
            "Core energy excludes external drivers and calibration infrastructure.",
            "No silicon measurement, foundry signoff, yield, continuous-input guarantee or global optimum is claimed.",
            "A submitted PR is not acceptance, a rank or an award.",
        ],
        "evidence_sha256": {
            "entry_metadata.json": entry.digest(ROOT / "entry_metadata.json"),
            "results/study/selection.json": entry.digest(entry.STUDY / "selection.json"),
            "results/study/verified_measurements.csv": entry.digest(entry.STUDY / "verified_measurements.csv"),
            "results/study/professional/measurements.csv": entry.digest(
                entry.STUDY / "professional" / "measurements.csv"
            ),
            "layout_compact_repair/verification-receipt.json": physical.RECEIPT_SHA256,
        },
    }


def readme_text(facts: dict, design_table: str) -> str:
    layout = facts["layout"]
    return f"""# Comparator Atlas: When Calibration Is Not Enough

**Wei-Lun Hsu — National Tsing Hua University**  
IEEE SSCS Code-a-Chip · ISSCC 2027 · MIT License

[Notebook]({facts["notebook_url"]}) |
[Run in Colab]({facts["colab_url"]}) |
[Reproduction instructions](REPRODUCIBILITY.md)

## Overview

Offset calibration alone does not ensure that a comparator finishes its
decision in time. This notebook follows a SKY130 StrongARM comparator from
device sizing and calibration through PVT evaluation, layout and parasitic
extraction. Interactive waveforms explain the difference between a wrong
decision and an unresolved one.

The workflow includes a nine-candidate design comparison, an additional
lower-energy control, and a physical implementation of the selected
27-transistor circuit.

## Results

The schematic comparison uses the same local calibration policy, a 1 ns
deadline and sampled absolute inputs of at least 1 mV:

{design_table}

These are finite-grid results: 45 PVT combinations at controlled width
stress plus four nominal controls. The lower-energy candidate was evaluated
after the original selection.

The separate nominal-layout study uses code zero, five PVT conditions and
four signed inputs per condition. DRC/LVS and device/connection controls pass.
RC gives **{layout["rc_correct_1ns"]}/{layout["rc_sampled_points"]} correct
points at the original 1 ns deadline** and
**{layout["rc_correct_posthoc_2ns"]}/{layout["rc_sampled_points"]} at the retained
2 ns window**. The latter is post-hoc characterization; the original
1 ns pilot is not fully qualified.

Against the earlier legal balanced layout, matched TT +/-3 mV mean RC
delay improves from {layout["previous_legal_rc_delay_ns"]:.3f} to
{layout["repaired_rc_delay_ns"]:.3f} ns, and core energy from
{layout["previous_legal_rc_energy_fj"]:.1f} to
{layout["repaired_rc_energy_fj"]:.1f} fJ/cycle.

## Run

Open the notebook in Colab and run all cells, or run locally:

```text
python -m pip install -r requirements-review.txt
python -m pytest --nbmake --nbmake-timeout=600 Comparator_Atlas.ipynb
```

Default execution analyzes the supplied data and remeasures saved waveforms.
Fresh SPICE examples and the full campaign are optional notebook modes.
The Colab link uses the submitted fork before upstream merge.
The project requires no commercial EDA license or paid API key.
Local CPU execution is supported; Colab's free tier has resource limits.

For the standalone interactive report, download and open
`results/study/report.html`. The Waveform Lab provides eight recorded
examples with a deadline cursor and complementary-rail thresholds.

## Files

- `Comparator_Atlas.ipynb` — circuit, methods, plots and discussion.
- `comparator_atlas/` — simulation, calibration and analysis code.
- `results/study/` — measurements, figures, report, poster and abstract.
- `layout_compact_repair/` — final layout, extraction and physical evidence.
- `REPRODUCIBILITY.md` — tool versions, data map and complete run commands.

## Scope

The calibrated schematic and nominal-layout experiments have different
scopes; extracted 45-condition PVT coverage has not been established.
Core energy excludes external drivers and calibration infrastructure.
The results are deterministic simulations, not silicon measurements or
foundry statistical yield. References and detailed conditions are in the
notebook.

## License and acknowledgment

Original code is [MIT licensed](LICENSE). Third-party notices are retained
in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
GitHub Copilot assisted implementation, experiment automation, figures and
documentation; the author is responsible for the work.
"""


def write_judge_guide(facts: dict) -> Path:
    schematic, layout = facts["schematic"], facts["layout"]
    text = f"""# Comparator Atlas - quick tour

**Wei-Lun Hsu - National Tsing Hua University**

[Notebook]({facts["notebook_url"]}) |
[Run in Colab]({facts["colab_url"]}) |
[Setup and data](REPRODUCIBILITY.md)

## Suggested reading order

1. **Question and circuit.** Read the abstract and 27-transistor circuit guide.
   The work asks when a calibrated regenerative comparator reaches a correct
   decision before a finite deadline, and what physical costs are involved.
2. **Compare the complete schematic grid.** At 1 ns and sampled absolute
   input at least 1 mV, the original and selected designs have
   {schematic["baseline_correct_at_1mv"]}/{schematic["points_at_1mv"]} and
   {schematic["selected_correct_at_1mv"]}/{schematic["points_at_1mv"]} correct
   points with the same local policy. Compare the lower-energy control too;
   no design is declared best for every specification.
3. **Inspect actual layout evidence.** View the hash-checked GDS, DRC/LVS
   negative controls and matched schematic/connectivity/C/RC results.
   Original 1 ns RC is {layout["rc_correct_1ns"]}/{layout["rc_sampled_points"]};
   the retained post-hoc 2 ns window is
   {layout["rc_correct_posthoc_2ns"]}/{layout["rc_sampled_points"]}.
   Both the success scope and the missed original target stay visible.

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
"""
    destination = ROOT / "REVIEWER_GUIDE.md"
    destination.write_text(text, encoding="utf-8")
    manifest = {
        "status": "competition_guide_generated_from_checked_evidence",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "facts": facts,
        "guide_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "new_physical_simulations": 0,
        "public_upload_performed": False,
    }
    output = ROOT / "results" / "presentation" / "reviewer_guide_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    print(write_judge_guide(load_facts()))
