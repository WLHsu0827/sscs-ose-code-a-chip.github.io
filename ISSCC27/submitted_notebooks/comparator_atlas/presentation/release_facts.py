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


def write_judge_guide(facts: dict) -> Path:
    schematic, layout = facts["schematic"], facts["layout"]
    text = f"""# Comparator Atlas - reviewer and demonstration guide

**Wei-Lun Hsu - National Tsing Hua University**

## Start with the current submission

- [View the executed primary notebook]({facts["notebook_url"]})
- [Run this submission in Colab now]({facts["colab_url"]})
- [Official submission PR]({facts["pull_request_url"]})
- [Public source tree]({facts["source_tree_url"]})

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
failed at slow corners. DRC, LVS and all {layout["structural_checks"]} structural
checks passed; the failure is not hidden. The 2 ns table is explicitly an
additional characterization of already saved waveforms, not a new passing
qualification threshold.

**Did the layout improve?** Against the earlier legal balanced layout, matched
TT +/-3 mV mean RC delay fell from {layout["previous_legal_rc_delay_ns"]:.5f}
to {layout["repaired_rc_delay_ns"]:.5f} ns and core energy from
{layout["previous_legal_rc_energy_fj"]:.2f} to {layout["repaired_rc_energy_fj"]:.2f}
fJ. This benefit belongs to the complete compact routing versus the legal
balanced layout, not to the four pad bridges alone. The repaired RC energy
still exceeds its matched {layout["matched_schematic_energy_fj"]:.2f} fJ
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
