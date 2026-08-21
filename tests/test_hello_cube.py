import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
# The harness must be checked out as a sibling of this repo, or named via IMG2_HARNESS_DIR.
HARNESS_DIR = Path(os.environ.get("IMG2_HARNESS_DIR", PLUGIN_DIR.parent / "img2-harness")).resolve()

EMIT = PLUGIN_DIR / "tools" / "emit_cube.py"
GATE = PLUGIN_DIR / "tools" / "gate_cube_structure.py"
FIXTURE_BYTES = b"\x89PNG\r\n\x1a\nhello-cube deterministic fixture" * 7


class HelloCubeTest(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp(prefix="hello-cube-test-"))
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        self.home = base / "img2home"
        self.home.mkdir()
        (self.home / "harness").symlink_to(HARNESS_DIR)
        self.workspace = base / "workspace"
        self.workspace.mkdir()
        self.image = base / "fixture.png"
        self.image.write_bytes(FIXTURE_BYTES)
        self.env = {**os.environ, "IMG2_HOME": str(self.home)}
        self.env.pop("IMG2THREEJS_HOME", None)

    def run_tool(self, script, *args):
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True, text=True, env=self.env, cwd=self.workspace,
        )

    def emit(self):
        proc = self.run_tool(EMIT, "--image", str(self.image), "--workspace", str(self.workspace))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc

    def artifact(self):
        return self.workspace / ".img2" / "artifacts" / "hello-cube" / "cube.js"

    def test_emit_is_deterministic(self):
        self.emit()
        first = self.artifact().read_bytes()
        self.emit()
        self.assertEqual(first, self.artifact().read_bytes())
        text = first.decode("utf-8")
        self.assertIn("new THREE.BoxGeometry(", text)
        self.assertIn("new THREE.MeshStandardMaterial(", text)

    def test_emit_derivation_and_state(self):
        self.emit()
        expected_hex = hashlib.sha256(FIXTURE_BYTES).digest()[:3].hex()
        text = self.artifact().read_text(encoding="utf-8")
        self.assertIn("0x" + expected_hex, text)
        state = json.loads((self.workspace / ".img2" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["version"], 1)
        sub = state["plugins"]["hello-cube"]
        self.assertEqual(sub["colorHex"], "#" + expected_hex)
        self.assertEqual(sub["lastImage"], str(self.image.resolve()))
        self.assertGreaterEqual(sub["size"], 0.5)
        self.assertLessEqual(sub["size"], 2.0)
        size = sub["size"]
        self.assertIn("new THREE.BoxGeometry(%s, %s, %s)" % (size, size, size), text)

    def test_gate_passes_on_good_artifact(self):
        self.emit()
        proc = self.run_tool(GATE, "--workspace", str(self.workspace))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["kind"], "img2.gate-verdict")
        self.assertEqual(doc["version"], 1)
        self.assertEqual(doc["gate"], "cube-structure")
        self.assertEqual(doc["plugin"], "hello-cube")
        self.assertEqual(doc["status"], "pass")
        self.assertEqual(doc["reasons"], [])
        self.assertIsInstance(doc["evidence"], dict)

    def test_gate_fails_on_missing_artifact(self):
        proc = self.run_tool(GATE, "--workspace", str(self.workspace))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["kind"], "img2.gate-verdict")
        self.assertEqual(doc["status"], "fail")
        self.assertTrue(doc["reasons"])

    def run_gate_runner(self):
        env = {**self.env, "PYTHONPATH": str(self.home / "harness")}
        return subprocess.run(
            [sys.executable, "-m", "img2_core.gate_runner",
             "--plugin-dir", str(PLUGIN_DIR), "--workspace", str(self.workspace)],
            capture_output=True, text=True, env=env, cwd=self.workspace,
        )

    def test_gate_runner_end_to_end_pass(self):
        self.emit()
        proc = self.run_gate_runner()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["kind"], "img2.gate-run")
        self.assertFalse(doc["stopped"])
        [result] = doc["results"]
        self.assertEqual(result["gate"], "cube-structure")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["envelope"]["plugin"], "hello-cube")

    def test_gate_runner_end_to_end_blocking_fail(self):
        proc = self.run_gate_runner()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertTrue(doc["stopped"])
        [result] = doc["results"]
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["exitCode"], 1)


if __name__ == "__main__":
    unittest.main()
