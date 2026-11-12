"""A user plugin and its state remain visible after a fresh Python process."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "server"
PYTHON = sys.executable


def run(code: str, state: Path) -> str:
    env = os.environ.copy()
    env["MARGA_STATE_DIR"] = str(state)
    env["JAVIS_ENABLE_USER_PLUGINS"] = "true"
    env["PYTHONPATH"] = str(SERVER)
    p = subprocess.run([PYTHON, "-c", code], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=15)
    if p.returncode:
        raise AssertionError(p.stderr or p.stdout)
    return p.stdout.strip()


with tempfile.TemporaryDirectory(prefix="marga-plugin-restart-") as td:
    state = Path(td)
    first = run(
        """
import json
from pathlib import Path
import plugins_host

root = plugins_host.GLOBAL_DIR / "restart-demo"
root.mkdir(parents=True)
(root / "plugin.yaml").write_text(
    "name: Restart Demo\\nslug: restart-demo\\nversion: 1.0\\n"
    "description: harmless persistence fixture\\nenabled: true\\n",
    encoding="utf-8")
(root / "plugin.py").write_text("def register(ctx): pass\\n", encoding="utf-8")
off = plugins_host.GLOBAL_DIR / "restart-off"
off.mkdir(parents=True)
(off / "plugin.yaml").write_text(
    "name: Restart Off\\nslug: restart-off\\nversion: 1.0\\n"
    "description: disabled persistence fixture\\nenabled: false\\n",
    encoding="utf-8")
(off / "plugin.py").write_text("def register(ctx): pass\\n", encoding="utf-8")
data = plugins_host.STATE_DIR / "plugin-data" / "restart-demo"
data.mkdir(parents=True)
(data / "config.json").write_text(json.dumps({"enabled_by_owner": True}), encoding="utf-8")
row = next(x for x in plugins_host.describe(None) if x["slug"] == "restart-demo")
off_row = next(x for x in plugins_host.describe(None) if x["slug"] == "restart-off")
assert row["enabled"] is True and row["loaded"] is True, row
assert off_row["enabled"] is False and off_row["loaded"] is False, off_row
print(row["source"])
""",
        state,
    )
    assert first == "user"
    second = run(
        """
import json
import plugins_host

row = next(x for x in plugins_host.describe(None) if x["slug"] == "restart-demo")
off_row = next(x for x in plugins_host.describe(None) if x["slug"] == "restart-off")
cfg = plugins_host.STATE_DIR / "plugin-data" / "restart-demo" / "config.json"
assert row["enabled"] is True and row["loaded"] is True, row
assert off_row["enabled"] is False and off_row["loaded"] is False, off_row
assert json.loads(cfg.read_text(encoding="utf-8"))["enabled_by_owner"] is True
print(row["slug"])
""",
        state,
    )
    assert second == "restart-demo"

print("OK - plugin files, enabled state, discovery, and plugin data survive restart")
