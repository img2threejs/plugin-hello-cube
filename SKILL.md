---
name: img2-hello-cube
description: "Generates a deterministic Three.js cube from any input image. Use when the user wants a quick image-to-Three.js smoke test."
---

# img2 hello-cube

Turns any input image into a deterministic Three.js cube snippet. The cube's color comes
from the image's SHA-256 hash and its edge size from the image's byte length, so the same
image always produces the same code.

## Usage

Run both commands from the user's project directory and pass that directory as
`--workspace`. Never point `--workspace` at this skill directory or any checkout.

1. Emit the cube from the user's image:

   ```bash
   python3 "$SKILL_DIR/tools/emit_cube.py" --image <path/to/image> --workspace "$PWD"
   ```

2. Gate the artifact before claiming success:

   ```bash
   python3 "$SKILL_DIR/tools/gate_cube_structure.py" --workspace "$PWD"
   ```

`$SKILL_DIR` is the directory containing this SKILL.md. The generated snippet lands at
`<workspace>/.img2/artifacts/hello-cube/cube.js`; it assumes `THREE` and a `scene` are in
scope. The gate prints one `img2.gate-verdict` JSON envelope and exits 0 (pass), 1 (fail),
or 2 (could not evaluate). Only report the cube as delivered when the gate passes.
