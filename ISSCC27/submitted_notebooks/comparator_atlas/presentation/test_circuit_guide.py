import pytest

from comparator_atlas.designs import circuit_text, get_design
from presentation.circuit_guide import check_topology, connections


def test_diagram_matches_the_actual_twenty_seven_device_topology():
    devices = connections(circuit_text(get_design("lvt_balanced_4b")))
    check_topology(devices)
    assert len(devices) == 27
    assert devices["Xinp"][:4] == ("xp", "vinp", "tail", "vss")
    assert devices["Xln"][:4] == ("qn", "qp", "xp", "vss")
    assert devices["Xsp3"][:4] == ("sp3", "tp3", "tail", "vss")


@pytest.mark.parametrize("terminal", range(5))
def test_changed_terminal_or_model_invalidates_the_annotated_guide(terminal):
    devices = connections(circuit_text(get_design("lvt_balanced_4b")))
    changed = list(devices["Xinp"])
    changed[terminal] = "incorrect"
    devices["Xinp"] = tuple(changed)
    with pytest.raises(ValueError, match="topology"):
        check_topology(devices)


def test_duplicate_instance_names_are_rejected():
    text = circuit_text(get_design("lvt_balanced_4b"))
    with pytest.raises(ValueError, match="duplicate"):
        connections(text + "\nXinp xp vinp tail vss sky130_fd_pr__nfet_01v8_lvt\n")
