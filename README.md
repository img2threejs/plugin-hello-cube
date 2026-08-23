# plugin-hello-cube

The **reference img2 plugin** — image → deterministic Three.js cube. It exists to
exercise every surface of the plugin contract with zero domain risk, and to be copied:
starting a new plugin means cloning this repo and replacing the cube logic.

File map (each maps to a section of the harness's `docs/PLUGIN_CONTRACT.md`):

| File | Contract | What it demonstrates |
|------|----------|----------------------|
| `plugin.json` | §5 | Manifest: capability edge, honest `requires` |
| `SKILL.md` | §8 | Trigger-style description; commands run with `--workspace .` |
| `tools/emit_cube.py` | §8, §11 | Verbatim bootstrap stanza; state via `update_plugin_state`; artifacts under `<workspace>/.img2/artifacts/` |
| `tools/gate_cube_structure.py` | §9 | Verdict envelope; exit codes agreeing with status |
| `gates.json`, `steps.json` | §9, §10 | Declared rows with `{workspace}`/`{plugin_dir}` tokens |
| `tests/` | — | Temp `$IMG2_HOME` + harness symlink pattern; gate pass AND fail; end-to-end through `img2_core.gate_runner` |

```bash
img2 add img2threejs/plugin-hello-cube      # install
python3 -m unittest discover -s tests       # test (needs a sibling/linked harness checkout)
```

Full walkthrough: `docs/WRITING_A_PLUGIN.md` in the [img2 harness](https://github.com/img2threejs/img2).
