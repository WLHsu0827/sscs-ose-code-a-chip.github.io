"""Generate the single public notebook, including the official Colab badge."""

from pathlib import Path
import textwrap

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def markdown(text: str):
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text: str):
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip())


def main() -> None:
    cells = [
        markdown("""
        # Comparator Atlas: When Calibration Is Not Enough

        **Wei-Lun Hsu — National Tsing Hua University**

        IEEE SSCS Code-a-Chip, ISSCC 2027 — open-source circuit-design and
        characterization study. Original project license: MIT.

        [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb)

        **Before upstream merge:**
        [run the current submitted version in Colab](https://colab.research.google.com/github/WLHsu0827/sscs-ose-code-a-chip.github.io/blob/wlhsu0827-comparator-atlas-isscc27/ISSCC27/submitted_notebooks/comparator_atlas/Comparator_Atlas.ipynb).
        The official-owner badge above becomes the canonical link after merge;
        it is not evidence that this entry has already been accepted.
        See [the reviewer guide](REVIEWER_GUIDE.md) for a short evaluation path.

        **Abstract.** A small switching-boundary offset does not guarantee a
        valid decision before a deadline. This notebook studies that distinction
        using unmodified SKY130 device models, a bounded nine-circuit search,
        a 49-condition original-versus-selected comparison, and a subsequently
        declared lower-energy control. It distinguishes wrong decisions,
        unresolved outputs, unavailable calibration, and numerical sensitivity.
        A separately scoped physical-layout addendum adds actual GDS,
        DRC/LVS negative controls, distributed RC extraction and a matched
        comparison against the schematic. Corrected evidence tables,
        actual waveforms and source hashes make the analysis inspectable.

        **Scope.** The 49-condition design study is schematic-level.
        The nominal-geometry layout addendum covers five conditions and
        four signed inputs per mode. These are deterministic simulations,
        not silicon, foundry yield, a new topology or a global optimum.
        Energy means the measured core VDD rail, excluding the input/clock
        drivers and calibration controller. The lower-energy comparison is
        explicitly post-selection, not a newly blinded benchmark.

        **Reproduction modes.** Default execution verifies the supplied evidence
        and recomputes plots and waveform metrics without a circuit simulator.
        Optional live simulation and the full campaign are separate switches
        below. Python 3.10 is supported for the organizer's notebook runner.
        A fresh complete SPICE campaign can take hours; it is not an implicit
        side effect of opening this notebook.
        """),
        code(r"""
        from pathlib import Path
        import importlib.util
        from importlib import metadata
        import subprocess
        import sys

        parts = (
            "ISSCC27", "submitted_notebooks", "comparator_atlas"
        )
        source = Path.cwd() / "comparator-atlas-source"
        candidates = [
            Path.cwd(),
            Path.cwd().joinpath(*parts),
            source.joinpath(*parts),
        ]
        entry_root = next(
            (p for p in candidates if (p / "entry_tools.py").is_file()),
            None,
        )
        if entry_root is None:
            if source.exists():
                raise RuntimeError(
                    "An incomplete source directory already exists. "
                    "Inspect it before retrying; it was not overwritten."
                )
            repository = (
                "https://github.com/WLHsu0827/"
                "sscs-ose-code-a-chip.github.io.git"
            )
            branch = "wlhsu0827-comparator-atlas-isscc27"
            subprocess.run(
                [
                    "git", "clone", "--quiet", "--depth", "1",
                    "--filter=blob:none", "--no-checkout",
                    "--single-branch", "--branch", branch,
                    repository, str(source),
                ],
                check=True,
            )
            subprocess.run(
                [
                    "git", "-C", str(source), "sparse-checkout",
                    "set", str(Path(*parts)),
                ],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(source), "checkout", "--quiet", branch],
                check=True,
            )
            entry_root = source.joinpath(*parts)
            if not (entry_root / "entry_tools.py").is_file():
                raise RuntimeError("The downloaded entry is incomplete.")
        required = {
            "numpy": "2.2.6",
            "pandas": "2.2.3",
            "matplotlib": "3.10.3",
            "nbformat": "5.10.4",
            "ipywidgets": "8.1.7",
        }
        needs_setup = []
        for name, version in required.items():
            if importlib.util.find_spec(name) is None:
                needs_setup.append(name)
            elif metadata.version(name) != version:
                needs_setup.append(name)
        if needs_setup:
            subprocess.run(
                [
                    sys.executable, "-m", "pip", "install", "-q",
                    "-r", str(entry_root / "requirements-review.txt"),
                ],
                check=True,
            )
        stale = []
        for name, version in required.items():
            loaded = sys.modules.get(name)
            if loaded is not None:
                loaded_version = getattr(loaded, "__version__", version)
                if loaded_version != version:
                    stale.append(name)
        if stale:
            raise RuntimeError(
                "Dependencies were updated but older packages are loaded. "
                "Restart the kernel/runtime once, then Run all."
            )
        sys.path.insert(0, str(entry_root))
        import matplotlib.pyplot as plt
        import pandas as pd
        from IPython.display import Code, Image, display
        import entry_tools as entry
        import layout_evidence as physical

        %matplotlib inline
        release_checksums = entry_root / "entry_checksums.json"
        if release_checksums.is_file():
            import json
            support_hashes = json.loads(
                release_checksums.read_text(encoding="utf-8")
            )
            support_hashes.pop("Comparator_Atlas.ipynb", None)
            entry.verify_files(
                entry_root,
                support_hashes,
            )
            print(
                "Public support files verified. The notebook itself "
                "remains editable for execution-mode switches."
            )
        else:
            print(
                "Development checkout: sealed experiment manifests "
                "will be verified; no release file map is present."
            )
        RUN_LIVE_SPICE = False
        RUN_FULL_CAMPAIGN = False
        print("Python:", sys.version.split()[0])
        print("Default: verified supplied evidence, not a fresh SPICE run.")
        """),
        markdown(r"""
        ## 1. State a falsifiable decision contract

        At deadline $T$ after the evaluation clock midpoint, the decision is
        valid only if **both** complementary outputs reach their assigned
        rails: one at least $0.8V_{\mathrm{DD}}$, the other at most
        $0.2V_{\mathrm{DD}}$. Its sign must equal that of the externally
        applied differential input. A resolved opposite sign is **wrong**;
        a missing complementary-rail decision is **unresolved**.
        Zero input is not counted in pass fractions.

        The sampled decision time excludes an early output glitch: it is the
        first saved valid sample after the final invalid sample, through the
        reporting deadline. A 1 ns decision deadline does not mean that a
        1 GHz clock was tested; the clock period is 10 ns.

        $$E_{\mathrm{core}}=-V_{\mathrm{DD}}
        \int_{20\,\mathrm{ns}}^{30\,\mathrm{ns}} I_{V_{\mathrm{DD}}}(t)\,dt.$$

        The full third cycle includes reset. Two previous cycles provide
        warmup. Input common mode is half the supply, clock edges are 50 ps,
        and each output carries a 5 fF ideal load unless an explicitly named
        interface stress changes that condition.

        Simulator errors, failed reset, missing waveforms, corrupt archives
        and unavailable calibration are not successful circuit results.
        All reported fractions refer to a finite declared grid, not yield
        or an input-probability distribution.
        """),
        markdown(r"""
        ## 2. Calibration must preserve unresolved intervals

        A zero-input trim scan locates candidates near a sign change. Input
        bisection then brackets confirmed opposite decisions. The score is

        $$M_T=\max(|v_-(T)|,\ |v_+(T)|).$$

        The midpoint of a wide unresolved interval is not evidence of a
        precisely known zero offset. The host search minimizes the larger
        absolute endpoint among measured candidates, with 0.2 mV input-bracket
        resolution. This is a documented heuristic around an assumed locally
        monotonic noiseless transfer, not a new calibration algorithm or proof
        of a global optimum.

        The long-deadline policy uses 3.5 ns; a separate ablation applies the
        same procedure at 1 ns. A TT/1.8 V/27 C reference-code policy transfers
        a single code across model corners. It is **not** a per-die factory
        calibration at an unknown fixed process corner.
        """),
        markdown("""
        ## 3. Physical circuit family and a frozen selection rule

        The conventional StrongARM core has eleven transistor instances,
        including four reset PFETs. Each trim magnitude bit adds one auxiliary
        analog input NFET and its digital source-gating NFET on each side.
        The selected circuit has 27 instances and **four magnitude bits plus
        sign**, supporting codes -15 through +15. An on-chip decoder and
        calibration controller are not implemented.

        The auxiliary analog gates track their respective input. No ideal
        source simply subtracts a fitted offset. All trim devices remain
        physically present at code zero; comparison within a design therefore
        retains its trim parasitic loading.

        Nine candidates vary device threshold flavor, dimensions and trim
        range. LVT applies to the main and auxiliary analog input paths;
        latch, tail and digital switches remain standard-VT.

        Selection used three PVT conditions and six inputs, with 2x mean
        training core-energy and 4x gate-area-proxy budgets. The ranking
        maximizes worst-case training coverage, then mean coverage, followed
        by boundary magnitude, energy and gate geometry. The gate-area proxy
        is the sum of transistor W times L, not placed/routed area.
        The first prototype informed the family. All rejected candidates
        remain visible in the recorded selection.
        """),
        code("""
        if RUN_FULL_CAMPAIGN:
            entry.full_reproduction()
        evidence = entry.load_evidence()
        selection = evidence["selection"]
        candidates = pd.DataFrame([
            {
                "design": item["design"]["name"],
                "input_device": item["design"]["input_device"],
                "transistors": item["design"]["transistor_count"],
                "gate_area_um2": item["design"]["gate_area_proxy_um2"],
                "worst_training_coverage":
                    item["worst_case_correct_fraction"],
                "mean_training_core_fj": item["mean_core_energy_fj"],
                "eligible": item["eligible"],
            }
            for item in selection["candidates"]
        ])
        display(candidates)
        print("Frozen selected design:", selection["selected_design"])
        display(Image(filename=str(physical.circuit_guide_path())))
        display(Code(
            (entry.STUDY / "selected_circuit.spice").read_text(),
            language="spice",
        ))
        """),
        markdown("""
        ## 4. Full comparison and an energy-efficient control

        The original comparison has 45 PVT combinations at one controlled
        main-pair width skew, plus four additional nominal skew controls:
        49 conditions per circuit. This is not every mismatch value at every
        PVT combination. With +4% skew, the two branch widths use multipliers
        1.04 and 0.96. This deliberately controlled perturbation is **not a
        foundry Monte Carlo mismatch distribution**.

        The selected/original comparison uses validation inputs distinct from
        the six current selection inputs. The three selection conditions
        remain identifiable; they are not relabeled as independent data.

        **Post-selection control.** An existing lower-energy LVT candidate,
        `lvt_base_3b`, is characterized on the same 49 conditions with code
        zero and local calibration. This addresses a stronger engineering
        question than comparison with the original circuit alone: whether
        the selected circuit's extra energy is justified by the desired
        decision band. This control was declared after viewing the original
        comparison and does not constitute a new blinded test set.

        The next tables show both average and worst-condition coverage.
        A design with a favorable average is not automatically acceptable
        if even one required condition fails.
        """),
        code("""
        print("Local policy; 1 ns; sampled |input| >= 1 mV")
        display(entry.summary(evidence, minimum_mv=1.0))
        print("Same policy and deadline; sampled |input| >= 3 mV")
        display(entry.summary(evidence, minimum_mv=3.0))
        display(entry.sampled_envelope(evidence))
        figure = entry.tradeoff_figure(evidence)
        display(figure)
        plt.close(figure)
        """),
        code("""
        import ipywidgets as widgets


        def inspect_tradeoff(minimum_mv, deadline_ns):
            display(entry.summary(evidence, minimum_mv, deadline_ns))


        minimum_control = widgets.SelectionSlider(
            options=[0.25, 0.5, 1.0, 3.0, 10.0, 30.0],
            value=1.0,
            description="Min |input| (mV)",
            continuous_update=False,
            style={"description_width": "initial"},
        )
        deadline_control = widgets.SelectionSlider(
            options=[0.25, 0.35, 0.5, 0.75, 1.0, 2.0],
            value=1.0,
            description="Deadline (ns)",
            continuous_update=False,
            style={"description_width": "initial"},
        )
        interactive_table = widgets.interactive_output(
            inspect_tradeoff,
            {
                "minimum_mv": minimum_control,
                "deadline_ns": deadline_control,
            },
        )
        display(minimum_control, deadline_control, interactive_table)
        """),
        markdown("""
        ## 5. Numerical sensitivity is a result, not a footnote

        The original 10-to-5 ps refinement exposed fourteen failed deadline
        checks across seven physical points. Refinement to 0.625 ps produced
        two consecutive passing halving comparisons under the unchanged
        limits: identical decision/outcome, at most 1% core-energy difference
        and at most 20 ps resolved-latency difference.

        The finest accepted waveform replaces **every** matching policy and
        deadline observation, including corrections that make the circuit
        look worse. Original coarse tables and the full refinement history
        remain available. No circuit, code, stimulus, deadline or frozen
        candidate choice changes during this process.

        The added energy-efficient control checks every nonzero input point
        under both policies at 10 and 5 ps, then applies the same stricter
        halving rule to sensitive points. Unresolved sensitivity blocks its
        inclusion as a completed comparison.

        These are numerical checks for declared observations, not proof of
        stability at every continuous input, random-noise immunity or
        production signoff.
        """),
        code("""
        numerical = pd.DataFrame([
            {
                "study": "original / selected",
                "initial_failed_checks":
                    evidence["stress"]["initial_numerical_failures"],
                "final_failed_checks":
                    evidence["stress"]["numerical_failures"],
                "refined_physical_points":
                    evidence["stress"]["refined_physical_points"],
            },
            {
                "study": "post-selection lower-energy control",
                "initial_failed_checks":
                    evidence["control"]["initial_failed_checks"],
                "final_failed_checks":
                    evidence["control"]["final_failed_checks"],
                "refined_physical_points":
                    evidence["control"]["refined_physical_points"],
            },
        ])
        display(numerical)
        """),
        markdown("""
        ## 6. Recompute metrics from actual transistor-level waveforms

        The following small, hash-checked waveform set is distributed with the
        entry. It is not a synthetic behavioral model. The same measurement
        function used in the campaign recomputes reset validity, rail-valid
        decisions, latency and full-cycle core energy.

        The weak SS/low-voltage/cold condition was known during selection.
        These traces illustrate mechanism; the complete condition tables
        support the finite-grid comparison.
        """),
        code("""
        measured, figure = entry.review_waveforms()
        display(measured)
        display(figure)
        plt.close(figure)
        if RUN_LIVE_SPICE:
            display(entry.live_spice_smoke())
        else:
            print(
                "Waveform metrics recomputed from checked saved SPICE data. "
                "Set RUN_LIVE_SPICE=True for fresh transistor simulation."
            )
        """),
        markdown("""
        ### Waveform lab: wrong, late, or correct?

        The controls below expose eight post-hoc teaching examples from
        already recorded SPICE data. The full waveform is rechecked before
        its excerpt is drawn. This is not a new performance experiment
        or the full raw-waveform atlas.

        Start with the **code-zero -1 mV schematic example**: its outputs
        resolve to the wrong polarity. Switch to the same circuit and
        input with calibration enabled, then to a cold-SS extracted RC
        example. At 1 ns that RC trace is late; reading its saved 2 ns
        observation does not retroactively pass the original 1 ns gate.

        Horizontal dotted lines are the fixed 80% / 20% output rail
        thresholds. The two cursor voltages, not only their difference,
        determine whether the decision is valid. Core energy always
        covers the complete saved 10 ns cycle.
        """),
        code("""
        from presentation import waveform_lab

        lab = waveform_lab.load_lab()


        def inspect_waveform(example, deadline_ns):
            figure, reading = waveform_lab.figure(
                lab, example, deadline_ns
            )
            display(figure, pd.DataFrame([reading]))
            plt.close(figure)


        example_control = widgets.Dropdown(
            options=[
                (sample["label"], sample["id"])
                for sample in lab["samples"]
            ],
            value="schematic_untrimmed",
            description="Stored waveform",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="95%"),
        )
        waveform_deadline = widgets.SelectionSlider(
            options=lab["deadlines_ns"],
            value=1.0,
            description="Deadline (ns)",
            continuous_update=False,
            style={"description_width": "initial"},
        )
        waveform_output = widgets.interactive_output(
            inspect_waveform,
            {
                "example": example_control,
                "deadline_ns": waveform_deadline,
            },
        )
        display(example_control, waveform_deadline, waveform_output)
        """),
        markdown("""
        ## 7. The input interface and calibration workload are not free

        Five original/selected PVT conditions are stressed with input history,
        finite source resistance and capacitance, altered common mode, and
        increased output loading. The calibration code is frozen before the
        interface changes. Results include the unfavorable cases: the faster
        LVT path can inject larger deterministic input disturbances and does
        not necessarily improve a heavily loaded interface.

        The measured pin error includes settling and kickback, not random
        thermal noise. These interface results apply to the original and
        selected circuits; the added lower-energy control has not silently
        inherited them.

        Calibration workload below counts distinct simulated probes. Each
        probe simulates three 10 ns cycles. This is **offline experiment
        workload**, not an implemented calibration latency or total on-chip
        energy. A practical system also needs reference/input generation,
        switching, a controller and storage; those implementation costs
        remain outside the measured core-rail energy.
        """),
        code("""
        display(entry.operating_summary(evidence))
        display(entry.calibration_workload(evidence))
        """),
        markdown("""
        ## 8. From schematic to a real extracted layout

        The layout uses the same selected 27-device circuit with nominally
        matched main inputs and code zero. It does not reproduce the
        schematic width-skew experiment as intentional geometry.
        Fifteen ordered ports, exact device flavors/dimensions/body ties,
        and actual mask geometry are checked before simulation.

        A first legal layout had positive-input failures after extraction.
        Balanced routing repaired the capacitive environment; a compact
        routing revision then required four real M2 bridges to eliminate
        narrow PFET body-pad notches. This final physical repair passes
        named-style DRC, independent LVS and deliberately wrong connection,
        bulk, width and SVT/LVT negative controls. It is not foundry signoff.

        **Three separate electrical exports:** connectivity-only LVS,
        C-only extraction, and distributed RC extraction. All native
        elements and their annotations remain retained. The GDS view below
        is parsed from the actual hash-checked file, not a drawn floorplan.
        """),
        code("""
        layout = physical.load_layout()
        display(physical.geometry_summary(layout))
        figure = physical.layout_figure(layout)
        display(figure)
        plt.close(figure)
        display(physical.matched_tt_comparison(layout))
        figure = physical.tt_cost_figure(layout)
        display(figure)
        plt.close(figure)
        """),
        markdown("""
        ### Keep the original failure and the measured operating range

        The repaired geometry improves the matched TT +/-3 mV RC result
        from about 0.843 ns / 521 fJ to 0.645 ns / 425 fJ, but still costs
        substantially more than its matched 244 fJ schematic result.
        This comparison is against the prior **legal balanced** layout,
        not the illegal compact predecessor that was never simulated.
        A bridge-only speed improvement cannot be isolated from this data.

        The original 1 ns pilot remains **not fully qualified**:
        RC is correct at 12/20 sampled points; eight SS points are late.
        In the already retained **2 ns window**, RC is correct at 20/20
        points across five conditions and +/-3, +/-10 mV. This second
        statement is explicitly post-hoc operating-range characterization,
        not a revised original gate, continuous-range guarantee or yield.
        Each mode has 20 points; the four-mode total of 80 is not 80
        independent RC tests. All retained 10-to-5 ps comparisons at
        2 ns pass the original numerical limits.

        The 45-condition nominal PVT expansion was not run. A 3.5 ns
        layout window was not evaluated and is not inferred from 2 ns.
        The clock remains 10 ns in every comparison.
        """),
        code("""
        display(physical.deadline_summary(layout))
        figure = physical.deadline_figure(layout)
        display(figure)
        plt.close(figure)
        layout_measurements, figure = (
            physical.review_layout_waveforms(layout)
        )
        display(layout_measurements)
        display(figure)
        plt.close(figure)
        """),
        markdown("""
        ### Reproduce the physical reference

        `layout_compact_repair` contains the exact native layout,
        connectivity/C/RC netlists, logs, measurements, numerical
        comparisons and six original RC waveform examples. Its 108-file
        local snapshot is explicitly distinguished from the full
        1,235-file CI payload. The preceding source and failed-layout
        snapshots remain in `layout_nominal27` and `layout_preflight`.

        The historical physical runner binds the original experimental
        source and branch. To rerun that exact experiment, use the pinned
        experimental checkout described in README.md, not the updated
        reviewer notebook checksum as a substitute. The original workflow
        reports failure at its unchanged 1 ns performance gate while
        retaining its successful DRC/LVS and all measured results.
        This is distinct from the fast default notebook review.
        """),
        markdown("""
        ## 9. Reproducibility, attribution and claim boundary

        `entry_tools.load_evidence()` checks source, protocol, selection and
        result hashes; recomputes the explicit numerical corrections; and
        rejects missing, duplicated or incorrectly represented observations.
        Archived Windows-style manifest keys are resolved portably without
        disabling source verification. Git attributes preserve the bytes
        of hash-bound source and data files across platforms.

        The default review path runs with Python 3.10 and no SPICE installation.
        The optional live path uses the unmodified pinned SKY130 models and
        an installed ngspice. Full reproduction is available through the
        source CLI and the explicit full-campaign switch; runtime, tool
        versions and the distinction from saved results are documented.

        **Supported:** deterministic schematic behavior and the separately
        scoped nominal-layout observations; a bounded design-space
        comparison; measured core-rail energy; an inspectable workflow.

        **Not supported:** a new topology, global optimum, fabrication-ready
        signoff, silicon performance, yield, noise-error probability, total
        system power, or superiority over unmatched published circuits.
        No "IEEE certification" or award is implied.

        ### References

        1. B. Razavi, “The StrongARM Latch [A Circuit for All Seasons],”
           *IEEE Solid-State Circuits Magazine*, vol. 7, no. 2, pp. 12–17,
           2015. DOI: [10.1109/MSSC.2015.2418155](https://doi.org/10.1109/MSSC.2015.2418155).
        2. S. Li, Z. Xu and T. Iizuka, “Analysis of strong-arm comparator with
           auxiliary pair for offset calibration,” *Analog Integrated Circuits
           and Signal Processing*, vol. 110, pp. 535–546, 2022.
           DOI: [10.1007/s10470-022-01992-6](https://doi.org/10.1007/s10470-022-01992-6).
        3. [Official SKY130 primitive models](https://github.com/google/skywater-pdk-libs-sky130_fd_pr),
           revision `f62031a1be9aefe902d6d54cddd6f59b57627436`.
           Original Apache-2.0 notices are retained.
        4. [Open SKY130/GF180 comparator optimization research](https://github.com/ChrisZonghaoLi/sky130_comparator_rl)
           and [an existing SKY130/LVT comparator example](https://github.com/edonD/sky130-comparator).
           Related ideas are credited; their code, figures, performance
           claims and statistical assumptions are not this study's evidence.
        5. [ngspice](https://ngspice.sourceforge.io/) and
           [Code-a-Chip rules](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io).
        6. [Magic extraction documentation](https://opencircuitdesign.com/magic/commandref/ext2spice.html),
           [distributed resistance extraction](https://opencircuitdesign.com/magic/commandref/extresist.html),
           and [open_pdks](https://github.com/RTimothyEdwards/open_pdks).

        **AI-assistance disclosure.** GitHub Copilot assisted code, experiment
        automation and documentation. Wei-Lun Hsu is responsible for reviewing,
        explaining and defending the submitted work. This assistance is not
        an assertion that a particular publication or award policy has been
        waived. Original code and prose are MIT licensed; third-party models
        and tools retain their own licenses.
        """),
    ]
    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.18"},
    })
    nbf.validate(notebook)
    destination = ROOT / "Comparator_Atlas.ipynb"
    nbf.write(notebook, destination)
    print(f"Generated {destination.name}: {len(cells)} cells")


if __name__ == "__main__":
    main()
