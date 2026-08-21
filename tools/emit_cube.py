import os, sys
root = os.environ.get("IMG2_HOME")
if root: sys.path.insert(0, os.path.join(root, "harness"))
else:
    try: import _img2_local; sys.path.insert(0, _img2_local.CORE)
    except ImportError: sys.exit("img2: core not linked - run `img2 sync`")
from img2_core import require_core_api
require_core_api(1)

import argparse
import hashlib
import json
from pathlib import Path

from img2_core import state as core_state
from img2_core.paths import resolve_workspace

PLUGIN_ID = "hello-cube"

TEMPLATE = """const geometry = new THREE.BoxGeometry({size}, {size}, {size});
const material = new THREE.MeshStandardMaterial({{ color: 0x{hex} }});
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);
"""


def derive(data):
    color_hex = hashlib.sha256(data).digest()[:3].hex()
    size = round(0.5 + (len(data) % 151) / 100, 2)
    return color_hex, size


def main(argv=None):
    parser = argparse.ArgumentParser(prog="emit_cube.py")
    parser.add_argument("--image", required=True)
    parser.add_argument("--workspace", default=None)
    args = parser.parse_args(argv)
    try:
        workspace = resolve_workspace(args.workspace)
    except ValueError as err:
        sys.exit("emit-cube: %s" % err)
    image = Path(args.image).expanduser()
    if not image.is_file():
        sys.exit("emit-cube: image not found: %s" % image)
    data = image.read_bytes()
    color_hex, size = derive(data)
    artifact = workspace / ".img2" / "artifacts" / PLUGIN_ID / "cube.js"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(TEMPLATE.format(size=size, hex=color_hex), encoding="utf-8")
    core_state.update_plugin_state(workspace, PLUGIN_ID, lambda entry: entry.update({
        "lastImage": str(image.resolve()),
        "colorHex": "#" + color_hex,
        "size": size,
    }))
    print(json.dumps({"artifact": str(artifact), "colorHex": "#" + color_hex, "size": size}))


if __name__ == "__main__":
    main()
