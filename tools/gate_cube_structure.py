import os, sys
root = os.environ.get("IMG2_HOME")
if root: sys.path.insert(0, os.path.join(root, "harness"))
else:
    try: import _img2_local; sys.path.insert(0, _img2_local.CORE)
    except ImportError: sys.exit("img2: core not linked - run `img2 sync`")
from img2_core import require_core_api
require_core_api(1)

import argparse
import json
import re

from img2_core.paths import resolve_workspace

GATE_ID = "cube-structure"
PLUGIN_ID = "hello-cube"
HEX_COLOR = re.compile(r"(?:0x|#)[0-9a-fA-F]{6}\b")


def emit(status, reasons, evidence):
    print(json.dumps({
        "kind": "img2.gate-verdict",
        "version": 1,
        "gate": GATE_ID,
        "plugin": PLUGIN_ID,
        "status": status,
        "reasons": reasons,
        "evidence": evidence,
    }))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gate_cube_structure.py")
    parser.add_argument("--workspace", default=None)
    args = parser.parse_args(argv)
    try:
        workspace = resolve_workspace(args.workspace)
    except ValueError as err:
        emit("error", [str(err)], {})
        return 2
    artifact = workspace / ".img2" / "artifacts" / PLUGIN_ID / "cube.js"
    evidence = {"artifact": str(artifact)}
    if not artifact.is_file():
        emit("fail", ["cube.js not found at %s" % artifact], evidence)
        return 1
    try:
        text = artifact.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        emit("error", ["cube.js could not be read: %s" % err], evidence)
        return 2
    evidence["bytes"] = len(text.encode("utf-8"))
    reasons = []
    if not text.strip():
        reasons.append("cube.js is empty")
    else:
        if "BoxGeometry" not in text:
            reasons.append("cube.js does not construct a BoxGeometry")
        match = HEX_COLOR.search(text)
        if match:
            evidence["colorHex"] = match.group(0)
        else:
            reasons.append("cube.js contains no 6-digit hex color literal")
    if reasons:
        emit("fail", reasons, evidence)
        return 1
    emit("pass", [], evidence)
    return 0


if __name__ == "__main__":
    sys.exit(main())
