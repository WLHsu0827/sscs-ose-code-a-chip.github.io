"""Draw the published topology without changing the circuit or its evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from comparator_atlas.designs import circuit_text, get_design
from entry_tools import verify_manifest

INK = "#15263f"
MUTED = "#63758b"
TEAL = "#008f83"
BLUE = "#3f679e"
ORANGE = "#bb7726"


def connections(text: str) -> dict[str, tuple[str, ...]]:
    devices = {}
    for line in text.splitlines():
        if not line.startswith("X"):
            continue
        fields = line.split()
        if len(fields) != 6 or fields[0] in devices:
            raise ValueError("Unexpected or duplicate transistor definition")
        devices[fields[0]] = tuple(fields[1:])
    return devices


def check_topology(devices: dict[str, tuple[str, ...]]) -> None:
    standard = "sky130_fd_pr__nfet_01v8"
    low_vt = "sky130_fd_pr__nfet_01v8_lvt"
    pfet = "sky130_fd_pr__pfet_01v8"
    expected = {
        "Xinp": ("xp", "vinp", "tail", "vss", low_vt),
        "Xinn": ("xn", "vinn", "tail", "vss", low_vt),
        "Xtail": ("tail", "clk", "vss", "vss", standard),
        "Xln": ("qn", "qp", "xp", "vss", standard),
        "Xlp": ("qp", "qn", "xn", "vss", standard),
        "Xpn": ("qn", "qp", "vdd", "vdd", pfet),
        "Xpp": ("qp", "qn", "vdd", "vdd", pfet),
    }
    for node in ("xp", "xn", "qp", "qn"):
        expected["Xr" + node] = (node, "clk", "vdd", "vdd", pfet)
    for side, drain, gate in (("p", "xp", "vinp"), ("n", "xn", "vinn")):
        for bit in range(4):
            source = f"s{side}{bit}"
            expected[f"Xt{side}{bit}"] = (drain, gate, source, "vss", low_vt)
            expected[f"Xs{side}{bit}"] = (source, f"t{side}{bit}", "tail", "vss", standard)
    if devices != expected:
        raise ValueError("The current electrical topology does not match this annotated diagram")


def wire(ax, xs, ys, color=INK):
    ax.plot(xs, ys, color=color, linewidth=1.6, solid_capstyle="round", zorder=1)


def node(ax, x, y, text, *, side="right"):
    ax.plot(x, y, "o", color=INK, markersize=4)
    ax.text(x + (0.15 if side == "right" else -0.15), y, text,
            ha="left" if side == "right" else "right", va="center",
            fontsize=12, weight="bold", color=INK)


def mos(ax, x, y, label, gate, *, kind="n", low_vt=False, size=""):
    color = TEAL if low_vt else ORANGE if kind == "p" else BLUE
    body = FancyBboxPatch((x - 0.58, y - 0.5), 1.16, 1,
                         boxstyle="round,pad=0.02,rounding_size=0.08",
                         edgecolor=color, facecolor="white", linewidth=1.5, zorder=2)
    ax.add_patch(body)
    ax.text(x, y + 0.13, label, ha="center", va="center", fontsize=10, color=INK, weight="bold")
    ax.text(x, y - 0.18, ("LVT " if low_vt else "") + ("PMOS" if kind == "p" else "NMOS"),
            ha="center", va="center", fontsize=8.3, color=color)
    wire(ax, [x, x], [y + 0.5, y + 0.8])
    wire(ax, [x, x], [y - 0.5, y - 0.8])
    ax.text(x + 0.10, y + 0.66, "S" if kind == "p" else "D", fontsize=8, color=MUTED)
    ax.text(x + 0.10, y - 0.76, "D" if kind == "p" else "S", fontsize=8, color=MUTED)
    wire(ax, [x - 1.04, x - 0.58], [y, y], color)
    if kind == "p":
        ax.add_patch(Circle((x - 0.68, y), 0.07, facecolor="white", edgecolor=color, linewidth=1.2, zorder=3))
    ax.text(x - 1.11, y, gate, ha="right", va="center", fontsize=10, color=color)
    if size:
        ax.text(x + 0.7, y, size, va="center", fontsize=8.5, color=MUTED)


def build() -> Path:
    verify_manifest("optimization_manifest.json")
    source = ROOT / "results" / "study" / "selected_circuit.spice"
    text = source.read_text(encoding="utf-8")
    design = get_design("lvt_balanced_4b")
    if text != circuit_text(design):
        raise ValueError("The published netlist and annotated sizing model differ")
    devices = connections(text)
    check_topology(devices)
    output = ROOT / "results" / "presentation"
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none",
                         "figure.facecolor": "white", "savefig.facecolor": "white", "pdf.fonttype": 42})
    figure = plt.figure(figsize=(16, 10))
    main = figure.add_axes([0.04, 0.21, 0.47, 0.66])
    reset = figure.add_axes([0.56, 0.61, 0.40, 0.23])
    trim = figure.add_axes([0.55, 0.19, 0.42, 0.37])
    for axis, limits in ((main, (0, 11, 0, 11)), (reset, (0, 11, 0, 4)), (trim, (0, 11, 0, 7))):
        axis.set(xlim=limits[:2], ylim=limits[2:])
        axis.axis("off")

    figure.text(0.04, 0.95, "Comparator Atlas | Circuit guide", fontsize=25, weight="bold", color=INK)
    figure.text(0.04, 0.915,
                "Published 27-transistor design: conventional StrongARM core + physical source-gated trim",
                fontsize=13, color=MUTED)
    main.set_title("A. Regenerative core (7 devices)", loc="left", fontsize=14, weight="bold", color=INK, pad=16)
    wire(main, [2.8, 8.2], [10.45, 10.45])
    node(main, 5.5, 10.45, "vdd")
    for x, is_positive in ((2.8, True), (8.2, False)):
        suffix = "n" if is_positive else "p"
        feedback = "qp" if is_positive else "qn"
        output_node = "qn" if is_positive else "qp"
        intermediate = "xp" if is_positive else "xn"
        input_node = "vinp" if is_positive else "vinn"
        wire(main, [x, x], [10.45, 9.8])
        mos(main, x, 9, "Xp" + suffix, feedback, kind="p",
            size=f"{design.latch_p_w:g} / 0.15")
        wire(main, [x, x], [8.2, 7.0])
        node(main, x, 7.6, output_node)
        mos(main, x, 6.2, "Xl" + suffix, feedback, size=f"{design.latch_n_w:g} / 0.15")
        wire(main, [x, x], [5.4, 4.4])
        node(main, x, 4.9, intermediate)
        mos(main, x, 3.6, "Xinp" if is_positive else "Xinn", input_node,
            low_vt=True, size=f"{design.input_w:g} / 0.15")
        wire(main, [x, x], [2.8, 2.35])
    wire(main, [2.8, 8.2], [2.35, 2.35])
    node(main, 5.5, 2.35, "tail")
    wire(main, [5.5, 5.5], [2.35, 2.0])
    mos(main, 5.5, 1.2, "Xtail", "clk", size=f"{design.tail_w:g} / 0.15")
    node(main, 5.5, 0.15, "vss")
    wire(main, [5.5, 5.5], [0.4, 0.15])
    main.text(0.0, 0.2, "Named qp/qn gate tags\nare cross-coupled feedback.", color=MUTED, fontsize=9)

    reset.set_title("B. Clocked reset devices (4 devices)", loc="left", fontsize=14, weight="bold", color=INK, pad=10)
    for y, device, drain in ((3.35, "Xrxp", "xp"), (2.5, "Xrxn", "xn"),
                              (1.65, "Xrqp", "qp"), (0.8, "Xrqn", "qn")):
        reset.text(0, y, "vdd", va="center", color=INK, fontsize=11)
        wire(reset, [0.8, 2.1], [y, y])
        patch = FancyBboxPatch((2.1, y - 0.29), 3.0, 0.58,
                              boxstyle="round,pad=0.02", facecolor="white", edgecolor=ORANGE, linewidth=1.4)
        reset.add_patch(patch)
        reset.text(3.6, y, f"{device}  PMOS  1 / 0.15", ha="center", va="center", fontsize=10, color=ORANGE)
        wire(reset, [5.1, 6.2], [y, y])
        reset.text(6.4, y, drain, va="center", fontsize=11, weight="bold", color=INK)
        reset.text(8.0, y, "gate = clk", va="center", fontsize=10, color=MUTED)

    trim.set_title("C. Expand one trim bit on each side (16 devices total)",
                   loc="left", fontsize=13, weight="bold", color=INK, pad=10)
    for x, side, drain, gate in ((3.0, "p", "xp", "vinp"), (8.4, "n", "xn", "vinn")):
        node(trim, x, 6.1, drain)
        wire(trim, [x, x], [6.1, 5.6])
        mos(trim, x, 4.8, f"Xt{side}[k]", gate, low_vt=True)
        node(trim, x, 3.7, f"s{side}[k]")
        wire(trim, [x, x], [4.0, 3.3])
        mos(trim, x, 2.5, f"Xs{side}[k]", f"t{side}[k]")
        wire(trim, [x, x], [1.7, 1.1])
        node(trim, x, 1.1, "tail")
    trim.text(0.0, 0.24, "Repeat k = 0, 1, 2, 3 on BOTH sides. No ideal offset subtraction.",
              fontsize=10, color=MUTED)

    figure.text(0.05, 0.151, "Polarity", color=TEAL, weight="bold", fontsize=12)
    figure.text(0.05, 0.126, "vinp > vinn discharges xp / qn first; a correct positive decision has qp high and qn low.",
                color=INK, fontsize=11)
    figure.text(0.56, 0.151, "Magnitude bits k         0          1          2          3", fontsize=11, color=INK)
    figure.text(0.56, 0.128, "Auxiliary LVT W/L     .42/1    .84/1   1.68/1   3.36/1", fontsize=10, color=TEAL)
    figure.text(0.56, 0.105, "Source switch W/L     1/.15    2/.15    4/.15    8/.15", fontsize=10, color=BLUE)
    figure.text(0.05, 0.075,
                "All W/L values are nominal micrometres. Every NMOS bulk = vss; every PMOS bulk = vdd (bulk wires omitted).",
                color=MUTED, fontsize=10)
    figure.text(0.05, 0.051,
                "Code 0 keeps all trim devices physically present. Sign + four magnitude bits select codes -15 through +15.",
                color=MUTED, fontsize=10)
    figure.text(0.05, 0.027,
                "Connectivity guide, not GDS or a performance claim. External 5 fF loads, ideal source drivers and controller are not drawn.",
                color=MUTED, fontsize=10)
    paths = [output / "circuit_guide.svg", output / "circuit_guide.pdf", output / "circuit_guide.png"]
    for path in paths:
        metadata = {"Creator": "Comparator Atlas"} if path.suffix == ".png" else (
            {"Creator": "Comparator Atlas", "Date": None} if path.suffix == ".svg"
            else {"Creator": "Comparator Atlas", "CreationDate": None, "ModDate": None}
        )
        figure.savefig(path, dpi=150, metadata=metadata)
    plt.close(figure)
    receipt = {
        "status": "topology_guide_checked_against_published_netlist",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "design": design.report(),
        "device_inventory": {name: dict(zip(("drain", "gate", "source", "bulk", "model"), pins))
                             for name, pins in devices.items()},
        "artifact_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "physical_layout_or_new_simulation_result": False,
        "published_entry_updated": False,
    }
    (output / "circuit_guide_manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Created a source-checked {len(devices)}-device guide in {output.relative_to(ROOT)}")
    return output


if __name__ == "__main__":
    build()
