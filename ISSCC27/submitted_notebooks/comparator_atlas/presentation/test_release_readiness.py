import ast
import hashlib
import json
from pathlib import Path
import textwrap

import pytest

from presentation.release_facts import COLAB_URL, NOTEBOOK, load_facts


def bootstrap_source() -> str:
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_entry_notebook.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    sources = [
        node.args[0].value for node in ast.walk(module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "code" and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ]
    first = next(source for source in sources if "entry_root = next(" in source)
    return textwrap.dedent(first)


def execute_directory_detection(monkeypatch, cwd: Path) -> dict:
    # Use the exact generated bootstrap through its directory-detection block.
    source = bootstrap_source()
    source = source[:source.index("required = {")]
    monkeypatch.chdir(cwd)
    namespace = {}
    exec(compile(source, "<notebook-bootstrap>", "exec"), namespace)
    return namespace


def test_current_colab_link_is_to_the_live_submission_branch():
    assert "/github/WLHsu0827/sscs-ose-code-a-chip.github.io/" in COLAB_URL
    assert "/blob/wlhsu0827-comparator-atlas-isscc27/" in COLAB_URL
    assert COLAB_URL.endswith("/" + NOTEBOOK)


def test_completed_colab_checkout_is_reused_after_kernel_restart(tmp_path, monkeypatch):
    entry = tmp_path / "comparator-atlas-source" / "ISSCC27" / "submitted_notebooks" / "comparator_atlas"
    entry.mkdir(parents=True)
    (entry / "entry_tools.py").write_text("# fixture\n")
    result = execute_directory_detection(monkeypatch, tmp_path)
    assert result["entry_root"] == entry


def test_incomplete_download_is_not_silently_overwritten(tmp_path, monkeypatch):
    (tmp_path / "comparator-atlas-source").mkdir()
    with pytest.raises(RuntimeError, match="incomplete"):
        execute_directory_detection(monkeypatch, tmp_path)


def test_project_directory_and_repository_root_are_supported(tmp_path, monkeypatch):
    entry = tmp_path / "ISSCC27" / "submitted_notebooks" / "comparator_atlas"
    entry.mkdir(parents=True)
    (entry / "entry_tools.py").write_text("# fixture\n")
    assert execute_directory_detection(monkeypatch, tmp_path)["entry_root"] == entry
    assert execute_directory_detection(monkeypatch, entry)["entry_root"] == entry


def test_final_presentation_facts_keep_schematic_and_layout_scopes_separate():
    facts = load_facts()
    assert facts["notebook"] == "Comparator_Atlas.ipynb"
    assert facts["schematic"]["selected_correct_at_1mv"] == 372
    assert facts["schematic"]["points_at_1mv"] == 392
    assert facts["layout"]["rc_correct_1ns"] == 12
    assert facts["layout"]["rc_correct_posthoc_2ns"] == 20
    assert facts["layout"]["rc_sampled_points"] == 20
    assert facts["layout"]["original_1ns_pilot_qualified"] is False
    assert facts["layout"]["posthoc_2ns_is_new_qualification"] is False


def test_pilot_limit_does_not_deny_the_subsequent_completed_full_grid():
    facts = load_facts()
    pilot, full = facts["layout"], facts["postlayout_pvt45"]
    assert pilot["scope"] == "original_five_condition_pilot"
    assert pilot["simulator"] == "ngspice-42"
    assert pilot["condition_count"] == 5
    assert pilot["pilot_full_45_condition_extracted_sweep_performed"] is False
    assert "full_45_condition_pex_performed" not in pilot
    assert full["scope"] == "subsequent_separately_declared_full_grid_study"
    assert full["simulator"] == "ngspice-47"
    assert full["full_45_condition_extracted_sweep_performed"] is True
    assert (full["conditions"], full["points_per_mode"]) == (45, 180)
    assert (full["primary_deadline_ns"], full["parallel_deadline_ns"]) == (2, 1)
    assert (full["rc_correct_2ns"], full["rc_correct_1ns"]) == (180, 156)
    assert full["old_five_condition_1ns_gate_reinterpreted"] is False
    limits = " ".join(facts["limits"])
    assert "that pilot did not perform a full 45-condition extracted sweep" in limits
    assert "ngspice-47 study completed 45 conditions and 180 RC points" in limits
    assert "Only the original ngspice-42 pilot's 2 ns result is post-hoc" in limits
    assert "prospectively declared 2 ns primary deadline" in limits


def test_published_fact_consumers_match_current_scoped_evidence():
    root = Path(__file__).resolve().parents[1]
    facts = load_facts()
    metadata = json.loads((root / "entry_metadata.json").read_bytes())
    pilot, full = metadata["layout_addendum"], metadata["postlayout_pvt45"]
    assert pilot["scope"] == facts["layout"]["scope"]
    assert pilot["simulator"] == facts["layout"]["simulator"]
    assert pilot["pilot_full_45_condition_extracted_sweep_performed"] is False
    assert "full_45_condition_pex_performed" not in pilot
    assert full["scope"] == facts["postlayout_pvt45"]["scope"]
    assert full["full_45_condition_extracted_sweep_performed"] is True
    assert (full["rc_correct_at_2ns"], full["rc_correct_at_1ns"]) == (180, 156)
    source_hash = hashlib.sha256((root / "presentation" / "release_facts.py").read_bytes()).hexdigest()
    for relative, source_key in (
        ("results/presentation/reviewer_guide_manifest.json", "source_sha256"),
        ("results/study/poster_manifest.json", "release_facts_source_sha256"),
    ):
        manifest = json.loads((root / relative).read_bytes())
        assert manifest["facts"] == facts
        assert manifest[source_key] == source_hash
