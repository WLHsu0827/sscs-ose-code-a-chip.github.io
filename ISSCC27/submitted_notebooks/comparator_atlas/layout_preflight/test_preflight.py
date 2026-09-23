import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("preflight", Path(__file__).with_name("preflight.py"))
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

DEVICE = {"cell": "test", "model": "sky130_fd_pr__nfet_01v8_lvt", "w_um": 0.42, "l_um": 4}


class EvidenceChecks(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.spice"
            path.write_text(text)
            return preflight.read_spice(path)

    def test_independent_reference_and_units(self):
        net = self.parse(preflight.independent_reference(DEVICE))
        self.assertEqual(preflight.check_device(net, DEVICE)["l_um"], 4)
        self.assertAlmostEqual(preflight.spice_number("0.0123f"), 1.23e-17)
        self.assertEqual(preflight.spice_number("1e2"), 100)

    def test_mutations_are_real_and_independent(self):
        for mutation in ("connection", "bulk", "width", "flavor"):
            with self.subTest(mutation=mutation):
                net = self.parse(preflight.independent_reference(DEVICE, mutation))
                with self.assertRaises(AssertionError):
                    preflight.check_device(net, DEVICE)

    def test_empty_lvs_cannot_pass(self):
        net = self.parse(".subckt test D G S B\n.ends\n")
        with self.assertRaises(AssertionError):
            preflight.check_device(net, DEVICE)

    def test_scale_directive_rejected(self):
        with self.assertRaises(AssertionError):
            self.parse(".option scale=1e-6\n" + preflight.independent_reference(DEVICE))

    def test_c_only_is_not_rc(self):
        net = self.parse(preflight.independent_reference(DEVICE))
        net["capacitors"] = [{"name": "C1", "nodes": ["D", "B"], "value": 1e-15}]
        with self.assertRaises(AssertionError):
            preflight.rc_metrics(net)

    def test_rc_must_reach_the_transistor(self):
        net = self.parse(preflight.independent_reference(DEVICE))
        net["devices"][0]["pins"][0] = "device_d"
        net["resistors"] = [
            {"name": "R1", "nodes": ["D", "internal"], "value": 10},
            {"name": "R2", "nodes": ["internal", "isolated"], "value": 20},
        ]
        net["capacitors"] = [{"name": "C1", "nodes": ["internal", "B"], "value": 1e-15}]
        with self.assertRaises(AssertionError):
            preflight.rc_metrics(net)
        net["resistors"][1]["nodes"][1] = "device_d"
        self.assertEqual(preflight.rc_metrics(net)["drain_resistance_sum_ohm"], 30)

    def test_empty_geometry_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty"
            path.write_text("magic\ntech sky130A\n<< end >>\n")
            with self.assertRaises(AssertionError):
                preflight.inspect_mag(path)
            path.write_bytes(b"\x00\x04\x04\x00")
            with self.assertRaises(AssertionError):
                preflight.inspect_gds(path)


if __name__ == "__main__":
    unittest.main()
