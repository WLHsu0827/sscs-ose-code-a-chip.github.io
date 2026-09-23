"""Execute and fail-closed inspect actual SKY130 layout-preflight artifacts."""

from __future__ import annotations

import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
MODELS = {
    "sky130_fd_pr__nfet_01v8": "nmos",
    "sky130_fd_pr__nfet_01v8_lvt": "nmos",
    "sky130_fd_pr__pfet_01v8": "pmos",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def spice_number(token: str) -> float:
    match = re.fullmatch(r"([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)(meg|[tgkmunpf]?)",
                         token.lower())
    require(match is not None, f"Unsupported SPICE number: {token!r}")
    scales = {"": 1, "t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3,
              "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15}
    result = float(match[1]) * scales[match[2]]
    require(math.isfinite(result), f"Nonfinite SPICE number: {token}")
    return result


def read_spice(path: Path) -> dict:
    logical = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("+"):
            require(bool(logical), "SPICE continuation without an initial line")
            logical[-1] += " " + line[1:]
        elif line and not line.startswith("*"):
            logical.append(line)
    result = {"devices": [], "resistors": [], "capacitors": [], "ports": []}
    for line in logical:
        tokens = line.split()
        first = tokens[0].lower()
        require(not (first in (".scale", ".option", ".options") and
                     "scale" in line.lower()), "Unexpected geometry scale directive")
        if first == ".subckt":
            require(not result["ports"], "Expected one flat top-level subcircuit")
            result["ports"] = tokens[2:]
            result["cell"] = tokens[1]
        elif first.startswith("x"):
            require(len(tokens) >= 8 and tokens[5] in MODELS,
                    f"Unexpected/non-four-terminal primitive: {line}")
            properties = dict(re.findall(r"(\w+)\s*=\s*([^\s]+)", " ".join(tokens[6:])))
            require({"w", "l"} <= properties.keys(), f"Missing geometry: {line}")
            result["devices"].append({
                "name": tokens[0], "pins": tokens[1:5], "model": tokens[5],
                "w_um": float(properties["w"]), "l_um": float(properties["l"]),
                "m": float(properties.get("m", "1")),
            })
        elif first.startswith(("r", "c")):
            require(len(tokens) == 4, f"Unexpected passive element: {line}")
            item = {"name": tokens[0], "nodes": tokens[1:3],
                    "value": spice_number(tokens[3])}
            result["resistors" if first.startswith("r") else "capacitors"].append(item)
        elif not first.startswith("."):
            raise AssertionError(f"Unrecognized SPICE element: {line}")
    require(result["ports"], f"No subcircuit ports in {path}")
    return result


def inspect_gds(path: Path) -> dict:
    data = path.read_bytes()
    offset, layer, datatype, element = 0, None, None, None
    layers = collections.Counter()
    end_library = False
    points = []
    while offset < len(data):
        require(offset + 4 <= len(data), "Truncated GDS record header")
        size, kind, _ = struct.unpack_from(">HBB", data, offset)
        require(size >= 4 and size % 2 == 0 and offset + size <= len(data),
                "Invalid/truncated GDS record")
        payload = data[offset + 4:offset + size]
        if kind in (8, 9):  # Boundary or path, not text/labels.
            element, layer, datatype, points = kind, None, None, []
        elif kind in (10, 11, 12):
            element = None
        elif kind == 13:
            layer = struct.unpack(">h", payload)[0]
        elif kind == 14:
            datatype = struct.unpack(">h", payload)[0]
        elif kind == 16 and element in (8, 9):
            require(len(payload) % 8 == 0, "Invalid GDS coordinates")
            points = list(struct.iter_unpack(">ii", payload))
        elif kind == 17 and element in (8, 9):
            require(layer is not None and datatype is not None and len(points) >= 2,
                    "GDS geometry has no layer/coordinates")
            require(len(set(points)) > 1, "Degenerate GDS geometry")
            layers[f"{layer}/{datatype}"] += 1
            element = None
        elif kind == 4:
            end_library = True
        offset += size
    require(end_library and layers, "Empty or incomplete GDS")
    return {"bytes": len(data), "geometry_by_layer": dict(sorted(layers.items()))}


def inspect_mag(path: Path) -> dict:
    layers = collections.Counter()
    labels = set()
    current = None
    for line in path.read_text().splitlines():
        if line.startswith("<< "):
            current = line[3:-3]
        elif line.startswith("rect "):
            x1, y1, x2, y2 = map(int, line.split()[1:])
            require(x2 > x1 and y2 > y1, "Degenerate Magic rectangle")
            layers[current] += 1
        elif line.startswith(("rlabel ", "flabel ")):
            labels.add(line.split()[-1])
    require(layers, "No painted Magic geometry")
    return {"rectangles_by_layer": dict(layers), "labels": sorted(labels)}


def independent_reference(spec: dict, mutation: str | None = None) -> str:
    pins, width, model = ["D", "G", "S", "B"], spec["w_um"], spec["model"]
    if mutation == "connection":
        pins[1] = "S"
    elif mutation == "bulk":
        pins[3] = "S"
    elif mutation == "width":
        width *= 2
    elif mutation == "flavor":
        require(model.endswith("_lvt"), "Flavor control must start with LVT")
        model = "sky130_fd_pr__nfet_01v8"
    elif mutation is not None:
        raise ValueError(f"Unknown reference mutation: {mutation}")
    return (f"* Independently generated from devices.json; geometry is in micrometres.\n"
            f".subckt {spec['cell']} D G S B\n"
            f"Xreference {' '.join(pins)} {model} w={width} l={spec['l_um']} m=1\n"
            f".ends {spec['cell']}\n")


def check_device(net: dict, spec: dict, connectivity: bool = True) -> dict:
    require(net["ports"] == ["D", "G", "S", "B"], f"Wrong port order: {net['ports']}")
    require(len(net["devices"]) == 1, f"Expected one real transistor: {net['devices']}")
    device = net["devices"][0]
    for key in ("model", "w_um", "l_um", "m"):
        expected = spec.get(key, 1)
        actual = device[key]
        equal = actual == expected if key == "model" else math.isclose(
            actual, expected, rel_tol=1e-6, abs_tol=1e-9)
        require(equal, f"{key}: expected {expected}, extracted {actual}")
    if connectivity:
        d, g, s, b = device["pins"]
        require(g == "G" and b == "B" and {d, s} == {"D", "S"},
                f"Wrong gate/bulk/source/drain connectivity: {device['pins']}")
        require(not net["capacitors"] and not net["resistors"],
                "LVS output unexpectedly contains parasitics")
    return device


def rc_metrics(net: dict) -> dict:
    require(len(net["resistors"]) >= 2 and net["capacitors"],
            "Missing actual distributed R or extracted C")
    for item in net["resistors"] + net["capacitors"]:
        require(item["value"] > 0, f"Nonpositive parasitic: {item}")
    reached = {"D"}
    while True:
        expanded = reached | {
            node for resistor in net["resistors"]
            if reached.intersection(resistor["nodes"]) for node in resistor["nodes"]
        }
        if expanded == reached:
            break
        reached = expanded
    drain_r = [r for r in net["resistors"] if set(r["nodes"]) <= reached]
    require(len(drain_r) >= 2, "External D does not reach a distributed resistance network")
    transistor_pins = {pin for device in net["devices"] for pin in
                       (device["pins"][0], device["pins"][2])}
    require(bool(reached & transistor_pins), "Routed D network does not reach a transistor")
    require(bool(reached - set(net["ports"])), "No internal distributed RC nodes")
    drain_c = [c for c in net["capacitors"] if reached.intersection(c["nodes"])]
    require(drain_c, "No capacitance on the routed drain network")
    return {
        "resistor_count": len(net["resistors"]),
        "capacitor_count": len(net["capacitors"]),
        "resistance_min_ohm": min(r["value"] for r in net["resistors"]),
        "resistance_max_ohm": max(r["value"] for r in net["resistors"]),
        "capacitance_min_f": min(c["value"] for c in net["capacitors"]),
        "capacitance_max_f": max(c["value"] for c in net["capacitors"]),
        "drain_resistor_count": len(drain_r),
        "drain_resistance_sum_ohm": sum(r["value"] for r in drain_r),
        "drain_capacitance_sum_f": sum(c["value"] for c in drain_c),
        "total_capacitance_f": sum(c["value"] for c in net["capacitors"]),
        "resistors": net["resistors"], "capacitors": net["capacitors"],
    }


def run_logged(command: list[str], path: Path, out: Path, env: dict,
               input_text: str | None = None) -> str:
    with path.open("w") as log:
        log.write("$ " + " ".join(command) + "\n")
        log.flush()
        result = subprocess.run(command, input=input_text, text=True, cwd=out,
                                env=env, stdout=log, stderr=subprocess.STDOUT, timeout=90)
    text = path.read_text()
    require(result.returncode == 0, f"Tool exited {result.returncode}; see {path.name}")
    require(not re.search(r"PREFLIGHT_\w+_ERROR|Error .*ignoring|errors reading the setup",
                          text, re.IGNORECASE), f"Tool/setup error in {path.name}")
    return text


def run_magic(out: Path, spec: dict, mode: str, route_length: int = 0) -> None:
    env = dict(os.environ, PREFLIGHT_CELL=spec["cell"], PREFLIGHT_MODE=mode,
               PREFLIGHT_MODEL=spec["model"], PREFLIGHT_WIDTH=str(spec["w_um"]),
               PREFLIGHT_LENGTH=str(spec["l_um"]), PREFLIGHT_ROUTE_LENGTH=str(route_length))
    rc = Path(env["PDK_ROOT"]) / "sky130A/libs.tech/magic/sky130A.magicrc"
    script = HERE / "preflight.tcl"
    text = run_logged(["magic", "-dnull", "-noconsole", "-rcfile", str(rc)],
                      out / "logs" / f"{spec['cell']}-magic.log", out, env,
                      f"source {{{script.as_posix()}}}\n")
    require(f"PREFLIGHT_MAGIC_COMPLETE {spec['cell']}" in text, "Magic did not finish")


def check_layout(out: Path, cell: str, negative: bool = False) -> dict:
    mag, gds = inspect_mag(out / f"{cell}.mag"), inspect_gds(out / f"{cell}.gds")
    report = (out / f"{cell}.drc.txt").read_text()
    match = re.search(r"^count: (\d+)$", report, re.MULTILINE)
    require(match is not None, "Missing DRC result")
    count = int(match[1])
    require("technology: sky130A" in report and "drc(full)" in report,
            "Wrong/inactive DRC technology or style")
    require(count > 0 if negative else count == 0, f"DRC count {count}: {report}")
    if not negative:
        require({"D", "G", "S", "B"} <= set(mag["labels"]), "Missing four terminal labels")
        require({"65/20", "66/20", "68/20"} <= gds["geometry_by_layer"].keys(),
                "GDS lacks active, poly, or metal1")
    return {"drc_count": count, "drc_style": "drc(full)", "mag": mag, "gds": gds}


def run_lvs(out: Path, spec: dict, mutation: str | None = None) -> dict:
    cell = spec["cell"]
    suffix = mutation or "positive"
    reference = out / f"{cell}-{suffix}.reference.spice"
    reference.write_text(independent_reference(spec, mutation))
    env = dict(os.environ, PREFLIGHT_CELL=cell,
               PREFLIGHT_LAYOUT=str(out / f"{cell}.lvs.spice"),
               PREFLIGHT_REFERENCE=str(reference), PREFLIGHT_SETUP=str(HERE / "strict_setup.tcl"),
               PREFLIGHT_LVS_REPORT=str(out / f"{cell}-{suffix}.lvs.txt"))
    text = run_logged(["netgen", "-batch", "source", str(HERE / "lvs.tcl")],
                      out / "logs" / f"{cell}-{suffix}-netgen.log", out, env)
    require(text.count("PREFLIGHT_DEVICE_CLASS") >= 2, "Primitive classes were not asserted")
    marker = re.search(r"PREFLIGHT_LVS_RESULT ([01]) (-?\d+)", text)
    require(marker is not None, "Missing explicit Netgen comparison result")
    equivalent, unique = map(int, marker.groups())
    passed = equivalent == 1 and unique == 1
    require(passed if mutation is None else not passed,
            f"LVS {'positive' if mutation is None else mutation} control had wrong outcome")
    require(unique != -1, "LVS was reduced to a black box")
    return {"equivalent": equivalent, "unique": unique, "expected_match": mutation is None}


def main(out: Path) -> int:
    out = out.resolve()
    (out / "logs").mkdir(exist_ok=True)
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    context = {
        "scope": "toolchain preflight only; not a comparator layout",
        "commit": os.environ.get("GITHUB_SHA"),
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}"
        if repository and run_id else None,
        "geometry_units": "micrometres; Magic extract style ngspice",
        "drc_style": "sky130A drc(full), Euclidean on",
        "pex_settings": {"threshold_milliohm": 0, "minresist_milliohm": 0,
                         "mindelay_ps": 0, "cthresh_ff": 0},
    }
    (out / "run-context.json").write_text(json.dumps(context, indent=2) + "\n")
    specs = json.loads((HERE / "devices.json").read_text())
    results = []

    def record(name, operation):
        try:
            detail = operation()
        except (AssertionError, OSError, ValueError, KeyError, subprocess.TimeoutExpired):
            detail = {"error": traceback.format_exc()}
            status = "FAIL"
        else:
            status = "PASS"
        print(f"{status}: {name}", flush=True)
        if status == "FAIL":
            print(detail["error"], file=sys.stderr, flush=True)
        results.append({"check": name, "status": status, "detail": detail})
        (out / "capabilities.json").write_text(json.dumps(results, indent=2) + "\n")
        return detail if status == "PASS" else None

    for spec in specs:
        cell = spec["cell"]
        generated = record(f"{cell}: generate/extract",
                           lambda s=spec: (run_magic(out, s, "device"), {"generated": True})[1])
        if generated is None:
            continue
        record(f"{cell}: geometry/DRC", lambda c=cell: check_layout(out, c))
        record(f"{cell}: transistor/model/W/L/body", lambda s=spec:
               check_device(read_spice(out / f"{s['cell']}.lvs.spice"), s))
        record(f"{cell}: Netgen LVS", lambda s=spec: run_lvs(out, s))

    negative_spec = next(spec for spec in specs if spec["cell"] == "n_lvt042_l4")
    for mutation in ("connection", "bulk", "width", "flavor"):
        record(f"negative LVS: {mutation}", lambda m=mutation: run_lvs(out, negative_spec, m))

    spacing_spec = dict(specs[0], cell="spacing_bad")
    record("negative DRC: 0.07um metal1 spacing", lambda: (
        run_magic(out, spacing_spec, "spacing"), check_layout(out, "spacing_bad", True))[1])

    routes = {}
    for cell, length in (("route_short", 20), ("route_long", 200)):
        spec = dict(specs[0], cell=cell)

        def make_route(s=spec, length=length):
            shutil.copyfile(out / "n_input3.mag", out / f"{s['cell']}.mag")
            run_magic(out, s, "route", length)
            return {"route_horizontal_leg_um": length, "route_width_um": 0.36}

        generated = record(f"{cell}: routed extraction", make_route)
        if generated is None:
            continue
        record(f"{cell}: geometry/DRC", lambda c=cell: check_layout(out, c))
        record(f"{cell}: connectivity LVS", lambda s=spec: run_lvs(out, s))

        def check_pex(s=spec):
            c_only = read_spice(out / f"{s['cell']}.c.spice")
            rc = read_spice(out / f"{s['cell']}.rc.spice")
            check_device(c_only, s, connectivity=False)
            check_device(rc, s, connectivity=False)
            require(c_only["capacitors"] and not c_only["resistors"],
                    "C-only result missing C or mixed with R")
            require((out / f"{s['cell']}.res.ext").stat().st_size > 0,
                    "No real extresist intermediate")
            metrics = rc_metrics(rc)
            metrics["c_only_capacitor_count"] = len(c_only["capacitors"])
            return metrics

        metrics = record(f"{cell}: actual distributed RC", check_pex)
        if metrics is not None:
            routes[cell] = metrics

    def compare_routes():
        require(len(routes) == 2, "Both routed probes must have valid RC results")
        short, long = routes["route_short"], routes["route_long"]
        rr = long["drain_resistance_sum_ohm"] / short["drain_resistance_sum_ohm"]
        cr = long["drain_capacitance_sum_f"] / short["drain_capacitance_sum_f"]
        require(rr > 3 and cr > 3, f"Long route did not increase physical RC: R={rr}, C={cr}")
        return {"long_to_short_drain_r_ratio": rr, "long_to_short_drain_c_ratio": cr}

    record("layout-derived RC length dependence", compare_routes)
    manifest = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "artifact-sha256.json":
            manifest[str(path.relative_to(out))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "artifact-sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [result["check"] for result in results if result["status"] == "FAIL"]
    print(json.dumps({"passed": len(results) - len(failed), "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
