"""Small offline controls; these are not substitutes for real tool execution."""

from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

import contract
import layout
import simulate


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def netlist(self, mutation=None):
        path = self.root / "reference.spice"
        path.write_text(contract.independent_reference(mutation))
        return contract.read_spice(path)

    def test_frozen_source_and_independent_table(self):
        audit = contract.audit_source()
        self.assertEqual(audit["device_count"], 27)
        self.assertEqual(sum(audit["model_counts"].values()), 27)
        self.assertEqual(len(audit["ordered_ports"]), 15)
        self.assertEqual(audit["published_blob_sha256"], audit["worktree_bytes_sha256"])
        self.assertAlmostEqual(audit["source_junction_parameters"]["Xinp"]["ad"], 0.87)

    def test_source_bytes_are_not_silently_canonicalized(self):
        source = contract.ENTRY / "results" / "study" / "selected_circuit.spice"
        changed = self.root / "changed.spice"
        changed.write_bytes(source.read_bytes().replace(b"\r\n", b"\n"))
        with self.assertRaisesRegex(AssertionError, "immutable Git blob"):
            contract.audit_source(changed)

    def test_nominal_arithmetic_is_bounded(self):
        self.assertEqual(contract.nominal_number("{3*(1+pair_skew)}"), 3)
        self.assertEqual(contract.nominal_number("{3*(1-pair_skew)}"), 3)
        for expression in ("f()", "__import__('os')", "other", "1e999", "2**100"):
            with self.subTest(expression=expression), self.assertRaises(AssertionError):
                contract.nominal_number(expression)

    def test_independent_positive(self):
        self.assertEqual(contract.check_netlist(self.netlist())["device_count"], 27)

    def test_all_independent_negatives(self):
        for mutation in ("connection", "bulk", "width", "flavor"):
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                contract.check_netlist(self.netlist(mutation))

    def test_length_multiplicity_count_and_port_controls(self):
        for change in ("length", "multiplicity", "count", "ports"):
            net = self.netlist()
            if change == "length":
                net["devices"][0]["l_um"] *= 2
            elif change == "multiplicity":
                net["devices"][0]["m"] = 2
            elif change == "count":
                net["devices"].pop()
            else:
                net["ports"][0:2] = net["ports"][1::-1]
            with self.subTest(change=change), self.assertRaises(AssertionError):
                contract.check_netlist(net)

    def test_source_drain_symmetry_is_allowed_not_gate_bulk(self):
        net = self.netlist()
        pins = net["devices"][0]["pins"]
        pins[0], pins[2] = pins[2], pins[0]
        contract.check_netlist(net)
        pins[1], pins[3] = pins[3], pins[1]
        with self.assertRaises(AssertionError):
            contract.check_netlist(net)

    def test_long_actual_resistor_chain_contracts_iteratively(self):
        net = self.netlist()
        nodes = ["xp", *[f"xp.n{i}" for i in range(5000)]]
        net["resistors"] = [
            {"name": f"R{i}", "nodes": [a, b], "value": 0.1, "annotation": ""}
            for i, (a, b) in enumerate(zip(nodes, nodes[1:]))
        ]
        net["devices"][0]["pins"][0] = nodes[-1]
        net["capacitors"] = [{"name": "C0", "nodes": [nodes[-1], "vss"],
                              "value": 1e-15, "annotation": "FLOATING"}]
        report = contract.check_netlist(net, rc=True)
        self.assertEqual(report["floating_annotations_retained"][0]["dc_anchors"], ["xp", "vss"])
        with self.assertRaisesRegex(AssertionError, "outside the RC"):
            contract.check_netlist(net)

    def test_short_unanchored_nonfinite_and_duplicate_controls(self):
        for change in ("short", "unanchored", "nonfinite", "duplicate"):
            net = self.netlist()
            if change == "short":
                net["resistors"] = [{"name": "R1", "nodes": ["xp", "xn"],
                                     "value": 1, "annotation": ""}]
            elif change == "unanchored":
                net["devices"][0]["pins"][0] = "orphan"
            elif change == "nonfinite":
                net["capacitors"] = [{"name": "C1", "nodes": ["xp", "vss"],
                                      "value": float("inf"), "annotation": ""}]
            else:
                net["devices"][1]["name"] = net["devices"][0]["name"].upper()
            with self.subTest(change=change), self.assertRaises(AssertionError):
                contract.check_netlist(net, rc=True)

    def test_real_gds_bounds_units_and_nonempty_geometry(self):
        def record(kind, payload=b""):
            return struct.pack(">HBB", len(payload)+4, kind, 0) + payload

        # GDS base-16 encoding: 1e-9 metres per database unit.
        value, exponent = 1e-9, 64
        while value < 1/16:
            value *= 16
            exponent -= 1
        real = bytes([exponent]) + round(value * 2**56).to_bytes(7)
        data = b"".join((
            record(3, real+real), record(8),
            record(16, b"".join(struct.pack(">ii", x, y) for x, y in (
                (-1000, -2000), (3000, -2000), (3000, 4000), (-1000, -2000)))),
            record(17), record(4),
        ))
        path = self.root / "geometry.gds"
        path.write_bytes(data)
        bounds = contract.gds_bounds(path)
        self.assertAlmostEqual(bounds["width_um"], 4)
        self.assertAlmostEqual(bounds["height_um"], 6)
        self.assertAlmostEqual(bounds["bbox_area_um2"], 24)
        path.write_bytes(record(3, real+real) + record(10))
        with self.assertRaisesRegex(AssertionError, "hierarchical"):
            contract.gds_bounds(path)
        path.write_bytes(data+b"\x00")
        with self.assertRaisesRegex(AssertionError, "header"):
            contract.gds_bounds(path)


class RoutingTests(unittest.TestCase):
    def test_routed_gate_area_includes_actual_via1_metal1_residue(self):
        mag = {
            "label_positions": {"G": [30, 10, 30, 10]},
            "rectangles": {
                "metal1": [[0, 0, 60, 20], [0, 80, 60, 100]],
                "via1": [[0, 20, 60, 80]],
                "viali": [[20, 5, 40, 25]],
            },
        }
        self.assertAlmostEqual(layout.gate_m1_area_um2(mag, "G"), 0.15)
        self.assertEqual(len(mag["rectangles"]["metal1"]), 2)

    def test_other_metals_and_disconnected_contact_area_do_not_count(self):
        for extra in ("via1", "via2", "metal2"):
            mag = {
                "label_positions": {"G": [30, 10, 30, 10]},
                "rectangles": {
                    "metal1": [[0, 0, 60, 20]],
                    extra: [[60, 20, 1000, 1000]] if extra == "via1"
                    else [[0, 0, 1000, 1000]],
                },
            }
            with self.subTest(layer=extra):
                self.assertAlmostEqual(layout.gate_m1_area_um2(mag, "G"), 0.03)
                self.assertLess(layout.gate_m1_area_um2(mag, "G"), 0.10)

    def test_reflection_transforms_actual_rectangles(self):
        self.assertEqual(layout.transform_rect([10, 20, 30, 40],
                         {"origin_um": [4.8, 0], "reflect_x": -1}),
                         [930, 20, 950, 40])

    def test_all_devices_have_unique_lanes_and_real_net_routes(self):
        placed = layout.placements()
        for value in placed.values():
            origin, reflection = value["origin_um"][0], value["reflect_x"]
            value["pins_um"] = {
                pin: [origin+reflection*x, y]
                for pin, x, y in (("D", -0.26, 0), ("G", 0, 2),
                                  ("S", 0.26, 0), ("B", -1.5, -2))
            }
        with tempfile.TemporaryDirectory() as directory:
            report = layout.make_routes(Path(directory), placed)
        routes = report["terminal_routes"]
        self.assertEqual(len(routes), 108)
        self.assertEqual(len({round(r["via1_um"][0], 6) for r in routes}), 108)
        self.assertEqual(set(report["buses"]), set(contract.NETS))
        self.assertTrue(all(r["metal2_centerline_um"] > 0 for r in routes))


class NumericalTests(unittest.TestCase):
    def history(self, energies):
        result = []
        steps = [10, 5, *contract.PROTOCOL["numerics"]["further_max_steps_ps"]]
        for index, (step, energy) in enumerate(zip(steps, energies)):
            result.append({
                "run_id": f"run{index}", "max_step_ps": step,
                "physical_identity": {"point": {"pair_skew": 0, "differential_v": 0.003},
                                      "mode": "rc", "netlist_sha256": "fixed-layout"},
                "measurements": [
                    {"deadline_ns": deadline, "decision": 1, "outcome": "correct",
                     "decision_time_ns": 0.1, "core_energy_fj": energy, "reset_ok": True}
                    for deadline in contract.PROTOCOL["numerics"]["reporting_deadlines_ns"]
                ],
            })
        return result

    def test_initial_agreement(self):
        self.assertTrue(contract.refinement_state(self.history([100, 100.2]))["qualified"])

    def test_sensitive_requires_two_halvings_and_fine_endpoint(self):
        rows = self.history([100, 105, 105, 105, 105])
        self.assertFalse(contract.refinement_state(rows[:4])["qualified"])
        state = contract.refinement_state(rows)
        self.assertTrue(state["qualified"])
        self.assertTrue(state["ever_sensitive"])
        self.assertEqual(state["finest_max_step_ps"], 0.625)

    def test_later_contradiction_is_never_erased(self):
        rows = self.history([100, 100, 100, 110, 110, 110])
        self.assertFalse(contract.refinement_state(rows[:5])["qualified"])
        state = contract.refinement_state(rows)
        self.assertTrue(state["qualified"])
        self.assertFalse(state["initially_sensitive"])
        self.assertTrue(state["ever_sensitive"])
        self.assertFalse(state["comparisons"][2]["passed"])

    def test_no_retuning_restart_duplicate_or_incomplete_deadlines(self):
        for change in ("retune", "restart", "duplicate", "deadline", "reset", "nan"):
            rows = self.history([100, 100])
            if change == "retune":
                rows[-1]["physical_identity"]["point"]["pair_skew"] = 0.04
            elif change == "restart":
                rows[-1]["max_step_ps"] = 10
            elif change == "duplicate":
                rows[-1]["run_id"] = rows[0]["run_id"]
            elif change == "deadline":
                rows[-1]["measurements"][0]["deadline_ns"] = 1
            elif change == "reset":
                rows[-1]["measurements"][0]["reset_ok"] = False
            else:
                rows[-1]["measurements"][0]["core_energy_fj"] = float("nan")
            with self.subTest(change=change), self.assertRaises(AssertionError):
                contract.refinement_state(rows)


class SimulationContractTests(unittest.TestCase):
    def point(self):
        return SimpleNamespace(
            pair_skew=0, trim_code=0, design_name="lvt_balanced_4b", load_ff=5,
            common_mode_ratio=0.5, source_resistance_ohm=0, sample_cap_ff=0,
            previous_differential_v=None, corner="tt", vdd_v=1.8, temperature_c=27,
            differential_v=0.003, max_step_ps=5,
        )

    def geometry(self):
        return "\n".join(
            f'NOMINAL27_GEOMETRY {d["name"]} {d["model"]} {d["w_um"]*1e-6} {d["l_um"]*1e-6}'
            for d in contract.DEVICES
        )

    def test_deck_preserves_native_parasitics_and_scales_exactly_once(self):
        native = contract.independent_reference().replace(
            ".ends atlas", "Rnative xp xp.n0 1.234\nCnative xp.n0 vss 0.09p $ **FLOATING\n.ends atlas")
        deck = simulate.make_deck("rc", self.point(), native, Path("private-models"), contract.DEVICES)
        self.assertIn(native.rstrip(), deck)
        self.assertEqual(deck.count("scale=1u"), 1)
        self.assertIn("Xdut vinp vinn clk vdd 0 qp qn tp0 tp1 tp2 tp3 tn0 tn1 tn2 tn3 atlas\n", deck)
        self.assertIn("tran 5p 30n 19n 5p", deck)
        self.assertIn("v(xdut.xp) v(xdut.xn) i(vdd) v(vinp) v(vinn)", deck)
        self.assertEqual(deck.count("echo NOMINAL27_GEOMETRY "), 27)
        self.assertIn("@m.xdut.xinp.msky130_fd_pr__nfet_01v8_lvt[w]", deck)

    def test_nominal_source_and_no_retuning_or_double_scale(self):
        native = (contract.ENTRY / "results" / "study" / "selected_circuit.spice").read_text()
        deck = simulate.make_deck("schematic", self.point(), native, Path("models"), contract.DEVICES)
        self.assertIn("atlas pair_skew=0\n", deck)
        for setting, value in (("pair_skew", 0.04), ("trim_code", 1), ("load_ff", 10)):
            point = self.point()
            setattr(point, setting, value)
            with self.subTest(setting=setting), self.assertRaises(AssertionError):
                simulate.make_deck("schematic", point, native, Path("models"), contract.DEVICES)
        with self.assertRaises(AssertionError):
            simulate.make_deck("rc", self.point(), ".option scale=1u\n"+native, Path("models"),
                               contract.DEVICES)

    def test_actual_geometry_parser_requires_all_instances_and_si_units(self):
        text = self.geometry()
        self.assertEqual(simulate.audit_geometry(text, contract.DEVICES)["observed_device_count"], 27)
        for bad in (text.replace("3e-06", "3e-12", 1), "\n".join(text.splitlines()[:-1]),
                    text.replace("nfet_01v8_lvt", "nfet_01v8", 1),
                    text.replace("3e-06", "nan", 1)):
            with self.subTest(bad=bad[:110]), self.assertRaises(AssertionError):
                simulate.audit_geometry(bad, contract.DEVICES)

    def test_actual_geometry_commands_are_instance_specific(self):
        commands = simulate.geometry_commands(contract.DEVICES)
        queries = [line for line in commands if line.startswith("let ")]
        self.assertEqual(len(queries), 54)
        self.assertEqual(len(set(queries)), 54)
        self.assertTrue(any("msky130_fd_pr__pfet_01v8[l]" in line for line in queries))


if __name__ == "__main__":
    unittest.main()
